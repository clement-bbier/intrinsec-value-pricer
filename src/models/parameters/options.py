"""
src/models/params/options.py

ANALYTICAL EXTENSIONS PARAMETERS (MASTER ARCHITECTURE)
====================================================
Role: Modular overrides for Monte Carlo, Scenarios, Peers, and SOTP.
Scope: Stochastic shocks, deterministic cases, historical audits, and segment analysis.
Architecture: Polymorphic Strategy-Aligned Shocks.
              Factors common volatility parameters without polluting Graham with Beta logic.
"""

from __future__ import annotations
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field

# ==============================================================================
# 1. MONTE CARLO STOCHASTIC SHOCKS (Polymorphic Branching)
# ==============================================================================

class BaseMCShocks(BaseModel):
    """Universal stochastic foundation for all projection models."""
    growth_volatility: Optional[float] = Field(None, description="Volatility of the FCF/Revenue/Earnings growth rate.")

class BetaModelMCShocks(BaseMCShocks):
    """Intermediate branch for models requiring Beta/WACC sensitivity (DCF, RIM, DDM)."""
    beta_volatility: Optional[float] = Field(None, description="Volatility of the systematic risk factor (Beta).")

class StandardMCShocks(BetaModelMCShocks):
    """Specific shocks for DCF Standard, DDM, and FCFE models."""
    type: Literal["standard"] = "standard"
    fcf_volatility: Optional[float] = Field(None, description="Volatility of the base Cash Flow.")
    dividend_volatility: Optional[float] = Field(None, description="Volatility of the dividend payout.")

class GrowthMCShocks(BetaModelMCShocks):
    """Specific shocks for Revenue/Margin Growth models."""
    type: Literal["growth"] = "growth"
    revenue_volatility: Optional[float] = Field(None, description="Volatility of the top-line revenue.")
    margin_volatility: Optional[float] = Field(None, description="Volatility of the FCF/EBITDA margin.")

class RIMMCShocks(BetaModelMCShocks):
    """Specific shocks for Residual Income (RIM) models."""
    type: Literal["rim"] = "rim"
    roe_volatility: Optional[float] = Field(None, description="Volatility of the Return on Equity.")

class GrahamMCShocks(BaseMCShocks):
    """Specific shocks for Graham screening (Strictly ignores Beta/Market Volatility)."""
    type: Literal["graham"] = "graham"
    eps_volatility: Optional[float] = Field(None, description="Volatility of the Normalized EPS.")

# Union for Pydantic type discrimination
MCShockUnion = Union[StandardMCShocks, GrowthMCShocks, RIMMCShocks, GrahamMCShocks]

class MCParameters(BaseModel):
    """
    Monte Carlo Simulation orchestrator.

    The 'shocks' attribute will automatically adapt its fields based on
    the selected valuation strategy.
    """
    enabled: bool = False
    iterations: Optional[int] = Field(5000, ge=100, le=50000)
    shocks: Optional[MCShockUnion] = None

# ==============================================================================
# 2. DETERMINISTIC SCENARIOS & PEERS
# ==============================================================================

class Scenario(BaseModel):
    """
    Represents a single deterministic valuation case.
    Used for multi-scenario weighting (e.g., Bull, Base, Bear).
    """
    name: str
    probability: Optional[float] = Field(0.33, ge=0, le=1)
    growth_override: Optional[float] = None
    margin_override: Optional[float] = None
    eps_override: Optional[float] = None

class ScenariosParameters(BaseModel):
    """Manager for probabilistic weighted scenarios analysis."""
    enabled: bool = False
    cases: List[Scenario] = Field(default_factory=list)

class PeersParameters(BaseModel):
    """Configuration for relative valuation and peer-group triangulation."""
    enabled: bool = False
    tickers: List[str] = Field(default_factory=list)

# ==============================================================================
# 3. STRUCTURAL EXTENSIONS (SOTP & BACKTEST)
# ==============================================================================

class BacktestParameters(BaseModel):
    """Settings for historical accuracy and model performance tracking."""
    enabled: bool = False
    lookback_years: Optional[int] = Field(3, ge=1, le=10)

class SOTPSegment(BaseModel):
    """Represents an individual business unit in a SOTP valuation."""
    name: str
    ev_value: Optional[float] = None
    method: str = "Market"

class SOTPParameters(BaseModel):
    """Configuration for Sum-of-the-Parts (conglomerate) valuation."""
    enabled: bool = False
    conglomerate_discount: Optional[float] = Field(0.0, ge=0, le=1)
    segments: List[SOTPSegment] = Field(default_factory=list)

# ==============================================================================
# 4. THE BUNDLE (Unified Container)
# ==============================================================================

class ExtensionBundleParameters(BaseModel):
    """Unified container for all optional analytical modules."""
    monte_carlo: MCParameters = Field(default_factory=MCParameters)
    scenarios: ScenariosParameters = Field(default_factory=ScenariosParameters)
    backtest: BacktestParameters = Field(default_factory=BacktestParameters)
    peers: PeersParameters = Field(default_factory=PeersParameters)
    sotp: SOTPParameters = Field(default_factory=SOTPParameters)