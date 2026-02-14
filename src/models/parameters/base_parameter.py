"""
src/models/parameters/base_parameter.py

ROOT PARAMETERS CONTAINER
=========================
Role: Central orchestrator for all valuation inputs.
Scope: Aggregates Identity, Common Levers, Strategy, and Extensions.
Architecture: Pydantic V2.
Style: Numpy docstrings.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.models.company import Company
from src.models.parameters.common import CommonParameters
from src.models.parameters.options import ExtensionBundleParameters
from src.models.parameters.strategies import StrategyUnionParameters


class Parameters(BaseModel):
    """
    Unified container for a complete valuation session's inputs.

    This model follows the 'Ghost Architecture': fields start as None
    to allow for a traceable resolution between User inputs, Provider data,
    and Defaults.

    Attributes
    ----------
    structure : Company
        Static company identity and market witness price (Ticker, Name, Price).
    common : CommonParameters
        Universal inputs for WACC (Rates) and Equity Bridge (Debt/Cash) calculation.
    strategy : StrategyUnionParameters
        Specific inputs for the selected valuation model (Polymorphic).
    extensions : ExtensionBundleParameters
        Configuration for Monte Carlo, Scenarios, Peers, and SOTP.
    """

    # --- Pillar 1: Identity (Frozen/Static) ---
    structure: Company = Field(description="Static company identity and market witness price.")

    # --- Pillar 2: Shared Levers (Environment & Structure) ---
    common: CommonParameters = Field(
        default_factory=CommonParameters, description="Universal inputs for WACC and Equity Bridge calculation."
    )

    # --- Pillar 3: Methodology (The Core Strategy) ---
    strategy: StrategyUnionParameters = Field(description="Specific inputs for the selected valuation model.")

    # --- Pillar 4: Analytical Options (Optional Modules) ---
    extensions: ExtensionBundleParameters = Field(
        default_factory=ExtensionBundleParameters,
        description="Configuration for Monte Carlo, Scenarios, Peers, and SOTP.",
    )
