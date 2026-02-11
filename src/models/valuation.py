"""
src/models/valuation.py

VALUATION ENVELOPES
===================
Role: Actionable triggers and result containers for the Backend.
Architecture: Clean-cut Request/Result separation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from src.core.diagnostics import DiagnosticEvent
from src.models.enums import ValuationMethodology
from src.models.parameters.base_parameter import Parameters

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

class ValuationRunMetadata(BaseModel):
    """
    Immutable provenance record for every valuation run.

    Attributes
    ----------
    run_id : str
        Unique identifier for this valuation run.
    timestamp_utc : datetime
        UTC timestamp when the valuation was executed.
    engine_version : str
        Version of the valuation engine.
    model_name : str
        Valuation methodology used (e.g., "FCFF_STANDARD").
    ticker : str
        Stock ticker symbol.
    random_seed : int, optional
        Monte Carlo random seed for reproducibility.
    input_hash : str
        SHA-256 hash of serialized DCFParameters for change detection.
    execution_time_ms : int, optional
        Execution time in milliseconds.
    """
    model_config = ConfigDict(frozen=True)

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    engine_version: str = "12.0.0"
    model_name: str
    ticker: str
    random_seed: int | None = None
    input_hash: str = ""
    execution_time_ms: int | None = None

class AuditReport(BaseModel):
    """Summary of the validation checks performed during valuation."""
    global_score: float = 100.0
    critical_warnings: int = 0
    events: list[DiagnosticEvent] = Field(default_factory=list)

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
    audit_report: AuditReport | None = None
    upside_pct: float | None = None
    metadata: ValuationRunMetadata | None = None

    # Optional: Helper to access IV quickly without digging into results.common
    # Can be populated post-init or computed property.
    # For Pydantic v2, simpler to just access via .results.common.intrinsic_value_per_share

    def compute_upside(self) -> None:
        """Calculates the potential upside/downside vs market price."""
        market_price = self.request.parameters.structure.current_price
        iv = self.results.common.intrinsic_value_per_share

        if market_price and market_price > 0 and iv is not None:
            self.upside_pct = (iv - market_price) / market_price
        else:
            self.upside_pct = None  # Explicitly unknown
