"""
src/models/results/main.py

ROOT RESULTS CONTAINER (THE OUTPUT BUNDLE)
==========================================
Role: Central orchestrator for all generated valuation outputs.
Scope: Aggregates Common results, Strategy projections, and Extension outputs.
Architecture: Pydantic V2. This is the primary object returned by the Engines.

Style: Numpy docstrings.
"""

from __future__ import annotations
from pydantic import BaseModel, Field

from src.models.results.common import CommonResults
from src.models.results.strategies import StrategyUnionResults
from src.models.results.options import ExtensionBundleResults


class Results(BaseModel):
    """
    Unified container for a complete valuation session's outputs.

    This model acts as the 'Mirror' of the Parameters object, storing only 
    the resolved and calculated data generated during the valuation process.
    """

    # --- Pillar 2: Common Results (WACC & Bridge) ---
    common: CommonResults = Field(
        description="Resolved financial environment and calculated Equity Bridge outputs."
    )

    # --- Pillar 3: Strategy Results (Projections) ---
    strategy: StrategyUnionResults = Field(
        description="Model-specific projection arrays and intermediate strategy outputs."
    )

    # --- Pillars 4 & 5: Extension Results (Optional Modules) ---
    extensions: ExtensionBundleResults = Field(
        description="Calculated outputs for Monte Carlo, Scenarios, Backtest, and Peers."
    )