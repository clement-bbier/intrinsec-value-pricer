"""
src/models/company.py

COMPANY IDENTITY & CLASSIFICATION
=================================
Role: Descriptive and immutable data container.
Scope: Identity, sector, industry, and current market price (as a witness).
Architecture: Pydantic V2. Contains no overrideable calculation data.

Style: Numpy docstrings.
"""

from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class Company(BaseModel):
    """
    Represents the fixed identity of a company.

    This class serves as a reference for display and audit (Pillar 1).
    It contains only descriptive data that is not intended to be
    modified for the financial calculation itself.
    """
    # Immutable to ensure integrity throughout the workflow
    model_config = ConfigDict(frozen=True)

    # --- Identification ---
    ticker: str
    name: str = "Unknown"
    currency: str

    # --- Sectoral Classification ---
    sector: str = "Unknown"
    industry: str = "Unknown"
    country: str = "Unknown"
    headquarters: str = "Unknown"

    # --- Market Witness (Sacred) ---
    current_price: float

'''
src/models/financials.py

UNIFIED COMPANY FINANCIALS MODEL
================================
Role: Central data container for company-specific financial information.
Scope: Aggregates identity, market prices, balance sheets, and cash flow metrics.
Architecture: Pydantic-based for type safety and automated validation.

Style: Numpy docstrings.


from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict
from src.config.constants import ModelDefaults




class Company(BaseModel):
    """
    Unified container for company financial data.

    This model centralizes all variables required for DCF, Graham, and RIM
    valuation engines, as well as sectoral peer triangulation.

    Attributes
    ----------
    ticker : str
        The stock market ticker symbol.
    name : str, default="Unknown"
        Legal name of the entity.
    currency : str
        Reporting currency for all numeric values.
    sector : str, default="Unknown"
        Broad economic sector (e.g., Technology).
    industry : str, default="Unknown"
        Specific industry classification.
    country : str, default="Unknown"
        Country of headquarters or primary exchange.
    current_price : float
        Latest available market price per share.
    shares_outstanding : float
        Total count of shares currently in circulation.
    beta : float
        Systemic risk coefficient (Market Beta).
    total_debt : float
        Gross interest-bearing liabilities.
    cash_and_equivalents : float
        Total liquid assets and near-cash instruments.
    minority_interests : float
        Portion of subsidiaries not owned by the parent.
    pension_provisions : float
        Liabilities for employee post-retirement benefits.
    book_value : float
        Total shareholder equity (Accounting value).
    book_value_per_share : float, optional
        Book value divided by shares outstanding.
    revenue_ttm : float, optional
        Trailing Twelve Months total revenue.
    ebitda_ttm : float, optional
        Trailing Twelve Months EBITDA.
    ebit_ttm : float, optional
        Trailing Twelve Months EBIT (Operating Income).
    net_income_ttm : float, optional
        Trailing Twelve Months Net Profit.
    interest_expense : float
        Annual interest charges on debt.
    eps_ttm : float, optional
        Trailing Twelve Months Earnings Per Share.
    dividend_share : float, optional
        Latest annual dividend paid per share.
    fcf_last : float, optional
        Most recent Free Cash Flow value.
    fcf_fundamental_smoothed : float, optional
        Averaged or normalized fundamental FCF.
    net_borrowing_ttm : float, optional
        Net change in debt principal over the last 12 months.
    capex : float, optional
        Capital expenditures for the period.
    depreciation_and_amortization : float, optional
        Non-cash D&A charges.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # --- Identity & Classification ---
    ticker: str
    name: str = "Unknown"
    currency: str
    sector: str = "Unknown"
    industry: str = "Unknown"
    country: str = "Unknown"

    # --- Market Context ---
    current_price: float
    shares_outstanding: float
    beta: float = ModelDefaults.DEFAULT_BETA

    # --- Balance Sheet (Equity Bridge Components) ---
    total_debt: float = ModelDefaults.DEFAULT_TOTAL_DEBT
    cash_and_equivalents: float = ModelDefaults.DEFAULT_CASH_EQUIVALENTS
    minority_interests: float = ModelDefaults.DEFAULT_MINORITY_INTERESTS
    pension_provisions: float = ModelDefaults.DEFAULT_PENSION_PROVISIONS
    book_value: float = ModelDefaults.DEFAULT_BOOK_VALUE
    book_value_per_share: Optional[float] = None

    # --- Income Statement (Performance) ---
    revenue_ttm: Optional[float] = None
    ebitda_ttm: Optional[float] = None
    ebit_ttm: Optional[float] = None
    net_income_ttm: Optional[float] = None
    interest_expense: float = ModelDefaults.DEFAULT_INTEREST_EXPENSE
    eps_ttm: Optional[float] = None

    # --- Cash Flow & Reconciliation ---
    dividend_share: Optional[float] = None
    fcf_last: Optional[float] = None
    fcf_fundamental_smoothed: Optional[float] = None
    net_borrowing_ttm: Optional[float] = None
    capex: Optional[float] = None
    depreciation_and_amortization: Optional[float] = None

    @property
    def market_cap(self) -> float:
        """
        Calculates the total Market Capitalization.
        $$MarketCap = Price \times Shares_{outstanding}$$
        """
        return self.current_price * self.shares_outstanding

    @property
    def net_debt(self) -> float:
        """
        Calculates the Net Debt position.
        $$NetDebt = TotalDebt - Cash$$
        """
        return self.total_debt - self.cash_and_equivalents

    @property
    def dividends_total_calculated(self) -> float:
        """
        Calculates total dividends paid to all shares.
        $$Dividends_{total} = DPS \times Shares_{outstanding}$$
        """
        return (self.dividend_share or 0.0) * self.shares_outstanding

    @property
    def fcf(self) -> Optional[float]:
        """Alias for fcf_last to support legacy engine calls."""
        return self.fcf_last

    @property
    def pe_ratio(self) -> Optional[float]:
        """
        Calculates the Price-to-Earnings (P/E) Ratio.
        Returns None if data is missing or if earnings are negative.
        """
        if (self.eps_ttm is not None and self.eps_ttm > 0 and
            self.current_price is not None and self.current_price > 0):
            return self.current_price / self.eps_ttm
        return None

    @property
    def pb_ratio(self) -> Optional[float]:
        """
        Calculates the Price-to-Book (P/B) Ratio.
        """
        if (self.book_value_per_share is not None and self.book_value_per_share > 0 and
            self.current_price is not None and self.current_price > 0):
            return self.current_price / self.book_value_per_share
        return None

    @property
    def ev_ebitda_ratio(self) -> Optional[float]:
        """
        Calculates the EV/EBITDA Ratio.
        Note: Per legacy logic, this uses Market Cap as the numerator proxy.
        """
        if (self.ebitda_ttm is not None and self.ebitda_ttm > 0 and
            self.market_cap is not None and self.market_cap > 0):
            return self.market_cap / self.ebitda_ttm
        return None
'''