"""
src/models/valuation.py

VALUATION ENVELOPES
===================
Role: Actionable triggers and result containers for the Backend.
Architecture: Clean-cut Request/Result separation.
Style: Numpy docstrings.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from src.core.diagnostics import DiagnosticEvent
from src.models.benchmarks import CompanyStats, MarketContext
from src.models.company import CompanySnapshot
from src.models.enums import ValuationMethodology
from src.models.parameters.base_parameter import Parameters

# IMPORTANT: Import the new Results structure
from src.models.results.base_result import Results


class ValuationRequest(BaseModel):
    """
    The formal trigger sent to the Valuation Engine.

    Attributes
    ----------
    mode : ValuationMethodology
        Selected valuation model (Strategy).
    parameters : Parameters
        The complete bundle containing Identity, Common, Strategy, and Extensions.
    """

    mode: ValuationMethodology = Field(..., description="Selected valuation model.")
    parameters: Parameters = Field(
        ..., description="The complete bundle containing Identity, Common, Strategy, and Extensions."
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

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    engine_version: str = "12.0.0"
    model_name: str
    ticker: str
    random_seed: int | None = None
    input_hash: str = ""
    execution_time_ms: int | None = None


class AuditReport(BaseModel):
    """
    Summary of the validation checks performed during valuation.

    Attributes
    ----------
    global_score : float
        Overall health score of the valuation inputs (0-100).
    critical_warnings : int
        Count of blocking or severe issues found.
    events : list[DiagnosticEvent]
        Detailed list of all validation events.
    """

    global_score: float = 100.0
    critical_warnings: int = 0
    events: list[DiagnosticEvent] = Field(default_factory=list)


class ValuationResult(BaseModel):
    """
    The final output envelope returned by the Engine.
    Contains the Request trace and the structured Results bundle.

    Attributes
    ----------
    request : ValuationRequest
        Traceability of the initial query.
    results : Results
        The core calculated payload (Common, Strategy, Extensions).
    financials : CompanySnapshot | None
        The raw financial snapshot from the data provider (Yahoo Finance).
        Contains the original currency and market data used for resolution.
    audit_report : AuditReport | None
        Validation and health checks report.
    upside_pct : float | None
        Computed potential upside vs market price.
    metadata : ValuationRunMetadata | None
        Execution details (timestamp, version, timing).
    market_context : MarketContext | None
        Sectoral benchmark data used for relative comparison (Pillar 3).
    company_stats : CompanyStats | None
        Computed ratios for the target company based on TTM data (Pillar 3).
    """

    # Traceability
    request: ValuationRequest

    # The Core Payload
    results: Results

    # Financial Snapshot (Source of Truth for display)
    financials: CompanySnapshot | None = Field(
        default=None, description="Raw financial snapshot from data provider (Yahoo Finance)."
    )

    # Metadata & Reporting (Optional / Computed)
    audit_report: AuditReport | None = None
    upside_pct: float | None = None
    metadata: ValuationRunMetadata | None = None

    # --- Contextual Data (Pillar 3) ---
    market_context: MarketContext | None = Field(
        default=None, description="Sectoral benchmark data used for relative comparison."
    )
    company_stats: CompanyStats | None = Field(
        default=None, description="Computed ratios for the target company based on TTM data."
    )

    def compute_upside(self) -> None:
        """Calculates the potential upside/downside vs market price."""
        market_price = self.request.parameters.structure.current_price
        iv = self.results.common.intrinsic_value_per_share

        if market_price and market_price > 0 and iv is not None:
            self.upside_pct = (iv - market_price) / market_price
        else:
            self.upside_pct = None  # Explicitly unknown
