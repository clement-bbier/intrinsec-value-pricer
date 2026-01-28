"""
infra/auditing/auditors.py

INSTITUTIONAL AUDITORS — Specialized model validation.
======================================================
Architecture: SOLID - Each auditor manages pillars specific to its valuation logic.
This module provides the granular test implementation for the Audit Engine.

Style: Numpy docstrings
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional

from src.models import (
    ValuationResult, AuditPillar, AuditPillarScore, AuditStep, AuditSeverity
)
from src.config import AuditThresholds
from src.i18n import StrategyFormulas

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. INTERFACES AND BASE CLASS
# ==============================================================================

class IValuationAuditor(ABC):
    """Interface defining the contract for valuation-specific auditing."""

    @abstractmethod
    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        """Calculates score and diagnostics for each audit pillar."""
        pass

    @abstractmethod
    def get_max_potential_checks(self) -> int:
        """Returns the total number of tests this auditor can perform."""
        pass

class BaseAuditor(IValuationAuditor, ABC):
    """
    Base Auditor providing common mechanics for test registration
    and cross-model data validation.
    """

    def __init__(self):
        # Internal registry for individual audit steps
        self._audit_steps: List[AuditStep] = []

    def _add_audit_step(self, key: str, value: Any, threshold: Any,
                        severity: AuditSeverity, condition: bool,
                        penalty: float = 0.0, formula: Optional[str] = None) -> float:
        """
        Registers a control point and returns the penalty if the check fails.
        """
        verdict = bool(condition)
        self._audit_steps.append(AuditStep(
            step_id=len(self._audit_steps) + 1,
            step_key=key,
            indicator_value=str(value),
            threshold_value=str(threshold),
            severity=severity,
            verdict=verdict,
            evidence=f"{value} vs {threshold}" if threshold else str(value),
            rule_formula=formula or StrategyFormulas.NA
        ))
        return 0.0 if verdict else penalty

    def _audit_data_confidence(self, result: ValuationResult) -> Tuple[float, int]:
        """
        Transversal analysis of source data quality (e.g., Beta stability).
        """
        score = 100.0
        f = result.financials

        # Beta Validity Test: Checks if the systemic risk is within normal bounds
        score -= self._add_audit_step(
            key="AUDIT_DATA_BETA",
            value=f.beta,
            threshold=f"{AuditThresholds.BETA_MIN}-{AuditThresholds.BETA_MAX}",
            severity=AuditSeverity.WARNING,
            condition=(f.beta is not None and AuditThresholds.BETA_MIN <= f.beta <= AuditThresholds.BETA_MAX),
            formula=rf"{AuditThresholds.BETA_MIN} \leq \beta \leq {AuditThresholds.BETA_MAX}"
        )
        return max(0.0, score), len(self._audit_steps)

# ==============================================================================
# 2. SPECIFIC IMPLEMENTATIONS
# ==============================================================================

class DCFAuditor(BaseAuditor):
    """Auditor for DCF-based models (FCFF, FCFE, DDM)."""

    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        """Audits DCF-specific pillars: Data Confidence and Model Risk."""
        score_data, count = self._audit_data_confidence(result)

        return {
            AuditPillar.DATA_CONFIDENCE: AuditPillarScore(
                pillar=AuditPillar.DATA_CONFIDENCE,
                score=score_data,
                check_count=count
            ),
            AuditPillar.MODEL_RISK: AuditPillarScore(
                pillar=AuditPillar.MODEL_RISK,
                score=100.0, # Base score, to be penalized by specific DCF checks
                check_count=1
            )
        }

    def get_max_potential_checks(self) -> int:
        return 5

class RIMAuditor(DCFAuditor):
    """Specialized auditor for Residual Income Models (Banks)."""
    pass

class GrahamAuditor(BaseAuditor):
    """Specialized auditor for Graham's Defensive Value."""

    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        # Simplified logic: Graham does not rely on Beta or WACC
        return {
            AuditPillar.DATA_CONFIDENCE: AuditPillarScore(
                pillar=AuditPillar.DATA_CONFIDENCE,
                score=100.0,
                check_count=1
            )
        }

    def get_max_potential_checks(self) -> int:
        return 2

class MultiplesAuditor(DCFAuditor):
    """Auditor for relative valuation triangulation."""
    pass

# ==============================================================================
# 3. ALIASES AND BACKWARD COMPATIBILITY
# ==============================================================================

StandardValuationAuditor = DCFAuditor
FundamentalValuationAuditor = DCFAuditor
FCFEAuditor = DCFAuditor
DDMAuditor = DCFAuditor