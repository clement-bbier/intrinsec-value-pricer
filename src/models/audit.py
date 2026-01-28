"""
src/models/audit_models

AUDIT SYSTEM MODELS
===================
Role: Data structures for financial valuation auditing and validation.
Scope: Includes pillar-based scoring, detailed audit reports, and output contracts.
Architecture: Pydantic-based containers for type-safe institutional scoring.

Style: Numpy docstrings
"""

from __future__ import annotations

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .enums import AuditPillar, InputSource
from .glass_box import AuditStep
from src.config.constants import ModelDefaults


class AuditPillarScore(BaseModel):
    """
    Score data for a specific audit pillar.

    Represents the evaluation result of an individual audit dimension,
    including its score, weighting, and detailed diagnostics.

    Attributes
    ----------
    pillar : AuditPillar
        The specific audit dimension being evaluated (e.g., Data Confidence).
    score : float, default=ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR
        The raw score achieved for this pillar (0.0 to 100.0).
    weight : float, default=ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR
        The relative weighting of this pillar in the global score.
    contribution : float, default=ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR
        The weighted contribution to the final audit score.
    diagnostics : List[str], default=[]
        List of specific issues or warnings identified for this pillar.
    check_count : int, default=0
        Total number of technical checks performed within this pillar.
    """
    pillar: AuditPillar
    score: float = ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR
    weight: float = ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR
    contribution: float = ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR
    diagnostics: List[str] = Field(default_factory=list)
    check_count: int = 0


class AuditScoreBreakdown(BaseModel):
    """
    Structural breakdown of the global audit score by pillar.

    Provides a transparent view of how the final reliability score
    is mathematically aggregated.

    Attributes
    ----------
    pillars : Dict[AuditPillar, AuditPillarScore]
        Detailed scores indexed by their respective pillars.
    aggregation_formula : str
        The LaTeX or textual representation of the aggregation formula.
    total_score : float, default=0.0
        The final aggregated global audit score.
    """
    pillars: Dict[AuditPillar, AuditPillarScore]
    aggregation_formula: str
    total_score: float = 0.0


class AuditLog(BaseModel):
    """
    Audit log entry for event tracking.

    Detailed record of a specific audit event, capturing the severity
    and the resulting score penalty applied.

    Attributes
    ----------
    category : str
        The functional category of the event (e.g., SOLVENCY, BETA).
    severity : str
        The severity level of the finding (CRITICAL, WARNING, etc.).
    message : str
        Descriptive technical message or localized error key.
    penalty : float
        The specific numeric penalty subtracted from the audit score.
    """
    category: str
    severity: str
    message: str
    penalty: float


class AuditReport(BaseModel):
    """
    Comprehensive Institutional Audit Report.

    The final synthesis of the valuation audit, including global scoring,
    pillar breakdowns, and full check logs.

    Attributes
    ----------
    global_score : float
        The final global reliability score (typically 0-100).
    rating : str
        Qualitative institutional rating (e.g., AAA, AA, BBB, C).
    audit_mode : Union[InputSource, str]
        The data input strategy used for the audit (AUTO vs MANUAL).
    audit_depth : int, default=0
        The total number of unique checks executed.
    audit_coverage : float, default=0.0
        The ratio of executed checks vs. potential model checks (%).
    audit_steps : List[AuditStep], default=[]
        Detailed technical steps for Glass Box transparency.
    pillar_breakdown : AuditScoreBreakdown, optional
        Categorized score ventilation by evaluation pillar.
    logs : List[AuditLog], default=[]
        Detailed chronological logs of all audit findings.
    breakdown : Dict[str, float], default={}
        Simplified categorical decomposition for UI charts.
    block_monte_carlo : bool, default=False
        Flag to prevent stochastic simulation if data quality is too low.
    critical_warning : bool, default=False
        Indicates if any CRITICAL severity issues were identified.
    """
    global_score: float
    rating: str
    audit_mode: Union[InputSource, str]
    audit_depth: int = 0
    audit_coverage: float = 0.0
    audit_steps: List[AuditStep] = Field(default_factory=list)
    pillar_breakdown: Optional[AuditScoreBreakdown] = None
    logs: List[AuditLog] = Field(default_factory=list)
    breakdown: Dict[str, float] = Field(default_factory=dict)
    block_monte_carlo: bool = False
    critical_warning: bool = False


class ValuationOutputContract(BaseModel):
    """
    Validation output contract schema.

    Specifies the availability of essential parts in a valuation
    result to satisfy audit and UI rendering requirements.

    Attributes
    ----------
    has_params : bool
        Indicates if calculation parameters are present.
    has_projection : bool
        Indicates if future cash flow projections are available.
    has_terminal_value : bool
        Indicates if the terminal value has been calculated.
    has_intrinsic_value : bool
        Indicates if the final intrinsic value is available.
    has_audit : bool
        Indicates if a valid audit report has been generated.
    """
    model_config = ConfigDict(frozen=True)

    has_params: bool
    has_projection: bool
    has_terminal_value: bool
    has_intrinsic_value: bool
    has_audit: bool

    def is_valid(self) -> bool:
        """
        Validates if the output contract meets the minimum analytical requirements.

        Requirements:
            - Calculation parameters must be present.
            - Intrinsic value must be calculated.
            - Audit report must be generated.

        Returns
        -------
        bool
            True if all mandatory components are present.
        """
        return all([self.has_params, self.has_intrinsic_value, self.has_audit])