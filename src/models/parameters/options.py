"""
src/models/parameters/options.py

ANALYTICAL EXTENSIONS PARAMETERS (DATA LAYER)
=============================================
Role: Definitions of the data structures for optional modules.
Architecture: Pydantic V2 Models.
Naming Convention: Must be named '...Parameters' to avoid confusion with Resolvers.
"""

from __future__ import annotations
from typing import List, Optional, Union, Literal, Annotated
from pydantic import Field, BaseModel

from src.models.parameters.ui_bridge import UIKey
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
    type: Literal["standard"] = "standard"
    fcf_volatility: Annotated[Optional[float], UIKey("vol_flow", scale="pct")] = None
    dividend_volatility: Annotated[Optional[float], UIKey("vol_flow", scale="pct")] = None

class GrahamMCShocksParameters(BaseMCShocksParameters):
    type: Literal["graham"] = "graham"
    eps_volatility: Annotated[Optional[float], UIKey("vol_flow", scale="pct")] = None

MCShockUnion = Union[StandardMCShocksParameters, GrahamMCShocksParameters]

class MCParameters(BaseNormalizedModel):
    """Configuration for Monte Carlo simulation."""
    enabled: Annotated[bool, UIKey("enable", scale="raw")] = False
    iterations: Annotated[Optional[int], UIKey("sims", scale="raw")] = Field(None, ge=100, le=50000)
    shocks: Optional[MCShockUnion] = None


# ==============================================================================
# 2. SENSITIVITY (DETERMINISTIC) - [Clean Code Update]
# ==============================================================================

class SensitivityParameters(BaseNormalizedModel):
    """Configuration for the 2D Sensitivity Matrix."""
    enabled: Annotated[bool, UIKey("sensi_enable", scale="raw")] = False
    steps: Annotated[Optional[int], UIKey("sensi_steps", scale="raw")] = Field(None, ge=3, le=9)
    wacc_span: Annotated[Optional[float], UIKey("sensi_wacc", scale="pct")] = None
    growth_span: Annotated[Optional[float], UIKey("sensi_growth", scale="pct")] = None


# ==============================================================================
# 3. SCENARIOS & EXTENSIONS
# ==============================================================================

class ScenarioParameters(BaseNormalizedModel):
    """Single scenario definition."""
    name: str = "Base Case"
    probability: Annotated[Optional[float], UIKey("p", scale="raw")] = None
    growth_override: Annotated[Optional[float], UIKey("g", scale="pct")] = None
    margin_override: Annotated[Optional[float], UIKey("m", scale="pct")] = None

class ScenariosParameters(BaseNormalizedModel):
    enabled: Annotated[bool, UIKey("scenario_enable", scale="raw")] = False
    cases: List[ScenarioParameters] = Field(default_factory=list)

class BacktestParameters(BaseNormalizedModel):
    enabled: Annotated[bool, UIKey("bt_enable", scale="raw")] = False
    lookback_years: Annotated[int, UIKey("bt_lookback", scale="raw")] = Field(3, ge=1, le=10)

class PeersParameters(BaseNormalizedModel):
    enabled: Annotated[bool, UIKey("peer_enable", scale="raw")] = False
    tickers: Annotated[List[str], UIKey("peer_list")] = Field(default_factory=list)

class BusinessUnit(BaseModel):
    name: str
    value: Optional[float] = None

class SOTPParameters(BaseNormalizedModel):
    enabled: Annotated[bool, UIKey("sotp_enable", scale="raw")] = False
    conglomerate_discount: Annotated[Optional[float], UIKey("sotp_disc", scale="pct")] = None
    segments: Annotated[List[BusinessUnit], UIKey("sotp_segs")] = Field(default_factory=list)

# ==============================================================================
# 4. THE BUNDLE
# ==============================================================================

class ExtensionBundleParameters(BaseModel):
    """
    Unified container for all optional analytical modules.
    Must use 'Parameters' suffix, NOT 'Resolvers'.
    """
    monte_carlo: MCParameters = Field(default_factory=MCParameters)
    sensitivity: SensitivityParameters = Field(default_factory=SensitivityParameters)
    scenarios: ScenariosParameters = Field(default_factory=ScenariosParameters)
    backtest: BacktestParameters = Field(default_factory=BacktestParameters)
    peers: PeersParameters = Field(default_factory=PeersParameters)
    sotp: SOTPParameters = Field(default_factory=SOTPParameters)