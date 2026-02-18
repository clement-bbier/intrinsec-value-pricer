"""
infra/ref_data/country_matrix.py

MACRO-ECONOMIC COUNTRY MATRIX — JANUARY 2026 UPDATE
===================================================
Role: Provides foundational macro-economic data and official sources per country.
Used as the primary anchor for Risk-Free rates, Tax rates, and ERP resolution.

Architecture: Reference Data Layer.
Style: Numpy docstrings.
"""

from typing import TypedDict


class CountryData(TypedDict):
    """
    Schema for country-specific macroeconomic parameters.

    Attributes
    ----------
    tax_rate : float
        Standard corporate tax rate (decimal).
    marginal_tax_rate : float
        Long-term marginal legal tax rate for terminal value calculations (decimal).
    risk_free_rate : float
        10Y Sovereign Bond yield as of Jan 2026.
    market_risk_premium : float
        Equity Risk Premium (ERP) based on Damodaran/Buy-side standards.
    inflation_rate : float
        Long-term inflation target (used for g floor).
    rf_ticker : str
        Yahoo Finance ticker for live risk-free rate tracking.
    url_central_bank : str
        Official Central Bank data link for audit verification.
    url_tax_source : str
        Official tax authority or advisory source.
    url_risk_premium : str
        Source for the specific ERP calculation.
    """

    tax_rate: float
    marginal_tax_rate: float
    risk_free_rate: float
    market_risk_premium: float
    inflation_rate: float
    rf_ticker: str
    url_central_bank: str
    url_tax_source: str
    url_risk_premium: str


# Reference sources for buy-side audit traceability
GLOBAL_URLS = {
    "risk_premium": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html",
    "trading_economics": "https://tradingeconomics.com/bonds",
}

# ==============================================================================
# MACRO KNOWLEDGE BASE (UPDATED JANUARY 2026)
# ==============================================================================


COUNTRY_CONTEXT: dict[str, CountryData] = {
    "United States": {
        "tax_rate": 0.21,
        "marginal_tax_rate": 0.21,  # Federal statutory rate
        "risk_free_rate": 0.0425,  # Yield curve shift (Feb 2026)
        "market_risk_premium": 0.046,  # Damodaran Jan 26 update
        "inflation_rate": 0.027,  # Core sticky inflation
        "rf_ticker": "^TNX",
        "url_central_bank": "https://fred.stlouisfed.org/series/DGS10",
        "url_tax_source": "https://taxfoundation.org/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"],
    },
    "France": {
        "tax_rate": 0.361,  # Exceptional contribution for 2026
        "marginal_tax_rate": 0.25,  # Long-term normalized rate (post-exceptional period)
        "risk_free_rate": 0.0345,  # OAT 10Y Feb 2026
        "market_risk_premium": 0.053,
        "inflation_rate": 0.019,
        "rf_ticker": "FR10YT=RR",
        "url_central_bank": "https://www.banque-france.fr/",
        "url_tax_source": "https://www.economie.gouv.fr/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"],
    },
    "Germany": {
        "tax_rate": 0.301,  # Statutory trade tax adjustment
        "marginal_tax_rate": 0.301,  # Long-term rate (trade tax + corporate tax)
        "risk_free_rate": 0.0289,  # Bund 10Y Feb 2026
        "market_risk_premium": 0.051,
        "inflation_rate": 0.020,
        "rf_ticker": "^GDBR10",
        "url_central_bank": "https://www.bundesbank.de/",
        "url_tax_source": "https://taxfoundation.org/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"],
    },
    "United Kingdom": {
        "tax_rate": 0.25,
        "marginal_tax_rate": 0.25,  # Statutory rate
        "risk_free_rate": 0.035,  # Gilt 10Y
        "market_risk_premium": 0.058,
        "inflation_rate": 0.022,
        "rf_ticker": "^GJGB10",
        "url_central_bank": "https://www.bankofengland.co.uk/",
        "url_tax_source": "https://www.gov.uk/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"],
    },
    "China": {
        "tax_rate": 0.25,
        "marginal_tax_rate": 0.25,  # Statutory rate
        "risk_free_rate": 0.021,  # PBOC Rate cuts trend
        "market_risk_premium": 0.068,  # Adjusted systemic risk premium
        "inflation_rate": 0.025,
        "rf_ticker": "^CN10Y",
        "url_central_bank": "http://www.pbc.gov.cn/",
        "url_tax_source": "http://www.chinatax.gov.cn/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"],
    },
    "Japan": {
        "tax_rate": 0.354,  # Effective rate with 2026 defense surtax
        "marginal_tax_rate": 0.30,  # Long-term normalized rate (post-surtax period)
        "risk_free_rate": 0.0226,  # Normalized JGB 10Y
        "market_risk_premium": 0.059,
        "inflation_rate": 0.015,
        "rf_ticker": "^JGBS10",
        "url_central_bank": "https://www.mof.go.jp/",
        "url_tax_source": "https://www.nta.go.jp/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"],
    },
}

# Institutional Default fallback
DEFAULT_COUNTRY = COUNTRY_CONTEXT["United States"]

# ==============================================================================
# RESILIENT EXTRACTION LOGIC
# ==============================================================================


def get_country_context(country_name: str | None) -> CountryData:
    """
    Retrieves the macro context for a given country.

    Implements fuzzy matching to handle API variations (e.g., 'France (Republic of)').

    Parameters
    ----------
    country_name : Optional[str]
        The raw country name string from the data provider.

    Returns
    -------
    CountryData
        The most relevant macro-economic dataset. Defaults to US context if not found.
    """
    if not country_name or not isinstance(country_name, str):
        return DEFAULT_COUNTRY

    # 1. Exact match attempt
    if country_name in COUNTRY_CONTEXT:
        return COUNTRY_CONTEXT[country_name]

    # 2. Case-insensitive fuzzy/partial matching
    clean_name = country_name.lower()
    for key, val in COUNTRY_CONTEXT.items():
        if key.lower() in clean_name:
            return val

    # 3. Institutional fallback to USD/US context
    return DEFAULT_COUNTRY
