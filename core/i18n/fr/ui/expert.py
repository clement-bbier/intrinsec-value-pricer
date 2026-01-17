"""
core/i18n/fr/ui/expert.py

Textes des terminaux experts.
Internationalisation : Tous les textes UI pour switch FR/EN futur.
"""


class ExpertTerminalTexts:
    """Titres, Sections, Labels et Tooltips des Terminaux Experts."""

    # ==========================================================================
    # TITRES DES TERMINAUX
    # ==========================================================================
    TITLE_FCFF_STD = "Terminal Expert : FCFF Standard"
    TITLE_FCFF_FUND = "Terminal Expert : FCFF Fundamental"
    TITLE_FCFF_GROWTH = "Terminal Expert : FCFF Growth"
    TITLE_FCFE = "Terminal Expert : FCFE (Direct Equity)"
    TITLE_DDM = "Terminal Expert : Dividend Discount Model"
    TITLE_RIM = "Terminal Expert : RIM"
    TITLE_GRAHAM = "Terminal Expert : Graham"

    # ==========================================================================
    # SECTIONS COMMUNES
    # ==========================================================================
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

    # ==========================================================================
    # LABELS DES INPUTS
    # ==========================================================================
    INP_PROJ_YEARS = "Annees de projection"
    INP_FCF_TTM = "Dernier flux TTM"
    INP_FCF_SMOOTHED = "Flux lisse de cycle"
    INP_REV_TTM = "Chiffre d'affaires TTM"
    INP_GROWTH_G = "Croissance moyenne attendue g"
    INP_FCF_GROWTH = "Croissance FCF Phase 1"
    INP_DIV_GROWTH = "Croissance dividendes Phase 1"
    INP_PERP_G = "Croissance perpetuelle (gn)"
    INP_BV_INITIAL = "Valeur comptable initiale BV0"
    INP_NI_TTM = "Resultat Net TTM"
    INP_EPS_NORM = "BPA normalise EPS"
    INP_YIELD_AAA = "Rendement Obligations AAA (Y)"
    INP_PRICE_WEIGHTS = "Prix de l'action"
    INP_RF = "Taux sans risque Rf"
    INP_BETA = "Coefficient Beta"
    INP_MRP = "Prime de risque marche MRP"
    INP_KD = "Cout de la dette brut kd"
    INP_TAX = "Taux d'imposition effectif"
    INP_EXIT_MULT = "Multiple de sortie"
    INP_REV_GROWTH = "Croissance CA (g_rev)"
    INP_MARGIN_TARGET = "Marge FCF cible (%)"
    INP_GROWTH_LT = "Croissance long terme g (%)"
    INP_OMEGA = "Facteur de persistance (omega)"

    # Equity Bridge
    INP_DEBT = "Dette Totale"
    INP_CASH = "Tresorerie"
    INP_SHARES = "Actions en circulation"
    INP_MINORITIES = "Interets Minoritaires"
    INP_PENSIONS = "Provisions Pensions"

    # Specificites FCFE
    INP_FCFE_NI = "Resultat Net (Net Income TTM)"
    INP_FCFE_ADJ = "Ajustements Cash (Amort - Capex - BFR)"
    INP_FCFE_BASE = "Flux FCFE de base"
    INP_NET_BORROWING = "Variation nette de la dette"

    # Specificites DDM
    INP_DIVIDEND_BASE = "Dernier dividende annuel ($D_0$)"
    INP_PAYOUT_TARGET = "Ratio de distribution cible (Payout %)"
    INP_PE_TARGET = "Multiple P/E Cible (Sortie)"

    INP_MANUAL_PEERS = "Tickers des concurrents"

    # ==========================================================================
    # TOOLTIPS / HELP TEXTS
    # ==========================================================================
    HELP_PROJ_YEARS = "Horizon de projection explicite avant valeur terminale"
    HELP_GROWTH_RATE = "Decimal. Laisser vide = estimation automatique Yahoo Finance"
    HELP_FCF_TTM = "Free Cash Flow TTM. Vide = calcul automatique Yahoo Finance"
    HELP_FCF_SMOOTHED = "FCF moyen sur 3-5 ans. Vide = calcul automatique"
    HELP_REV_TTM = "Chiffre d'affaires TTM. Vide = Auto Yahoo"
    HELP_REV_GROWTH = "Taux de croissance annuel du CA. Vide = Auto"
    HELP_MARGIN_TARGET = "Marge FCF/CA a atteindre en fin de projection"
    HELP_PRICE_WEIGHTS = "Prix de l'action pour calcul des poids E/V. Vide = Auto Yahoo"
    HELP_RF = "Taux sans risque (OAT 10 ans, Treasury). Vide = Auto"
    HELP_BETA = "Beta levered de l'action. Vide = Auto Yahoo"
    HELP_MRP = "Prime de risque marche (historique ~5-6%). Vide = Auto"
    HELP_KD = "Cout de la dette brut avant impot. Vide = Auto"
    HELP_TAX = "Taux d'imposition effectif. Vide = Auto"
    HELP_PERP_G = "Croissance long terme (≤ PIB nominal ~2-3%). Vide = Auto"
    HELP_EXIT_MULT = "Multiple EV/EBITDA a la sortie. Vide = Auto sectoriel"
    HELP_OMEGA = "omega in [0,1]. 0 = profits normalises immediatement. 1 = persistance infinie"
    HELP_DEBT = "Dette totale (court + long terme). Vide = Auto"
    HELP_CASH = "Tresorerie et equivalents. Vide = Auto"
    HELP_SHARES = "Actions en circulation (diluted). Vide = Auto"
    HELP_MINORITIES = "Interets minoritaires a deduire. Vide = 0"
    HELP_PENSIONS = "Provisions retraites non financees. Vide = 0"
    HELP_FCFE_BASE = "Free Cash Flow to Equity. Vide = Auto Yahoo"
    HELP_NET_BORROWING = "Delta Dette nette (+ = emission, - = remboursement). Vide = 0"
    HELP_DIVIDEND_BASE = "Dernier dividende annuel par action. Vide = Auto Yahoo"
    HELP_DIV_GROWTH = "g doit etre soutenable. SGR = ROE x (1 - Payout) est une borne superieure."
    HELP_BV_INITIAL = "Book Value totale. Vide = Auto Yahoo"
    HELP_NI_TTM = "Net Income TTM. Vide = Auto Yahoo"
    HELP_EPS_NORM = "BPA normalise (moyenne 3 ans recommandee). Vide = Auto"
    HELP_GROWTH_LT = "Croissance attendue sur 7-10 ans (decimal). Vide = Auto"
    HELP_YIELD_AAA = "Rendement obligations AAA actuelles. Vide = Auto"
    HELP_MANUAL_PEERS = "Tickers separes par virgule. Vide = auto-discovery sectorielle"
    HELP_PEER_TRIANGULATION = "Compare la valeur DCF aux multiples des pairs sectoriels"

    # Monte Carlo Tooltips
    HELP_MC_ENABLE = "Active la simulation stochastique pour quantifier l'incertitude"
    HELP_MC_SIMS = "Plus de simulations = resultat plus stable mais plus lent"
    HELP_MC_VOL_FLOW = "Incertitude sur le flux de depart (±5% typique)"
    HELP_MC_VOL_BETA = "Incertitude sur le beta (±10% typique)"
    HELP_MC_VOL_G = "Incertitude sur le taux de croissance"
    HELP_MC_VOL_OMEGA = "Incertitude sur le facteur de persistance"
    HELP_MC_VOL_GN = "Incertitude sur la croissance perpetuelle"
    HELP_MC_RHO = "Correlation entre les variables aleatoires"

    # Scenarios Tooltips
    HELP_SCENARIO_ENABLE = "Active l'analyse multi-scenarios avec ponderation probabiliste"
    HELP_SCENARIO_PROBA_SUM = "Somme des probabilites = {total:.0%}. Doit etre egale a 100%."
    HELP_SOTP_DISCOUNT = "Decote appliquee pour manque de synergies ou complexite"

    # ==========================================================================
    # LABELS INTERACTIFS
    # ==========================================================================
    LBL_TV_METHOD = "Methode de sortie (TV)"
    RADIO_TV_METHOD = "Modele de sortie (TV)"
    TV_GORDON = "Croissance Perpetuelle (Gordon)"
    TV_EXIT = "Multiple de Sortie / P/E"
    LBL_VOL_OMEGA = "Vol. omega (persistance)"
    LBL_VOL_GN = "Vol. gn (perp.)"

    # ==========================================================================
    # MONTE CARLO
    # ==========================================================================
    MC_CALIBRATION = "Activer Monte Carlo"
    MC_ITERATIONS = "Nombre d'iterations"
    MC_VOL_BASE_FLOW = "Vol. Flux Base (Y0)"
    MC_VOL_BETA = "Vol. Beta"
    MC_VOL_G = "Vol. g"
    MC_RHO = "Correlation (rho)"
    MC_SECTION_VOL = "**Calibration des volatilites (ecarts-types)**"

    # ==========================================================================
    # SLIDERS
    # ==========================================================================
    SLIDER_PROJ_YEARS = "Horizon de projection (t annees)"
    SLIDER_PROJ_T = "Annees de projection (t)"
    SLIDER_PROJ_N = "Annees de projection (n)"

    # ==========================================================================
    # BOUTONS
    # ==========================================================================
    BTN_CALCULATE = "Lancer la valorisation"
    BTN_VALUATE_STD = "Lancer la valorisation : {ticker}"

    # ==========================================================================
    # SCENARIOS
    # ==========================================================================
    INP_SCENARIO_ENABLE = "Activer l'analyse de scenarios"
    INP_SCENARIO_PROBA = "Probabilite (%)"
    INP_SCENARIO_GROWTH = "Croissance g"
    INP_SCENARIO_MARGIN = "Marge FCF"
    LABEL_SCENARIO_BULL = "Optimiste (Bull Case)"
    LABEL_SCENARIO_BASE = "Reference (Base Case)"
    LABEL_SCENARIO_BEAR = "Pessimiste (Bear Case)"
    SCENARIO_HINT = "Definissez des variantes. Laissez vide pour utiliser la valeur de base."

    # ==========================================================================
    # TRIANGULATION
    # ==========================================================================
    LBL_PEER_ENABLE = "Activer la triangulation par multiples"
    LBL_PEERS_SELECTED = "Peers selectionnes : {peers}"

    # ==========================================================================
    # NOTES ET CAPTIONS
    # ==========================================================================
    NOTE_GRAHAM = "Formule de Graham : approximation historique. A utiliser comme screening, pas comme valorisation definitive."
    NOTE_DDM_SGR = "Rappel : g doit etre soutenable. SGR = ROE x (1 - Payout) est une borne superieure."
