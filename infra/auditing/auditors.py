"""
infra/auditing/auditors.py

INSTITUTIONAL AUDITORS — Specialized model validation.
======================================================
Architecture: SOLID - Each auditor manages pillars specific to its valuation logic.
Provides granular test implementations for the global Audit Engine.

Test Matrix (Model-Specific Applicability)
------------------------------------------
| Test                    | FCFF | FCFE | DDM | Graham | RIM | Multiples |
|-------------------------|------|------|-----|--------|-----|-----------|
| Beta Validity           |  ✓   |  ✓   |  ✓  |   ✗    |  ✓  |     ✓     |
| Data Freshness          |  ✓   |  ✓   |  ✓  |   ✓    |  ✓  |     ✓     |
| WACC-g Spread           |  ✓   |  ✗   |  ✗  |   ✗    |  ✗  |     ✗     |
| Ke-g Spread             |  ✗   |  ✓   |  ✓  |   ✗    |  ✓  |     ✗     |
| ICR (Solvency)          |  ✓   |  ✓   |  ✗  |   ✗    |  ✗  |     ✗     |
| Reinvestment Ratio      |  ✓   |  ✓   |  ✗  |   ✗    |  ✗  |     ✗     |
| Payout Sustainability   |  ✗   |  ✗   |  ✓  |   ✗    |  ✗  |     ✗     |
| ROE-Ke Spread           |  ✗   |  ✗   |  ✗  |   ✗    |  ✓  |     ✗     |
| Omega Bounds            |  ✗   |  ✗   |  ✗  |   ✗    |  ✓  |     ✗     |
| Graham Multiplier Rule  |  ✗   |  ✗   |  ✗  |   ✓    |  ✗  |     ✗     |
| Cohort Size             |  ✗   |  ✗   |  ✗  |   ✗    |  ✗  |     ✓     |
| Cohort Dispersion (CV)  |  ✗   |  ✗   |  ✗  |   ✗    |  ✗  |     ✓     |

Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.config.constants import AuditThresholds
from src.i18n import AuditTexts, StrategyFormulas
from src.models import (
    AuditPillar,
    AuditPillarScore,
    DiagnosticLevel,
    AuditStep,
    Company,
    ValuationResult,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# AUDIT THRESHOLDS EXTENSIONS
# ==============================================================================

class ExtendedAuditThresholds:
    """
    Extended thresholds for comprehensive audit coverage.

    Centralizes model-specific limits that complement the base AuditThresholds.
    These values are calibrated to institutional standards.

    Attributes
    ----------
    DATA_FRESHNESS_MAX_MONTHS : int
        Maximum acceptable age of financial data in months.
    PROVIDER_CONFIDENCE_MIN : float
        Minimum confidence score from data provider.
    REINVESTMENT_RATIO_MIN : float
        Minimum CapEx/D&A ratio for sustainable growth.
    GROWTH_PHASE1_TO_GN_MAX_RATIO : float
        Maximum ratio of Phase 1 growth to terminal growth.
    PAYOUT_RATIO_WARNING : float
        Payout ratio threshold triggering a warning.
    PAYOUT_RATIO_CRITICAL : float
        Payout ratio threshold triggering critical alert.
    OMEGA_MIN : float
        Minimum persistence factor for RIM models.
    OMEGA_MAX : float
        Maximum persistence factor for RIM models.
    LTD_RATIO_MAX : float
        Maximum Loans-to-Deposits ratio for banks.
    GRAHAM_MULTIPLIER_MAX : float
        Graham's defensive limit for PE × PB.
    GRAHAM_GROWTH_MAX : float
        Maximum growth rate for Graham defensive model.
    MULTIPLES_CV_MAX : float
        Maximum coefficient of variation for peer multiples.
    MULTIPLES_PE_OUTLIER : float
        PE ratio threshold for outlier detection.
    MULTIPLES_COHORT_MIN : int
        Minimum number of peers for reliable triangulation.
    """

    DATA_FRESHNESS_MAX_MONTHS: int = 6
    PROVIDER_CONFIDENCE_MIN: float = 0.7

    # DCF Model
    REINVESTMENT_RATIO_MIN: float = 0.8
    GROWTH_PHASE1_TO_GN_MAX_RATIO: float = 3.0

    # DDM Model
    PAYOUT_RATIO_WARNING: float = 0.90
    PAYOUT_RATIO_CRITICAL: float = 1.0

    # RIM Model (Banks)
    OMEGA_MIN: float = 0.1
    OMEGA_MAX: float = 0.95
    LTD_RATIO_MAX: float = 1.2

    # Graham Model
    GRAHAM_MULTIPLIER_MAX: float = 22.5
    GRAHAM_GROWTH_MAX: float = 0.10

    # Multiples Model
    MULTIPLES_CV_MAX: float = 0.50
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
    def audit_pillars(
        self,
        result: ValuationResult
    ) -> Dict[AuditPillar, AuditPillarScore]:
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
    Base Auditor providing common mechanics for test registration.

    Implements transversal audit checks that apply to all valuation models
    regardless of methodology.

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
        severity: DiagnosticLevel,
        condition: bool,
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
        severity : DiagnosticLevel
            Criticality level (CRITICAL, WARNING, INFO).
        condition : bool
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
        return penalty if not verdict else 0.0

    def _audit_data_confidence(
        self,
        result: ValuationResult,
        check_beta: bool = True
    ) -> Tuple[float, int]:
        """
        Transversal analysis of source data quality (Pillar 1).

        Parameters
        ----------
        result : ValuationResult
            The valuation result containing financials.
        check_beta : bool, optional
            Whether to validate Beta (False for Graham model).

        Returns
        -------
        Tuple[float, int]
            (pillar_score, number_of_checks_performed)
        """
        score = 100.0
        financials = result.financials
        initial_count = len(self._audit_steps)

        # Test 1: Beta Validity (conditional)
        if check_beta:
            beta = financials.beta
            beta_valid = (
                beta is not None and
                AuditThresholds.BETA_MIN <= beta <= AuditThresholds.BETA_MAX
            )
            score -= self._add_audit_step(
                key=AuditTexts.KEY_BETA_VALIDITY,
                value=beta,
                threshold=f"{AuditThresholds.BETA_MIN}-{AuditThresholds.BETA_MAX}",
                severity=DiagnosticLevel.WARNING,
                condition=beta_valid,
                penalty=15.0
            )

        # Test 2: Data Freshness
        age_months = self._calculate_data_age_months(financials)
        max_age = ExtendedAuditThresholds.DATA_FRESHNESS_MAX_MONTHS
        score -= self._add_audit_step(
            key=AuditTexts.KEY_DATA_FRESHNESS,
            value=f"{age_months} mois",
            threshold=f"≤ {max_age}",
            severity=DiagnosticLevel.WARNING,
            condition=age_months <= max_age,
            penalty=10.0
        )

        return max(0.0, score), len(self._audit_steps) - initial_count

    @staticmethod
    def _calculate_data_age_months(financials: Company) -> int:
        """
        Calculates the age of financial data in months.

        Parameters
        ----------
        financials : Company
            Financial data object with optional last_updated attribute.

        Returns
        -------
        int
            Number of months since last data update (0 if unknown).
        """
        last_updated = getattr(financials, 'last_updated', None)
        if last_updated is None:
            return 0

        try:
            if isinstance(last_updated, str):
                last_updated = datetime.fromisoformat(last_updated)
            delta = datetime.now() - last_updated
            return max(0, delta.days // 30)
        except (ValueError, TypeError):
            return 0


# ==============================================================================
# 2. DCF AUDITOR — Cash Flow Models (FCFF, FCFE)
# ==============================================================================

class DCFAuditor(BaseAuditor):
    """
    Auditor for DCF-based models (FCFF, FCFE).

    Focus Areas
    -----------
    - Mathematical stability (WACC-g spread)
    - Solvency (Interest Coverage Ratio)
    - Reinvestment adequacy (CapEx vs Depreciation)
    """

    def audit_pillars(
        self,
        result: ValuationResult
    ) -> Dict[AuditPillar, AuditPillarScore]:
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

        Tests Performed
        ---------------
        1. Solvency (ICR - Interest Coverage Ratio)
        2. WACC-g Spread (Mathematical stability)
        3. Reinvestment Ratio (CapEx sustainability)

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
        financials = result.financials
        params = result.params
        initial_count = len(self._audit_steps)

        # Test 1: Solvency (Interest Coverage Ratio)
        icr = self._calculate_icr(financials)
        icr_threshold = AuditThresholds.ICR_MIN
        score -= self._add_audit_step(
            key=AuditTexts.KEY_ICR_WARNING,
            value=f"{icr:.2f}x",
            threshold=f"≥ {icr_threshold}x",
            severity=DiagnosticLevel.WARNING,
            condition=icr >= icr_threshold,
            penalty=20.0
        )

        # Test 2: WACC-g Spread (Mathematical Stability)
        discount_rate = result.discount_rate
        perpetual_growth = params.growth.perpetual_growth_rate or 0.02

        if discount_rate > 0:
            spread = discount_rate - perpetual_growth
            spread_min = AuditThresholds.WACC_G_SPREAD_MIN
            score -= self._add_audit_step(
                key=AuditTexts.KEY_WACC_G_SPREAD,
                value=f"{spread:.2%}",
                threshold=f"≥ {spread_min:.1%}",
                severity=DiagnosticLevel.CRITICAL,
                condition=spread >= spread_min,
                penalty=50.0
            )

        # Test 3: Reinvestment Ratio (CapEx Sustainability)
        reinvestment_ratio = self._calculate_reinvestment_ratio(financials)
        if reinvestment_ratio is not None:
            reinv_min = ExtendedAuditThresholds.REINVESTMENT_RATIO_MIN
            score -= self._add_audit_step(
                key=AuditTexts.KEY_REINVESTMENT_DEFICIT,
                value=f"{reinvestment_ratio:.1f}x",
                threshold=f"≥ {reinv_min}x",
                severity=DiagnosticLevel.WARNING,
                condition=reinvestment_ratio >= reinv_min,
                penalty=15.0
            )

        return max(0.0, score), len(self._audit_steps) - initial_count

    @staticmethod
    def _calculate_icr(financials: Company) -> float:
        """
        Calculates Interest Coverage Ratio safely.

        Parameters
        ----------
        financials : Company
            Financial data with EBIT and interest expense.

        Returns
        -------
        float
            ICR value (100.0 if no interest expense).
        """
        interest = abs(float(financials.interest_expense or 0.0))
        ebit = abs(float(financials.ebit_ttm or 0.0))

        if interest == 0.0:
            return 100.0

        return ebit / interest

    @staticmethod
    def _calculate_reinvestment_ratio(
        financials: Company
    ) -> Optional[float]:
        """
        Calculates CapEx to Depreciation & Amortization ratio.

        Uses the correct attribute name as defined in CompanyFinancials model.

        Parameters
        ----------
        financials : Company
            Financial data with capex and depreciation_and_amortization.

        Returns
        -------
        Optional[float]
            Ratio value, or None if D&A is zero/missing.
        """
        capex = abs(float(financials.capex or 0.0))
        depreciation = abs(float(financials.depreciation_and_amortization or 0.0))

        if depreciation == 0.0:
            return None

        return capex / depreciation

    def get_max_potential_checks(self) -> int:
        """Returns maximum audit checks for DCF models."""
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
        score, count = super()._audit_model_risk(result)
        initial_count = len(self._audit_steps)
        financials = result.financials

        # Test: Dividend Sustainability (Payout Ratio)
        payout_ratio = self._calculate_payout_ratio(financials)

        if payout_ratio is not None:
            payout_limit = ExtendedAuditThresholds.PAYOUT_RATIO_WARNING
            score -= self._add_audit_step(
                key=AuditTexts.KEY_PAYOUT_UNSUSTAINABLE,
                value=f"{payout_ratio:.0%}",
                threshold=f"< {payout_limit:.0%}",
                severity=DiagnosticLevel.WARNING,
                condition=payout_ratio < payout_limit,
                penalty=20.0
            )

        additional_checks = len(self._audit_steps) - initial_count
        return max(0.0, score), count + additional_checks

    @staticmethod
    def _calculate_payout_ratio(financials: Company) -> Optional[float]:
        """
        Calculates dividend payout ratio.

        Parameters
        ----------
        financials : Company
            Financial data with dividends and net income.

        Returns
        -------
        Optional[float]
            Payout ratio, or None if net income is zero/missing.
        """
        net_income = financials.net_income_ttm
        if not net_income or net_income == 0:
            return None

        dividends = financials.dividends_total_calculated or 0.0
        return abs(dividends / net_income)

    def get_max_potential_checks(self) -> int:
        """Returns maximum audit checks for DDM model."""
        return 8


# ==============================================================================
# 4. RIM AUDITOR — Residual Income Model (Banks)
# ==============================================================================

class RIMAuditor(BaseAuditor):
    """
    Specialized auditor for Residual Income Models (Banks).

    Focus Areas
    -----------
    - Value creation (ROE vs Ke spread)
    - Persistence factor (Omega bounds)
    """

    def audit_pillars(
        self,
        result: ValuationResult
    ) -> Dict[AuditPillar, AuditPillarScore]:
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
        score_model, count_model = self._audit_rim_risk(result)

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

    def _audit_rim_risk(self, result: ValuationResult) -> Tuple[float, int]:
        """
        RIM-specific model risk analysis.

        Tests Performed
        ---------------
        1. ROE-Ke Spread (Value creation)
        2. Omega Bounds (Persistence factor)

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
        initial_count = len(self._audit_steps)
        financials = result.financials
        params = result.params

        # Test 1: ROE-Ke Spread (Value Creation)
        book_value = financials.book_value
        net_income = financials.net_income_ttm
        discount_rate = result.discount_rate

        if book_value and book_value > 0 and net_income:
            roe = net_income / book_value
            spread = roe - discount_rate

            score -= self._add_audit_step(
                key=AuditTexts.KEY_ROE_KE_NEGATIVE,
                value=f"{spread:.2%}",
                threshold="> 0%",
                severity=DiagnosticLevel.CRITICAL,
                condition=spread > 0,
                penalty=40.0
            )

        # Test 2: Omega Bounds (Persistence Factor)
        omega = params.growth.exit_multiple_value or 0.60
        omega_min = ExtendedAuditThresholds.OMEGA_MIN
        omega_max = ExtendedAuditThresholds.OMEGA_MAX

        score -= self._add_audit_step(
            key=AuditTexts.KEY_OMEGA_BOUNDS,
            value=f"{omega:.2f}",
            threshold=f"[{omega_min}, {omega_max}]",
            severity=DiagnosticLevel.WARNING,
            condition=omega_min <= omega <= omega_max,
            penalty=20.0
        )

        return max(0.0, score), len(self._audit_steps) - initial_count

    def get_max_potential_checks(self) -> int:
        """Returns maximum audit checks for RIM model."""
        return 6


