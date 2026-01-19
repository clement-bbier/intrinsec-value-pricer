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


class StrategyFormulas:
    """Formules LaTeX standardisées pour toutes les méthodes de valorisation."""

    # === COÛT DU CAPITAL ===
    CAPM = r"K_e = R_f + \beta \times ERP"
    WACC = r"WACC = \frac{V_E}{V_E + V_D} \times K_e + \frac{V_D}{V_E + V_D} \times K_d \times (1 - T_c)"

    # === VALEUR TERMINALE ===
    GORDON = r"TV_n = \frac{FCF_n \times (1 + g_\infty)}{WACC - g_\infty}"
    TERMINAL_MULTIPLE = r"TV_n = FCF_n \times Multiple"

    # === GROWTH MARGIN ===
    GROWTH_MARGIN_CONV = r"FCF_t = Rev_t \times [Margin_0 + (Margin_n - Margin_0) \times \frac{t}{n}]"

    # === PROJECTION ===
    FCF_PROJECTION = r"FCF_t = FCF_0 \times (1+g)^t"

    # === TERMINAL VALUE ===
    TERMINAL_EXIT_MULTIPLE = r"TV = EBITDA_n \times Multiple"

    # === BASE VALUES ===
    FCF_BASE = r"FCF_0"
    REVENUE_BASE = r"Rev_0"
    EPS_BASE = r"EPS"
    BV_BASE = r"BV_0"
    FCF_NORMALIZED = r"FCF_{norm}"

    # === TRIANGULATION ===
    TRIANGULATION_AVERAGE = r"IV = \frac{\sum Signals}{N}"

    # === MONTE CARLO ===
    MC_VALID_RATIO = r"\frac{N_{valid}}{N_{total}}"
    MC_MEDIAN = r"Median(IV_i)"
    MC_SENSITIVITY = r"\frac{\partial P50}{\partial \rho}"
    MC_STRESS = r"f(g \to 0, \beta \to 1.5)"

    # === FCFE ===
    FCFE_RECONSTRUCTION = r"FCFE = NI + \text{NonCashAdj} + \text{Net Borrowing}"
    FCFE_EQUITY_VALUE = r"\text{Equity Value}"

    # === DIVIDEND ===
    DIVIDEND_BASE = r"D_0 \times \text{Shares}"

    # === PROJECTION ===
    FLOW_PROJECTION = r"Flow_t = Flow_{t-1} \times (1+g)"

    # === PAYOUT ===
    PAYOUT_RATIO = r"Payout = \frac{Div_{TTM}}{EPS_{TTM}}"

    # === SUM RI ===
    RI_SUM = r"\sum_{t=1}^{n} \frac{NI_t - (k_e \times BV_{t-1})}{(1+k_e)^t}"

    # === FINAL VALUES ===
    RIM_FINAL = r"IV = BV_0 + \sum PV(RI) + PV(TV)"

    # === VALEUR ACTUELLE NETTE ===
    NPV = r"PV = \sum_{t=1}^{n} \frac{FCF_t}{(1 + r)^t} + \frac{TV_n}{(1 + r)^n}"

    # === DCF STANDARD (ST-2.2) ===
    DCF_STANDARD = r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}"

    # === AUTRES FORMULES ===
    EQUITY_BRIDGE = r"Equity = EV - Debt + Cash - Minority - Provisions"
    VALUE_PER_SHARE = r"IV = \frac{Equity}{Shares\ Outstanding}"

    # === MONTE CARLO ===
    MC_VOLATILITY_MATRIX = r"\sigma = [\sigma_\beta, \sigma_g, \sigma_{Y_0}]"

    # === RELATIFS / MULTIPLES (ST-2.2) ===
    PE_MULTIPLE = r"P/E = \frac{Price}{EPS}"
    EV_EBITDA_MULTIPLE = r"EV/EBITDA = \frac{Enterprise\ Value}{EBITDA}"
    PRICE_FROM_PE = r"Price_{P/E} = \frac{Net\ Income \times Median\ P/E}{Shares}"
    PRICE_FROM_EV_EBITDA = r"Price_{EV/EBITDA} = \frac{EBITDA \times Median\ EV/EBITDA - Debt + Cash}{Shares}"

    # === RIM BANKS ===
    RIM_RESIDUAL_INCOME = r"RI_t = NI_t - (K_e \times BV_{t-1})"
    RIM_PERSISTENCE = r"TV_{RI} = \frac{RI_n \times \omega}{1 + k_e - \omega}"

    # === GRAHAM ===
    GRAHAM_MULTIPLIER = r"M = 8.5 + 2g"
    GRAHAM_VALUE = r"IV = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}"


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
    TRIANGULATION_SUB = "Moyenne de {count} signaux valides"
    TRIANGULATION_FINAL = "Valeur hybride obtenue par la moyenne des methodes relatives."
