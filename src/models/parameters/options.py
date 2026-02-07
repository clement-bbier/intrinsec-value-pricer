"""
src/models/parameters/options.py

ANALYTICAL EXTENSIONS PARAMETERS
================================
Role: Definitions of the data structures for optional modules.
Architecture: Pydantic V2 Models.
Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import List, Optional, Union, Literal, Annotated
from pydantic import Field, BaseModel

from src.models.parameters.input_metadata import UIKey
from src.models.parameters.common import BaseNormalizedModel


# ==============================================================================
# 1. MONTE CARLO (STOCHASTIC)
# ==============================================================================

class BaseMCShocksParameters(BaseNormalizedModel):
    """Universal stochastic foundation."""
    growth_volatility: Annotated[Optional[float], UIKey("vol_growth", scale="pct")] = None

class BetaModelMCShocksParameters(BaseMCShocksParameters):
    """Models requiring Beta sensitivity."""
    beta_volatility: Annotated[Optional[float], UIKey("vol_beta", scale="pct")] = None

class StandardMCShocksParameters(BetaModelMCShocksParameters):
    """Shocks for standard DCF models."""
    type: Literal["standard"] = "standard"
    fcf_volatility: Annotated[Optional[float], UIKey("vol_flow", scale="pct")] = None
    dividend_volatility: Annotated[Optional[float], UIKey("vol_flow", scale="pct")] = None

class GrahamMCShocksParameters(BaseMCShocksParameters):
    """Shocks specific to Graham formula."""
    type: Literal["graham"] = "graham"
    eps_volatility: Annotated[Optional[float], UIKey("vol_flow", scale="pct")] = None

MCShockUnion = Union[StandardMCShocksParameters, GrahamMCShocksParameters]

class MCParameters(BaseNormalizedModel):
    """
    Configuration for Monte Carlo simulation.

    Attributes
    ----------
    enabled : bool
        Whether to run the stochastic simulation.
    iterations : int | None
        Number of random draws (e.g., 5000).
    shocks : MCShockUnion | None
        Polymorphic container for volatility settings based on the strategy.
    """
    enabled: Annotated[bool, UIKey("enable", scale="raw")] = False
    iterations: Annotated[Optional[int], UIKey("sims", scale="raw")] = Field(None, ge=100, le=50000)
    shocks: Optional[MCShockUnion] = None


# ==============================================================================
# 2. SENSITIVITY (DETERMINISTIC)
# ==============================================================================

class SensitivityParameters(BaseNormalizedModel):
    """
    Configuration for the 2D Sensitivity Matrix.

    Attributes
    ----------
    enabled : bool
        Whether to generate the heatmap.
    steps : int | None
        Number of steps on each axis (e.g., 5 for a 5x5 matrix).
    wacc_span : float | None
        Range of deviation for WACC (e.g., 0.01 for +/- 1%).
    growth_span : float | None
        Range of deviation for Growth (e.g., 0.005 for +/- 0.5%).
    """
    enabled: Annotated[bool, UIKey("sensi_enable", scale="raw")] = False
    steps: Annotated[Optional[int], UIKey("sensi_steps", scale="raw")] = Field(None, ge=3, le=9)
    wacc_span: Annotated[Optional[float], UIKey("sensi_wacc", scale="pct")] = None
    growth_span: Annotated[Optional[float], UIKey("sensi_growth", scale="pct")] = None


# ==============================================================================
# 3. SCENARIOS & EXTENSIONS
# ==============================================================================

class ScenarioParameters(BaseNormalizedModel):
    """
    Single scenario definition.

    Attributes
    ----------
    name : str
        Label of the scenario (e.g., "Bear Case").
    probability : float | None
        Weight of the scenario in the weighted average (0.0 to 1.0).
    growth_override : float | None
        Hard adjustment to the base growth rate.
    margin_override : float | None
        Hard adjustment to the base margins.
    """
    name: str = "Base Case"
    probability: Annotated[Optional[float], UIKey("p", scale="raw")] = None
    growth_override: Annotated[Optional[float], UIKey("g", scale="pct")] = None
    margin_override: Annotated[Optional[float], UIKey("m", scale="pct")] = None

class ScenariosParameters(BaseNormalizedModel):
    """Collection of deterministic scenarios."""
    enabled: Annotated[bool, UIKey("scenario_enable", scale="raw")] = False
    cases: List[ScenarioParameters] = Field(default_factory=list)

class BacktestParameters(BaseNormalizedModel):
    """Configuration for historical accuracy testing."""
    enabled: Annotated[bool, UIKey("bt_enable", scale="raw")] = False
    lookback_years: Annotated[int, UIKey("bt_lookback", scale="raw")] = Field(3, ge=1, le=10)

class PeersParameters(BaseNormalizedModel):
    """Configuration for peer-based relative valuation."""
    enabled: Annotated[bool, UIKey("peer_enable", scale="raw")] = False
    tickers: Annotated[List[str], UIKey("peer_list")] = Field(default_factory=list)

class BusinessUnit(BaseModel):
    """A single segment in Sum-Of-The-Parts."""
    name: str
    value: Optional[float] = None

class SOTPParameters(BaseNormalizedModel):
    """
    Configuration for Sum-Of-The-Parts (Conglomerate) valuation.

    Attributes
    ----------
    enabled : bool
        Whether to use SOTP instead of consolidated DCF.
    conglomerate_discount : float | None
        Discount applied to the sum of parts (typically 10-20%).
    segments : List[BusinessUnit]
        List of manual valuations per business unit.
    """
    enabled: Annotated[bool, UIKey("sotp_enable", scale="raw")] = False
    conglomerate_discount: Annotated[Optional[float], UIKey("sotp_disc", scale="pct")] = None
    segments: Annotated[List[BusinessUnit], UIKey("sotp_segs")] = Field(default_factory=list)


# ==============================================================================
# 4. THE BUNDLE
# ==============================================================================

class ExtensionBundleParameters(BaseModel):
    """
    Unified container for all optional analytical modules.

    Attributes
    ----------
    monte_carlo : MCParameters
        Stochastic simulation settings.
    sensitivity : SensitivityParameters
        Sensitivity heatmap settings.
    scenarios : ScenariosParameters
        Multi-scenario analysis settings.
    backtest : BacktestParameters
        Historical backtesting settings.
    peers : PeersParameters
        Relative valuation settings.
    sotp : SOTPParameters
        Sum-Of-The-Parts settings.
    """
    monte_carlo: MCParameters = Field(default_factory=MCParameters)
    sensitivity: SensitivityParameters = Field(default_factory=SensitivityParameters)
    scenarios: ScenariosParameters = Field(default_factory=ScenariosParameters)
    backtest: BacktestParameters = Field(default_factory=BacktestParameters)
    peers: PeersParameters = Field(default_factory=PeersParameters)
    sotp: SOTPParameters = Field(default_factory=SOTPParameters)