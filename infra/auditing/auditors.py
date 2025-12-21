"""
infra/auditing/auditors.py

Auditeurs de valorisation — Chapitre 6
Responsabilité : mesurer les piliers d’incertitude.

Principes :
- Aucune agrégation globale ici
- Chaque règle alimente un pilier explicite
- Les aberrations économiques restent bloquantes
- Le moteur d’audit est unique
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from core.models import (
    ValuationResult,
    DCFValuationResult,
    GrahamValuationResult,
    AuditLog,
    AuditPillar,
    AuditPillarScore,
    InputSource
)

logger = logging.getLogger(__name__)


# ==============================================================================
# BASE AUDITOR — MESURE DES PILIERS
# ==============================================================================

class IValuationAuditor(ABC):
    """
    Auditeur abstrait et implémentation par défaut.

    Rôle :
    - produire des scores par pilier
    - produire des logs explicatifs
    - bloquer les aberrations
    """

    def audit_pillars(
        self,
        result: ValuationResult
    ) -> Dict[AuditPillar, AuditPillarScore]:
        """
        Point d’entrée principal.
        Retourne les scores par pilier (non agrégés).
        """
        pillars: Dict[AuditPillar, AuditPillarScore] = {}

        data_score, data_logs = self._audit_data_confidence(result)
        assumption_score, assumption_logs = self._audit_assumption_risk(result)
        model_score, model_logs = self._audit_model_risk(result)
        fit_score, fit_logs = self._audit_method_fit(result)

        pillars[AuditPillar.DATA_CONFIDENCE] = data_score
        pillars[AuditPillar.ASSUMPTION_RISK] = assumption_score
        pillars[AuditPillar.MODEL_RISK] = model_score
        pillars[AuditPillar.METHOD_FIT] = fit_score

        return pillars

    # ------------------------------------------------------------------
    # DATA CONFIDENCE
    # ------------------------------------------------------------------
    def _audit_data_confidence(
        self,
        result: ValuationResult
    ) -> Tuple[AuditPillarScore, List[AuditLog]]:
        logs: List[AuditLog] = []
        score = 100.0
        f = result.financials

        is_expert = (
            result.request is not None
            and result.request.input_source == InputSource.MANUAL
        )

        if is_expert:
            logs.append(
                AuditLog(
                    category="Data",
                    severity="INFO",
                    message="Mode EXPERT : données présumées exactes. Qualité informative.",
                    penalty=0
                )
            )

        # Dette incohérente
        if f.total_debt == 0 and f.interest_expense > 0:
            logs.append(
                AuditLog(
                    category="Data",
                    severity="WARN",
                    message="Dette nulle mais charges d’intérêts présentes.",
                    penalty=-10
                )
            )
            if not is_expert:
                score -= 10

        # Beta atypique
        if f.beta < 0.4 or f.beta > 3.0:
            logs.append(
                AuditLog(
                    category="Data",
                    severity="WARN",
                    message=f"Beta atypique ({f.beta:.2f}).",
                    penalty=-10
                )
            )
            if not is_expert:
                score -= 10

        # Proxy macro
        if f.source_growth == "macro":
            logs.append(
                AuditLog(
                    category="Data",
                    severity="WARN",
                    message="Croissance issue de proxy macro-économique.",
                    penalty=-20
                )
            )
            if not is_expert:
                score -= 20

        score = max(0.0, min(100.0, score))

        return (
            AuditPillarScore(
                pillar=AuditPillar.DATA_CONFIDENCE,
                score=score,
                weight=0.0,
                contribution=0.0,
                diagnostics=[l.message for l in logs]
            ),
            logs
        )

    # ------------------------------------------------------------------
    # ASSUMPTION RISK
    # ------------------------------------------------------------------
    def _audit_assumption_risk(
        self,
        result: ValuationResult
    ) -> Tuple[AuditPillarScore, List[AuditLog]]:
        logs: List[AuditLog] = []
        score = 100.0
        p = result.params

        # Croissance irréaliste
        if p.fcf_growth_rate > 0.20:
            logs.append(
                AuditLog(
                    category="Assumptions",
                    severity="HIGH",
                    message=f"Croissance élevée ({p.fcf_growth_rate:.1%}).",
                    penalty=-20
                )
            )
            score -= 20

        # Spread terminal faible
        if isinstance(result, DCFValuationResult):
            spread = result.wacc - p.perpetual_growth_rate
            if spread <= 0:
                raise ValueError(
                    "Aberration économique : WACC ≤ g terminal."
                )
            elif spread < 0.015:
                logs.append(
                    AuditLog(
                        category="Assumptions",
                        severity="HIGH",
                        message=f"Spread WACC − g très faible ({spread:.2%}).",
                        penalty=-25
                    )
                )
                score -= 25

        score = max(0.0, min(100.0, score))

        return (
            AuditPillarScore(
                pillar=AuditPillar.ASSUMPTION_RISK,
                score=score,
                weight=0.0,
                contribution=0.0,
                diagnostics=[l.message for l in logs]
            ),
            logs
        )

    # ------------------------------------------------------------------
    # MODEL RISK
    # ------------------------------------------------------------------
    def _audit_model_risk(
        self,
        result: ValuationResult
    ) -> Tuple[AuditPillarScore, List[AuditLog]]:
        logs: List[AuditLog] = []
        score = 100.0

        if isinstance(result, DCFValuationResult):
            tv_weight = (
                result.discounted_terminal_value / result.enterprise_value
                if result.enterprise_value > 0 else 1.0
            )

            if tv_weight > 0.85:
                logs.append(
                    AuditLog(
                        category="Model",
                        severity="HIGH",
                        message=f"Dépendance excessive à la valeur terminale ({tv_weight:.1%}).",
                        penalty=-30
                    )
                )
                score -= 30
            elif tv_weight > 0.70:
                logs.append(
                    AuditLog(
                        category="Model",
                        severity="MEDIUM",
                        message=f"Poids TV élevé ({tv_weight:.1%}).",
                        penalty=-15
                    )
                )
                score -= 15

        if isinstance(result, GrahamValuationResult):
            logs.append(
                AuditLog(
                    category="Model",
                    severity="INFO",
                    message="Méthode Graham : heuristique, non DCF.",
                    penalty=-20
                )
            )
            score -= 20

        score = max(0.0, min(100.0, score))

        return (
            AuditPillarScore(
                pillar=AuditPillar.MODEL_RISK,
                score=score,
                weight=0.0,
                contribution=0.0,
                diagnostics=[l.message for l in logs]
            ),
            logs
        )

    # ------------------------------------------------------------------
    # METHOD FIT
    # ------------------------------------------------------------------
    def _audit_method_fit(
        self,
        result: ValuationResult
    ) -> Tuple[AuditPillarScore, List[AuditLog]]:
        logs: List[AuditLog] = []
        score = 100.0
        # f = result.financials # (Inutilisé ici mais gardé pour cohérence structurelle)

        # Graham appliqué à une entreprise non rentable
        if isinstance(result, GrahamValuationResult):
            if result.eps_used <= 0:
                raise ValueError(
                    "Méthode Graham inapplicable : EPS négatif."
                )

        # DCF appliqué à des flux absents
        if isinstance(result, DCFValuationResult):
            if not result.projected_fcfs:
                raise ValueError(
                    "Méthode DCF inapplicable : flux projetés absents."
                )

        score = max(0.0, min(100.0, score))

        return (
            AuditPillarScore(
                pillar=AuditPillar.METHOD_FIT,
                score=score,
                weight=0.0,
                contribution=0.0,
                diagnostics=[l.message for l in logs]
            ),
            logs
        )


# ==============================================================================
# STANDARD AUDITOR — LA CLASSE MANQUANTE
# ==============================================================================

class StandardValuationAuditor(IValuationAuditor):
    """
    Implémentation standard de l'auditeur.
    Hérite de toute la logique définie dans IValuationAuditor.
    Utilisée par défaut par le moteur d'audit.
    """
    pass