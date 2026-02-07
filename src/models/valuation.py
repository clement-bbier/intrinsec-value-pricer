"""
src/models/valuation.py

VALUATION ENVELOPES
===================
Role: Actionable triggers and result containers for the Backend.
Architecture: Clean-cut Request/Result separation.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from src.models.enums import ValuationMethodology
from src.models.parameters.base_parameter import Parameters
from src.core.diagnostics import DiagnosticEvent

class ValuationRequest(BaseModel):
    """
    The formal trigger sent to the Valuation Engine.

    Parameters already contains the Ticker (Pillar 1) and
    individual field sources. This envelope only adds the
    Instruction (Mode).
    """
    mode: ValuationMethodology = Field(..., description="Selected valuation model.")
    parameters: Parameters = Field(
        ...,
        description="The complete bundle containing Identity, Common, Strategy, and Extensions."
    )

class AuditReport(BaseModel):
    """Summary of the validation checks performed during valuation."""
    global_score: float = 100.0
    critical_warnings: int = 0
    events: List[DiagnosticEvent] = Field(default_factory=list)

class ValuationResult(BaseModel):
    """
    The final output envelope returned by the Engine.
    """
    # Traceability
    request: ValuationRequest

    # Outcomes
    intrinsic_value_per_share: float
    model_details: Dict[str, Any] = Field(default_factory=dict)
    audit_report: Optional[AuditReport] = None
    upside_pct: Optional[float] = None

    def compute_upside(self) -> None:
        """Calculates the potential upside/downside vs market price."""
        market_price = self.request.parameters.structure.current_price
        if market_price > 0:
            self.upside_pct = (self.intrinsic_value_per_share - market_price) / market_price
        else:
            self.upside_pct = 0.0