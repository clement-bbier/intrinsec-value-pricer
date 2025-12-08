"""
infra/ref_data/country_matrix.py
Base de données macro-économiques et sources officielles par pays.
"""

from typing import TypedDict, Dict, Optional

class CountryData(TypedDict):
    tax_rate: float            # Taux d'impôt sociétés (Corp Tax Rate)
    risk_free_rate: float      # Taux sans risque (10Y Govt Bond) - Valeur par défaut
    market_risk_premium: float # Prime de risque marché (MRP)
    inflation_rate: float      # Inflation LT cible

    # Sources Officielles (Liens cliquables pour la Phase 2)
    url_central_bank: str      # Source pour le Taux Sans Risque (Rf)
    url_tax_source: str        # Source pour la fiscalité
    url_risk_premium: str      # Source pour la Prime de Risque (Damodaran/Survey)

# Liens globaux génériques (Fallback)
GLOBAL_URLS = {
    "risk_premium": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html", # Damodaran (Reference Mondiale)
    "trading_economics": "https://tradingeconomics.com/bonds" # Agrégateur fiable si lien banque centrale cassé
}

# Base de Connaissance Étendue (G20 + Suisse + Pays-Bas + Espagne...)
COUNTRY_CONTEXT: Dict[str, CountryData] = {

    # --- AMÉRIQUE DU NORD ---
    "United States": {
        "tax_rate": 0.21, "risk_free_rate": 0.042, "market_risk_premium": 0.050, "inflation_rate": 0.025,
        "url_central_bank": "https://fred.stlouisfed.org/series/DGS10",
        "url_tax_source": "https://taxfoundation.org/data/all/global/corporate-tax-rates-by-country-2024/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "Canada": {
        "tax_rate": 0.265, "risk_free_rate": 0.035, "market_risk_premium": 0.050, "inflation_rate": 0.020,
        "url_central_bank": "https://www.bankofcanada.ca/rates/interest-rates/canadian-bonds/",
        "url_tax_source": "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/corporations/corporation-tax-rates.html",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },

    # --- EUROPE (Zone Euro & Hors Zone) ---
    "France": {
        "tax_rate": 0.258, "risk_free_rate": 0.031, "market_risk_premium": 0.055, "inflation_rate": 0.020,
        "url_central_bank": "https://www.banque-france.fr/statistiques/taux-et-cours/taux-indicatifs-des-bons-du-tresor-et-oat",
        "url_tax_source": "https://www.economie.gouv.fr/entreprises/impot-sur-societes-is",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "Germany": {
        "tax_rate": 0.30, "risk_free_rate": 0.026, "market_risk_premium": 0.055, "inflation_rate": 0.020,
        "url_central_bank": "https://www.bundesbank.de/en/statistics/money-and-capital-markets/interest-rates-and-yields/yields-of-listed-federal-securities-616616",
        "url_tax_source": "https://taxfoundation.org/location/germany/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "United Kingdom": {
        "tax_rate": 0.25, "risk_free_rate": 0.041, "market_risk_premium": 0.060, "inflation_rate": 0.025,
        "url_central_bank": "https://www.bankofengland.co.uk/boeapps/database/Yields.asp",
        "url_tax_source": "https://www.gov.uk/corporation-tax-rates",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "Italy": {
        "tax_rate": 0.24, "risk_free_rate": 0.039, "market_risk_premium": 0.070, "inflation_rate": 0.020,
        "url_central_bank": "https://www.bancaditalia.it/compiti/operazioni-mef/tassi-rendimento/index.html",
        "url_tax_source": "https://taxfoundation.org/location/italy/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "Spain": {
        "tax_rate": 0.25, "risk_free_rate": 0.034, "market_risk_premium": 0.065, "inflation_rate": 0.020,
        "url_central_bank": "https://www.bde.es/webbe/en/estadisticas/temas/tipos-interes/deuda-publica-mercado-secundario.html",
        "url_tax_source": "https://taxfoundation.org/location/spain/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "Netherlands": {
        "tax_rate": 0.258, "risk_free_rate": 0.028, "market_risk_premium": 0.050, "inflation_rate": 0.020,
        "url_central_bank": "https://www.dnb.nl/en/statistics/data-search/#/details/interest-rates-government-bonds",
        "url_tax_source": "https://business.gov.nl/regulation/corporation-tax/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "Switzerland": {
        "tax_rate": 0.197, "risk_free_rate": 0.011, "market_risk_premium": 0.045, "inflation_rate": 0.010,
        "url_central_bank": "https://www.snb.ch/en/iabout/stat/statpub/zins/id/statpub_zins_ch",
        "url_tax_source": "https://kpmg.com/ch/en/home/services/tax/tax-rates-switzerland.html",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },

    # --- ASIE ---
    "Japan": {
        "tax_rate": 0.306, "risk_free_rate": 0.009, "market_risk_premium": 0.060, "inflation_rate": 0.010,
        "url_central_bank": "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/index.htm",
        "url_tax_source": "https://www.nta.go.jp/english/taxes/corporation/index.htm",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "China": {
        "tax_rate": 0.25, "risk_free_rate": 0.024, "market_risk_premium": 0.065, "inflation_rate": 0.030,
        "url_central_bank": "http://www.pbc.gov.cn/en/108156/index.html",
        "url_tax_source": "http://www.chinatax.gov.cn/eng/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "India": {
        "tax_rate": 0.252, "risk_free_rate": 0.071, "market_risk_premium": 0.075, "inflation_rate": 0.045,
        "url_central_bank": "https://www.rbi.org.in/Scripts/BS_NSDPDisplay.aspx",
        "url_tax_source": "https://incometaxindia.gov.in/Pages/charts-and-tables.aspx",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
    "Australia": {
        "tax_rate": 0.30, "risk_free_rate": 0.041, "market_risk_premium": 0.050, "inflation_rate": 0.025,
        "url_central_bank": "https://www.rba.gov.au/statistics/tables/#interest-rates",
        "url_tax_source": "https://www.ato.gov.au/rates/changes-to-company-tax-rates/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },

    # --- AUTRES ÉMERGENTS MAJEURS ---
    "Brazil": {
        "tax_rate": 0.34, "risk_free_rate": 0.110, "market_risk_premium": 0.085, "inflation_rate": 0.040,
        "url_central_bank": "https://www.bcb.gov.br/en/statistics",
        "url_tax_source": "https://taxfoundation.org/location/brazil/",
        "url_risk_premium": GLOBAL_URLS["risk_premium"]
    },
}

# Fallback USA par défaut pour les pays inconnus
DEFAULT_COUNTRY = COUNTRY_CONTEXT["United States"]

def get_country_context(country_name: str) -> CountryData:
    """
    Récupère le contexte (Données par défaut + Liens Sources) pour un pays.
    Gère la recherche partielle (ex: 'China (Mainland)' -> 'China').
    """
    if not country_name:
        return DEFAULT_COUNTRY

    # 1. Recherche exacte
    if country_name in COUNTRY_CONTEXT:
        return COUNTRY_CONTEXT[country_name]

    # 2. Recherche partielle
    for key, val in COUNTRY_CONTEXT.items():
        if key.lower() in country_name.lower():
            return val

    # 3. Fallback USA si inconnu
    return DEFAULT_COUNTRY