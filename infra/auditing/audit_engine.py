"""
infra/auditing/audit_engine.py
Audit Engine — Chapitre 6 (Version V9.0)
Rôle : Routage dynamique, extraction des AuditSteps et génération du rapport final.
Architecture : Centralisation de la traçabilité Glass Box.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional

from core.models import (
    ValuationResult, ValuationMode, AuditReport, AuditLog,
    AuditPillar, AuditPillarScore, AuditScoreBreakdown, InputSource,
    AuditStep, AuditSeverity
)
from app.ui_components.ui_texts import AuditEngineTexts, AuditCategories

logger = logging.getLogger(__name__)

class AuditorFactory:
    """Fabrique de routage des auditeurs par mode de valorisation."""
    @staticmethod
    def get_auditor(mode: ValuationMode):
        from infra.auditing.auditors import (
            DCFAuditor, RIMAuditor, GrahamAuditor, StandardValuationAuditor
        )
        mapping = {
            ValuationMode.FCFF_TWO_STAGE: DCFAuditor,
            ValuationMode.FCFF_NORMALIZED:  DCFAuditor,
            ValuationMode.FCFF_REVENUE_DRIVEN: DCFAuditor,
            ValuationMode.RESIDUAL_INCOME_MODEL: RIMAuditor,
            ValuationMode.GRAHAM_1974_REVISED: GrahamAuditor,
        }
        auditor_class = mapping.get(mode, StandardValuationAuditor)
        return auditor_class()

class AuditEngine:
    @staticmethod
    def compute_audit(result: ValuationResult, auditor: Any = None) -> AuditReport:
        """
        Orchestre l'audit complet :
        1. Exécute les tests via l'auditeur.
        2. Extrait les AuditSteps (Glass Box).
        3. Calcule le score pondéré et la couverture.
        4. Génère le verdict final.
        """
        try:
            if result.request is None:
                logger.warning(AuditEngineTexts.NO_REQUEST_WARNING)
                return AuditEngine._fallback_report("ValuationResult.request is None")

            if auditor is None:
                auditor = AuditorFactory.get_auditor(result.request.mode)

            # 1. Exécution de l'audit (Remplit auditor._audit_steps)
            raw_pillars = auditor.audit_pillars(result)
            all_steps: List[AuditStep] = getattr(auditor, "_audit_steps", [])

            max_potential_checks = auditor.get_max_potential_checks()
            source_mode = result.request.input_source if result.request else InputSource.AUTO

            # 2. Pondération par pilier
            weights_profile = MODE_WEIGHTS.get(source_mode, MODE_WEIGHTS[InputSource.AUTO])
            weighted_pillars: Dict[AuditPillar, AuditPillarScore] = {}
            total_weighted_score, total_checks_executed = 0.0, 0

            for pillar, raw_score_obj in raw_pillars.items():
                weight = weights_profile.get(pillar, 0.0)
                contribution = raw_score_obj.score * weight
                total_checks_executed += raw_score_obj.check_count

                weighted_pillars[pillar] = AuditPillarScore(
                    pillar=pillar, score=raw_score_obj.score, weight=weight,
                    contribution=contribution, diagnostics=raw_score_obj.diagnostics,
                    check_count=raw_score_obj.check_count
                )
                total_weighted_score += contribution

            # 3. Calcul de la couverture et du score final
            coverage = AuditEngine._calculate_coverage(total_checks_executed, max_potential_checks)
            final_global_score = total_weighted_score * coverage
            rating = AuditEngine._compute_rating(final_global_score)

            # 4. Génération des logs (Legacy Support) et détection des blocages
            legacy_logs = AuditEngine._sync_legacy_logs(all_steps, weighted_pillars)

            # Détection de blocage Monte Carlo (Si score nul ou erreur critique sur invariant)
            is_blocked_mc = (
                final_global_score <= 0 or
                any(s.severity == AuditSeverity.CRITICAL and not s.verdict for s in all_steps)
            )

            return AuditReport(
                global_score=final_global_score,
                rating=rating,
                audit_depth=total_checks_executed,
                audit_mode=source_mode,
                audit_coverage=coverage,
                audit_steps=all_steps,  # Glass Box intégrée
                logs=legacy_logs,
                breakdown={p.value: ps.score for p, ps in weighted_pillars.items()},
                pillar_breakdown=AuditScoreBreakdown(
                    pillars=weighted_pillars,
                    aggregation_formula=AuditEngineTexts.AGGREGATION_FORMULA,
                    total_score=final_global_score
                ),
                block_monte_carlo=is_blocked_mc,
                block_history=final_global_score < 30,
                critical_warning=any(s.severity == AuditSeverity.CRITICAL for s in all_steps)
            )

        except Exception as e:
            logger.error(f"AuditEngine Crash: {str(e)}", exc_info=True)
            return AuditEngine._fallback_report(str(e))

    @staticmethod
    def _calculate_coverage(executed: int, max_potential: int) -> float:
        if max_potential <= 0: return 0.0
        return min(1.0, (executed / max_potential))

    @staticmethod
    def _compute_rating(score: float) -> str:
        if score >= 90: return "AAA"
        if score >= 75: return "AA"
        if score >= 60: return "BBB"
        if score >= 40: return "BB"
        return "C"

    @staticmethod
    def _sync_legacy_logs(steps: List[AuditStep], pillars: Dict[AuditPillar, AuditPillarScore]) -> List[AuditLog]:
        """
        Crée un pont entre les nouveaux AuditSteps et les anciens AuditLogs.
        Évite de casser le moteur de feedback UI actuel.
        """
        logs = []
        for step in steps:
            # On ne logue que les alertes dans le flux principal de messages
            if not step.verdict:
                logs.append(AuditLog(
                    category=step.step_key.split('_')[1] if '_' in step.step_key else "GENERAL",
                    severity=step.severity.value,
                    message=step.step_key, # La clé sera traduite par l'UI via le registre
                    penalty=0.0
                ))
        return logs

    @staticmethod
    def _fallback_report(error: str) -> AuditReport:
        """Génère un rapport de secours en cas de crash du moteur."""
        return AuditReport(
            global_score=0.0, rating=AuditEngineTexts.FALLBACK_RATING, audit_depth=0,
            audit_mode=InputSource.SYSTEM, audit_coverage=0.0,
            logs=[AuditLog(
                category=AuditCategories.SYSTEM,
                severity="CRITICAL",
                message=AuditEngineTexts.ENGINE_FAILURE_PREFIX.format(error=error),
                penalty=0
            )],
            breakdown={}, pillar_breakdown=None, block_monte_carlo=True, critical_warning=True
        )

# Configuration des poids institutionnels par source de données
MODE_WEIGHTS = {
    InputSource.AUTO: {
        AuditPillar.DATA_CONFIDENCE: 0.30, AuditPillar.ASSUMPTION_RISK: 0.30,
        AuditPillar.MODEL_RISK: 0.25, AuditPillar.METHOD_FIT: 0.15,
    },
    InputSource.MANUAL: {
        AuditPillar.DATA_CONFIDENCE: 0.10, AuditPillar.ASSUMPTION_RISK: 0.50,
        AuditPillar.MODEL_RISK: 0.20, AuditPillar.METHOD_FIT: 0.20,
    }
}