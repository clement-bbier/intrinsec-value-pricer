"""
src/models/glass_box.py

GLASS BOX TRACEABILITY MODELS
=============================
Role: Data structures for comprehensive valuation step tracking.
Scope: Supports financial auditing, pedagogical rendering, and variable lineage.
Architecture: Pydantic V2 containers for traceable calculation chains.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.config.constants import ModelDefaults
from src.core.formatting import format_smart_number
from src.models.enums import ParametersSource, VariableSource


class VariableInfo(BaseModel):
    """
    Detailed information for a specific variable in a formula.
    Tracks provenance and the impact of analyst overrides.
    """
    symbol: str = Field(..., description="Mathematical symbol (e.g., 'WACC').")
    value: float
    formatted_value: str = ""
    source: VariableSource = VariableSource.SYSTEM
    description: str = ""
    is_overridden: bool = False
    original_value: float | None = None

    def model_post_init(self, __context: Any) -> None:
        """Delegates formatting to the central utility."""
        if not self.formatted_value:
            # Symbols known to represent percentage values
            pct_symbols = {'r', 'g', 'Ke', 'Kd', 'Kd(1-t)', 'WACC', 'g_perp', 'tax', 'MRP', 'Rf'}
            self.formatted_value = format_smart_number(
                self.value,
                is_pct=(abs(self.value) < 1 and self.symbol in pct_symbols)
            )

class TraceHypothesis(BaseModel):
    """Qualitative assumption applied within a calculation step."""
    name: str
    value: Any
    unit: str = ""
    source: ParametersSource = ParametersSource.SYSTEM
    comment: str | None = None

class CalculationStep(BaseModel):
    """
    Documented Calculation Step.
    Represents a single mathematical formula applied in the process.
    """
    step_id: int = ModelDefaults.DEFAULT_STEP_ID
    step_key: str = ""
    label: str = ""
    theoretical_formula: str = ""  # LaTeX
    actual_calculation: str = ""    # Substituted values
    variables_map: dict[str, VariableInfo] = Field(default_factory=dict)
    hypotheses: list[TraceHypothesis] = Field(default_factory=list)
    result: float = ModelDefaults.DEFAULT_RESULT_VALUE
    unit: str = ""
    interpretation: str = ""
    source: str = ""

    def get_variable(self, symbol: str) -> VariableInfo | None:
        """Retrieves variable metadata by its mathematical symbol."""
        return self.variables_map.get(symbol)
