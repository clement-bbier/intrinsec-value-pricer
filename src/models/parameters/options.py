"""
src/models/parameters/options.py

ANALYTICAL EXTENSIONS PARAMETERS
================================
Role: Modular overrides for Monte Carlo, Scenarios, Peers, and SOTP.
Architecture: Polymorphic Strategy-Aligned Shocks using BaseNormalizedModel.
"""

from __future__ import annotations
from typing import List, Optional, Union, Literal, Annotated
from pydantic import Field, BaseModel
from src.models.parameters.ui_bridge import UIKey
from .common import BaseNormalizedModel

class BaseMCShocksParameters(BaseNormalizedModel):
    """Universal stochastic foundation."""
    growth_volatility: Annotated[Optional[float], UIKey("vol_growth", scale="pct")] = None

class BetaModelMCShocksParameters(BaseMCShocksParameters):
    """Models requiring Beta sensitivity."""
    beta_volatility: Annotated[Optional[float], UIKey("vol_beta", scale="pct")] = None

class StandardMCShocksParameters(BetaModelMCShocksParameters):
    """Specific shocks for DCF Standard, DDM, and FCFE."""
    type: Literal["standard"] = "standard"
    fcf_volatility: Annotated[Optional[float], UIKey("vol_flow", scale="pct")] = None
    dividend_volatility: Annotated[Optional[float], UIKey("vol_flow", scale="pct")] = None

class GrahamMCShocksParameters(BaseMCShocksParameters):
    """Specific shocks for Graham screening."""
    type: Literal["graham"] = "graham"
    eps_volatility: Annotated[Optional[float], UIKey("vol_flow", scale="pct")] = None

MCShockUnion = Union[StandardMCShocksParameters, GrahamMCShocksParameters]

class MCParameters(BaseNormalizedModel):
    """Monte Carlo Simulation orchestrator."""
    enabled: Annotated[bool, UIKey("enable", scale="raw")] = False
    iterations: Annotated[Optional[int], UIKey("sims", scale="raw")] = Field(5000, ge=100, le=50000)
    shocks: Optional[MCShockUnion] = None

class ScenarioParameters(BaseNormalizedModel):
    """Single deterministic valuation case."""
    probability: Annotated[Optional[float], UIKey("p", scale="raw")] = None
    growth_override: Annotated[Optional[float], UIKey("g", scale="pct")] = None
    margin_override: Annotated[Optional[float], UIKey("m", scale="pct")] = None

class ScenariosParameters(BaseNormalizedModel):
    """Manager for weighted scenarios analysis."""
    enabled: Annotated[bool, UIKey("scenario_enable", scale="raw")] = False
    cases: List[ScenarioParameters] = Field(default_factory=list)

class ExtensionBundleParameters(BaseModel):
    """Unified container for all optional analytical modules."""
    monte_carlo: MCParameters = Field(default_factory=MCParameters)
    scenarios: ScenariosParameters = Field(default_factory=ScenariosParameters)