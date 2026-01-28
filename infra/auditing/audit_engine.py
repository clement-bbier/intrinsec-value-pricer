"""
infra/auditing/audit_engine.py

INSTITUTIONAL AUDIT ENGINE
==========================
Role: Orchestrates multi-pillar reliability audits, SOTP reconciliation,
and sector-specific consistency checks (e.g., SBC dilution).

Architecture: Centralized Risk Hub.
Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, List, cast, Optional

from src.models import (
    ValuationResult, ValuationMode, AuditReport, AuditLog,
    AuditPillar, AuditPillarScore, AuditScoreBreakdown, InputSource,
    AuditStep, AuditSeverity
)
from src.i18n import (
    AuditEngineTexts,
    AuditMessages,
    AuditTexts
)
from src.config import AuditThresholds, AuditWeights

logger = logging.getLogger(__name__)

class AuditorFactory:
    """Factory for routing specialized auditors based on valuation mode."""

    @staticmethod
    def get_auditor(mode: ValuationMode) -> Any:
        """Retrieves the specific auditor implementation from the registry."""
        from src.valuation.registry import get_auditor
        return get_auditor(mode)

class AuditEngine:
    """
    Central Audit Engine.

    Aggregates technical validation steps into a standardized institutional
    confidence score by applying weighted pillar analysis and sector penalties.
    """

    @staticmethod
    def compute_audit(result: ValuationResult, auditor: Optional[Any] = None) -> AuditReport:
        """
        Computes the global audit report for a given valuation result.

        The scoring logic follows the institutional standard:
        $$Score_{final} = (\sum_{p=1}^{n} Score_{p} \times Weight_{p}) \times Coverage$$

        Parameters
        ----------
        result : ValuationResult
            The complete valuation result to be audited.
        auditor : Optional[Any], default=None
            Specific auditor instance. Fetched via AuditorFactory if None.

        Returns
        -------
        AuditReport
            Exhaustive audit report including rating, coverage, and pillar breakdown.
        """
        try:
            if result.request is None:
                logger.warning(AuditEngineTexts.NO_REQUEST_WARNING)
                return AuditEngine._fallback_report("ValuationResult.request is None")

            # 1. Base Audit Initialization
            auditor = auditor or AuditorFactory.get_auditor(result.request.mode)
            raw_pillars = auditor.audit_pillars(cast(Any, result))
            all_steps: List[AuditStep] = getattr(auditor, "_audit_steps", [])

            # 2. Sequential Enrichment (SBC & SOTP integrity)
            all_steps.extend(AuditEngine._process_sbc_audit(result, raw_pillars))

            if result.params.sotp.enabled:
                all_steps.extend(AuditEngine._process_sotp_audit(result, raw_pillars))

            # 3. Weighted Aggregation
            source_mode = result.request.input_source
            max_checks = AuditEngine._get_max_checks(result, auditor)
            pillar_data = AuditEngine._aggregate_pillars(raw_pillars, source_mode)

            # 4. Final Scoring & Coverage Adjustment
            coverage = AuditEngine._calculate_coverage(pillar_data['total_checks'], max_checks)
            final_score = pillar_data['weighted_score'] * coverage

            # 5. Report Synthesis
            return AuditReport(
                global_score=final_score,
                rating=AuditEngine._compute_rating(final_score),
                audit_depth=pillar_data['total_checks'],
                audit_mode=source_mode,
                audit_coverage=coverage,
                audit_steps=all_steps,
                logs=AuditEngine._sync_legacy_logs(all_steps),
                pillar_breakdown=AuditScoreBreakdown(
                    pillars=pillar_data['pillars'],
                    aggregation_formula=AuditEngineTexts.AGGREGATION_FORMULA,
                    total_score=final_score
                ),
                block_monte_carlo=AuditEngine._should_block_mc(final_score, all_steps),
                critical_warning=any(s.severity == AuditSeverity.CRITICAL and not s.verdict for s in all_steps)
            )

        except Exception as e:
            logger.error(f"AuditEngine Crash: {str(e)}", exc_info=True)
            return AuditEngine._fallback_report(str(e))

    # --- PRIVATE LOGIC ---

    @staticmethod
    def _process_sbc_audit(result: ValuationResult, pillars: Dict[AuditPillar, AuditPillarScore]) -> List[AuditStep]:
        """Audits SBC consistency and applies penalties to Assumption Risk pillar."""
        steps = AuditEngine._audit_sbc_integrity(result)
        # Apply 15% penalty if SBC check fails for Tech companies
        if any(s.step_key == "SBC_DILUTION_CHECK" and not s.verdict for s in steps):
            if AuditPillar.ASSUMPTION_RISK in pillars:
                pillars[AuditPillar.ASSUMPTION_RISK].score *= 0.85
        return steps

    @staticmethod
    def _process_sotp_audit(result: ValuationResult, pillars: Dict[AuditPillar, AuditPillarScore]) -> List[AuditStep]:
        """Audits SOTP reconciliation and applies penalties to Data Confidence pillar."""
        steps = AuditEngine._audit_sotp_integrity(result)
        # Apply 30% penalty if revenue reconciliation fails
        if any(s.step_key == "SOTP_REVENUE_CHECK" and not s.verdict for s in steps):
            if AuditPillar.DATA_CONFIDENCE in pillars:
                pillars[AuditPillar.DATA_CONFIDENCE].score *= 0.70
        return steps

    @staticmethod
    def _aggregate_pillars(raw_pillars: Dict[AuditPillar, AuditPillarScore], source: InputSource) -> Dict[str, Any]:
        """Calculates weighted contributions per pillar."""
        weights = MODE_WEIGHTS.get(source, MODE_WEIGHTS[InputSource.AUTO])
        weighted_pillars = {}
        total_score, total_checks = 0.0, 0

        for pillar, score_obj in raw_pillars.items():
            w = weights.get(pillar, 0.0)
            contribution = score_obj.score * w
            total_score += contribution
            total_checks += score_obj.check_count

            weighted_pillars[pillar] = AuditPillarScore(
                pillar=pillar, score=score_obj.score, weight=w,
                contribution=contribution, diagnostics=score_obj.diagnostics,
                check_count=score_obj.check_count
            )
        return {'pillars': weighted_pillars, 'weighted_score': total_score, 'total_checks': total_checks}

    @staticmethod
    def _audit_sbc_integrity(result: ValuationResult) -> List[AuditStep]:
        """Checks for missing SBC dilution in Technology sectors."""
        steps = []
        sector = result.financials.sector
        dilution = result.params.growth.annual_dilution_rate or 0.0

        if sector == "Technology" and dilution <= 0.001:
            raw_msg = AuditMessages.SBC_DILUTION_MISSING
            steps.append(AuditStep(
                step_key="SBC_DILUTION_CHECK",
                label=AuditTexts.LBL_SOTP_DISCOUNT_CHECK, # Reusing SOTP label logic if specific SBC label missing
                verdict=False,
                severity=AuditSeverity.WARNING,
                indicator_value=f"{dilution:.2%}",
                evidence=raw_msg.format(sector=sector)
            ))
        return steps

    @staticmethod
    def _audit_sotp_integrity(result: ValuationResult) -> List[AuditStep]:
        """Verifies segment revenue reconciliation."""
        steps = []
        p, f = result.params.sotp, result.financials
        if not p.segments: return steps

        seg_rev_sum = sum(s.revenue for s in p.segments if s.revenue)
        if f.revenue_ttm and f.revenue_ttm > 0:
            gap = abs(seg_rev_sum - f.revenue_ttm) / f.revenue_ttm
            steps.append(AuditStep(
                step_key="SOTP_REVENUE_CHECK",
                label=AuditTexts.LBL_SOTP_REVENUE_CHECK,
                verdict=gap < AuditThresholds.SOTP_REVENUE_GAP_WARNING,
                severity=AuditSeverity.WARNING if gap < AuditThresholds.SOTP_REVENUE_GAP_ERROR else AuditSeverity.CRITICAL,
                indicator_value=f"{gap:.1%}",
                evidence=AuditMessages.SOTP_REVENUE_MISMATCH.format(gap=gap)
            ))
        return steps

    @staticmethod
    def _calculate_coverage(executed: int, max_potential: int) -> float:
        """Calculates completion ratio."""
        return min(1.0, (executed / max_potential)) if max_potential > 0 else 0.0

    @staticmethod
    def _compute_rating(score: float) -> str:
        """Maps numeric score to institutional letter rating."""
        if score >= 90: return "AAA"
        if score >= 75: return "AA"
        if score >= 60: return "BBB"
        if score >= 40: return "BB"
        return "C"

    @staticmethod
    def _should_block_mc(score: float, steps: List[AuditStep]) -> bool:
        """Determines if Monte Carlo should be disabled due to low data quality."""
        return score <= 0 or any(s.severity == AuditSeverity.CRITICAL and not s.verdict for s in steps)

    @staticmethod
    def _get_max_checks(result: ValuationResult, auditor: Any) -> int:
        """Computes expected test count based on active modules."""
        base = auditor.get_max_potential_checks()
        sotp = 2 if result.params.sotp.enabled else 0
        return base + sotp + 1

    @staticmethod
    def _sync_legacy_logs(steps: List[AuditStep]) -> List[AuditLog]:
        """Utility for legacy log compatibility."""
        return [
            AuditLog(
                category=s.step_key.split('_')[0] if '_' in s.step_key else "GENERAL",
                severity=s.severity.value, message=s.step_key, penalty=0.0
            ) for s in steps if not s.verdict
        ]

    @staticmethod
    def _fallback_report(error: str) -> AuditReport:
        """Generates a critical failure report."""
        return AuditReport(
            global_score=0.0, rating="C", audit_depth=0,
            audit_mode=InputSource.SYSTEM, audit_coverage=0.0,
            logs=[AuditLog(category="SYSTEM", severity="CRITICAL", message=f"ERR: {error}", penalty=0)],
            pillar_breakdown=None, block_monte_carlo=True, critical_warning=True
        )

# --- CONFIGURATION INITIALIZATION ---

def _build_mode_weights() -> Dict[InputSource, Dict[AuditPillar, float]]:
    """Initializes weight maps from constants."""
    return {
        src: {getattr(AuditPillar, k): v for k, v in getattr(AuditWeights, src.name).items()}
        for src in [InputSource.AUTO, InputSource.MANUAL]
    }

MODE_WEIGHTS = _build_mode_weights()