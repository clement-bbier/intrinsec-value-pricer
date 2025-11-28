from dataclasses import dataclass
from typing import List


@dataclass
class CompanyFinancials:
    """
    Normalized financial data for a single company.
    This is what the infra layer (Yahoo, etc.) must provide.
    """
    ticker: str
    currency: str

    current_price: float
    shares_outstanding: float

    total_debt: float
    cash_and_equivalents: float

    fcf_last: float  # Last known Free Cash Flow to the Firm (FCFF)
    beta: float      # Equity beta used in CAPM


@dataclass
class DCFParameters:
    """
    Assumptions used in the DCF model.
    Usually come from config/settings.yaml + user overrides.
    """
    risk_free_rate: float        # Rf
    market_risk_premium: float   # MRP
    cost_of_debt: float          # pre-tax cost of debt
    tax_rate: float              # effective tax rate (0–1)

    fcf_growth_rate: float       # Stage 1 FCF growth (0–1)
    perpetual_growth_rate: float # Terminal growth (0–1)

    projection_years: int        # Number of years in the explicit forecast


@dataclass
class DCFResult:
    """
    Full DCF result, including intermediate values for transparency.
    """
    # Rates
    wacc: float
    cost_of_equity: float
    after_tax_cost_of_debt: float

    # Cash-flow projections
    projected_fcfs: List[float]
    discount_factors: List[float]

    # Valuation components
    sum_discounted_fcf: float
    terminal_value: float
    discounted_terminal_value: float
    enterprise_value: float
    equity_value: float

    # Final output
    intrinsic_value_per_share: float
