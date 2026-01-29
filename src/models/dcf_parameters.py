"""
src/models/dcf_parameters.py

DCF MODEL INPUT PARAMETERS
==========================
Role: Pure data structures for DCF model configuration.
Scope: Holds financial rates, growth assumptions, and simulation settings.
Architecture: Pydantic V2. Scaling logic is deferred to the UI entry layer.

Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from .enums import TerminalValueMethod
from .scenarios import ScenarioParameters, SOTPParameters
from src.config.constants import ModelDefaults


class CoreRateParameters(BaseModel):
    """Financial discounting and rate parameters (Standardized Units)."""
    risk_free_rate: Optional[float] = None
    risk_free_source: str = "N/A"
    market_risk_premium: Optional[float] = None
    corporate_aaa_yield: Optional[float] = None
    cost_of_debt: Optional[float] = None
    tax_rate: Optional[float] = None
    manual_cost_of_equity: Optional[float] = None
    wacc_override: Optional[float] = None
    manual_beta: Optional[float] = None


class GrowthParameters(BaseModel):
    """Forecasting and growth trajectory assumptions (Standardized Units)."""
    fcf_growth_rate: Optional[float] = None
    projection_years: int = ModelDefaults.DEFAULT_PROJECTION_YEARS
    high_growth_years: int = ModelDefaults.DEFAULT_HIGH_GROWTH_YEARS
    terminal_method: TerminalValueMethod = TerminalValueMethod.GORDON_GROWTH
    perpetual_growth_rate: Optional[float] = None
    exit_multiple_value: Optional[float] = None
    target_equity_weight: Optional[float] = None
    target_debt_weight: Optional[float] = None
    target_fcf_margin: Optional[float] = None
    annual_dilution_rate: Optional[float] = None

    # Analyst Overrides
    manual_fcf_base: Optional[float] = None
    manual_stock_price: Optional[float] = None
    manual_total_debt: Optional[float] = None
    manual_cash: Optional[float] = None
    manual_minority_interests: Optional[float] = None
    manual_pension_provisions: Optional[float] = None
    manual_shares_outstanding: Optional[float] = None
    manual_book_value: Optional[float] = None
    manual_net_borrowing: Optional[float] = None
    manual_dividend_base: Optional[float] = None


class MonteCarloConfig(BaseModel):
    """Probabilistic sensitivity configuration (Standardized Units)."""
    enable_monte_carlo: bool = False
    num_simulations: int = 2000
    base_flow_volatility: Optional[float] = None
    beta_volatility: Optional[float] = None
    growth_volatility: Optional[float] = None
    terminal_growth_volatility: Optional[float] = None
    correlation_beta_growth: float = -0.30


class DCFParameters(BaseModel):
    """Main orchestrator for DCF parameters."""
    rates: CoreRateParameters = Field(default_factory=CoreRateParameters)
    growth: GrowthParameters = Field(default_factory=GrowthParameters)
    monte_carlo: MonteCarloConfig = Field(default_factory=MonteCarloConfig)
    scenarios: ScenarioParameters = Field(default_factory=ScenarioParameters)
    sotp: SOTPParameters = Field(default_factory=SOTPParameters)

    @property
    def projection_years(self) -> int:
        return self.growth.projection_years

    def normalize_weights(self) -> None:
        """Normalizes Equity/Debt weights to ensure they sum to unity (1.0)."""
        w_e = self.growth.target_equity_weight or 0.0
        w_d = self.growth.target_debt_weight or 0.0
        total = w_e + w_d
        if total > 0:
            self.growth.target_equity_weight = w_e / total
            self.growth.target_debt_weight = w_d / total
        else:
            self.growth.target_equity_weight = 1.0
            self.growth.target_debt_weight = 0.0

    @classmethod
    def from_legacy(cls, data: Dict[str, Any]) -> DCFParameters:
        """Maps legacy flat dictionaries to the new segmented architecture."""
        return cls(
            rates=CoreRateParameters(**data),
            growth=GrowthParameters(**data),
            monte_carlo=MonteCarloConfig(**data)
        )