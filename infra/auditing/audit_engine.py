"""
infra/auditing/audit_engine.py
Audit Engine — VERSION V13.0 (Sprint 6 Final)
Rôle : Routage dynamique et Audit d'intégrité SOTP (Conglomérat).
Standards : SOLID, Zéro Hardcoding (ui_texts.py).
"""

from __future__ import annotations
import logging
from typing import Dict, Any, List, cast

from core.models import (
    ValuationResult, ValuationMode, AuditReport, AuditLog,
    AuditPillar, AuditPillarScore, AuditScoreBreakdown, InputSource,
    AuditStep, AuditSeverity
)
from app.ui_components.ui_texts import (
    AuditEngineTexts,
    AuditCategories,
    AuditMessages,
    AuditTexts
)

logger = logging.getLogger(__name__)

class AuditorFactory:
    """Fabrique de routage des auditeurs par mode de valorisation (Sprint 6 Ready)."""
    @staticmethod
    def get_auditor(mode: ValuationMode):
        from infra.auditing.auditors import (
            DCFAuditor, RIMAuditor, GrahamAuditor,
            StandardValuationAuditor, FCFEAuditor, DDMAuditor
        )

        mapping = {
            ValuationMode.FCFF_TWO_STAGE: DCFAuditor,
            ValuationMode.FCFF_NORMALIZED: DCFAuditor,
            ValuationMode.FCFF_REVENUE_DRIVEN: DCFAuditor,
            ValuationMode.FCFE_TWO_STAGE: FCFEAuditor,
            ValuationMode.DDM_GORDON_GROWTH: DDMAuditor,
            ValuationMode.RESIDUAL_INCOME_MODEL: RIMAuditor,
            ValuationMode.GRAHAM_1974_REVISED: GrahamAuditor,
        }

        return mapping.get(mode, StandardValuationAuditor)()

class AuditEngine:
    """
    Moteur central d'audit.
    Transforme une série de tests techniques en un score de confiance institutionnel.
    """
    @staticmethod
    def compute_audit(result: ValuationResult, auditor: Any = None) -> AuditReport:
        try:
            if result.request is None:
                logger.warning(AuditEngineTexts.NO_REQUEST_WARNING)
                return AuditEngine._fallback_report("ValuationResult.request is None")

            if auditor is None:
                auditor = AuditorFactory.get_auditor(result.request.mode)

            # 1. Exécution de l'audit spécifique au modèle (Beta, WACC, g, etc.)
            raw_pillars = auditor.audit_pillars(cast(Any, result))
            all_steps: List[AuditStep] = getattr(auditor, "_audit_steps", [])

            # --- AJOUT SPRINT 6 : Audit d'intégrité SOTP ---
            if result.params.sotp.enabled:
                sotp_steps = AuditEngine._audit_sotp_integrity(result)
                all_steps.extend(sotp_steps)

                # Pénalité automatique sur le pilier DATA si la réconciliation échoue
                if any(s.step_key == "SOTP_REVENUE_CHECK" and not s.verdict for s in sotp_steps):
                    if AuditPillar.DATA_CONFIDENCE in raw_pillars:
                        raw_pillars[AuditPillar.DATA_CONFIDENCE].score *= 0.70 # -30%

            max_potential_checks = auditor.get_max_potential_checks() + (2 if result.params.sotp.enabled else 0)
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
                    pillar=pillar, score=raw_score_obj.score, weight=weight,
                    contribution=contribution, diagnostics=raw_score_obj.diagnostics,
                    check_count=raw_score_obj.check_count
                )
                total_weighted_score += contribution

            # 3. Calcul du score final
            coverage = AuditEngine._calculate_coverage(total_checks_executed, max_potential_checks)
            final_global_score = total_weighted_score * coverage
            rating = AuditEngine._compute_rating(final_global_score)

            # 4. Synchronisation des logs
            legacy_logs = AuditEngine._sync_legacy_logs(all_steps)

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
    def _audit_sotp_integrity(result: ValuationResult) -> List[AuditStep]:
        """Règles spécifiques pour les conglomérats (ST 4.3)."""
        steps = []
        p = result.params.sotp
        f = result.financials

        if not p.segments:
            return steps

        # TEST 1 : Réconciliation des Revenus
        seg_revenues = [s.revenue for s in p.segments if s.revenue is not None]
        if len(seg_revenues) == len(p.segments) and f.revenue_ttm and f.revenue_ttm > 0:
            gap = abs(sum(seg_revenues) - f.revenue_ttm) / f.revenue_ttm
            steps.append(AuditStep(
                step_key="SOTP_REVENUE_CHECK",
                label=AuditTexts.LBL_SOTP_REVENUE_CHECK,
                verdict=gap < 0.05, # Tolérance 5%
                severity=AuditSeverity.WARNING if gap < 0.15 else AuditSeverity.ERROR,
                evidence=AuditMessages.SOTP_REVENUE_MISMATCH.format(gap=gap)
            ))

        # TEST 2 : Prudence de la Décote
        if p.conglomerate_discount > 0.25:
            steps.append(AuditStep(
                step_key="SOTP_DISCOUNT_CHECK",
                label=AuditTexts.LBL_SOTP_DISCOUNT_CHECK,
                verdict=False,
                severity=AuditSeverity.WARNING,
                evidence=AuditMessages.SOTP_DISCOUNT_AGGRESSIVE.format(val=p.conglomerate_discount)
            ))

        return steps

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
    def _sync_legacy_logs(steps: List[AuditStep]) -> List[AuditLog]:
        logs = []
        for step in steps:
            if not step.verdict:
                logs.append(AuditLog(
                    category=step.step_key.split('_')[0] if '_' in step.step_key else "GENERAL",
                    severity=step.severity.value,
                    message=step.step_key,
                    penalty=0.0
                ))
        return logs

    @staticmethod
    def _fallback_report(error: str) -> AuditReport:
        return AuditReport(
            global_score=0.0, rating=AuditEngineTexts.FALLBACK_RATING, audit_depth=0,
            audit_mode=InputSource.SYSTEM, audit_coverage=0.0,
            logs=[AuditLog(
                category=AuditCategories.SYSTEM, severity="CRITICAL",
                message=AuditEngineTexts.ENGINE_FAILURE_PREFIX.format(error=error),
                penalty=0
            )],
            pillar_breakdown=None, block_monte_carlo=True, critical_warning=True
        )

# PONDÉRATIONS STANDARDS
MODE_WEIGHTS = {
    InputSource.AUTO: {
        AuditPillar.DATA_CONFIDENCE: 0.30,
        AuditPillar.ASSUMPTION_RISK: 0.30,
        AuditPillar.MODEL_RISK: 0.25,
        AuditPillar.METHOD_FIT: 0.15,
    },
    InputSource.MANUAL: {
        AuditPillar.DATA_CONFIDENCE: 0.10,
        AuditPillar.ASSUMPTION_RISK: 0.50,
        AuditPillar.MODEL_RISK: 0.20,
        AuditPillar.METHOD_FIT: 0.20,
    }
}