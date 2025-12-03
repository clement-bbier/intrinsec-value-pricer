from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class ValuationMode(str, Enum):
    """
    Available valuation modes for the DCF engine.
    Internal technical enum; UI will map this to nicer labels.
    """

    SIMPLE_FCFF = "simple_fcff"
    FUNDAMENTAL_FCFF = "fundamental_fcff"
    MARKET_MULTIPLES = "market_multiples"
    ADVANCED_SIMULATION = "advanced_simulation"


@dataclass
class CompanyFinancials:
    """
    Normalized financial data for a single company.
    Provided by data providers (e.g., Yahoo).
    """

    ticker: str
    currency: str

    current_price: float
    shares_outstanding: float

    total_debt: float
    cash_and_equivalents: float

    fcf_last: float  # Last known Free Cash Flow to the Firm (FCFF)
    beta: float      # Equity beta used in CAPM

    def to_log_dict(self) -> Dict[str, Any]:
        """Return a dict representation useful for structured logging."""
        return {
            "ticker": self.ticker,
            "currency": self.currency,
            "current_price": self.current_price,
            "shares_outstanding": self.shares_outstanding,
            "total_debt": self.total_debt,
            "cash_and_equivalents": self.cash_and_equivalents,
            "fcf_last": self.fcf_last,
            "beta": self.beta,
        }

    def __repr__(self) -> str:
        return (
            f"CompanyFinancials("
            f"ticker={self.ticker}, currency={self.currency}, "
            f"price={self.current_price:.2f}, shares={self.shares_outstanding:.0f}, "
            f"debt={self.total_debt:.2f}, cash={self.cash_and_equivalents:.2f}, "
            f"fcf_last={self.fcf_last:.2f}, beta={self.beta:.3f})"
        )


@dataclass
class DCFParameters:
    """
    Assumptions used in the DCF valuation.
    Derived from settings + provider logic.
    """

    risk_free_rate: float        # Rf
    market_risk_premium: float   # MRP
    cost_of_debt: float          # pre-tax cost of debt
    tax_rate: float              # effective tax rate (0–1)

    fcf_growth_rate: float       # Stage 1 FCF growth (0–1)
    perpetual_growth_rate: float # Terminal growth (0–1)

    projection_years: int        # Number of forecast years

    def to_log_dict(self) -> Dict[str, Any]:
        return {
            "risk_free_rate": self.risk_free_rate,
            "market_risk_premium": self.market_risk_premium,
            "cost_of_debt": self.cost_of_debt,
            "tax_rate": self.tax_rate,
            "fcf_growth_rate": self.fcf_growth_rate,
            "perpetual_growth_rate": self.perpetual_growth_rate,
            "projection_years": self.projection_years,
        }

    def __repr__(self) -> str:
        return (
            f"DCFParameters(Rf={self.risk_free_rate:.4f}, MRP={self.market_risk_premium:.4f}, "
            f"Rd={self.cost_of_debt:.4f}, Tax={self.tax_rate:.3f}, "
            f"g=${self.fcf_growth_rate:.4f}, g∞={self.perpetual_growth_rate:.4f}, "
            f"years={self.projection_years})"
        )


@dataclass
class DCFResult:
    """
    Full DCF result, with intermediate values for transparency.
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

    # Final result
    intrinsic_value_per_share: float

    def to_log_dict(self) -> Dict[str, Any]:
        return {
            "wacc": self.wacc,
            "cost_of_equity": self.cost_of_equity,
            "after_tax_cost_of_debt": self.after_tax_cost_of_debt,
            "projected_fcfs": self.projected_fcfs,
            "discount_factors": self.discount_factors,
            "sum_discounted_fcf": self.sum_discounted_fcf,
            "terminal_value": self.terminal_value,
            "discounted_terminal_value": self.discounted_terminal_value,
            "enterprise_value": self.enterprise_value,
            "equity_value": self.equity_value,
            "intrinsic_value_per_share": self.intrinsic_value_per_share,
        }

    def __repr__(self) -> str:
        return (
            "DCFResult("
            f"WACC={self.wacc:.4f}, "
            f"Re={self.cost_of_equity:.4f}, "
            f"Rd_after_tax={self.after_tax_cost_of_debt:.4f}, "
            f"EV={self.enterprise_value:.2f}, "
            f"Equity={self.equity_value:.2f}, "
            f"IV/share={self.intrinsic_value_per_share:.2f})"
        )