# ==============================================================================
# 5. GRAHAM AUDITOR — Defensive Value
# ==============================================================================

class GrahamAuditor(BaseAuditor):
    """
    Specialized auditor for Graham's Defensive Value.

    Focus Areas
    -----------
    - Graham multiplier rule (PE × PB ≤ 22.5)

    Note
    ----
    Beta validation is disabled as Graham model does not rely on CAPM.
    """

    def audit_pillars(
        self,
        result: ValuationResult
    ) -> Dict[AuditPillar, AuditPillarScore]:
        """
        Audits Graham-specific pillars.

        Parameters
        ----------
        result : ValuationResult
            Graham valuation output to audit.

        Returns
        -------
        Dict[AuditPillar, AuditPillarScore]
            Scores for DATA_CONFIDENCE and MODEL_RISK pillars.
        """
        # Graham model does not use Beta
        score_data, count_data = self._audit_data_confidence(result, check_beta=False)
        score_model, count_model = self._audit_graham_risk(result)

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

    def _audit_graham_risk(self, result: ValuationResult) -> Tuple[float, int]:
        """
        Graham-specific model risk analysis.

        Tests Performed
        ---------------
        1. Graham Multiplier (PE × PB ≤ 22.5)

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
        initial_count = len(self._audit_steps)
        financials = result.financials

        # Test: Graham Multiplier Rule (PE × PB ≤ 22.5)
        pe_ratio = financials.pe_ratio or 0.0
        pb_ratio = financials.pb_ratio or 0.0
        graham_multiplier = pe_ratio * pb_ratio
        multiplier_limit = ExtendedAuditThresholds.GRAHAM_MULTIPLIER_MAX

        score -= self._add_audit_step(
            key=AuditTexts.KEY_GRAHAM_MULTIPLIER,
            value=f"{graham_multiplier:.1f}",
            threshold=f"≤ {multiplier_limit}",
            severity=DiagnosticLevel.WARNING,
            condition=graham_multiplier <= multiplier_limit,
            penalty=30.0
        )

        return max(0.0, score), len(self._audit_steps) - initial_count

    def get_max_potential_checks(self) -> int:
        """Returns maximum audit checks for Graham model."""
        return 5


# ==============================================================================
# 6. MULTIPLES AUDITOR — Relative Valuation
# ==============================================================================

class MultiplesAuditor(BaseAuditor):
    """
    Auditor for relative valuation triangulation.

    Focus Areas
    -----------
    - Cohort quality (Sample size)
    - Cohort dispersion (Coefficient of Variation)
    """

    def audit_pillars(
        self,
        result: ValuationResult
    ) -> Dict[AuditPillar, AuditPillarScore]:
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

        Tests Performed
        ---------------
        1. Cohort Size Adequacy
        2. Cohort Dispersion (Coefficient of Variation)

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

        triangulation = result.multiples_triangulation
        if not triangulation:
            return 0.0, 0

        peers = triangulation.multiples_data.peers

        # Test 1: Cohort Size Adequacy
        cohort_size = len(peers)
        min_cohort = ExtendedAuditThresholds.MULTIPLES_COHORT_MIN

        score -= self._add_audit_step(
            key=AuditTexts.KEY_COHORT_SMALL,
            value=str(cohort_size),
            threshold=f"≥ {min_cohort}",
            severity=DiagnosticLevel.WARNING,
            condition=cohort_size >= min_cohort,
            penalty=20.0
        )

        # Test 2: Cohort Dispersion (CV)
        pe_values = [p.pe_ratio for p in peers if p.pe_ratio and p.pe_ratio > 0]

        if len(pe_values) >= 3:
            cv = self._calculate_coefficient_of_variation(pe_values)
            cv_max = ExtendedAuditThresholds.MULTIPLES_CV_MAX

            if cv is not None:
                score -= self._add_audit_step(
                    key=AuditTexts.KEY_HIGH_DISPERSION,
                    value=f"{cv:.1%}",
                    threshold=f"≤ {cv_max:.0%}",
                    severity=DiagnosticLevel.WARNING,
                    condition=cv <= cv_max,
                    penalty=20.0
                )

        return max(0.0, score), len(self._audit_steps) - initial_count

    @staticmethod
    def _calculate_coefficient_of_variation(values: List[float]) -> Optional[float]:
        """
        Calculates Coefficient of Variation (std / mean).

        Parameters
        ----------
        values : List[float]
            List of numeric values.

        Returns
        -------
        Optional[float]
            CV value as Python float, or None if calculation fails.
        """
        if not values or len(values) < 2:
            return None

        arr = np.array(values, dtype=np.float64)
        mean_val = float(np.mean(arr))

        if mean_val == 0.0:
            return None

        std_val = float(np.std(arr))
        return std_val / mean_val

    def get_max_potential_checks(self) -> int:
        """Returns maximum audit checks for Multiples model."""
        return 6


# ==============================================================================
# ALIASES FOR REGISTRY SUPPORT
# ==============================================================================

FCFEAuditor = DCFAuditor
StandardValuationAuditor = DCFAuditor
FundamentalValuationAuditor = DCFAuditor