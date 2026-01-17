"""
core/models/dcf_inputs.py
Parametres d'entree pour les modeles DCF.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from core.models.enums import TerminalValueMethod
from core.models.scenarios import ScenarioParameters, SOTPParameters


def _decimal_guard(v: Any) -> Optional[float]:
    """Convertit les pourcentages en decimales si necessaire."""
    if v is None or v == "":
        return None
    try:
        val = float(v)
        return val / 100.0 if 1.0 < val <= 100.0 else val
    except (ValueError, TypeError):
        return None


class CoreRateParameters(BaseModel):
    """Parametres de taux (WACC, Ke, Kd)."""
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
    @classmethod
    def enforce_decimal(cls, v: Any) -> Any:
        return _decimal_guard(v)


class GrowthParameters(BaseModel):
    """Parametres de croissance et projections."""
    fcf_growth_rate: Optional[float] = None
    projection_years: int = 5
    high_growth_years: int = 0
    terminal_method: TerminalValueMethod = TerminalValueMethod.GORDON_GROWTH
    perpetual_growth_rate: Optional[float] = None
    exit_multiple_value: Optional[float] = None
    target_equity_weight: Optional[float] = None
    target_debt_weight: Optional[float] = None
    target_fcf_margin: Optional[float] = None

    # Surcharges Analyste
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

    @field_validator('fcf_growth_rate', 'perpetual_growth_rate', mode='before')
    @classmethod
    def enforce_decimal(cls, v: Any) -> Any:
        return _decimal_guard(v)


class MonteCarloConfig(BaseModel):
    """Configuration des simulations Monte Carlo."""
    enable_monte_carlo: bool = False
    num_simulations: int = 2000
    base_flow_volatility: Optional[float] = None
    beta_volatility: Optional[float] = None
    growth_volatility: Optional[float] = None
    terminal_growth_volatility: Optional[float] = None
    correlation_beta_growth: float = -0.30

    @field_validator('beta_volatility', 'growth_volatility', 'terminal_growth_volatility', mode='before')
    @classmethod
    def enforce_decimal(cls, v: Any) -> Any:
        return _decimal_guard(v)


class DCFParameters(BaseModel):
    """Conteneur principal des parametres DCF."""
    rates: CoreRateParameters = Field(default_factory=CoreRateParameters)
    growth: GrowthParameters = Field(default_factory=GrowthParameters)
    monte_carlo: MonteCarloConfig = Field(default_factory=MonteCarloConfig)
    scenarios: ScenarioParameters = Field(default_factory=ScenarioParameters)
    sotp: SOTPParameters = Field(default_factory=SOTPParameters)

    # Alias pour acces rapide
    @property
    def projection_years(self) -> int:
        return self.growth.projection_years

    def normalize_weights(self) -> None:
        """Normalise les poids equity/debt pour sommer a 1."""
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
    def from_legacy(cls, data: Dict[str, Any]) -> 'DCFParameters':
        """Construit depuis un dictionnaire plat (compatibilite)."""
        return cls(
            rates=CoreRateParameters(**data),
            growth=GrowthParameters(**data),
            monte_carlo=MonteCarloConfig(**data)
        )
