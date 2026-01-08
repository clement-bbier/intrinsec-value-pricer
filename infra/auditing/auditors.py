"""
infra/auditing/auditors.py
AUDITEUR INSTITUTIONNEL V6.7 — LOGIQUE DE DÉTECTION AVANCÉE (None-Safe)
Rôle : Mesurer les piliers d’incertitude via le DiagnosticRegistry et Invariants Macro.
Version : Hedge Fund Standard - Zéro Crash sur données manquantes.
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
from core.diagnostics import DiagnosticRegistry, DiagnosticEvent, SeverityLevel

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

    def _event_to_log(self, event: DiagnosticEvent, category: str, penalty: float) -> AuditLog:
        """Helper pour convertir un événement de diagnostic en log d'audit compatible."""
        return AuditLog(
            category=category,
            severity=event.severity.value,
            message=f"{event.message} (Code: {event.code})",
            penalty=penalty
        )

    # ------------------------------------------------------------------
    # 1. DATA CONFIDENCE (Qualité des données sources)
    # ------------------------------------------------------------------
    def _audit_data_confidence(self, result: ValuationResult) -> Tuple[AuditPillarScore, List[AuditLog]]:
        logs, score, f = [], 100.0, result.financials
        is_expert = result.request.input_source == InputSource.MANUAL if result.request else False

        # --- Test Beta (Immunisé contre None) ---
        if f.beta is None:
            logs.append(AuditLog(category="Data", severity="WARNING", message="Coefficient Beta manquant ou non récupéré.", penalty=-15))
            if not is_expert: score -= 15
        elif f.beta < 0.4 or f.beta > 3.0:
            event = DiagnosticRegistry.DATA_NEGATIVE_BETA(f.beta)
            logs.append(self._event_to_log(event, "Data", -10))
            if not is_expert: score -= 10

        # --- Test de Solvabilité (ICR) ---
        if f.ebit_ttm is not None and f.interest_expense is not None and f.interest_expense > 0:
            icr = f.ebit_ttm / f.interest_expense
            if icr < 1.5:
                event = DiagnosticRegistry.DATA_MISSING_CORE_METRIC(f"Solvabilité (ICR: {icr:.2f} < 1.5)")
                logs.append(self._event_to_log(event, "Data", -20))
                if not is_expert: score -= 20
        elif not is_expert:
            # On ne pénalise que si on n'est pas en mode expert (en expert, l'analyste peut avoir ses raisons)
            logs.append(AuditLog(category="Data", severity="INFO", message="Vérification de solvabilité impossible (données partielles).", penalty=0))

        # --- Test Cash vs MarketCap ---
        if f.market_cap > 0 and f.cash_and_equivalents is not None:
            if f.cash_and_equivalents > f.market_cap:
                logs.append(AuditLog(category="Data", severity="CRITICAL", message="Absurdité détectée : Cash > Capitalisation boursière.", penalty=-30))
                score -= 30

        score = max(0.0, min(100.0, score))
        return AuditPillarScore(pillar=AuditPillar.DATA_CONFIDENCE, score=score, weight=0.0, contribution=0.0, diagnostics=[l.message for l in logs]), logs

    # ------------------------------------------------------------------
    # 2. ASSUMPTION RISK (Risque lié aux projections)
    # ------------------------------------------------------------------
    def _audit_assumption_risk(self, result: ValuationResult) -> Tuple[AuditPillarScore, List[AuditLog]]:
        logs, score, p = [], 100.0, result.params

        # --- Croissance agressive ---
        if p.fcf_growth_rate is not None:
            if p.fcf_growth_rate > 0.20:
                event = DiagnosticRegistry.RISK_EXCESSIVE_GROWTH(p.fcf_growth_rate)
                logs.append(self._event_to_log(event, "Assumptions", -20))
                score -= 20
        else:
            logs.append(AuditLog(category="Assumptions", severity="WARNING", message="Taux de croissance g non défini.", penalty=-10))
            score -= 10

        # --- Test Croissance Terminale vs Taux Sans Risque (Macro-invariants) ---
        if p.perpetual_growth_rate is not None and p.risk_free_rate is not None:
            if p.perpetual_growth_rate > p.risk_free_rate:
                logs.append(AuditLog(
                    category="Assumptions",
                    severity="HIGH",
                    message=f"Divergence macro : g perpétuel ({p.perpetual_growth_rate:.2%}) > Rf ({p.risk_free_rate:.2%}).",
                    penalty=-20
                ))
                score -= 20

        # --- Test de marge de sécurité (Spread WACC - g) ---
        if isinstance(result, DCFValuationResult):
            if result.wacc is not None and p.perpetual_growth_rate is not None:
                spread = result.wacc - p.perpetual_growth_rate
                if spread < 0.015:
                    logs.append(AuditLog(category="Assumptions", severity="HIGH", message=f"Faible spread WACC-g ({spread:.2%}) : risque de TV infinie.", penalty=-25))
                    score -= 25

        score = max(0.0, min(100.0, score))
        return AuditPillarScore(pillar=AuditPillar.ASSUMPTION_RISK, score=score, weight=0.0, contribution=0.0, diagnostics=[l.message for l in logs]), logs

    # ------------------------------------------------------------------
    # 3. MODEL RISK (Risque de structure mathématique)
    # ------------------------------------------------------------------
    def _audit_model_risk(self, result: ValuationResult) -> Tuple[AuditPillarScore, List[AuditLog]]:
        logs, score = [], 100.0

        if isinstance(result, DCFValuationResult):
            # Évaluation du poids de la valeur terminale (TV)
            if result.enterprise_value > 0 and result.discounted_terminal_value is not None:
                tv_weight = result.discounted_terminal_value / result.enterprise_value
                if tv_weight > 0.85:
                    logs.append(AuditLog(category="Model", severity="HIGH", message=f"Dépendance excessive à la Valeur Terminale ({tv_weight:.1%}).", penalty=-30))
                    score -= 30

            # --- Validation de la convergence (Gordon Shapiro) ---
            if result.params.perpetual_growth_rate is not None and result.wacc is not None:
                if result.params.perpetual_growth_rate >= result.wacc:
                    event = DiagnosticRegistry.MODEL_G_DIVERGENCE(result.params.perpetual_growth_rate, result.wacc)
                    logs.append(self._event_to_log(event, "Model", -100))
                    score = 0.0

        score = max(0.0, min(100.0, score))
        return AuditPillarScore(pillar=AuditPillar.MODEL_RISK, score=score, weight=0.0, contribution=0.0, diagnostics=[l.message for l in logs]), logs

    # ------------------------------------------------------------------
    # 4. METHOD FIT (Adéquation modèle / entreprise)
    # ------------------------------------------------------------------
    def _audit_method_fit(self, result: ValuationResult) -> Tuple[AuditPillarScore, List[AuditLog]]:
        logs, score, f = [], 100.0, result.financials

        if isinstance(result, RIMValuationResult):
            # Test de rentabilité des fonds propres (ROE) pour le modèle RIM
            if f.eps_ttm is not None and f.book_value_per_share is not None and f.book_value_per_share > 0:
                roe = f.eps_ttm / f.book_value_per_share
                if roe < result.cost_of_equity:
                    logs.append(AuditLog(category="Fit", severity="WARN", message=f"ROE ({roe:.1%}) inférieur au coût du capital (Ke).", penalty=-10))
                    score -= 10

        score = max(0.0, min(100.0, score))
        return AuditPillarScore(pillar=AuditPillar.METHOD_FIT, score=score, weight=0.0, contribution=0.0, diagnostics=[l.message for l in logs]), logs

class StandardValuationAuditor(IValuationAuditor):
    """Implémentation normative standard."""
    pass