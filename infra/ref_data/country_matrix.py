"""
infra/ref_data/country_matrix.py
Base de données macro-économiques et sources officielles par pays.
Version : 2026.1 — Janvier 2026 Update
"""

from typing import TypedDict, Dict

class CountryData(TypedDict):
    tax_rate: float
    risk_free_rate: float      # Taux 10Y (Souverain au 01/2026)
    market_risk_premium: float # Prime de risque marché (ERP)
    inflation_rate: float      # Cible inflation long-terme
    rf_ticker: str
    url_central_bank: str
    url_tax_source: str
    url_risk_premium: str

# Sources de référence pour l'audit buy-side
GLOBAL_URLS = {
    "risk_premium": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html",
    "trading_economics": "https://tradingeconomics.com/bonds"
}

# ==============================================================================
# BASE DE CONNAISSANCE MACRO (MISE À JOUR JANVIER 2026)
# ==============================================================================
COUNTRY_CONTEXT: Dict[str, CountryData] = {
    "United States": {
        "tax_rate": 0.21,
        "risk_free_rate": 0.038,     # Stabilisation T-Bond 10Y
        "market_risk_premium": 0.045, # Normalisation prime US
        "inflation_rate": 0.024,
        "rf_ticker": "^TNX",
        "url_central_bank": "https://fred.stlouisfed.org/series/DGS10",
        "url_tax_source": "https://taxfoundation.org/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "France": {
        "tax_rate": 0.250,           # Trajectoire loi de finances
        "risk_free_rate": 0.029,     # OAT 10Y Janvier 2026
        "market_risk_premium": 0.053,
        "inflation_rate": 0.020,
        "rf_ticker": "FR10YT=RR",
        "url_central_bank": "https://www.banque-france.fr/",
        "url_tax_source": "https://www.economie.gouv.fr/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "Germany": {
        "tax_rate": 0.299,
        "risk_free_rate": 0.022,     # Bund 10Y
        "market_risk_premium": 0.051,
        "inflation_rate": 0.020,
        "rf_ticker": "^GDBR10",
        "url_central_bank": "https://www.bundesbank.de/",
        "url_tax_source": "https://taxfoundation.org/location/germany/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "United Kingdom": {
        "tax_rate": 0.25,
        "risk_free_rate": 0.035,     # Gilt 10Y
        "market_risk_premium": 0.058,
        "inflation_rate": 0.022,
        "rf_ticker": "^GJGB10",
        "url_central_bank": "https://www.bankofengland.co.uk/",
        "url_tax_source": "https://www.gov.uk/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "China": {
        "tax_rate": 0.25,
        "risk_free_rate": 0.021,     # Poursuite baisse des taux PBOC
        "market_risk_premium": 0.068, # Prime ajustée risque systémique
        "inflation_rate": 0.025,
        "rf_ticker": "^CN10Y",
        "url_central_bank": "http://www.pbc.gov.cn/",
        "url_tax_source": "http://www.chinatax.gov.cn/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "Japan": {
        "tax_rate": 0.306,
        "risk_free_rate": 0.012,     # Sortie confirmée des taux proches de zéro
        "market_risk_premium": 0.059,
        "inflation_rate": 0.015,
        "rf_ticker": "^JGBS10",
        "url_central_bank": "https://www.mof.go.jp/",
        "url_tax_source": "https://www.nta.go.jp/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    }
}

# Configuration par défaut
DEFAULT_COUNTRY = COUNTRY_CONTEXT["United States"]

# ==============================================================================
# LOGIQUE D'EXTRACTION RÉSILIENTE
# ==============================================================================

def get_country_context(country_name: str) -> CountryData:
    """
    Récupère le contexte macro. Résistant aux None ou strings vides.
    Supporte le matching partiel pour la compatibilité Yahoo (ex: 'France (Republic of)').
    """
    if not country_name or not isinstance(country_name, str):
        return DEFAULT_COUNTRY

    # 1. Correspondance exacte
    if country_name in COUNTRY_CONTEXT:
        return COUNTRY_CONTEXT[country_name]

    # 2. Correspondance partielle (Insensible à la casse)
    clean_name = country_name.lower()
    for key, val in COUNTRY_CONTEXT.items():
        if key.lower() in clean_name:
            return val

    # 3. Fallback institutionnel
    return DEFAULT_COUNTRY
