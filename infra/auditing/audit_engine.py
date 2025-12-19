"""
infra/auditing/audit_engine.py

Audit Engine — Chapitre 6
Audit comme méthode normalisée et auditable.

Responsabilités :
- Router vers l’auditeur métier
- Agréger les piliers d’incertitude
- Appliquer les pondérations (mode × modèle)
- Produire un AuditReport entièrement explicable
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from core.models import (
    ValuationResult,
    ValuationMode,
    AuditReport,
    AuditLog,
    AuditPillar,
    AuditPillarScore,
    AuditScoreBreakdown,
    InputSource
)

from infra.auditing.auditors import IValuationAuditor

logger = logging.getLogger(__name__)


# ==============================================================================
# PONDÉRATIONS NORMATIVES — MODE × MÉTHODE
# ==============================================================================

# Invariants par MODE
MODE_WEIGHTS = {
    InputSource.AUTO: {
        AuditPillar.DATA_CONFIDENCE: 0.30,
        AuditPillar.ASSUMPTION_RISK: 0.30,
        AuditPillar.MODEL_RISK: 0.25,
        AuditPillar.METHOD_FIT: 0.15,
    },
    InputSource.MANUAL: {  # EXPERT
        AuditPillar.DATA_CONFIDENCE: 0.10,
        AuditPillar.ASSUMPTION_RISK: 0.40,
        AuditPillar.MODEL_RISK: 0.30,
        AuditPillar.METHOD_FIT: 0.20,
    },
}


# ==============================================================================
# AUDIT ENGINE
# ==============================================================================

class AuditEngine:
    """
    Moteur d’audit central — Chapitre 6.

    - Le moteur est unique
    - Les règles sont dans les auditeurs
    - Le score est une formule explicite
    """

    @staticmethod
    def compute_audit(
        result: ValuationResult,
        auditor: IValuationAuditor
    ) -> AuditReport:
        """
        Point d’entrée unique pour l’audit final.

        Paramètres :
        - result : résultat de valorisation
        - auditor : auditeur métier déjà sélectionné

        Retour :
        - AuditReport complet et auditable
        """

        try:
            # --------------------------------------------------------------
            # 1. MESURE DES PILIERS (AUCUNE AGRÉGATION ICI)
            # --------------------------------------------------------------
            pillar_scores = auditor.audit_pillars(result)

            # --------------------------------------------------------------
            # 2. RÉCUPÉRATION DU MODE (AUTO / EXPERT)
            # --------------------------------------------------------------
            if result.request is None:
                raise ValueError("Audit impossible sans ValuationRequest.")

            input_source = result.request.input_source
            weights = MODE_WEIGHTS[input_source]

            # --------------------------------------------------------------
            # 3. AGRÉGATION EXPLICITE DU SCORE
            # --------------------------------------------------------------
            total_score = 0.0
            enriched_pillars: Dict[AuditPillar, AuditPillarScore] = {}

            for pillar, pillar_score in pillar_scores.items():
                weight = weights[pillar]
                contribution = pillar_score.score * weight

                enriched_pillars[pillar] = AuditPillarScore(
                    pillar=pillar,
                    score=pillar_score.score,
                    weight=weight,
                    contribution=contribution,
                    diagnostics=pillar_score.diagnostics
                )

                total_score += contribution

            total_score = max(0.0, min(100.0, total_score))

            # --------------------------------------------------------------
            # 4. RATING (INDICATIF, NON CONTRACTUEL)
            # --------------------------------------------------------------
            rating = AuditEngine._compute_rating(total_score)

            # --------------------------------------------------------------
            # 5. CONSTRUCTION DU RAPPORT FINAL
            # --------------------------------------------------------------
            breakdown = AuditScoreBreakdown(
                pillars=enriched_pillars,
                aggregation_formula="Σ (w_i × S_i), avec Σ w_i = 1",
                total_score=total_score
            )

            return AuditReport(
                global_score=total_score,
                rating=rating,
                audit_mode=auditor.__class__.__name__,
                logs=AuditEngine._collect_logs(enriched_pillars),
                breakdown={p.value: s.score for p, s in enriched_pillars.items()},
                pillar_breakdown=breakdown,
                critical_warning=any(
                    s.score < 40 for s in enriched_pillars.values()
                )
            )

        except Exception as exc:
            logger.error("Audit failed", exc_info=True)
            return AuditEngine._fallback_report(str(exc))

    # ------------------------------------------------------------------
    # UTILITAIRES
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_rating(score: float) -> str:
        if score >= 90:
            return "AAA (High Confidence)"
        if score >= 75:
            return "AA (Good)"
        if score >= 60:
            return "BBB (Moderate)"
        if score >= 40:
            return "BB (Speculative)"
        return "C (Low Confidence)"

    @staticmethod
    def _collect_logs(
        pillars: Dict[AuditPillar, AuditPillarScore]
    ) -> list[AuditLog]:
        logs: list[AuditLog] = []
        for ps in pillars.values():
            for msg in ps.diagnostics:
                logs.append(
                    AuditLog(
                        category=ps.pillar.value,
                        severity="INFO",
                        message=msg,
                        penalty=0
                    )
                )
        return logs

    @staticmethod
    def _fallback_report(error: str) -> AuditReport:
        return AuditReport(
            global_score=0.0,
            rating="Error",
            audit_mode="SystemFailure",
            logs=[
                AuditLog(
                    category="System",
                    severity="CRITICAL",
                    message=f"Audit failure: {error}",
                    penalty=-100
                )
            ],
            breakdown={},
            pillar_breakdown=None,
            critical_warning=True
        )
