"""
infra/auditing/auditors.py

INSTITUTIONAL AUDITORS — Specialized model validation.
======================================================
Architecture: SOLID - Each auditor manages pillars specific to its valuation logic.
This module provides the granular test implementation for the Audit Engine.

Style: Numpy docstrings
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import numpy as np

from src.models import (
    ValuationResult, AuditPillar, AuditPillarScore, AuditStep, AuditSeverity, CompanyFinancials
)
from src.config import AuditThresholds
from src.i18n import StrategyFormulas

logger = logging.getLogger(__name__)


# ==============================================================================
# AUDIT THRESHOLDS EXTENSIONS
# ==============================================================================

class ExtendedAuditThresholds:
    """
    Extended thresholds for comprehensive audit coverage.

    These complement the base AuditThresholds with model-specific limits.
    """

    # Data Freshness
    DATA_FRESHNESS_MAX_MONTHS: int = 6
    PROVIDER_CONFIDENCE_MIN: float = 0.7

    # DCF Model
    REINVESTMENT_RATIO_MIN: float = 1.0
    GROWTH_PHASE1_TO_GN_MAX_RATIO: float = 3.0
    GROWTH_TO_CAGR_MAX_RATIO: float = 2.0

    # DDM Model
    PAYOUT_RATIO_WARNING: float = 0.90
    PAYOUT_RATIO_CRITICAL: float = 1.0

    # RIM Model (Banks)
    OMEGA_MIN: float = 0.1
    OMEGA_MAX: float = 0.9
    LTD_RATIO_MAX: float = 1.2  # Loans to Deposits

    # Graham Model
    GRAHAM_YIELD_GAP_MIN: float = 0.02  # 2% minimum spread
    GRAHAM_MULTIPLIER_MAX: float = 22.5  # PE × PB
    GRAHAM_GROWTH_MAX: float = 0.10  # 10% max for defensive

    # Multiples Model
    MULTIPLES_CV_MAX: float = 0.50  # Coefficient of Variation
    MULTIPLES_PE_OUTLIER: float = 100.0
    MULTIPLES_COHORT_MIN: int = 5


# ==============================================================================
# 1. INTERFACES AND BASE CLASS
# ==============================================================================

class IValuationAuditor(ABC):
    """
    Interface defining the contract for valuation-specific auditing.

    Each auditor implementation must provide pillar-based scoring
    and declare its maximum test coverage for audit completeness metrics.
    """

    @abstractmethod
    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        """
        Calculates score and diagnostics for each audit pillar.

        Parameters
        ----------
        result : ValuationResult
            The valuation output to audit.

        Returns
        -------
        Dict[AuditPillar, AuditPillarScore]
            Mapping of pillars to their computed scores and check counts.
        """
        pass

    @abstractmethod
    def get_max_potential_checks(self) -> int:
        """
        Returns the total number of tests this auditor can perform.

        Returns
        -------
        int
            Maximum number of audit checks for coverage calculation.
        """
        pass


class BaseAuditor(IValuationAuditor, ABC):
    """
    Base Auditor providing common mechanics for test registration
    and cross-model data validation.

    This class implements transversal audit checks that apply to all
    valuation models regardless of methodology.

    Attributes
    ----------
    _audit_steps : List[AuditStep]
        Internal registry for individual audit steps.
    """

    def __init__(self):
        """Initializes the auditor with an empty audit step registry."""
        self._audit_steps: List[AuditStep] = []

    def _add_audit_step(
        self,
        key: str,
        value: Any,
        threshold: Any,
        severity: AuditSeverity,
        condition: Any,
        penalty: float = 0.0,
        formula: Optional[str] = None
    ) -> float:
        """
        Registers a control point and returns the penalty if the check fails.

        Parameters
        ----------
        key : str
            Unique identifier for the audit step (used for i18n lookup).
        value : Any
            The actual value being tested.
        threshold : Any
            The reference threshold for comparison.
        severity : AuditSeverity
            Criticality level (CRITICAL, WARNING, INFO).
        condition : Any
            True if the test passes, False otherwise.
        penalty : float, optional
            Points to deduct from the pillar score if test fails.
        formula : str, optional
            LaTeX formula describing the audit rule.

        Returns
        -------
        float
            The penalty amount (0.0 if passed, penalty value if failed).
        """
        verdict = bool(condition)
        self._audit_steps.append(AuditStep(
            step_id=len(self._audit_steps) + 1,
            step_key=key,
            indicator_value=str(value),
            threshold_value=str(threshold),
            severity=severity,
            verdict=verdict,
            evidence=f"{value} vs {threshold}" if threshold else str(value),
            rule_formula=formula or StrategyFormulas.NA
        ))
        return float(penalty) if not verdict else 0.0

    # ══════════════════════════════════════════════════════════════════════════
    # TRANSVERSAL AUDITS (Apply to all models)
    # ══════════════════════════════════════════════════════════════════════════

    def _audit_data_confidence(self, result: ValuationResult) -> Tuple[float, int]:
        """
        Transversal analysis of source data quality.

        Tests performed:
        1. Beta validity (systemic risk within normal bounds)
        2. Data freshness (financial statements age)
        3. Provider confidence score

        Parameters
        ----------
        result : ValuationResult
            The valuation result containing financials and metadata.

        Returns
        -------
        Tuple[float, int]
            (pillar_score, number_of_checks_performed)
        """
        score = 100.0
        f = result.financials
        initial_count = len(self._audit_steps)

        # ─────────────────────────────────────────────────────────────────────
        # TEST 1: Beta Validity
        # ─────────────────────────────────────────────────────────────────────
        score -= self._add_audit_step(
            key="AUDIT_DATA_BETA",
            value=f.beta,
            threshold=f"{AuditThresholds.BETA_MIN}-{AuditThresholds.BETA_MAX}",
            severity=AuditSeverity.WARNING,
            condition=(
                f.beta is not None and
                AuditThresholds.BETA_MIN <= f.beta <= AuditThresholds.BETA_MAX
            ),
            penalty=15.0,
            formula=rf"{AuditThresholds.BETA_MIN} \leq \beta \leq {AuditThresholds.BETA_MAX}"
        )

        # ─────────────────────────────────────────────────────────────────────
        # TEST 2: Data Freshness
        # ─────────────────────────────────────────────────────────────────────
        data_age_months = self._calculate_data_age_months(f)
        freshness_threshold = ExtendedAuditThresholds.DATA_FRESHNESS_MAX_MONTHS

        score -= self._add_audit_step(
            key="AUDIT_DATA_FRESHNESS",
            value=f"{data_age_months} mois",
            threshold=f"≤ {freshness_threshold} mois",
            severity=AuditSeverity.WARNING,
            condition=(data_age_months <= freshness_threshold),
            penalty=10.0,
            formula=rf"Age\_donnees \leq {freshness_threshold}\ mois"
        )

        # ─────────────────────────────────────────────────────────────────────
        # TEST 3: Provider Confidence Score
        # ─────────────────────────────────────────────────────────────────────
        confidence_score = getattr(f, 'confidence_score', 1.0) or 1.0
        confidence_min = ExtendedAuditThresholds.PROVIDER_CONFIDENCE_MIN

        score -= self._add_audit_step(
            key="AUDIT_PROVIDER_CONFIDENCE",
            value=f"{confidence_score:.0%}",
            threshold=f"≥ {confidence_min:.0%}",
            severity=AuditSeverity.WARNING,
            condition=(confidence_score >= confidence_min),
            penalty=10.0,
            formula=rf"Confidence\_Score \geq {confidence_min:.0%}"
        )

        checks_performed = len(self._audit_steps) - initial_count
        return max(0.0, score), checks_performed

    @staticmethod
    def _calculate_data_age_months(financials) -> int:
        """
        Calculates the age of financial data in months.

        Parameters
        ----------
        financials : CompanyFinancials
            Financial data object with optional last_updated attribute.

        Returns
        -------
        int
            Number of months since last data update (0 if unknown).
        """
        last_updated = getattr(financials, 'last_updated', None)
        if last_updated is None:
            return 0  # Assume fresh if unknown

        try:
            if isinstance(last_updated, str):
                last_updated = datetime.fromisoformat(last_updated)
            delta = datetime.now() - last_updated
            return max(0, delta.days // 30)
        except (ValueError, TypeError):
            return 0


# ==============================================================================
# 2. DCF AUDITOR — Cash Flow Models (FCFF, FCFE, DDM)
# ==============================================================================

class DCFAuditor(BaseAuditor):
    """
    Auditor for DCF-based models (FCFF, FCFE, DDM).

    Focus areas:
    - Mathematical stability (WACC-g spread)
    - Solvency (Interest Coverage Ratio)
    - Growth coherence (Phase 1 vs Terminal)
    - Reinvestment adequacy (CapEx vs Depreciation)
    """

    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        """
        Audits DCF-specific pillars: Data Confidence and Model Risk.

        Parameters
        ----------
        result : ValuationResult
            DCF valuation output to audit.

        Returns
        -------
        Dict[AuditPillar, AuditPillarScore]
            Scores for DATA_CONFIDENCE and MODEL_RISK pillars.
        """
        score_data, count_data = self._audit_data_confidence(result)
        score_model, count_model = self._audit_model_risk(result)

        return {
            AuditPillar.DATA_CONFIDENCE: AuditPillarScore(
                pillar=AuditPillar.DATA_CONFIDENCE,
                score=score_data,
                check_count=count_data
            ),
            AuditPillar.MODEL_RISK: AuditPillarScore(
                pillar=AuditPillar.MODEL_RISK,
                score=score_model,
                check_count=count_model
            )
        }

    def _audit_model_risk(self, result: ValuationResult) -> Tuple[float, int]:
        """
        Structural analysis for DCF models.

        Tests performed:
        1. Solvency (ICR - Interest Coverage Ratio)
        2. WACC-g Spread (Mathematical stability)
        3. Growth Coherence (Phase 1 vs Terminal)
        4. Reinvestment Ratio (CapEx sustainability)

        Parameters
        ----------
        result : ValuationResult
            DCF valuation result to audit.

        Returns
        -------
        Tuple[float, int]
            (pillar_score, number_of_checks_performed)
        """
        score = 100.0
        p = result.params
        f = result.financials
        initial_count = len(self._audit_steps)

        # ─────────────────────────────────────────────────────────────────────
        # TEST 1: Solvency (Interest Coverage Ratio)
        # ─────────────────────────────────────────────────────────────────────
        icr = self._calculate_icr(f)
        icr_threshold = AuditThresholds.ICR_MIN

        score -= self._add_audit_step(
            key="AUDIT_SOLVENCY_ICR",
            value=f"{icr:.2f}x",
            threshold=f"≥ {icr_threshold}x",
            severity=AuditSeverity.WARNING,
            condition=(icr >= icr_threshold),
            penalty=20.0,
            formula=rf"\frac{{EBIT}}{{Int.Exp}} \geq {icr_threshold}"
        )

        # ─────────────────────────────────────────────────────────────────────
        # TEST 2: WACC-g Spread (Mathematical Stability)
        # ─────────────────────────────────────────────────────────────────────
        wacc = getattr(result, "wacc", None)
        gn = getattr(p.growth, 'perpetual_growth_rate', None)

        if wacc is not None and gn is not None:
            spread = wacc - gn
            spread_min = AuditThresholds.WACC_G_SPREAD_MIN

            score -= self._add_audit_step(
                key="AUDIT_WACC_G_SPREAD",
                value=f"{spread:.2%}",
                threshold=f"≥ {spread_min:.2%}",
                severity=AuditSeverity.CRITICAL,
                condition=(spread >= spread_min),
                penalty=50.0,
                formula=rf"WACC - g_n \geq {spread_min:.2%}"
            )

        # ─────────────────────────────────────────────────────────────────────
        # TEST 3: Growth Coherence (Phase 1 vs Terminal)
        # ─────────────────────────────────────────────────────────────────────
        g_phase1 = getattr(p.growth, 'fcf_growth_rate', None)

        if g_phase1 is not None and gn is not None and gn > 0:
            growth_ratio = g_phase1 / gn
            max_ratio = ExtendedAuditThresholds.GROWTH_PHASE1_TO_GN_MAX_RATIO

            score -= self._add_audit_step(
                key="AUDIT_GROWTH_COHERENCE",
                value=f"{growth_ratio:.1f}x",
                threshold=f"≤ {max_ratio:.1f}x",
                severity=AuditSeverity.WARNING,
                condition=(growth_ratio <= max_ratio),
                penalty=15.0,
                formula=rf"\frac{{g_{{phase1}}}}{{g_n}} \leq {max_ratio}"
            )

        # ─────────────────────────────────────────────────────────────────────
        # TEST 4: Reinvestment Ratio (CapEx Sustainability)
        # ─────────────────────────────────────────────────────────────────────
        reinvestment_ratio = self._calculate_reinvestment_ratio(f)
        reinv_min = ExtendedAuditThresholds.REINVESTMENT_RATIO_MIN

        if reinvestment_ratio is not None:
            score -= self._add_audit_step(
                key="AUDIT_REINVESTMENT_RATIO",
                value=f"{reinvestment_ratio:.0%}",
                threshold=f"≥ {reinv_min:.0%}",
                severity=AuditSeverity.WARNING,
                condition=(reinvestment_ratio >= reinv_min),
                penalty=15.0,
                formula=rf"\frac{{CapEx}}{{D\&A}} \geq {reinv_min:.0%}"
            )

        checks_performed = len(self._audit_steps) - initial_count
        return max(0.0, score), checks_performed

    @staticmethod
    def _calculate_icr(financials) -> float:
        """
        Calculates Interest Coverage Ratio safely.
        """
        # Récupération sécurisée avec valeur par défaut 0
        ebit_val = getattr(financials, 'ebit_ttm', 0.0)
        interest_val = getattr(financials, 'interest_expense', 0.0)

        # Conversion forcée en float pour le calcul
        ebit = float(ebit_val) if ebit_val is not None else 0.0
        interest = float(interest_val) if interest_val is not None else 0.0

        # Protection contre la division par zéro (Dette nulle = Couverture infinie)
        if interest == 0.0:
            return 100.0

        # Retourne un float pur pour satisfaire le linter
        return float(abs(ebit / interest))

    @staticmethod
    def _calculate_reinvestment_ratio(financials: CompanyFinancials) -> Optional[float]:
        """
        Calculates CapEx to Depreciation ratio.

        Parameters
        ----------
        financials : CompanyFinancials
            Financial data with capex and depreciation.

        Returns
        -------
        Optional[float]
            Ratio value, or None if depreciation is zero/missing.
        """
        capex = abs(getattr(financials, 'capex', 0) or 0)
        depreciation = abs(getattr(financials, 'depreciation', 0) or 0)

        if depreciation == 0:
            return None

        return capex / depreciation

    def get_max_potential_checks(self) -> int:
        """Returns maximum audit checks for DCF models."""
        # Base: 3 (Beta, Freshness, Provider) + Model: 4 (ICR, WACC-g, Growth, Reinvest)
        return 7


# ==============================================================================
# 3. DDM AUDITOR — Dividend Discount Model
# ==============================================================================

class DDMAuditor(DCFAuditor):
    """
    Specialized auditor for Dividend Discount Models.

    Extends DCF auditor with dividend sustainability checks.
    """

    def _audit_model_risk(self, result: ValuationResult) -> Tuple[float, int]:
        """
        Audits DDM-specific model risks including dividend sustainability.

        Parameters
        ----------
        result : ValuationResult
            DDM valuation result to audit.

        Returns
        -------
        Tuple[float, int]
            (pillar_score, number_of_checks_performed)
        """
        # First, run base DCF audits
        score, count = super()._audit_model_risk(result)
        f = result.financials
        initial_count = len(self._audit_steps)

        # ─────────────────────────────────────────────────────────────────────
        # TEST: Dividend Sustainability (Payout Ratio)
        # ─────────────────────────────────────────────────────────────────────
        payout_ratio = self._calculate_payout_ratio(f)

        if payout_ratio is not None:
            # Warning level
            payout_warning = ExtendedAuditThresholds.PAYOUT_RATIO_WARNING
            payout_critical = ExtendedAuditThresholds.PAYOUT_RATIO_CRITICAL

            if payout_ratio >= payout_critical:
                severity = AuditSeverity.CRITICAL
                penalty = 30.0
            elif payout_ratio >= payout_warning:
                severity = AuditSeverity.WARNING
                penalty = 15.0
            else:
                severity = AuditSeverity.INFO
                penalty = 0.0

            score -= self._add_audit_step(
                key="AUDIT_DDM_PAYOUT",
                value=f"{payout_ratio:.0%}",
                threshold=f"< {payout_warning:.0%}",
                severity=severity,
                condition=(payout_ratio < payout_warning),
                penalty=penalty,
                formula=rf"Payout\ Ratio < {payout_warning:.0%}"
            )

        additional_checks = len(self._audit_steps) - initial_count
        return max(0.0, score), count + additional_checks

    @staticmethod
    def _calculate_payout_ratio(financials) -> Optional[float]:
        """
        Calculates dividend payout ratio.

        Parameters
        ----------
        financials : CompanyFinancials
            Financial data with dividends and net income.

        Returns
        -------
        Optional[float]
            Payout ratio, or None if net income is zero/missing.
        """
        dividends = getattr(financials, 'dividends_paid', None)
        net_income = getattr(financials, 'net_income', None)

        if not net_income or net_income == 0:
            return None

        if not dividends:
            return 0.0

        return abs(dividends / net_income)

    def get_max_potential_checks(self) -> int:
        """Returns maximum audit checks for DDM model."""
        return super().get_max_potential_checks() + 1  # +1 for payout ratio


# ==============================================================================
# 4. RIM AUDITOR — Residual Income Model (Banks)
# ==============================================================================

class RIMAuditor(BaseAuditor):
    """
    Specialized auditor for Residual Income Models (Banks).

    Focus areas:
    - Value creation (ROE vs Ke spread)
    - Persistence factor (Omega bounds)
    - Asset quality indicators
    """

    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        """
        Audits RIM-specific pillars.

        Parameters
        ----------
        result : ValuationResult
            RIM valuation output to audit.

        Returns
        -------
        Dict[AuditPillar, AuditPillarScore]
            Scores for DATA_CONFIDENCE and MODEL_RISK pillars.
        """
        score_data, count_data = self._audit_data_confidence(result)
        score_model, count_model = self._audit_rim_model_risk(result)

        return {
            AuditPillar.DATA_CONFIDENCE: AuditPillarScore(
                pillar=AuditPillar.DATA_CONFIDENCE,
                score=score_data,
                check_count=count_data
            ),
            AuditPillar.MODEL_RISK: AuditPillarScore(
                pillar=AuditPillar.MODEL_RISK,
                score=score_model,
                check_count=count_model
            )
        }

    def _audit_rim_model_risk(self, result: ValuationResult) -> Tuple[float, int]:
        """
        RIM-specific model risk analysis.

        Tests performed:
        1. ROE-Ke Spread (Value creation)
        2. Omega Bounds (Persistence factor)
        3. Asset Quality (NI volatility or LTD ratio)

        Parameters
        ----------
        result : ValuationResult
            RIM valuation result to audit.

        Returns
        -------
        Tuple[float, int]
            (pillar_score, number_of_checks_performed)
        """
        score = 100.0
        p = result.params
        f = result.financials
        initial_count = len(self._audit_steps)

        # ─────────────────────────────────────────────────────────────────────
        # TEST 1: ROE-Ke Spread (Value Creation)
        # ─────────────────────────────────────────────────────────────────────
        roe = self._calculate_roe(f)
        ke = getattr(result, "cost_of_equity", None) or getattr(result, "ke", None)

        if roe is not None and ke is not None:
            spread = roe - ke

            # Negative spread = value destruction
            if spread < 0:
                severity = AuditSeverity.CRITICAL
                penalty = 40.0
            elif spread < 0.01:  # Less than 1% spread
                severity = AuditSeverity.WARNING
                penalty = 20.0
            else:
                severity = AuditSeverity.INFO
                penalty = 0.0

            score -= self._add_audit_step(
                key="AUDIT_RIM_ROE_KE_SPREAD",
                value=f"{spread:.2%}",
                threshold="> 0%",
                severity=severity,
                condition=(spread > 0),
                penalty=penalty,
                formula=r"ROE - K_e > 0"
            )

        # ─────────────────────────────────────────────────────────────────────
        # TEST 2: Omega Bounds (Persistence Factor)
        # ─────────────────────────────────────────────────────────────────────
        omega = getattr(p.terminal, 'exit_multiple_value', None) if hasattr(p, 'terminal') else None
        # Also check in growth parameters
        if omega is None:
            omega = getattr(p, 'exit_multiple_value', None)

        if omega is not None:
            omega_min = ExtendedAuditThresholds.OMEGA_MIN
            omega_max = ExtendedAuditThresholds.OMEGA_MAX

            is_valid = omega_min <= omega <= omega_max

            if omega > omega_max:
                severity = AuditSeverity.CRITICAL
                penalty = 35.0
            elif omega < omega_min:
                severity = AuditSeverity.WARNING
                penalty = 20.0
            else:
                severity = AuditSeverity.INFO
                penalty = 0.0

            score -= self._add_audit_step(
                key="AUDIT_RIM_OMEGA_BOUNDS",
                value=f"{omega:.2f}",
                threshold=f"[{omega_min}, {omega_max}]",
                severity=severity,
                condition=is_valid,
                penalty=penalty,
                formula=rf"{omega_min} \leq \omega \leq {omega_max}"
            )

        # ─────────────────────────────────────────────────────────────────────
        # TEST 3: Asset Quality (Loans to Deposits or NI Volatility)
        # ──────────��──────────────────────────────────────────────────────────
        ltd_ratio = self._calculate_ltd_ratio(f)

        if ltd_ratio is not None:
            ltd_max = ExtendedAuditThresholds.LTD_RATIO_MAX

            score -= self._add_audit_step(
                key="AUDIT_RIM_ASSET_QUALITY",
                value=f"{ltd_ratio:.0%}",
                threshold=f"≤ {ltd_max:.0%}",
                severity=AuditSeverity.WARNING,
                condition=(ltd_ratio <= ltd_max),
                penalty=15.0,
                formula=rf"\frac{{Loans}}{{Deposits}} \leq {ltd_max:.0%}"
            )

        checks_performed = len(self._audit_steps) - initial_count
        return max(0.0, score), checks_performed

    @staticmethod
    def _calculate_roe(financials) -> Optional[float]:
        """
        Calculates Return on Equity.

        Parameters
        ----------
        financials : CompanyFinancials
            Financial data with net income and book value.

        Returns
        -------
        Optional[float]
            ROE value, or None if book value is zero/missing.
        """
        net_income = getattr(financials, 'net_income', None)
        book_value = getattr(financials, 'book_value', None)

        if not book_value or book_value == 0:
            return None

        if not net_income:
            return 0.0

        return net_income / book_value

    @staticmethod
    def _calculate_ltd_ratio(financials) -> Optional[float]:
        """
        Calculates Loans to Deposits ratio (bank-specific).

        Parameters
        ----------
        financials : CompanyFinancials
            Financial data with loans and deposits.

        Returns
        -------
        Optional[float]
            LTD ratio, or None if not available.
        """
        loans = getattr(financials, 'total_loans', None)
        deposits = getattr(financials, 'total_deposits', None)

        if not deposits or deposits == 0:
            return None

        if not loans:
            return 0.0

        return loans / deposits

    def get_max_potential_checks(self) -> int:
        """Returns maximum audit checks for RIM model."""
        # Base: 3 (Beta, Freshness, Provider) + RIM: 3 (ROE-Ke, Omega, LTD)
        return 6


# ==============================================================================
# 5. GRAHAM AUDITOR — Defensive Value
# ==============================================================================

class GrahamAuditor(BaseAuditor):
    """
    Specialized auditor for Graham's Defensive Value.

    Focus areas:
    - Margin of safety (Yield gap)
    - Graham multiplier rule (PE × PB)
    - Growth prudence (Conservative projections)
    """

    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        """
        Audits Graham-specific pillars with focus on margin of safety.

        Parameters
        ----------
        result : ValuationResult
            Graham valuation output to audit.

        Returns
        -------
        Dict[AuditPillar, AuditPillarScore]
            Scores for DATA_CONFIDENCE and MODEL_RISK pillars.
        """
        # Graham uses simplified data confidence (no Beta dependency)
        score_data, count_data = self._audit_graham_data_confidence(result)
        score_model, count_model = self._audit_graham_model_risk(result)

        return {
            AuditPillar.DATA_CONFIDENCE: AuditPillarScore(
                pillar=AuditPillar.DATA_CONFIDENCE,
                score=score_data,
                check_count=count_data
            ),
            AuditPillar.MODEL_RISK: AuditPillarScore(
                pillar=AuditPillar.MODEL_RISK,
                score=score_model,
                check_count=count_model
            )
        }

    def _audit_graham_data_confidence(self, result: ValuationResult) -> Tuple[float, int]:
        """
        Simplified data confidence audit for Graham model.

        Graham model does not rely on Beta or WACC, so we only check
        data freshness and provider confidence.

        Parameters
        ----------
        result : ValuationResult
            Graham valuation result to audit.

        Returns
        -------
        Tuple[float, int]
            (pillar_score, number_of_checks_performed)
        """
        score = 100.0
        f = result.financials
        initial_count = len(self._audit_steps)

        # Data Freshness
        data_age_months = self._calculate_data_age_months(f)
        freshness_threshold = ExtendedAuditThresholds.DATA_FRESHNESS_MAX_MONTHS

        score -= self._add_audit_step(
            key="AUDIT_DATA_FRESHNESS",
            value=f"{data_age_months} mois",
            threshold=f"≤ {freshness_threshold} mois",
            severity=AuditSeverity.WARNING,
            condition=(data_age_months <= freshness_threshold),
            penalty=10.0,
            formula=rf"Age\_donnees \leq {freshness_threshold}\ mois"
        )

        # Provider Confidence
        confidence_score = getattr(f, 'confidence_score', 1.0) or 1.0
        confidence_min = ExtendedAuditThresholds.PROVIDER_CONFIDENCE_MIN

        score -= self._add_audit_step(
            key="AUDIT_PROVIDER_CONFIDENCE",
            value=f"{confidence_score:.0%}",
            threshold=f"≥ {confidence_min:.0%}",
            severity=AuditSeverity.WARNING,
            condition=(confidence_score >= confidence_min),
            penalty=10.0,
            formula=rf"Confidence\_Score \geq {confidence_min:.0%}"
        )

        checks_performed = len(self._audit_steps) - initial_count
        return max(0.0, score), checks_performed

    def _audit_graham_model_risk(self, result: ValuationResult) -> Tuple[float, int]:
        """
        Graham-specific model risk analysis.

        Tests performed:
        1. Yield Gap (Earnings yield vs AAA bonds)
        2. Graham Multiplier (PE × PB ≤ 22.5)
        3. Growth Prudence (g ≤ 10%)

        Parameters
        ----------
        result : ValuationResult
            Graham valuation result to audit.

        Returns
        -------
        Tuple[float, int]
            (pillar_score, number_of_checks_performed)
        """
        score = 100.0
        p = result.params
        f = result.financials
        initial_count = len(self._audit_steps)

        # ─────────────────────────────────────────────────────────────────────
        # TEST 1: Yield Gap (Margin of Safety)
        # ─────────────────────────────────────────────────────────────────────
        pe_ratio = getattr(f, 'pe_ratio', None)
        aaa_yield = getattr(p, 'corporate_aaa_yield', None)

        if pe_ratio is not None and pe_ratio > 0 and aaa_yield is not None:
            earnings_yield = 1.0 / pe_ratio
            yield_gap = earnings_yield - aaa_yield
            gap_min = ExtendedAuditThresholds.GRAHAM_YIELD_GAP_MIN

            score -= self._add_audit_step(
                key="AUDIT_GRAHAM_YIELD_GAP",
                value=f"{yield_gap:.2%}",
                threshold=f"≥ {gap_min:.2%}",
                severity=AuditSeverity.WARNING,
                condition=(yield_gap >= gap_min),
                penalty=20.0,
                formula=rf"\frac{{1}}{{PE}} - Y_{{AAA}} \geq {gap_min:.2%}"
            )

        # ─────────────────────────────────────────────────────────────────────
        # TEST 2: Graham Multiplier Rule (PE × PB ≤ 22.5)
        # ─────────────────────────────────────────────────────────────────────
        pb_ratio = getattr(f, 'pb_ratio', None)

        if pe_ratio is not None and pb_ratio is not None:
            graham_mult = pe_ratio * pb_ratio
            mult_max = ExtendedAuditThresholds.GRAHAM_MULTIPLIER_MAX

            score -= self._add_audit_step(
                key="AUDIT_GRAHAM_MULTIPLIER",
                value=f"{graham_mult:.1f}",
                threshold=f"≤ {mult_max}",
                severity=AuditSeverity.WARNING,
                condition=(graham_mult <= mult_max),
                penalty=25.0,
                formula=rf"PE \times PB \leq {mult_max}"
            )

        # ─────────────────────────────────────────────────────────────────────
        # TEST 3: Growth Prudence (Conservative Projections)
        # ─────────────────────────────────────────────────────────────────────
        g_rate = getattr(p.growth, 'fcf_growth_rate', None) if hasattr(p, 'growth') else None

        if g_rate is not None:
            g_max = ExtendedAuditThresholds.GRAHAM_GROWTH_MAX

            score -= self._add_audit_step(
                key="AUDIT_GRAHAM_GROWTH_PRUDENCE",
                value=f"{g_rate:.1%}",
                threshold=f"≤ {g_max:.0%}",
                severity=AuditSeverity.WARNING,
                condition=(g_rate <= g_max),
                penalty=15.0,
                formula=rf"g \leq {g_max:.0%}"
            )

        checks_performed = len(self._audit_steps) - initial_count
        return max(0.0, score), checks_performed

    def get_max_potential_checks(self) -> int:
        """Returns maximum audit checks for Graham model."""
        # Data: 2 (Freshness, Provider) + Model: 3 (Yield Gap, Multiplier, Growth)
        return 5


# ==============================================================================
# 6. MULTIPLES AUDITOR — Relative Valuation
# ==============================================================================

class MultiplesAuditor(BaseAuditor):
    """
    Auditor for relative valuation triangulation.

    Focus areas:
    - Cohort quality (Dispersion / CV)
    - Outlier detection (Extreme multiples)
    - Sample size adequacy
    """

    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        """
        Audits multiples-specific pillars.

        Parameters
        ----------
        result : ValuationResult
            Multiples valuation output to audit.

        Returns
        -------
        Dict[AuditPillar, AuditPillarScore]
            Scores for DATA_CONFIDENCE and MODEL_RISK pillars.
        """
        score_data, count_data = self._audit_data_confidence(result)
        score_model, count_model = self._audit_multiples_risk(result)

        return {
            AuditPillar.DATA_CONFIDENCE: AuditPillarScore(
                pillar=AuditPillar.DATA_CONFIDENCE,
                score=score_data,
                check_count=count_data
            ),
            AuditPillar.MODEL_RISK: AuditPillarScore(
                pillar=AuditPillar.MODEL_RISK,
                score=score_model,
                check_count=count_model
            )
        }

    def _audit_multiples_risk(self, result: ValuationResult) -> Tuple[float, int]:
        """
        Multiples-specific model risk analysis.

        Tests performed:
        1. Cohort Dispersion (Coefficient of Variation)
        2. Outlier Detection (Extreme PE values)
        3. Cohort Size Adequacy

        Parameters
        ----------
        result : ValuationResult
            Multiples valuation result to audit.

        Returns
        -------
        Tuple[float, int]
            (pillar_score, number_of_checks_performed)
        """
        score = 100.0
        initial_count = len(self._audit_steps)

        # Get peer multiples data from result
        triangulation = getattr(result, 'multiples_triangulation', None)
        peers_data = getattr(triangulation, 'peer_multiples', []) if triangulation else []

        # ─────────────────────────────────────────────────────────────────────
        # TEST 1: Cohort Size Adequacy
        # ─────────────────────────────────────────────────────────────────────
        cohort_size = len(peers_data)
        min_cohort = ExtendedAuditThresholds.MULTIPLES_COHORT_MIN

        score -= self._add_audit_step(
            key="AUDIT_MULTIPLES_COHORT_SIZE",
            value=str(cohort_size),
            threshold=f"≥ {min_cohort}",
            severity=AuditSeverity.WARNING,
            condition=(cohort_size >= min_cohort),
            penalty=15.0,
            formula=rf"N_{{peers}} \geq {min_cohort}"
        )

        # Only run further tests if we have peers
        if peers_data:
            # Extract PE ratios from peers
            pe_values = self._extract_pe_values(peers_data)

            if pe_values:
                # ─────────────────────────────────────────────────────────────
                # TEST 2: Cohort Dispersion (CV)
                # ─────────────────────────────────────────────────────────────
                cv = self._calculate_cv(pe_values)
                cv_max = ExtendedAuditThresholds.MULTIPLES_CV_MAX

                if cv is not None:
                    score -= self._add_audit_step(
                        key="AUDIT_MULTIPLES_DISPERSION",
                        value=f"{cv:.0%}",
                        threshold=f"≤ {cv_max:.0%}",
                        severity=AuditSeverity.WARNING,
                        condition=(cv <= cv_max),
                        penalty=20.0,
                        formula=rf"CV = \frac{{\sigma}}{{\mu}} \leq {cv_max:.0%}"
                    )

                # ─────────────────────────────────────────────────────────────
                # TEST 3: Outlier Detection
                # ─────────────────────────────────────────────────────────────
                outlier_threshold = ExtendedAuditThresholds.MULTIPLES_PE_OUTLIER
                outliers = [pe for pe in pe_values if pe > outlier_threshold]
                outlier_count = len(outliers)

                score -= self._add_audit_step(
                    key="AUDIT_MULTIPLES_OUTLIERS",
                    value=str(outlier_count),
                    threshold="0",
                    severity=AuditSeverity.WARNING,
                    condition=(outlier_count == 0),
                    penalty=10.0 * min(outlier_count, 3),  # Cap penalty
                    formula=rf"PE_{{peer}} < {outlier_threshold}"
                )

        checks_performed = len(self._audit_steps) - initial_count
        return max(0.0, score), checks_performed

    @staticmethod
    def _extract_pe_values(peers_data: List) -> List[float]:
        """
        Extracts PE ratios from peer data objects.

        Parameters
        ----------
        peers_data : List
            List of peer data objects or dictionaries.

        Returns
        -------
        List[float]
            List of valid PE ratios.
        """
        pe_values = []
        for peer in peers_data:
            if isinstance(peer, dict):
                pe = peer.get('pe_ratio') or peer.get('pe')
            else:
                pe = getattr(peer, 'pe_ratio', None) or getattr(peer, 'pe', None)

            if pe is not None and pe > 0:
                pe_values.append(pe)

        return pe_values

    @staticmethod
    def _calculate_cv(values: List[float]) -> Optional[float]:
        """
        Calculates Coefficient of Variation (std / mean).
        """
        if not values or len(values) < 2:
            return None

        # Conversion en array numpy pour les performances
        arr = np.array(values, dtype=np.float64)
        mean_val = np.mean(arr)

        # Vérification sécurisée du dénominateur (proche de zéro)
        if np.isclose(float(mean_val), 0.0):
            return None

        std_val = np.std(arr)

        # On force le retour en float Python standard
        return float(std_val / mean_val)

    def get_max_potential_checks(self) -> int:
        """Returns maximum audit checks for Multiples model."""
        # Base: 3 (Beta, Freshness, Provider) + Multiples: 3 (Size, CV, Outliers)
        return 6


# ==============================================================================
# 7. FCFE AUDITOR — Direct Equity (with leverage considerations)
# ==============================================================================

class FCFEAuditor(DCFAuditor):
    """
    Specialized auditor for Free Cash Flow to Equity models.

    Extends DCF auditor with leverage-specific checks.
    """
    pass  # Inherits all DCF checks, which are appropriate for FCFE


# ==============================================================================
# 8. ALIASES AND BACKWARD COMPATIBILITY
# ==============================================================================

StandardValuationAuditor = DCFAuditor
FundamentalValuationAuditor = DCFAuditor