"""
infra/auditing/audit_engine.py
Audit Engine — Chapitre 6 (Version V10.0 - Sprint 3)
Rôle : Routage dynamique vers les auditeurs et génération du Reliability Score.
Architecture : Support intégral des modèles Direct Equity (FCFE/DDM).
"""

from __future__ import annotations
import logging
from typing import Dict, Any, List, cast

from core.models import (
    ValuationResult, ValuationMode, AuditReport, AuditLog,
    AuditPillar, AuditPillarScore, AuditScoreBreakdown, InputSource,
    AuditStep, AuditSeverity
)
from app.ui_components.ui_texts import AuditEngineTexts, AuditCategories

logger = logging.getLogger(__name__)

class AuditorFactory:
    """Fabrique de routage des auditeurs par mode de valorisation (Sprint 3 Ready)."""
    @staticmethod
    def get_auditor(mode: ValuationMode):
        from infra.auditing.auditors import (
            DCFAuditor,
            RIMAuditor,
            GrahamAuditor,
            StandardValuationAuditor,
            FCFEAuditor,
            DDMAuditor
        )

        mapping = {
            # Approche Entité (Firm)
            ValuationMode.FCFF_TWO_STAGE: DCFAuditor,
            ValuationMode.FCFF_NORMALIZED: DCFAuditor,
            ValuationMode.FCFF_REVENUE_DRIVEN: DCFAuditor,

            # Approche Actionnaire (Direct Equity)
            ValuationMode.FCFE_TWO_STAGE: FCFEAuditor,
            ValuationMode.DDM_GORDON_GROWTH: DDMAuditor,

            # Autres Modèles
            ValuationMode.RESIDUAL_INCOME_MODEL: RIMAuditor,
            ValuationMode.GRAHAM_1974_REVISED: GrahamAuditor,
        }

        auditor_class = mapping.get(mode, StandardValuationAuditor)
        return auditor_class()

class AuditEngine:
    """
    Moteur central d'audit.
    Transforme une série de tests techniques en un score de confiance institutionnel.
    """
    @staticmethod
    def compute_audit(result: ValuationResult, auditor: Any = None) -> AuditReport:
        """
        Orchestre l'audit complet :
        1. Sélectionne l'auditeur via la Factory.
        2. Calcule les scores par pilier (Data, Assumption, Model, Fit).
        3. Applique les pondérations selon la source (Auto vs Expert).
        4. Détermine le rating final (AAA, AA, etc.).
        """
        try:
            if result.request is None:
                logger.warning(AuditEngineTexts.NO_REQUEST_WARNING)
                return AuditEngine._fallback_report("ValuationResult.request is None")

            if auditor is None:
                auditor = AuditorFactory.get_auditor(result.request.mode)

            # 1. Exécution de l'audit spécifique au modèle
            raw_pillars = auditor.audit_pillars(cast(Any, result))
            all_steps: List[AuditStep] = getattr(auditor, "_audit_steps", [])

            max_potential_checks = auditor.get_max_potential_checks()
            source_mode = result.request.input_source

            # 2. Pondération par pilier selon le profil de l'utilisateur
            weights_profile = MODE_WEIGHTS.get(source_mode, MODE_WEIGHTS[InputSource.AUTO])
            weighted_pillars: Dict[AuditPillar, AuditPillarScore] = {}
            total_weighted_score, total_checks_executed = 0.0, 0

            for pillar, raw_score_obj in raw_pillars.items():
                weight = weights_profile.get(pillar, 0.0)
                contribution = raw_score_obj.score * weight
                total_checks_executed += raw_score_obj.check_count

                weighted_pillars[pillar] = AuditPillarScore(
                    pillar=pillar,
                    score=raw_score_obj.score,
                    weight=weight,
                    contribution=contribution,
                    diagnostics=raw_score_obj.diagnostics,
                    check_count=raw_score_obj.check_count
                )
                total_weighted_score += contribution

            # 3. Calcul de la couverture et du score final (Pénalité si données manquantes)
            coverage = AuditEngine._calculate_coverage(total_checks_executed, max_potential_checks)
            final_global_score = total_weighted_score * coverage
            rating = AuditEngine._compute_rating(final_global_score)

            # 4. Synchronisation des logs et détection des blocages Monte Carlo
            legacy_logs = AuditEngine._sync_legacy_logs(all_steps)

            # Un audit critique ou un score nul bloque la simulation stochastique
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
                audit_steps=all_steps,
                logs=legacy_logs,
                breakdown={p.value: ps.score for p, ps in weighted_pillars.items()},
                pillar_breakdown=AuditScoreBreakdown(
                    pillars=weighted_pillars,
                    aggregation_formula=AuditEngineTexts.AGGREGATION_FORMULA,
                    total_score=final_global_score
                ),
                block_monte_carlo=is_blocked_mc,
                critical_warning=any(s.severity == AuditSeverity.CRITICAL and not s.verdict for s in all_steps)
            )

        except Exception as e:
            logger.error(f"AuditEngine Crash: {str(e)}", exc_info=True)
            return AuditEngine._fallback_report(str(e))

    @staticmethod
    def _calculate_coverage(executed: int, max_potential: int) -> float:
        """Détermine le taux de complétion de l'audit."""
        if max_potential <= 0: return 0.0
        return min(1.0, (executed / max_potential))

    @staticmethod
    def _compute_rating(score: float) -> str:
        """Convertit le score numérique en notation financière standard."""
        if score >= 90: return "AAA"
        if score >= 75: return "AA"
        if score >= 60: return "BBB"
        if score >= 40: return "BB"
        return "C"

    @staticmethod
    def _sync_legacy_logs(steps: List[AuditStep]) -> List[AuditLog]:
        """Convertit les AuditSteps en AuditLogs pour assurer la compatibilité UI."""
        logs = []
        for step in steps:
            if not step.verdict:
                logs.append(AuditLog(
                    category=step.step_key.split('_')[1] if '_' in step.step_key else "GENERAL",
                    severity=step.severity.value,
                    message=step.step_key,
                    penalty=0.0
                ))
        return logs

    @staticmethod
    def _fallback_report(error: str) -> AuditReport:
        """Rapport de secours pour prévenir le crash de l'application entière."""
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

# ==============================================================================
# CONFIGURATION DES PONDERATIONS (MARKET STANDARDS)
# ==============================================================================
MODE_WEIGHTS = {
    # En mode Auto, la confiance dans la donnée brute est primordiale (30%)
    InputSource.AUTO: {
        AuditPillar.DATA_CONFIDENCE: 0.30,
        AuditPillar.ASSUMPTION_RISK: 0.30,
        AuditPillar.MODEL_RISK: 0.25,
        AuditPillar.METHOD_FIT: 0.15,
    },
    # En mode Expert, le risque repose sur les hypothèses saisies par l'utilisateur (50%)
    InputSource.MANUAL: {
        AuditPillar.DATA_CONFIDENCE: 0.10,
        AuditPillar.ASSUMPTION_RISK: 0.50,
        AuditPillar.MODEL_RISK: 0.20,
        AuditPillar.METHOD_FIT: 0.20,
    }
}