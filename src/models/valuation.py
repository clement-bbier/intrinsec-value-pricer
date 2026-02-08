"""
src/models/valuation.py

VALUATION ENVELOPES
===================
Role: Actionable triggers and result containers for the Backend.
Architecture: Clean-cut Request/Result separation.
"""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field

from src.models.enums import ValuationMethodology
from src.models.parameters.base_parameter import Parameters
from src.core.diagnostics import DiagnosticEvent

# IMPORTANT: Import the new Results structure
from src.models.results.base_result import Results

class ValuationRequest(BaseModel):
    """
    The formal trigger sent to the Valuation Engine.
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
    Contains the Request trace and the structured Results bundle.
    """
    # Traceability
    request: ValuationRequest

    # The Core Payload (The nested structure you were trying to pass)
    results: Results

    # Metadata & Reporting (Optional / Computed)
    audit_report: Optional[AuditReport] = None
    upside_pct: Optional[float] = None

    # Optional: Helper to access IV quickly without digging into results.common
    # Can be populated post-init or computed property.
    # For Pydantic v2, simpler to just access via .results.common.intrinsic_value_per_share

    def compute_upside(self) -> None:
        """Calculates the potential upside/downside vs market price."""
        market_price = self.request.parameters.structure.current_price
        iv = self.results.common.intrinsic_value_per_share

        if market_price and market_price > 0:
            self.upside_pct = (iv - market_price) / market_price
        else:
            self.upside_pct = 0.0