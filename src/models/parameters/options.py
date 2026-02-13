"""
src/models/parameters/options.py

ANALYTICAL EXTENSIONS PARAMETERS
================================
Role: Definitions of the data structures for optional modules.
Architecture: Pydantic V2 Models.
Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from src.config.constants import BacktestDefaults, MonteCarloDefaults, SensitivityDefaults, SOTPDefaults, UIKeys
from src.models.parameters.common import BaseNormalizedModel
from src.models.parameters.input_metadata import UIKey

# ==============================================================================
# 1. MONTE CARLO (STOCHASTIC)
# ==============================================================================

class BaseMCShocksParameters(BaseNormalizedModel):
    """Universal stochastic foundation."""
    growth_volatility: Annotated[float | None, UIKey(UIKeys.VOL_GROWTH, scale="pct")] = None

class BetaModelMCShocksParameters(BaseMCShocksParameters):
    """Models requiring Beta sensitivity."""
    beta_volatility: Annotated[float | None, UIKey(UIKeys.VOL_BETA, scale="pct")] = None

class StandardMCShocksParameters(BetaModelMCShocksParameters):
    """Shocks for standard DCF models."""
    type: Literal["standard"] = "standard"
    fcf_volatility: Annotated[float | None, UIKey(UIKeys.VOL_FLOW, scale="pct")] = None
    dividend_volatility: Annotated[float | None, UIKey(UIKeys.VOL_FLOW, scale="pct")] = None

class GrahamMCShocksParameters(BaseMCShocksParameters):
    """Shocks specific to Graham formula."""
    type: Literal["graham"] = "graham"
    eps_volatility: Annotated[float | None, UIKey(UIKeys.VOL_FLOW, scale="pct")] = None

MCShockUnion = StandardMCShocksParameters | GrahamMCShocksParameters

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
    random_seed : int | None
        Random seed for reproducibility (default: 42).
    """
    enabled: Annotated[bool, UIKey(UIKeys.MC_ENABLE, scale="raw")] = False
    iterations: Annotated[int, UIKey(UIKeys.MC_SIMS, scale="raw")] = Field(
        default=MonteCarloDefaults.DEFAULT_SIMULATIONS,
        ge=MonteCarloDefaults.MIN_SIMULATIONS,
        le=MonteCarloDefaults.MAX_SIMULATIONS
    )
    shocks: MCShockUnion | None = None
    random_seed: int | None = 42


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
    enabled: Annotated[bool, UIKey(UIKeys.SENS_ENABLE, scale="raw")] = False
    steps: Annotated[int, UIKey(UIKeys.SENS_RANGE, scale="raw")] = Field(
        default=SensitivityDefaults.DEFAULT_STEPS,
        ge=3, le=9
    )
    wacc_span: Annotated[float | None, UIKey(UIKeys.SENS_STEP, scale="pct")] = (
        SensitivityDefaults.DEFAULT_WACC_SPAN
    )
    growth_span: Annotated[float | None, UIKey(UIKeys.SENS_STEP, scale="pct")] = (
        SensitivityDefaults.DEFAULT_GROWTH_SPAN
    )


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
    probability: Annotated[float | None, UIKey(UIKeys.SCENARIO_P, scale="raw")] = None
    growth_override: Annotated[float | None, UIKey(UIKeys.SCENARIO_G, scale="pct")] = None
    margin_override: Annotated[float | None, UIKey(UIKeys.SCENARIO_M, scale="pct")] = None

class ScenariosParameters(BaseNormalizedModel):
    """Collection of deterministic scenarios."""
    enabled: Annotated[bool, UIKey(UIKeys.SCENARIO_ENABLE, scale="raw")] = False
    cases: list[ScenarioParameters] = Field(default_factory=list)

class BacktestParameters(BaseNormalizedModel):
    """Configuration for historical accuracy testing."""
    enabled: Annotated[bool, UIKey(UIKeys.BT_ENABLE, scale="raw")] = False
    lookback_years: Annotated[int, UIKey(UIKeys.BT_LOOKBACK, scale="raw")] = Field(
        default=BacktestDefaults.DEFAULT_LOOKBACK_YEARS,
        ge=1, le=10
    )

class PeersParameters(BaseNormalizedModel):
    """Configuration for peer-based relative valuation."""
    enabled: Annotated[bool, UIKey(UIKeys.PEER_ENABLE, scale="raw")] = False
    tickers: Annotated[list[str], UIKey(UIKeys.PEER_LIST)] = Field(default_factory=list)

class BusinessUnit(BaseModel):
    """A single segment in Sum-Of-The-Parts."""
    name: str
    value: float | None = None

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
    enabled: Annotated[bool, UIKey(UIKeys.SOTP_ENABLE, scale="raw")] = False
    conglomerate_discount: Annotated[float, UIKey(UIKeys.SOTP_DISCOUNT, scale="pct")] = (
        SOTPDefaults.DEFAULT_CONGLOMERATE_DISCOUNT
    )
    segments: Annotated[list[BusinessUnit], UIKey(UIKeys.SOTP_SEGS)] = Field(default_factory=list)


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
