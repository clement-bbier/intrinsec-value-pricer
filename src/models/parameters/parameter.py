"""
src/models/params/main.py

ROOT PARAMETERS CONTAINER (THE INPUT BUNDLE)
============================================
Role: Central orchestrator for all valuation inputs.
Scope: Aggregates Identity, Common Levers, Strategy, and Extensions.
Architecture: Pydantic V2. This is the primary object passed to Calculation Engines.

Style: Numpy docstrings.
"""

from __future__ import annotations
from pydantic import BaseModel, Field

from src.models.company import Company
from src.models.parameters.common import CommonParameters
from src.models.parameters.strategies import StrategyUnionParameters
from src.models.parameters.options import ExtensionBundleParameters


class Parameters(BaseModel):
    """
    Unified container for a complete valuation session's inputs.

    This model follows the 'Ghost Architecture' where fields start as None
    to allow for a traceable resolution between User, Provider, and Fallback.
    """

    # --- Pillar 1: Identity (Frozen/Static) ---
    structure: Company = Field(
        description="Static company identity and market witness price."
    )

    # --- Pillar 2: Shared Levers (Environment & Structure) ---
    common: CommonParameters = Field(
        default_factory=CommonParameters,
        description="Universal inputs for WACC and Equity Bridge calculation."
    )

    # --- Pillar 3: Methodology (The Core Strategy) ---
    strategy: StrategyUnionParameters = Field(
        description="Specific inputs for the selected valuation model (e.g., DCF, Graham)."
    )

    # --- Pillar 4: Analytical Options (Optional Modules) ---
    extensions: ExtensionBundleParameters = Field(
        default_factory=ExtensionBundleParameters,
        description="Configuration for Monte Carlo, Scenarios, Peers, and SOTP."
    )