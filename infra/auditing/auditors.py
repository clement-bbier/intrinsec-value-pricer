"""
infra/auditing/auditors.py
AUDITEUR INSTITUTIONNEL V6.0 — LOGIQUE DE DÉTECTION AVANCÉE
Rôle : Mesurer les piliers d’incertitude sans altérer les calculs financiers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from core.models import (
    ValuationResult,
    DCFValuationResult,
    RIMValuationResult,
    GrahamValuationResult,
    AuditLog,
    AuditPillar,
    AuditPillarScore,
    InputSource
)

logger = logging.getLogger(__name__)

class IValuationAuditor(ABC):
    """
    Interface et implémentation de base de l'auditeur expert.
    Raisonnement par piliers isolés pour une transparence totale (Glass Box).
    """

    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        """Exécute le scan complet des 4 piliers de confiance."""
        pillars: Dict[AuditPillar, AuditPillarScore] = {}

        pillars[AuditPillar.DATA_CONFIDENCE], _ = self._audit_data_confidence(result)
        pillars[AuditPillar.ASSUMPTION_RISK], _ = self._audit_assumption_risk(result)
        pillars[AuditPillar.MODEL_RISK], _ = self._audit_model_risk(result)
        pillars[AuditPillar.METHOD_FIT], _ = self._audit_method_fit(result)

        return pillars

    # ------------------------------------------------------------------
    # 1. DATA CONFIDENCE (Qualité des données sources)
    # ------------------------------------------------------------------
    def _audit_data_confidence(self, result: ValuationResult) -> Tuple[AuditPillarScore, List[AuditLog]]:
        logs, score, f = [], 100.0, result.financials
        is_expert = result.request.input_source == InputSource.MANUAL if result.request else False

        # --- Tests de cohérence existants ---
        if f.total_debt == 0 and f.interest_expense > 0:
            logs.append(AuditLog(category="Data", severity="WARN", message="Dette nulle mais intérêts déclarés.", penalty=-10))
            if not is_expert: score -= 10

        if f.beta < 0.4 or f.beta > 3.0:
            logs.append(AuditLog(category="Data", severity="WARN", message=f"Beta atypique ({f.beta:.2f}).", penalty=-10))
            if not is_expert: score -= 10

        # --- NOUVEAU : Test de Solvabilité (ICR) ---
        if f.ebit_ttm and f.interest_expense and f.interest_expense > 0:
            icr = f.ebit_ttm / f.interest_expense
            if icr < 1.5:
                logs.append(AuditLog(category="Data", severity="CRITICAL", message=f"Solvabilité critique (ICR: {icr:.2f}).", penalty=-20))
                if not is_expert: score -= 20

        # --- NOUVEAU : Test Cash vs MarketCap ---
        if f.cash_and_equivalents > f.market_cap and f.market_cap > 0:
            logs.append(AuditLog(category="Data", severity="CRITICAL", message="Absurdité : Cash > Capitalisation. Vérifiez les actions.", penalty=-30))
            score -= 30

        score = max(0.0, min(100.0, score))
        return AuditPillarScore(pillar=AuditPillar.DATA_CONFIDENCE, score=score, weight=0.0, contribution=0.0, diagnostics=[l.message for l in logs]), logs

    # ------------------------------------------------------------------
    # 2. ASSUMPTION RISK (Risque lié aux projections)
    # ------------------------------------------------------------------
    def _audit_assumption_risk(self, result: ValuationResult) -> Tuple[AuditPillarScore, List[AuditLog]]:
        logs, score, p = [], 100.0, result.params

        # Croissance agressive
        if p.fcf_growth_rate > 0.20:
            logs.append(AuditLog(category="Assumptions", severity="HIGH", message=f"Croissance élevée ({p.fcf_growth_rate:.1%}).", penalty=-20))
            score -= 20

        if isinstance(result, DCFValuationResult):
            spread = result.wacc - p.perpetual_growth_rate
            if spread < 0.015:
                logs.append(AuditLog(category="Assumptions", severity="HIGH", message=f"Spread WACC-g très faible ({spread:.2%}).", penalty=-25))
                score -= 25

            # --- NOUVEAU : Test Croissance vs GDP ---
            if p.perpetual_growth_rate > 0.04:
                logs.append(AuditLog(category="Assumptions", severity="WARN", message="Croissance terminale > 4% (optimisme macro).", penalty=-15))
                score -= 15

        score = max(0.0, min(100.0, score))
        return AuditPillarScore(pillar=AuditPillar.ASSUMPTION_RISK, score=score, weight=0.0, contribution=0.0, diagnostics=[l.message for l in logs]), logs

    # ------------------------------------------------------------------
    # 3. MODEL RISK (Risque de structure mathématique)
    # ------------------------------------------------------------------
    def _audit_model_risk(self, result: ValuationResult) -> Tuple[AuditPillarScore, List[AuditLog]]:
        logs, score = [], 100.0

        if isinstance(result, DCFValuationResult):
            tv_weight = result.discounted_terminal_value / result.enterprise_value if result.enterprise_value > 0 else 1.0
            if tv_weight > 0.85:
                logs.append(AuditLog(category="Model", severity="HIGH", message=f"Dépendance excessive à la TV ({tv_weight:.1%}).", penalty=-30))
                score -= 30

        if isinstance(result, GrahamValuationResult):
            logs.append(AuditLog(category="Model", severity="INFO", message="Modèle Graham : absence de flux actualisés.", penalty=-20))
            score -= 20

        score = max(0.0, min(100.0, score))
        return AuditPillarScore(pillar=AuditPillar.MODEL_RISK, score=score, weight=0.0, contribution=0.0, diagnostics=[l.message for l in logs]), logs

    # ------------------------------------------------------------------
    # 4. METHOD FIT (Adéquation modèle / entreprise)
    # ------------------------------------------------------------------
    def _audit_method_fit(self, result: ValuationResult) -> Tuple[AuditPillarScore, List[AuditLog]]:
        logs, score, f = [], 100.0, result.financials

        # --- NOUVEAU : Test ROE vs Ke pour RIM (Banques) ---
        if isinstance(result, RIMValuationResult):
            if f.eps_ttm and f.book_value_per_share and f.book_value_per_share > 0:
                roe = f.eps_ttm / f.book_value_per_share
                if roe < result.cost_of_equity:
                    logs.append(AuditLog(category="Fit", severity="WARN", message=f"ROE ({roe:.1%}) < Coût Capital ({result.cost_of_equity:.1%}).", penalty=-10))
                    score -= 10

        # Graham sur non-rentable
        if isinstance(result, GrahamValuationResult) and result.eps_used <= 0:
            raise ValueError("Graham inapplicable : EPS négatif.")

        score = max(0.0, min(100.0, score))
        return AuditPillarScore(pillar=AuditPillar.METHOD_FIT, score=score, weight=0.0, contribution=0.0, diagnostics=[l.message for l in logs]), logs

class StandardValuationAuditor(IValuationAuditor):
    """Implémentation normative standard."""
    pass