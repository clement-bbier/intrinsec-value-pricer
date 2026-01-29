"""
src/models/glass_box.py

GLASS BOX TRACEABILITY MODELS
=============================
Role: Data structures for comprehensive valuation step tracking.
Scope: Supports financial auditing, pedagogical rendering, and variable lineage.
Architecture: Pydantic-based containers for traceable calculation chains.

Style: Numpy docstrings.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .enums import AuditSeverity
from src.config.constants import ModelDefaults


class VariableSource(str, Enum):
    """
    Source of a variable used in a calculation.

    Categorizes the origin of data points to drive audit confidence scoring.
    """

    YAHOO_FINANCE = "Yahoo Finance"
    MANUAL_OVERRIDE = "Surcharge Expert"
    CALCULATED = "Calculé"
    DEFAULT = "Défaut Système"
    MACRO_PROVIDER = "Données Macro"


class VariableInfo(BaseModel):
    """
    Detailed information for a specific variable in a formula.

    Tracks every component of a mathematical expression, including its
    provenance and the impact of analyst overrides.

    Attributes
    ----------
    symbol : str
        Mathematical symbol (e.g., "WACC", "g", "FCF₀").
    value : float
        The raw numeric value used in the calculation.
    formatted_value : str, default=""
        Display-ready value (e.g., "8.50%", "150.50 M€").
    source : VariableSource, default=VariableSource.CALCULATED
        Origin identifier (Yahoo, Expert, Calculated, etc.).
    description : str, default=""
        Pedagogical description of the variable's role.
    is_overridden : bool, default=False
        Flag indicating if the user manually changed the automated value.
    original_value : float, optional
        The original automated value if an override was applied.
    """
    symbol: str
    value: float
    formatted_value: str = ""
    source: VariableSource = VariableSource.CALCULATED
    description: str = ""
    is_overridden: bool = False
    original_value: Optional[float] = None

    def model_post_init(self, __context: Any) -> None:
        """
        Generates formatted_value if not explicitly provided.
        Standardizes financial units (Billions, Millions, Percentages).
        """
        if not self.formatted_value:
            if abs(self.value) < 1:
                self.formatted_value = f"{self.value:.2%}"
            elif abs(self.value) >= 1e9:
                self.formatted_value = f"{self.value/1e9:,.2f} B"
            elif abs(self.value) >= 1e6:
                self.formatted_value = f"{self.value/1e6:,.2f} M"
            else:
                self.formatted_value = f"{self.value:,.2f}"


class TraceHypothesis(BaseModel):
    """
    Specific hypothesis applied within a calculation step.

    Used to document qualitative assumptions or fixed parameters.

    Attributes
    ----------
    name : str
        The name of the hypothesis.
    value : Any
        The associated value.
    unit : str, default=""
        Unit of measurement.
    source : str, default="auto"
        Source identifier.
    comment : str, optional
        Contextual analyst notes.
    """
    name: str
    value: Any
    unit: str = ""
    source: str = "auto"
    comment: Optional[str] = None


class CalculationStep(BaseModel):
    """
    Documented Calculation Step (Glass Box Pillar).

    Represents a single mathematical formula applied in the valuation process,
    fully traceable for audit and analyst education.

    Attributes
    ----------
    step_id : int, default=ModelDefaults.DEFAULT_STEP_ID
        Sequential ID of the step in the workflow.
    step_key : str, default=""
        Unique registry key for i18n lookup.
    label : str, default=""
        Display title for the calculation step.
    theoretical_formula : str, default=""
        LaTeX representation of the abstract formula.
    actual_calculation : str, default=""
        Numerical substitution string showing real values in the formula.
    variables_map : Dict[str, VariableInfo], default={}
        Mapping of symbols to their detailed variable metadata.
    hypotheses : List[TraceHypothesis], default=[]
        List of assumptions specifically linked to this step.
    actual_calculation : str, default=""
        Legacy formatted substitution string.
    result : float, default=ModelDefaults.DEFAULT_RESULT_VALUE
        The numeric output of the calculation.
    unit : str, default=""
        Result unit (e.g., €, %, x).
    interpretation : str, default=""
        Localized pedagogical explanation of the result.
    """
    step_id: int = ModelDefaults.DEFAULT_STEP_ID
    step_key: str = ""
    label: str = ""
    theoretical_formula: str = ""
    actual_calculation: str = ""
    variables_map: Dict[str, VariableInfo] = Field(default_factory=dict)
    hypotheses: List[TraceHypothesis] = Field(default_factory=list)
    result: float = ModelDefaults.DEFAULT_RESULT_VALUE
    unit: str = ""
    interpretation: str = ""
    source: str = ""

    def get_variable(self, symbol: str) -> Optional[VariableInfo]:
        """Retrieves variable metadata by its mathematical symbol."""
        return self.variables_map.get(symbol)

    def has_overrides(self) -> bool:
        """Determines if any component of this step was manually overridden."""
        return any(v.is_overridden for v in self.variables_map.values())


class AuditStep(BaseModel):
    """
    Audit Check Step with Verdict.

    Represents a single consistency or risk verification performed
    by the Audit Engine.

    Attributes
    ----------
    step_id : int, default=ModelDefaults.DEFAULT_STEP_ID
        Sequential order of the check.
    step_key : str, default=""
        Unique identifier for the audit check.
    label : str, default=""
        Human-readable title of the check.
    rule_formula : str, default=""
        The business rule formula (LaTeX or text).
    indicator_value : Union[float, str], default=ModelDefaults.DEFAULT_INDICATOR_VALUE
        The observed value of the KPI being tested.
    threshold_value : Union[float, str, None]
        The limit or benchmark for the check.
    severity : AuditSeverity, default=AuditSeverity.INFO
        Classification of the risk (CRITICAL, WARNING, etc.).
    verdict : bool, default=True
        Result of the validation (True = PASS).
    evidence : str, default=""
        Justification or detailed finding for the verdict.
    description : str, default=""
        Detailed background on the audit check.
    """
    step_id: int = ModelDefaults.DEFAULT_STEP_ID
    step_key: str = ""
    label: str = ""
    rule_formula: str = ""
    indicator_value: Union[float, str] = ModelDefaults.DEFAULT_INDICATOR_VALUE
    threshold_value: Union[float, str, None] = None
    severity: AuditSeverity = AuditSeverity.INFO
    verdict: bool = True
    evidence: str = ""
    description: str = ""