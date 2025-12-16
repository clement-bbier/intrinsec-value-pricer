"""
infra/ref_data/country_matrix.py
Base de données macro-économiques et sources officielles par pays.
"""

from typing import TypedDict, Dict

class CountryData(TypedDict):
    tax_rate: float
    risk_free_rate: float      # Taux 10Y (défaut si macro provider down)
    market_risk_premium: float # Prime de risque marché
    inflation_rate: float      # Cible inflation LP
    url_central_bank: str
    url_tax_source: str
    url_risk_premium: str

# Sources génériques
GLOBAL_URLS = {
    "risk_premium": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html",
    "trading_economics": "https://tradingeconomics.com/bonds"
}

# Base de Connaissance (Extrait représentatif)
COUNTRY_CONTEXT: Dict[str, CountryData] = {
    "United States": {
        "tax_rate": 0.21, "risk_free_rate": 0.042, "market_risk_premium": 0.050, "inflation_rate": 0.025,
        "url_central_bank": "https://fred.stlouisfed.org/series/DGS10",
        "url_tax_source": "https://taxfoundation.org/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "France": {
        "tax_rate": 0.258, "risk_free_rate": 0.031, "market_risk_premium": 0.055, "inflation_rate": 0.020,
        "url_central_bank": "https://www.banque-france.fr/",
        "url_tax_source": "https://www.economie.gouv.fr/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "Germany": {
        "tax_rate": 0.30, "risk_free_rate": 0.026, "market_risk_premium": 0.055, "inflation_rate": 0.020,
        "url_central_bank": "https://www.bundesbank.de/",
        "url_tax_source": "https://taxfoundation.org/location/germany/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "United Kingdom": {
        "tax_rate": 0.25, "risk_free_rate": 0.041, "market_risk_premium": 0.060, "inflation_rate": 0.025,
        "url_central_bank": "https://www.bankofengland.co.uk/",
        "url_tax_source": "https://www.gov.uk/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "China": {
        "tax_rate": 0.25, "risk_free_rate": 0.024, "market_risk_premium": 0.065, "inflation_rate": 0.030,
        "url_central_bank": "http://www.pbc.gov.cn/",
        "url_tax_source": "http://www.chinatax.gov.cn/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "Japan": {
        "tax_rate": 0.306, "risk_free_rate": 0.009, "market_risk_premium": 0.060, "inflation_rate": 0.010,
        "url_central_bank": "https://www.mof.go.jp/",
        "url_tax_source": "https://www.nta.go.jp/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    }
}

# Fallback
DEFAULT_COUNTRY = COUNTRY_CONTEXT["United States"]

def get_country_context(country_name: str) -> CountryData:
    """
    Récupère le contexte macro. Résistant aux None ou strings vides.
    """
    if not country_name or not isinstance(country_name, str):
        return DEFAULT_COUNTRY

    # 1. Exact Match
    if country_name in COUNTRY_CONTEXT:
        return COUNTRY_CONTEXT[country_name]

    # 2. Partial Match (ex: "China (Mainland)" -> "China")
    clean_name = country_name.lower()
    for key, val in COUNTRY_CONTEXT.items():
        if key.lower() in clean_name:
            return val

    # 3. Fallback
    return DEFAULT_COUNTRY