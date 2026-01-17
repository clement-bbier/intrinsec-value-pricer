"""
core/i18n/fr/backend/strategies.py
Sources et interpretations des strategies de calcul.
"""


class StrategySources:
    """Descriptions des sources de donnees utilisees dans les calculs."""
    WACC_TARGET = "Structure Cible"
    WACC_MARKET = "Structure de Marche"
    WACC_FALLBACK = "Structure de Secours (100% Equity)"
    WACC_MANUAL = "Surcharge manuelle : {wacc:.2%}"
    MANUAL_OVERRIDE = "Manual override (Expert)"
    YAHOO_TTM = "Last reported FCF (TTM) - Yahoo Deep Fetch"
    YAHOO_FUNDAMENTAL = "Fundamental smoothed FCF (Yahoo/Analyst)"
    YAHOO_TTM_SIMPLE = "Yahoo Finance (TTM)"
    CALCULATED_NI = "Calculated (Net Income / Shares)"
    ANALYST_OVERRIDE = "Surcharge Analyste"
    MACRO_MATRIX = "Matrix: {ticker}"
    MACRO_CURRENCY_FALLBACK = "Currency Fallback: {ticker}"
    MACRO_STATIC_FALLBACK = "Matrix Static Fallback (API Error)"
    MACRO_API_ERROR = "Matrix Fallback (API Error)"


class StrategyInterpretations:
    """Notes pedagogiques dynamiques generees par les strategies (Glass Box)."""
    
    # DCF & Abstract
    WACC = "Taux d'actualisation cible (WACC) de {wacc:.2%}, base sur la structure de capital actuelle."
    PROJ = "Projection sur {years} ans a un taux de croissance annuel moyen de {g:.2%}"
    TV = "Estimation de la valeur de l'entreprise au-dela de la periode explicite."
    EV = "Valeur totale de l'outil de production actualisee."
    BRIDGE = "Ajustement de la structure financiere."
    IV = "Estimation de la valeur reelle d'une action pour {ticker}."

    # RIM
    RIM_TV = "Estimation de la persistance des surprofits."

    # Growth
    GROWTH_REV = "Point de depart du modele base sur le chiffre d'affaires TTM."
    GROWTH_MARGIN = "Modelisation de l'amelioration operationnelle vers une marge FCF normative."
    GROWTH_TV = "Valeur de l'entreprise a l'infini basee sur la derniere marge convergee."
    GROWTH_EV = "Somme actualisee des flux et de la valeur terminale."
    GROWTH_IV = "Estimation finale du prix theorique par titre."

    # Fundamental
    FUND_NORM = "Le modele utilise un flux lisse sur un cycle complet."
    FUND_VIABILITY = "Validation de la capacite a generer des flux positifs sur un cycle."

    # Graham
    GRAHAM_EPS = "Benefice par action utilise comme socle de rentabilite."
    GRAHAM_MULT = "Prime de croissance appliquee selon le bareme revise de Graham."
    GRAHAM_IV = "Estimation de la valeur intrinseque ajustee par le rendement AAA."

    # Monte Carlo
    MC_CLAMP_NOTE = " (Ecrete de {g_raw:.1%} pour coherence WACC)"
    MC_INIT = "Calibration des lois normales multivariees.{note}"
    MC_SAMPLING_SUB = "Generation de {count} vecteurs d'inputs via Decomposition de Cholesky."
    MC_SAMPLING_INTERP = "Application des correlations pour garantir la coherence economique."
    MC_FILTERING = "Elimination des scenarios de divergence pour stabiliser la distribution."
    MC_SENS_NEUTRAL = "Neutre (rho=0)"
    MC_SENS_BASE = "Base (rho=-0.3)"
    MC_SENS_INTERP = "Audit de l'impact de la correlation sur la stabilite."
    MC_STRESS_SUB = "Bear Case = {val:,.2f} {curr}"
    MC_STRESS_INTERP = "Scenario de stress : croissance nulle et risque eleve."

    FCFE_LOGIC = "Le modele FCFE valorise les fonds propres apres service de la dette."
    DDM_LOGIC = "Le modele DDM repose sur la distribution future."

    RELATIVE_PE = r"Valeur basee sur le multiple P/E median du secteur ({val:.1f}x)."
    RELATIVE_EBITDA = r"Valeur basee sur le multiple EV/EBITDA median ({val:.1f}x)."
    TRIANGULATION_FINAL = "Valeur hybride obtenue par la moyenne des methodes relatives."
