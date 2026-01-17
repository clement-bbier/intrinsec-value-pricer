"""
core/i18n/fr/ui/expert.py
Textes des terminaux experts.
"""


class ExpertTerminalTexts:
    """Titres, Sections et Labels specifiques aux Terminaux Experts."""

    # Titres des terminaux
    TITLE_FCFF_STD = "Terminal Expert : FCFF Standard"
    TITLE_FCFF_FUND = "Terminal Expert : FCFF Fundamental"
    TITLE_FCFF_GROWTH = "Terminal Expert : FCFF Growth"
    TITLE_FCFE = "Terminal Expert : FCFE (Direct Equity)"
    TITLE_DDM = "Terminal Expert : Dividend Discount Model"
    TITLE_RIM = "Terminal Expert : RIM"
    TITLE_GRAHAM = "Terminal Expert : Graham"

    # Sections communes
    SEC_1_FLOW = "#### 1. Flux de base"
    SEC_1_FCF_STD = "#### 1. Flux de tresorerie de base ($FCF_0$)"
    SEC_1_FCF_NORM = "#### 1. Flux normalise de base ($FCF_{norm}$)"
    SEC_1_REV_BASE = "#### 1. Chiffre d'Affaires de base ($Rev_0$)"
    SEC_1_FCFE_BASE = "#### 1. Reconstruction du Flux Actionnaire (FCFE)"
    SEC_1_DDM_BASE = "#### 1. Dividende de depart ($D_0$)"
    SEC_1_RIM_BASE = "#### 1. Valeur Comptable ($BV_0$) & Profits ($NI_t$)"
    SEC_1_GRAHAM_BASE = "#### 1. Benefices ($EPS$) & Croissance attendue ($g$)"

    SEC_2_PROJ = "#### 2. Phase de croissance explicite"
    SEC_2_PROJ_FUND = "#### 2. Croissance moyenne de cycle"
    SEC_2_PROJ_GROWTH = "#### 2. Horizon & Convergence des Marges"
    SEC_2_PROJ_RIM = "#### 2. Horizon & Croissance des profits"
    SEC_2_GRAHAM = "#### 2. Conditions de Marche AAA & Fiscalite"

    SEC_3_CAPITAL = "#### 3. Cout du Capital (Actualisation)"
    SEC_4_GROWTH = "#### 4. Hypotheses de Croissance"
    SEC_4_TERMINAL = "#### 4. Valeur de continuation (Sortie)"
    SEC_5_TERMINAL = "#### 5. Valeur terminale"
    SEC_5_BRIDGE = "#### 5. Ajustements de structure (Equity Bridge)"
    SEC_6_MC = "#### 6. Simulation Probabiliste (Incertitude)"
    SEC_7_PEERS = "#### 7. Cohorte de Comparables (Triangulation)"
    SEC_8_SCENARIOS = "#### 8. Analyse de Scenarios Deterministes (Bull/Base/Bear)"

    # Labels des Inputs
    INP_PROJ_YEARS = "Annees de projection"
    INP_FCF_TTM = "Dernier flux TTM (devise entreprise, Vide = Auto Yahoo)"
    INP_FCF_SMOOTHED = "Flux lisse de cycle (devise entreprise, Vide = Auto Yahoo)"
    INP_REV_TTM = "Chiffre d'affaires TTM (devise entreprise, Vide = Auto Yahoo)"
    INP_GROWTH_G = "Croissance moyenne attendue g (decimal, Vide = Auto Yahoo)"
    INP_FCF_GROWTH = "Croissance FCF Phase 1"
    INP_DIV_GROWTH = "Croissance dividendes Phase 1"
    INP_PERP_G = "Croissance perpetuelle (g)"
    INP_BV_INITIAL = "Valeur comptable initiale BV0 (Vide = Auto Yahoo)"
    INP_NI_TTM = "Resultat Net TTM NIt (Vide = Auto Yahoo)"
    INP_EPS_NORM = "BPA normalise EPS (Vide = Auto Yahoo)"
    INP_YIELD_AAA = "Rendement Obligations AAA Y (decimal, Vide = Auto Yahoo)"
    INP_PRICE_WEIGHTS = "Prix de l'action pour calcul des poids (Vide = Auto Yahoo)"
    INP_RF = "Taux sans risque Rf (decimal, Vide = Auto Yahoo)"
    INP_BETA = "Coefficient Beta (facteur x, Vide = Auto Yahoo)"
    INP_MRP = "Prime de risque marche MRP (decimal, Vide = Auto Yahoo)"
    INP_KD = "Cout de la dette brut kd (decimal, Vide = Auto Yahoo)"
    INP_TAX = "Taux d'imposition effectif (decimal, Vide = Auto Yahoo)"
    INP_EXIT_MULT = "Multiple de sortie"

    # Equity Bridge
    INP_DEBT = "Dette Totale (Vide = Auto Yahoo)"
    INP_CASH = "Tresorerie (Vide = Auto Yahoo)"
    INP_SHARES = "Actions en circulation (Vide = Auto Yahoo)"
    INP_MINORITIES = "Interets Minoritaires (Vide = Auto Yahoo)"
    INP_PENSIONS = "Provisions Pensions (Vide = Auto Yahoo)"

    # Specificites FCFE
    INP_FCFE_NI = "Resultat Net (Net Income TTM)"
    INP_FCFE_ADJ = "Ajustements Cash (Amort - Capex - BFR)"
    INP_FCFE_BASE = "Flux FCFE de base (Vide = Auto Yahoo)"
    INP_NET_BORROWING = "Variation nette de la dette ($Net Borrowing$)"

    # Specificites DDM
    INP_DIVIDEND_BASE = "Dernier dividende annuel paye ($D_0$)"
    INP_PAYOUT_TARGET = "Ratio de distribution cible (Payout %)"
    INP_PE_TARGET = "Multiple P/E Cible (Sortie)"

    INP_MANUAL_PEERS = "Tickers des concurrents (separes par une virgule)"

    # Labels Interactifs
    LBL_TV_METHOD = "Methode de sortie (TV)"
    RADIO_TV_METHOD = "Modele de sortie (TV)"
    TV_GORDON = "Croissance Perpetuelle (Gordon)"
    TV_EXIT = "Multiple de Sortie / P/E"

    # Monte Carlo
    MC_CALIBRATION = "Calibration des Volatilites (Monte Carlo) :"
    MC_ITERATIONS = "Nombre d'iterations"
    MC_VOL_BASE_FLOW = "Vol. Flux Base (Y0)"
    MC_VOL_BETA = "Vol. Beta"
    MC_VOL_G = "Vol. g"

    # Sliders
    SLIDER_PROJ_YEARS = "Horizon de projection (t annees)"
    SLIDER_PROJ_T = "Annees de projection (t)"
    SLIDER_PROJ_N = "Annees de projection (n)"

    # Boutons
    BTN_CALCULATE = "Lancer la valorisation"
    BTN_VALUATE_STD = "Lancer la valorisation : {ticker}"

    # Scenarios
    INP_SCENARIO_ENABLE = "Activer l'analyse de scenarios"
    INP_SCENARIO_PROBA = "Probabilite du scenario (%)"
    INP_SCENARIO_GROWTH = "Croissance g (decimal)"
    INP_SCENARIO_MARGIN = "Marge FCF specifique"
    LABEL_SCENARIO_BULL = "Optimiste (Bull Case)"
    LABEL_SCENARIO_BASE = "Reference (Base Case)"
    LABEL_SCENARIO_BEAR = "Pessimiste (Bear Case)"
