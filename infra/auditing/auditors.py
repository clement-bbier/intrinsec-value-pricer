"""
infra/auditing/auditors.py
AUDITEUR INSTITUTIONNEL — VERSION V10.0 (Sprint 3 : Equity Expansion)
Rôle : Analyse multidimensionnelle de la fiabilité avec traçabilité AuditStep.
Note : Migration intégrale V9.0 + Rigueur Hedge Fund pour FCFE et DDM.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any

from core.models import (
    ValuationResult, DCFValuationResult, RIMValuationResult, GrahamValuationResult,
    EquityDCFValuationResult, AuditLog, AuditPillar, AuditPillarScore,
    InputSource, DCFParameters, AuditStep, AuditSeverity
)
# Migration DT-001/002: Import depuis core.i18n au lieu de app.ui_components
from core.i18n import AuditMessages, AuditCategories
from core.config import AuditPenalties, AuditThresholds, TechnicalDefaults

logger = logging.getLogger(__name__)

# ==============================================================================
# 0. INTERFACE ET SOCLE DE BASE
# ==============================================================================

class IValuationAuditor(ABC):
    @abstractmethod
    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        pass

    @abstractmethod
    def get_max_potential_checks(self) -> int:
        pass

class BaseAuditor(IValuationAuditor):
    # Seuils de pénalités centralisés (DT-010)
    PENALTY_CRITICAL = AuditPenalties.CRITICAL
    PENALTY_HIGH = AuditPenalties.HIGH
    PENALTY_MEDIUM = AuditPenalties.MEDIUM
    PENALTY_LOW = AuditPenalties.LOW

    def __init__(self):
        self._audit_steps: List[AuditStep] = []

    def add_audit_step(self,
                       key: str,
                       value: Any,
                       threshold: Any,
                       severity: AuditSeverity,
                       condition: bool,
                       penalty: float = 0.0) -> float:
        """
        Enregistre un test d'audit et retourne la pénalité à déduire du score.
        """
        verdict = bool(condition)
        step = AuditStep(
            step_id=len(self._audit_steps) + 1,
            step_key=key,
            indicator_value=value,
            threshold_value=threshold,
            severity=severity,
            verdict=verdict,
            evidence=f"{value} vs {threshold}" if threshold else str(value)
        )
        self._audit_steps.append(step)
        return 0.0 if verdict else penalty

    def _get_steps_by_prefix(self, prefix: str) -> List[AuditStep]:
        return [s for s in self._audit_steps if s.step_key.startswith(prefix)]

    def _audit_data_confidence(self, result: ValuationResult) -> Tuple[float, int]:
        """Analyse de la qualité des données sources (Tests 1 à 4)."""
        score = 100.0
        f = result.financials
        is_expert = result.request.input_source == InputSource.MANUAL if result.request else False

        # Test 1 : Beta (DT-010: seuils centralisés)
        penalty = self.add_audit_step(
            key="AUDIT_DATA_BETA",
            value=f.beta,
            threshold=f"{AuditThresholds.BETA_MIN} - {AuditThresholds.BETA_MAX}",
            severity=AuditSeverity.WARNING,
            condition=(f.beta is not None and AuditThresholds.BETA_MIN <= f.beta <= AuditThresholds.BETA_MAX),
            penalty=self.PENALTY_MEDIUM if not is_expert else 0.0
        )
        score -= penalty

        # Test 2 : Solvabilité (ICR) (DT-010: seuil centralisé)
        ebit = f.ebit_ttm or 0.0
        icr = ebit / f.interest_expense if f.interest_expense > 0 else 0.0
        penalty = self.add_audit_step(
            key="AUDIT_DATA_ICR",
            value=round(icr, 2),
            threshold=f"> {AuditThresholds.ICR_MIN}",
            severity=AuditSeverity.WARNING,
            condition=(icr > AuditThresholds.ICR_MIN or f.interest_expense == 0),
            penalty=self.PENALTY_MEDIUM
        )
        score -= penalty

        # Test 3 : Position Net-Net
        is_net_net = f.market_cap > 0 and f.cash_and_equivalents > f.market_cap
        penalty = self.add_audit_step(
            key="AUDIT_DATA_CASH",
            value=f.cash_and_equivalents,
            threshold=f"MCap: {f.market_cap:,.0f}",
            severity=AuditSeverity.CRITICAL,
            condition=not is_net_net,
            penalty=self.PENALTY_CRITICAL
        )
        score -= penalty

        # Test 4 : Liquidité (Small Cap)
        penalty = self.add_audit_step(
            key="AUDIT_DATA_LIQUIDITY",
            value=f.market_cap,
            threshold="> 250M",
            severity=AuditSeverity.WARNING,
            condition=(f.market_cap >= 250_000_000),
            penalty=self.PENALTY_LOW
        )
        score -= penalty

        return max(0.0, score), 4

    def _audit_macro_invariants(self, params: DCFParameters) -> float:
        """Analyse de la cohérence macro-économique (Tests 5 à 6)."""
        score_adj = 0.0
        r, g = params.rates, params.growth

        # Test 5 : Convergence Gordon (gn <= Rf)
        g_perp = g.perpetual_growth_rate or 0.0
        rf = r.risk_free_rate or 0.0
        score_adj += self.add_audit_step(
            key="AUDIT_MACRO_G_RF",
            value=f"{g_perp:.2%}",
            threshold=f"Rf: {rf:.2%}",
            severity=AuditSeverity.WARNING,
            condition=(g_perp <= rf),
            penalty=self.PENALTY_MEDIUM
        )

        # Test 6 : Plancher Taux Sans Risque
        score_adj += self.add_audit_step(
            key="AUDIT_MACRO_RF_FLOOR",
            value=f"{rf:.2%}",
            threshold="> 1.0%",
            severity=AuditSeverity.WARNING,
            condition=(rf >= 0.01),
            penalty=self.PENALTY_LOW
        )
        return score_adj

# ==============================================================================
# 1. AUDITEUR DCF (FCFF)
# ==============================================================================

class DCFAuditor(BaseAuditor):
    def get_max_potential_checks(self) -> int: return 12

    def audit_pillars(self, result: DCFValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        p, f = result.params, result.financials
        pillars: Dict[AuditPillar, AuditPillarScore] = {}

        # 1. DATA CONFIDENCE
        score, checks = self._audit_data_confidence(result)
        ebit = f.ebit_ttm or 0.0
        lev = f.total_debt / ebit if ebit > 0 else 0.0
        score -= self.add_audit_step(
            key="AUDIT_DATA_LEVERAGE", value=round(lev, 2), threshold="< 4.0x",
            severity=AuditSeverity.WARNING, condition=(lev < 4.0), penalty=self.PENALTY_MEDIUM
        )
        pillars[AuditPillar.DATA_CONFIDENCE] = AuditPillarScore(pillar=AuditPillar.DATA_CONFIDENCE, score=max(0.0, score), check_count=checks + 1)

        # 2. ASSUMPTION RISK
        score = 100.0 - self._audit_macro_invariants(p)
        ratio = abs(f.capex / (f.depreciation_and_amortization or 1.0)) if f.capex else 0.0
        score -= self.add_audit_step(
            key="AUDIT_MODEL_REINVEST", value=round(ratio, 2), threshold="> 0.8",
            severity=AuditSeverity.WARNING, condition=(ratio >= 0.8), penalty=self.PENALTY_MEDIUM
        )
        g_val = p.growth.fcf_growth_rate or 0.0
        score -= self.add_audit_step(
            key="AUDIT_MODEL_GLIM", value=f"{g_val:.2%}", threshold="< 20%",
            severity=AuditSeverity.WARNING, condition=(g_val <= TechnicalDefaults.GROWTH_AUDIT_THRESHOLD), penalty=self.PENALTY_HIGH
        )
        pillars[AuditPillar.ASSUMPTION_RISK] = AuditPillarScore(pillar=AuditPillar.ASSUMPTION_RISK, score=max(0.0, score), check_count=4)

        # 3. MODEL RISK
        score = 100.0
        score -= self.add_audit_step(
            key="AUDIT_MODEL_WACC", value=f"{result.wacc:.2%}", threshold="> 6%",
            severity=AuditSeverity.WARNING, condition=(result.wacc >= 0.06), penalty=self.PENALTY_MEDIUM
        )
        tv_w = (result.discounted_terminal_value / result.enterprise_value) if result.enterprise_value > 0 else 0.0
        score -= self.add_audit_step(
            key="AUDIT_MODEL_TVC", value=f"{tv_w:.2%}", threshold="< 90%",
            severity=AuditSeverity.WARNING, condition=(tv_w <= 0.90), penalty=self.PENALTY_HIGH
        )
        gn = p.growth.perpetual_growth_rate or 0.0
        score -= self.add_audit_step(
            key="AUDIT_MODEL_G_WACC", value=f"g:{gn:.2%}", threshold=f"WACC:{result.wacc:.2%}",
            severity=AuditSeverity.CRITICAL, condition=(gn < result.wacc), penalty=100.0
        )
        pillars[AuditPillar.MODEL_RISK] = AuditPillarScore(pillar=AuditPillar.MODEL_RISK, score=max(0.0, score), check_count=3)
        pillars[AuditPillar.METHOD_FIT] = AuditPillarScore(pillar=AuditPillar.METHOD_FIT, score=100.0, check_count=1)

        return pillars

# ==============================================================================
# 2. AUDITEUR FCFE (Direct Equity)
# ==============================================================================

class FCFEAuditor(BaseAuditor):
    """Auditeur spécialisé dans la soutenabilité du levier pour le FCFE."""
    def get_max_potential_checks(self) -> int: return 10

    def audit_pillars(self, result: EquityDCFValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        f, p = result.financials, result.params
        pillars: Dict[AuditPillar, AuditPillarScore] = {}

        # 1. DATA CONFIDENCE
        score, checks = self._audit_data_confidence(result)
        pillars[AuditPillar.DATA_CONFIDENCE] = AuditPillarScore(pillar=AuditPillar.DATA_CONFIDENCE, score=score, check_count=checks)

        # 2. ASSUMPTION RISK (Net Borrowing Sustainability)
        score = 100.0
        # Danger Hedge Fund : Dividendes/Flux financés par l'excès de dette
        net_borrowing = p.growth.manual_net_borrowing if p.growth.manual_net_borrowing is not None else (f.net_borrowing_ttm or 0.0)
        ni = f.net_income_ttm or 0.0
        if ni <= 0:
            # Si l'entreprise perd de l'argent, toute dette émise est un risque critique
            borrowing_risk = 1.0 if net_borrowing > 0 else 0.0
            penalty = self.PENALTY_CRITICAL if borrowing_risk > 0 else 0.0
        else:
            borrowing_ratio = net_borrowing / ni
            penalty = self.PENALTY_HIGH if borrowing_ratio > TechnicalDefaults.BORROWING_RATIO_MAX else 0.0
        score -= self.add_audit_step(
            key="AUDIT_FCFE_BORROWING", value=round(borrowing_ratio, 2), threshold=f"< {TechnicalDefaults.BORROWING_RATIO_MAX}x NI",
            severity=AuditSeverity.WARNING, condition=(borrowing_ratio < TechnicalDefaults.BORROWING_RATIO_MAX), penalty=self.PENALTY_HIGH
        )
        pillars[AuditPillar.ASSUMPTION_RISK] = AuditPillarScore(pillar=AuditPillar.ASSUMPTION_RISK, score=max(0.0, score), check_count=1)

        # 3. MODEL RISK (Ke & TV Concentration)
        score = 100.0
        score -= self.add_audit_step(
            key="AUDIT_MODEL_KE", value=f"{result.cost_of_equity:.2%}", threshold="> 5%",
            severity=AuditSeverity.WARNING, condition=(result.cost_of_equity >= 0.05), penalty=self.PENALTY_MEDIUM
        )
        pillars[AuditPillar.MODEL_RISK] = AuditPillarScore(pillar=AuditPillar.MODEL_RISK, score=max(0.0, score), check_count=1)
        pillars[AuditPillar.METHOD_FIT] = AuditPillarScore(pillar=AuditPillar.METHOD_FIT, score=100.0, check_count=1)

        return pillars

# ==============================================================================
# 3. AUDITEUR DDM (Dividend Discount Model)
# ==============================================================================

class DDMAuditor(BaseAuditor):
    """Vérifie la soutenabilité du dividende et de la croissance g."""
    def get_max_potential_checks(self) -> int: return 10

    def audit_pillars(self, result: EquityDCFValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        f, p = result.financials, result.params
        pillars: Dict[AuditPillar, AuditPillarScore] = {}

        # 1. DATA CONFIDENCE
        score, checks = self._audit_data_confidence(result)
        pillars[AuditPillar.DATA_CONFIDENCE] = AuditPillarScore(pillar=AuditPillar.DATA_CONFIDENCE, score=score, check_count=checks)

        # 2. ASSUMPTION RISK (Sustainable Growth Rate Audit)
        score = 100.0
        payout = f.dividends_total_calculated / (f.net_income_ttm or 1.0)
        score -= self.add_audit_step(
            key="AUDIT_DDM_PAYOUT", value=f"{payout:.1%}", threshold="< 100%",
            severity=AuditSeverity.CRITICAL, condition=(payout <= 1.0), penalty=self.PENALTY_HIGH
        )

        # Sustainable Growth Rate (SGR) = ROE * (1 - Payout)
        roe = (f.net_income_ttm / f.book_value) if f.book_value and f.book_value > 0 else 0.0
        sgr = roe * (1.0 - min(payout, 1.0))
        g_perp = p.growth.perpetual_growth_rate or 0.0

        score -= self.add_audit_step(
            key="AUDIT_MODEL_SGR", value=f"g:{g_perp:.1%}", threshold=f"SGR:{sgr:.1%}",
            severity=AuditSeverity.WARNING, condition=(g_perp <= sgr or roe == 0), penalty=self.PENALTY_MEDIUM
        )
        pillars[AuditPillar.ASSUMPTION_RISK] = AuditPillarScore(pillar=AuditPillar.ASSUMPTION_RISK, score=max(0.0, score), check_count=2)

        pillars[AuditPillar.MODEL_RISK] = AuditPillarScore(pillar=AuditPillar.MODEL_RISK, score=100.0, check_count=1)
        pillars[AuditPillar.METHOD_FIT] = AuditPillarScore(pillar=AuditPillar.METHOD_FIT, score=100.0, check_count=1)

        return pillars

# ==============================================================================
# 4. AUTRES AUDITEURS (RIM & GRAHAM)
# ==============================================================================

class RIMAuditor(BaseAuditor):
    def get_max_potential_checks(self) -> int: return 8

    def audit_pillars(self, result: RIMValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        f, p = result.financials, result.params
        pillars: Dict[AuditPillar, AuditPillarScore] = {}

        # 1. DATA CONFIDENCE (Standard Bancaire : Trésorerie ignorée)
        score, checks = self._audit_data_confidence(result)
        is_net_net_fail = any(s.step_key == "AUDIT_DATA_CASH" and not s.verdict for s in self._audit_steps)
        if is_net_net_fail:
            score += self.PENALTY_CRITICAL
            self.add_audit_step("AUDIT_DATA_CASH", "Bank Sector", "N/A", AuditSeverity.INFO, True)
        pillars[AuditPillar.DATA_CONFIDENCE] = AuditPillarScore(pillar=AuditPillar.DATA_CONFIDENCE, score=min(100.0, score), check_count=checks)

        # 2. ASSUMPTION RISK
        score = 100.0
        omega = p.growth.exit_multiple_value or 0.60
        score -= self.add_audit_step(key="AUDIT_MODEL_GLIM", value=omega, threshold="< 0.95",
            severity=AuditSeverity.WARNING, condition=(omega <= 0.95), penalty=self.PENALTY_HIGH)

        payout = f.dividends_total_calculated / (f.net_income_ttm or 1.0)
        score -= self.add_audit_step(key="AUDIT_MODEL_PAYOUT", value=f"{payout:.1%}", threshold="< 100%",
            severity=AuditSeverity.WARNING, condition=(payout <= 1.0), penalty=self.PENALTY_MEDIUM)
        pillars[AuditPillar.ASSUMPTION_RISK] = AuditPillarScore(pillar=AuditPillar.ASSUMPTION_RISK, score=max(0.0, score), check_count=2)

        # 3. METHOD FIT
        score = 100.0
        roe = f.eps_ttm / f.book_value_per_share if f.book_value_per_share else 0.0
        spread = abs(roe - result.cost_of_equity)
        score -= self.add_audit_step(key="AUDIT_FIT_SPREAD", value=f"{spread:.2%}", threshold="> 1%",
            severity=AuditSeverity.INFO, condition=(spread >= 0.01), penalty=self.PENALTY_LOW)

        pb = f.market_cap / (f.book_value or 1.0)
        score -= self.add_audit_step(key="AUDIT_FIT_PB", value=round(pb, 2), threshold="< 8.0x",
            severity=AuditSeverity.WARNING, condition=(pb <= 8.0), penalty=self.PENALTY_MEDIUM)

        pillars[AuditPillar.METHOD_FIT] = AuditPillarScore(pillar=AuditPillar.METHOD_FIT, score=max(0.0, score), check_count=2)
        pillars[AuditPillar.MODEL_RISK] = AuditPillarScore(pillar=AuditPillar.MODEL_RISK, score=100.0, check_count=1)

        return pillars

class GrahamAuditor(BaseAuditor):
    def get_max_potential_checks(self) -> int: return 4

    def audit_pillars(self, result: GrahamValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        f, p = result.financials, result.params
        score, checks = self._audit_data_confidence(result)

        g = p.growth.fcf_growth_rate or 0.0
        a_score = 100.0 - self.add_audit_step(key="AUDIT_MODEL_GLIM", value=f"{g:.1%}", threshold="< 15%",
            severity=AuditSeverity.WARNING, condition=(g <= 0.15), penalty=self.PENALTY_HIGH)

        fit_score = 100.0 if (f.eps_ttm or 0) > 0 else 0.0
        self.add_audit_step("AUDIT_FIT_SPREAD", f.eps_ttm, "> 0", AuditSeverity.CRITICAL, fit_score > 0)

        return {
            AuditPillar.DATA_CONFIDENCE: AuditPillarScore(pillar=AuditPillar.DATA_CONFIDENCE, score=score, check_count=checks),
            AuditPillar.ASSUMPTION_RISK: AuditPillarScore(pillar=AuditPillar.ASSUMPTION_RISK, score=a_score, check_count=1),
            AuditPillar.METHOD_FIT: AuditPillarScore(pillar=AuditPillar.METHOD_FIT, score=fit_score, check_count=1),
            AuditPillar.MODEL_RISK: AuditPillarScore(pillar=AuditPillar.MODEL_RISK, score=100.0, check_count=1)
        }

class StandardValuationAuditor(DCFAuditor):
    pass