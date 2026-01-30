"""
src/models/parameters.py

DCF MODEL INPUT PARAMETERS
==========================
Role: Pure data structures for DCF model configuration.
Scope: Holds financial rates, growth assumptions, and simulation settings.
Architecture: Pydantic V2. Scaling logic is deferred to the UI entry layer.

Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field, model_validator, ConfigDict

from . import CalculationStep
from .enums import TerminalValueMethod, SOTPMethod
from src.config.constants import ModelDefaults
from ..i18n import MODEL_VALIDATION_TEXTS

class SubModelBase(BaseModel):
    model_config = ConfigDict(extra='ignore')

class MonteCarloParameters(SubModelBase):
    """Probabilistic sensitivity configuration (Standardized Units)."""
    enabled: bool = Field(default=False, alias="enable_monte_carlo")
    num_simulations: int = 2000
    base_flow_volatility: Optional[float] = None
    beta_volatility: Optional[float] = None
    growth_volatility: Optional[float] = None
    terminal_growth_volatility: Optional[float] = None
    correlation_beta_growth: float = -0.30

class ScenarioVariant(BaseModel):
    """
    Represents a specific deterministic sensitivity variant.

    Defines the input parameters for a specific outcome case (e.g., Bull).

    Attributes
    ----------
    label : str
        Name of the scenario (Bull, Base, Bear).
    growth_rate : float, optional
        Scenario-specific Phase 1 growth rate.
    target_fcf_margin : float, optional
        Scenario-specific target FCF margin for convergence models.
    probability : float, default=ModelDefaults.DEFAULT_PROBABILITY
        The statistical weight assigned to this variant.
    """
    label: str
    growth_rate: Optional[float] = None
    target_fcf_margin: Optional[float] = None
    probability: float = ModelDefaults.DEFAULT_PROBABILITY


class ScenarioResult(BaseModel):
    """
    Individual output of a calculated scenario.

    Stores the intrinsic value and effective inputs used for a single case.

    Attributes
    ----------
    label : str
        The applied scenario label.
    intrinsic_value : float
        The fair value per share calculated under this variant.
    probability : float
        The associated probability weight.
    growth_used : float
        The actual growth rate applied by the engine.
    margin_used : float
        The actual FCF margin applied by the engine.
    """
    label: str
    intrinsic_value: float
    probability: float
    growth_used: float
    margin_used: float


class ScenarioSynthesis(BaseModel):
    """
    Synthesis of all sensitivity variants for UI rendering.

    Aggregates results into a single "Expected Value" and identifies extreme bounds.

    Attributes
    ----------
    variants : List[ScenarioResult]
        The collection of results per scenario.
    expected_value : float
        The probability-weighted mean of all variants.
    max_upside : float
        The highest valuation outcome (usually Bull).
    max_downside : float
        The lowest valuation outcome (usually Bear).
    """
    variants: List[ScenarioResult] = Field(default_factory=list)
    expected_value: float = ModelDefaults.DEFAULT_EXPECTED_VALUE
    max_upside: float = ModelDefaults.DEFAULT_MAX_UPSIDE
    max_downside: float = ModelDefaults.DEFAULT_MAX_DOWNSIDE


class ScenarioParameters(SubModelBase):
    """
    Deterministic scenario orchestration block.

    Governs the configuration of the Bull/Base/Bear sensitivity analysis.

    Attributes
    ----------
    enabled : bool
        Flag to activate scenario-based valuation.
    bull : ScenarioVariant
        Configuration for the optimistic case.
    base : ScenarioVariant
        Configuration for the central/expected case.
    bear : ScenarioVariant
        Configuration for the pessimistic case.
    """
    enabled: bool = Field(default=False, alias="enable_scenario")
    bull: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Bull", probability=0.25))
    base: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Base", probability=0.50))
    bear: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Bear", probability=0.25))

    @model_validator(mode='after')
    def validate_probabilities(self) -> 'ScenarioParameters':
        """
        Ensures that scenario weights sum to 100% when the engine is enabled.

        Raises
        ------
        ValueError
            If the sum of probabilities is outside the 0.98 - 1.02 range.
        """
        if self.enabled:
            total = self.bull.probability + self.base.probability + self.bear.probability
            if not (0.98 <= total <= 1.02):
                raise ValueError(MODEL_VALIDATION_TEXTS.SCENARIO_PROBABILITIES_SUM_ERROR)
        return self

class BacktestParameters(SubModelBase):
    enabled: bool = Field(default=False, alias="enable_backtest")

class PeerParameters(SubModelBase):
    enabled: bool = Field(default=False, alias="enable_peer_multiples")
    manual_peers: Optional[List[str]] = None

class BusinessUnit(BaseModel):
    """
    Represents a conglomerate operational segment (SOTP).

    An independent operational unit valued using its own specific logic.

    Attributes
    ----------
    name : str
        The segment identifier (e.g., "Cloud Services").
    enterprise_value : float
        The calculated Enterprise Value for the segment.
    revenue : float, optional
        The segment's specific revenue for attribution checks.
    method : SOTPMethod
        Valuation logic applied (DCF, Multiples, etc.).
    contribution_pct : float, optional
        Relative percentage of the total conglomerate value.
    calculation_trace : List[CalculationStep]
        Granular traceability for the segment's valuation.
    """
    name: str
    enterprise_value: float
    revenue: Optional[float] = None
    method: SOTPMethod = SOTPMethod.DCF
    contribution_pct: Optional[float] = None
    calculation_trace: List[CalculationStep] = Field(default_factory=list)

class SOTPParameters(SubModelBase):
    enabled: bool = Field(default=False, alias="enable_sotp")
    segments: List[BusinessUnit] = Field(default_factory=list)
    conglomerate_discount: float = ModelDefaults.DEFAULT_CONGLOMERATE_DISCOUNT


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


class Parameters(BaseModel):
    """Main orchestrator for parameters."""
    rates: CoreRateParameters = Field(default_factory=CoreRateParameters)
    growth: GrowthParameters = Field(default_factory=GrowthParameters)
    monte_carlo: MonteCarloParameters = Field(default_factory=MonteCarloParameters)
    scenario: ScenarioParameters = Field(default_factory=ScenarioParameters)
    backtest: BacktestParameters = Field(default_factory=BacktestParameters)
    peers: PeerParameters = Field(default_factory=PeerParameters)
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
    def from_legacy(cls, data: Dict[str, Any]) -> Parameters:
        """Maps legacy flat dictionaries to the new segmented architecture."""
        return cls(
            rates=CoreRateParameters(**data),
            growth=GrowthParameters(**data),
            monte_carlo=MonteCarloParameters(**data),
            scenario=ScenarioParameters(**data),
            sotp=SOTPParameters(**data),
            backtest=BacktestParameters(**data),
            peers=PeerParameters(**data)
        )