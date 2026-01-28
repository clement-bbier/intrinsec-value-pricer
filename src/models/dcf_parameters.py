"""
src/models/dcf_parameters.py

DCF MODEL INPUT PARAMETERS
==========================
Role: Configuration structures for parameters used in Discounted Cash Flow models.
Scope: Includes financial rates, growth trajectories, and Monte Carlo configurations.
Architecture: Pydantic V2 with mandatory classmethod validators and decimal guarding.

Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from .enums import TerminalValueMethod
from .scenarios import ScenarioParameters, SOTPParameters
from src.config.constants import ModelDefaults


def _decimal_guard(v: Any) -> Optional[float]:
    r"""
    Safely converts percentage-based inputs into decimal form.

    Formula applied:
    $$val_{decimal} = \begin{cases} val / 100 & \text{if } 1.0 < val \le 100.0 \\ val & \text{otherwise} \end{cases}$$
    """
    if v is None or v == "":
        return None
    try:
        val = float(v)
        # Standardizes values where 1.0 < v <= 100.0 (e.g., 5.0 becomes 0.05)
        return val / 100.0 if 1.0 < val <= 100.0 else val
    except (ValueError, TypeError):
        return None


class CoreRateParameters(BaseModel):
    """Financial discounting and rate parameters."""
    risk_free_rate: Optional[float] = None
    risk_free_source: str = "N/A"
    market_risk_premium: Optional[float] = None
    corporate_aaa_yield: Optional[float] = None
    cost_of_debt: Optional[float] = None
    tax_rate: Optional[float] = None
    manual_cost_of_equity: Optional[float] = None
    wacc_override: Optional[float] = None
    manual_beta: Optional[float] = None

    @field_validator('risk_free_rate', 'market_risk_premium', 'corporate_aaa_yield',
                     'cost_of_debt', 'tax_rate', mode='before')
    def enforce_decimal(cls, v: Any) -> Any:
        """Applies decimal normalization to raw rate inputs."""
        return _decimal_guard(v)


class GrowthParameters(BaseModel):
    """Forecasting and growth trajectory assumptions."""
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

    @field_validator('fcf_growth_rate', 'perpetual_growth_rate', 'annual_dilution_rate', mode='before')
    def enforce_decimal(cls, v: Any) -> Any:
        """Applies decimal normalization to growth and dilution inputs."""
        return _decimal_guard(v)


class MonteCarloConfig(BaseModel):
    """Probabilistic sensitivity configuration."""
    enable_monte_carlo: bool = False
    num_simulations: int = 2000
    base_flow_volatility: Optional[float] = None
    beta_volatility: Optional[float] = None
    growth_volatility: Optional[float] = None
    terminal_growth_volatility: Optional[float] = None
    correlation_beta_growth: float = -0.30

    @field_validator('beta_volatility', 'growth_volatility', 'terminal_growth_volatility', mode='before')
    def enforce_decimal(cls, v: Any) -> Any:
        """Applies decimal normalization to volatility inputs."""
        return _decimal_guard(v)


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