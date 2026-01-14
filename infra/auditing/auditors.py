"""
infra/auditing/auditors.py
AUDITEUR INSTITUTIONNEL — VERSION V9.0 (Segmenté)
Rôle : Analyse multidimensionnelle de la fiabilité via accès aux segments Rates & Growth.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional

from core.models import (
    ValuationResult, DCFValuationResult, RIMValuationResult, GrahamValuationResult,
    AuditLog, AuditPillar, AuditPillarScore, InputSource, DCFParameters
)
from app.ui_components.ui_texts import AuditMessages, AuditCategories

logger = logging.getLogger(__name__)

class IValuationAuditor(ABC):
    @abstractmethod
    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        pass

    @abstractmethod
    def get_max_potential_checks(self) -> int:
        pass

class BaseAuditor(IValuationAuditor):
    PENALTY_CRITICAL = 100.0
    PENALTY_HIGH = 35.0
    PENALTY_MEDIUM = 15.0
    PENALTY_LOW = 5.0

    def _create_log(self, category: str, severity: str, message: str, penalty: float = 0.0) -> AuditLog:
        return AuditLog(category=category, severity=severity, message=message, penalty=penalty)

    def _audit_data_confidence(self, result: ValuationResult) -> Tuple[float, List[AuditLog], int]:
        logs: List[AuditLog] = []
        score = 100.0
        f = result.financials
        # Vérification sécurisée de la source d'input
        is_expert = result.request.input_source == InputSource.MANUAL if result.request else False
        checks = 0

        # Test 1 : Beta (Default 1.0 dans CompanyFinancials)
        checks += 1
        if f.beta is None:
            logs.append(self._create_log(AuditCategories.DATA, "WARNING", AuditMessages.BETA_MISSING, -self.PENALTY_MEDIUM))
            if not is_expert:
                score -= self.PENALTY_MEDIUM
        elif not (0.4 <= f.beta <= 3.0):
            logs.append(self._create_log(AuditCategories.DATA, "WARNING", AuditMessages.BETA_ATYPICAL.format(beta=f.beta), -self.PENALTY_LOW))
            score -= self.PENALTY_LOW

        # Test 2 : Solvabilité (ICR)
        checks += 1
        ebit = f.ebit_ttm or 0.0
        if ebit > 0 and f.interest_expense > 0:
            icr = ebit / f.interest_expense
            if icr < 1.5:
                logs.append(self._create_log(AuditCategories.DATA, "WARNING", AuditMessages.SOLVENCY_FRAGILE.format(icr=icr), -self.PENALTY_MEDIUM))
                score -= self.PENALTY_MEDIUM

        # Test 3 : Position Net-Net
        checks += 1
        if f.market_cap > 0 and f.cash_and_equivalents > f.market_cap:
            logs.append(self._create_log(AuditCategories.DATA, "CRITICAL", AuditMessages.NET_NET_ANOMALY, -self.PENALTY_CRITICAL))
            score -= self.PENALTY_CRITICAL

        # Test 4 : Liquidité (Small Cap)
        checks += 1
        if f.market_cap < 250_000_000:
            logs.append(self._create_log(AuditCategories.DATA, "WARNING", AuditMessages.LIQUIDITY_SMALL_CAP, -self.PENALTY_LOW))
            score -= self.PENALTY_LOW

        return max(0.0, score), logs, checks

    def _audit_macro_invariants(self, params: DCFParameters) -> Tuple[float, List[str], int]:
        """Audit des invariants via les segments Rates et Growth."""
        score_adj = 0.0
        logs: List[str] = []
        checks = 0

        r, g = params.rates, params.growth

        # Test 5 : Convergence Gordon (gn < Rf)
        checks += 1
        g_perp = g.perpetual_growth_rate or 0.0
        rf = r.risk_free_rate or 0.0
        if g_perp > rf:
            logs.append(AuditMessages.MACRO_G_RF_DIV.format(g=g_perp, rf=rf))
            score_adj -= self.PENALTY_MEDIUM

        # Test 6 : Plancher Taux Sans Risque
        checks += 1
        if rf < 0.01:
            logs.append(AuditMessages.MACRO_RF_FLOOR)
            score_adj -= self.PENALTY_LOW

        return score_adj, logs, checks

class DCFAuditor(BaseAuditor):
    def get_max_potential_checks(self) -> int: return 12

    def audit_pillars(self, result: DCFValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        p, f = result.params, result.financials
        pillars: Dict[AuditPillar, AuditPillarScore] = {}

        # 1. DATA CONFIDENCE
        data_score, data_logs, d_checks = self._audit_data_confidence(result)
        d_checks += 1
        ebit = f.ebit_ttm or 0.0
        if ebit > 0 and (f.total_debt / ebit) > 4.0:
            data_logs.append(self._create_log(AuditCategories.DATA, "WARNING", AuditMessages.DCF_LEVERAGE_EXCESSIVE, -self.PENALTY_MEDIUM))
            data_score -= self.PENALTY_MEDIUM

        pillars[AuditPillar.DATA_CONFIDENCE] = AuditPillarScore(
            pillar=AuditPillar.DATA_CONFIDENCE,
            score=max(0.0, data_score),
            diagnostics=[log.message for log in data_logs],
            check_count=d_checks
        )

        # 2. ASSUMPTION RISK (Accès p.growth)
        m_adj, m_logs, m_checks = self._audit_macro_invariants(p)
        a_score, a_checks = 100.0 + m_adj, m_checks

        # Test CapEx/D&A
        a_checks += 1
        if f.capex and f.depreciation_and_amortization:
            if abs(f.capex) < f.depreciation_and_amortization * 0.8:
                m_logs.append(AuditMessages.DCF_REINVESTMENT_DEFICIT)
                a_score -= self.PENALTY_MEDIUM

        # Test Borne de croissance (gn du segment growth)
        a_checks += 1
        if (p.growth.fcf_growth_rate or 0.0) > 0.20:
            m_logs.append(AuditMessages.DCF_GROWTH_OUTSIDE_NORMS.format(g=p.growth.fcf_growth_rate))
            a_score -= self.PENALTY_HIGH

        pillars[AuditPillar.ASSUMPTION_RISK] = AuditPillarScore(
            pillar=AuditPillar.ASSUMPTION_RISK,
            score=max(0.0, a_score),
            diagnostics=m_logs,
            check_count=a_checks
        )

        # 3. MODEL RISK
        model_logs: List[str] = []
        model_score, model_checks = 100.0, 0

        # Plancher WACC
        model_checks += 1
        if result.wacc < 0.06:
            model_logs.append(AuditMessages.DCF_WACC_FLOOR.format(wacc=result.wacc))
            model_score -= self.PENALTY_MEDIUM

        # Poids TV
        model_checks += 1
        if result.enterprise_value > 0 and result.discounted_terminal_value:
            tv_weight = result.discounted_terminal_value / result.enterprise_value
            if tv_weight > 0.90:
                model_logs.append(AuditMessages.DCF_TV_CONCENTRATION.format(weight=tv_weight))
                model_score -= self.PENALTY_HIGH

        # Invariant Gordon (gn < WACC via segment growth)
        model_checks += 1
        if (p.growth.perpetual_growth_rate or 0.0) >= result.wacc:
            model_score = 0.0
            model_logs.append(AuditMessages.DCF_MATH_INSTABILITY)

        pillars[AuditPillar.MODEL_RISK] = AuditPillarScore(pillar=AuditPillar.MODEL_RISK, score=max(0.0, model_score), diagnostics=model_logs, check_count=model_checks)
        pillars[AuditPillar.METHOD_FIT] = AuditPillarScore(pillar=AuditPillar.METHOD_FIT, score=100.0, check_count=1)

        return pillars

class RIMAuditor(BaseAuditor):
    def get_max_potential_checks(self) -> int: return 8

    def audit_pillars(self, result: RIMValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        f, p = result.financials, result.params
        pillars: Dict[AuditPillar, AuditPillarScore] = {}

        # Data Confidence avec ajustement sectoriel banques
        data_score, raw_logs, d_checks = self._audit_data_confidence(result)
        refined_logs: List[AuditLog] = []

        for log in raw_logs:
            if "Trésorerie > Capitalisation" in log.message:
                data_score += self.PENALTY_CRITICAL
                refined_logs.append(self._create_log(AuditCategories.DATA, "INFO", AuditMessages.RIM_CASH_SECTOR_NOTE, 0))
            else:
                refined_logs.append(log)

        pillars[AuditPillar.DATA_CONFIDENCE] = AuditPillarScore(pillar=AuditPillar.DATA_CONFIDENCE, score=min(100.0, data_score), diagnostics=[log.message for log in refined_logs], check_count=d_checks)

        # Risque Hypothèses (ω via segment growth)
        a_logs: List[str] = []
        a_score, a_checks = 100.0, 0
        a_checks += 1
        omega = p.growth.exit_multiple_value or 0.60
        if omega > 0.95:
            a_logs.append(AuditMessages.RIM_PERSISTENCE_EXTREME)
            a_score -= self.PENALTY_HIGH

        a_checks += 1
        payout = f.dividends_total_calculated / (f.net_income_ttm or 1.0)
        if payout > 1.0:
            a_logs.append(AuditMessages.RIM_PAYOUT_EROSION.format(payout=payout))
            a_score -= self.PENALTY_MEDIUM

        pillars[AuditPillar.ASSUMPTION_RISK] = AuditPillarScore(pillar=AuditPillar.ASSUMPTION_RISK, score=max(0.0, a_score), diagnostics=a_logs, check_count=a_checks)

        # Adéquation Méthode
        fit_logs: List[str] = []
        fit_score, fit_checks = 100.0, 0
        fit_checks += 1
        if f.eps_ttm and f.book_value_per_share and f.book_value_per_share > 0:
            roe = f.eps_ttm / f.book_value_per_share
            if abs(roe - result.cost_of_equity) < 0.01:
                fit_logs.append(AuditMessages.RIM_SPREAD_ROE_KE_NULL)
                fit_score -= self.PENALTY_LOW

        fit_checks += 1
        if f.market_cap and f.book_value:
            pb_ratio = f.market_cap / f.book_value
            if pb_ratio > 8.0:
                fit_logs.append(AuditMessages.RIM_PB_RATIO_HIGH.format(pb=pb_ratio))
                fit_score -= self.PENALTY_MEDIUM

        pillars[AuditPillar.METHOD_FIT] = AuditPillarScore(pillar=AuditPillar.METHOD_FIT, score=max(0.0, fit_score), diagnostics=fit_logs, check_count=fit_checks)
        pillars[AuditPillar.MODEL_RISK] = AuditPillarScore(pillar=AuditPillar.MODEL_RISK, score=100.0, check_count=1)

        return pillars

class GrahamAuditor(BaseAuditor):
    def get_max_potential_checks(self) -> int: return 4

    def audit_pillars(self, result: GrahamValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        f, p = result.financials, result.params
        pillars: Dict[AuditPillar, AuditPillarScore] = {}
        data_score, data_logs, d_checks = self._audit_data_confidence(result)
        pillars[AuditPillar.DATA_CONFIDENCE] = AuditPillarScore(pillar=AuditPillar.DATA_CONFIDENCE, score=data_score, diagnostics=[log.message for log in data_logs], check_count=d_checks)

        # Prudence Graham (Segment growth)
        a_logs: List[str] = []
        a_score, g = 100.0, p.growth.fcf_growth_rate or 0.0
        if g > 0.15:
            a_logs.append(AuditMessages.GRAHAM_GROWTH_PRUDENCE.format(g=g))
            a_score -= self.PENALTY_HIGH

        pillars[AuditPillar.ASSUMPTION_RISK] = AuditPillarScore(pillar=AuditPillar.ASSUMPTION_RISK, score=max(0.0, a_score), diagnostics=a_logs, check_count=1)
        pillars[AuditPillar.METHOD_FIT] = AuditPillarScore(pillar=AuditPillar.METHOD_FIT, score=100.0 if (f.eps_ttm or 0) > 0 else 0.0, check_count=1)
        pillars[AuditPillar.MODEL_RISK] = AuditPillarScore(pillar=AuditPillar.MODEL_RISK, score=100.0, check_count=1)

        return pillars

class StandardValuationAuditor(DCFAuditor):
    pass