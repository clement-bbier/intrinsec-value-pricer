"""
core/i18n/fr/ui/expert.py

Architecture Modulaire des Textes pour Terminaux Experts.
==========================================================
Structure :
1. SharedTexts : Socle commun (Labels WACC, Bridge, Monte Carlo, etc.)
2. Classes Narratives : Spécificités par modèle (Ancrage et Projections).
"""

class SharedTexts:
    """
    SOCLE COMMUN - Contient tous les labels universels réutilisés par les widgets.
    """
    # ==========================================================================
    # SECTIONS TRANSVERSES (Réalignement des index 3 à 8)
    # ==========================================================================
    SEC_3_CAPITAL = "#### Étape 3 : Profil de Risque (Actualisation)"
    SEC_3_DESC = "Détermination du taux requis pour rémunérer le risque opérationnel et financier (WACC ou Ke)."

    SEC_4_TERMINAL = "#### Étape 4 : Valeur de Continuation (Sortie)"
    SEC_4_DESC = "Estimation de la valeur de l'entreprise au-delà de l'horizon de projection explicite."

    SEC_5_BRIDGE = "#### Étape 5 : Ajustements de Structure (Equity Bridge)"
    SEC_5_DESC = "Passage de la valeur de l'actif économique (EV) à la valeur revenant aux actionnaires (Equity)."

    # Correction de l'index : Monte Carlo devient l'Étape 6 pour correspondre aux widgets
    SEC_6_MC = "#### Option : Simulation Probabiliste (Incertitude)"
    SEC_6_DESC_MC = "Analyse de sensibilité par simulation de Monte Carlo pour quantifier la dispersion de la valeur."

    SEC_7_PEERS = "#### Option : Cohorte de Comparables (Triangulation)"
    SEC_7_DESC_PEERS = "Vérification de la cohérence du modèle intrinsèque via les multiples boursiers du secteur."

    SEC_8_SCENARIOS = "#### Option : Analyse de Scénarios (Convictions)"
    SEC_8_DESC_SCENARIOS = "Modélisation de variantes stratégiques (Bull/Bear) pour tester la robustesse de votre thèse."

    SEC_9_SOTP = "#### Option : Somme des Parties (Segmentation SOTP)"
    SEC_9_DESC = "Décomposition de la valeur d'entreprise par segments métier ou actifs distincts."

    # ==========================================================================
    # ÉTAPE 5 : STRUCTURE DE L'EQUITY BRIDGE (Organisation en 3 parties)
    # ==========================================================================

    BRIDGE_TITLE = "#### Équity Bridge"
    BRIDGE_SUBTITLE = "Réconciliation de la Valeur d'Entreprise vers la Valeur par Action"

    BRIDGE_COMPONENTS = "**1. Composantes de Structure**"
    BRIDGE_ADJUSTMENTS = "**2. Ajustements de Valeur**"
    BRIDGE_DILUTION = "**3. Ajustements Dilutifs (SBC)**"

    INP_DEBT = "Dette Totale"
    INP_CASH = "Trésorerie et Équivalents"
    INP_SHARES = "Actions en circulation (diluées)"
    INP_MINORITIES = "Intérêts Minoritaires"
    INP_PENSIONS = "Provisions Pensions"

    # ==========================================================================
    # ÉTAPE 6 : MONTE CARLO
    # ==========================================================================
    MC_VOLATILITIES = "**Calibration des volatilités (écarts-types)**"
    MC_CALIBRATION = "Activer Monte Carlo"
    MC_ITERATIONS = "Nombre d'itérations"

    MC_VOL_BASE_FLOW = "Vol. Flux de Base (Y0)"
    MC_VOL_BETA = "Vol. du Bêta"
    MC_VOL_G = "Vol. du taux g"
    LBL_VOL_OMEGA = "Vol. de ω (Persistance)"
    LBL_VOL_GN = "Vol. de gn (Perp.)"

    HELP_MC_VOL_FLOW = "Incertitude sur le flux de trésorerie de l'année 0."
    HELP_MC_VOL_BETA = "Dispersion possible du coefficient de risque (Bêta)."
    HELP_MC_VOL_G = "Variabilité de la croissance sur la phase explicite."
    HELP_MC_VOL_OMEGA = "Incertitude sur la persistance des profits (modèle RIM)."
    HELP_MC_VOL_GN = "Incertitude sur le taux de croissance à l'infini."

    # ==========================================================================
    # ÉTAPE 8 : SCÉNARIOS
    # ==========================================================================
    INP_SCENARIO_ENABLE = "Activer l'analyse de scénarios"
    INP_SCENARIO_PROBA = "Probabilité (%)"
    INP_SCENARIO_GROWTH = "Croissance g"
    INP_SCENARIO_MARGIN = "Marge FCF"

    LABEL_SCENARIO_BULL = "Optimiste (Bull Case)"
    LABEL_SCENARIO_BASE = "Référence (Base Case)"
    LABEL_SCENARIO_BEAR = "Pessimiste (Bear Case)"
    LBL_BULL = "Bull"
    LBL_BASE = "Base"
    LBL_BEAR = "Bear"

    SCENARIO_HINT = "Définissez des variantes. Laissez vide pour utiliser les données du modèle de base."
    ERR_SCENARIO_PROBA_SUM = "La somme des probabilités est de {sum}% (doit être 100%)."
    ERR_SCENARIO_INVALID = "Certains paramètres de scénarios sont invalides."

    # ==========================================================================
    # LABELS INPUTS UNIVERSELS & SLIDERS
    # ==========================================================================
    INP_PROJ_YEARS = "Années de projection"
    SLIDER_PROJ_YEARS = "Horizon de projection (t années)"

    INP_RF = "Taux sans risque (Rf)"
    INP_BETA = "Coefficient Bêta (β)"
    INP_MRP = "Prime de risque marché (MRP)"
    INP_KD = "Coût de la dette brut (kd)"
    INP_TAX = "Taux d'imposition effectif (τ)"
    INP_PERP_G = "Croissance perpétuelle (gn)"
    INP_EXIT_MULT = "Multiple de sortie cible"
    INP_GROWTH_G = "Croissance moyenne attendue (g)"
    INP_PRICE_WEIGHTS = "Prix de l'action (poids E/V)"
    INP_OMEGA = "Facteur de persistance (ω)"

    # ==========================================================================
    # TOOLTIPS & HELP TEXTS
    # ==========================================================================
    HELP_PROJ_YEARS = "Horizon explicite de projection avant le calcul de la valeur terminale."
    HELP_GROWTH_RATE = "Taux de croissance annuel moyen des flux. Vide = estimation automatique."
    HELP_RF = "Rendement des obligations d'État à 10 ans. Vide = Auto."
    HELP_BETA = "Mesure de la sensibilité au marché. Vide = Auto Yahoo."
    HELP_MRP = "Surprime historique exigée par les investisseurs (Equity Risk Premium)."
    HELP_KD = "Coût de la dette avant économie d'impôt."
    HELP_TAX = "Taux d'imposition effectif moyen attendu."
    HELP_PERP_G = "Taux de croissance à l'infini. Doit être ≤ croissance du PIB nominal."
    HELP_EXIT_MULT = "Multiple EV/EBITDA ou P/E attendu en fin de projection."
    HELP_SBC_DILUTION = "Estimation de la dilution liée au Stock-Based Compensation."
    HELP_PRICE_WEIGHTS = "Prix actuel servant à calculer les poids des fonds propres et de la dette."
    HELP_OMEGA = "Facteur de persistance : 0 = retour immédiat à la moyenne, 1 = persistance infinie."
    HELP_MC_ENABLE = "Lance une simulation stochastique pour évaluer l'incertitude du prix."
    HELP_MC_SIMS = "Nombre de tirages. 5000 est un bon compromis précision/vitesse."
    HELP_SCENARIO_ENABLE = "Permet de tester des hypothèses de croissance et de marge différentes."
    HELP_PEER_TRIANGULATION = "Compare la valeur intrinsèque aux multiples de trading des concurrents."
    HELP_SHARES = "Nombre total d'actions diluées en circulation."
    HELP_DEBT = "Dette financière brute totale."
    HELP_CASH = "Cash, équivalents et placements financiers."

    # Récupération des labels existants pour le tableau
    LBL_SEGMENT_NAME = "Nom du Segment"
    LBL_SEGMENT_VALUE = "Valeur d'Entreprise (EV)"
    LBL_SEGMENT_METHOD = "Méthode de Valo."
    LBL_DISCOUNT = "Décote de conglomérat (%)"
    LBL_SOTP_ENABLE = "Activer l'analyse SOTP"
    HELP_SOTP_ENABLE = "Permet de diviser la valeur totale entre différentes Business Units."
    SEC_SOTP_SEGMENTS = "**Répartition par segments**"
    SEC_SOTP_ADJUSTMENTS = "**Ajustements de holding**"
    # ==========================================================================
    # UI ELEMENTS & FACTORY
    # ==========================================================================
    CATEGORY_DEFENSIVE = "Défensif"
    CATEGORY_RELATIVE_SECTORIAL = "Relatif / Sectoriel"
    CATEGORY_FUNDAMENTAL_DCF = "Fondamental (DCF)"
    CATEGORY_OTHER = "Autre"

    LBL_PEER_ENABLE = "Activer la triangulation"
    INP_MANUAL_PEERS = "Tickers des concurrents"
    PLACEHOLDER_PEERS = "ex: AAPL, MSFT, GOOG"
    HELP_MANUAL_PEERS = "Séparez les tickers par des virgules."
    PEERS_SELECTED = "*Concurrents sélectionnés : {peers}*"

    RADIO_TV_METHOD = "Modèle de sortie (TV)"
    TV_GORDON = "Croissance Perpétuelle (Gordon)"
    TV_EXIT = "Multiple de Sortie / P/E"

    LABEL_DILUTION_SBC = "Dilution / SBC"
    INP_SBC_DILUTION = "Taux de dilution annuel attendu"
    WARN_SBC_TECH = "Le SBC impacte la valeur par action. Prévoyez 1-3% pour les entreprises technologiques."

    BTN_CALCULATE = "Lancer la Valorisation"

    # ==========================================================================
    # FORMULES (LATEX)
    # ==========================================================================
    FORMULA_BRIDGE = r"P = \frac{EV - \text{Dette} + \text{Cash} - \text{Minorités}}{\text{Actions}}"
    FORMULA_CAPITAL_KE = r"k_e = R_f + \beta \times MRP"
    FORMULA_CAPITAL_WACC = r"WACC = w_e [R_f + \beta(MRP)] + w_d [k_d(1-\tau)]"

    # Formules dynamiques pour l'Étape 4
    FORMULA_TV_GORDON = r"TV_n = \frac{FCF_n(1+g_n)}{WACC - g_n}"
    FORMULA_TV_EXIT = r"TV_n = FCF_{n+1} \times Multiple_{exit}"


# ==============================================================================
# CLASSES NARRATIVES SPÉCIFIQUES (Héritage de SharedTexts)
# ==============================================================================

class FCFFStandardTexts(SharedTexts):
    TITLE = "Terminal Expert : DCF Entité (FCFF)"
    DESCRIPTION = "Modèle DCF classique : flux opérationnels actualisés au coût moyen du capital (WACC)."
    STEP_1_TITLE = "#### Étape 1 : Flux d'Ancrage ($FCFF_0$)"
    STEP_1_DESC = "Définition du Free Cash Flow to Firm de référence (TTM) pour initier les projections."
    STEP_1_FORMULA = r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}"
    STEP_2_TITLE = "#### Étape 2 : Projection de la Croissance"
    STEP_2_DESC = "Hypothèses de croissance des flux durant la phase explicite de projection."
    INP_BASE = "Flux de trésorerie disponible (TTM)"
    HELP_BASE = "Dernier flux généré par l'exploitation. Vide = calcul automatique."

class FCFFNormalizedTexts(SharedTexts):
    TITLE = "Terminal Expert : FCFF Normalisé"
    DESCRIPTION = "DCF utilisant un flux lissé sur le cycle pour neutraliser la volatilité court terme."
    STEP_1_TITLE = "#### Étape 1 : Flux Normatif ($FCF_{norm}$)"
    STEP_1_DESC = "Estimation d'un flux de croisière lissé sur 3 à 5 ans pour stabiliser la base."
    STEP_1_FORMULA = r"V_0 = \sum \frac{FCF_{norm}(1+g)^t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}"
    STEP_2_TITLE = "#### Étape 2 : Dynamique de Croissance"
    STEP_2_DESC = "Projection de la croissance moyenne attendue sur le cycle à venir."
    INP_BASE = "Flux normalisé de cycle"
    HELP_BASE = "Moyenne des flux sur le cycle économique actuel. Vide = Auto."

class FCFFGrowthTexts(SharedTexts):
    TITLE = "Terminal Expert : Revenue-Driven Growth"
    DESCRIPTION = "Projection pilotée par le CA avec convergence progressive vers une marge cible."
    STEP_1_TITLE = "#### Étape 1 : Assiette de Revenus ($Rev_0$)"
    STEP_1_DESC = "Ancrage sur le Chiffre d'Affaires actuel pour modéliser l'expansion du business."
    STEP_1_FORMULA = r"V_0 = \sum \frac{Rev_t \times \text{Marge}_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}"
    STEP_2_TITLE = "#### Étape 2 : Convergence des Marges"
    STEP_2_DESC = "Évolution attendue de la rentabilité opérationnelle vers une marge de maturité."
    INP_BASE = "Chiffre d'Affaires (TTM)"
    INP_REV_GROWTH = "Croissance annuelle des revenus (g)"
    INP_MARGIN_TARGET = "Marge FCF cible (%)"

class RIMTexts(SharedTexts):
    TITLE = "Terminal Expert : Revenu Résiduel (RIM)"
    DESCRIPTION = "Valorisation par la Valeur Comptable brute et les profits anormaux."
    STEP_1_TITLE = "#### Étape 1 : Ancrage Bilan ($BV_0$)"
    STEP_1_DESC = "Saisie de la Valeur Comptable initiale (Equity) servant de socle au modèle."
    STEP_1_FORMULA = r"P = BV_0 + \sum \frac{NI_t - (k_e \cdot BV_{t-1})}{(1+k_e)^t}"
    STEP_2_TITLE = "#### Étape 2 : Profits Résiduels & Persistance"
    STEP_2_DESC = "Estimation des résultats nets futurs et de leur facteur de persistance (ω)."
    INP_BASE = "Valeur comptable initiale (Book Value)"
    INP_NI = "Résultat Net normatif (Net Income)"
    INP_OMEGA = "Facteur de persistance (ω)"

class GrahamTexts(SharedTexts):
    TITLE = "Terminal Expert : Valeur de Graham"
    DESCRIPTION = "Formule défensive liant BPA, croissance et rendement obligataire AAA."
    STEP_1_TITLE = "#### Étape 1 : Bénéfices & Croissance ($EPS$)"
    STEP_1_DESC = "Ancrage sur le bénéfice par action normalisé pour un screening prudent."
    STEP_1_FORMULA = r"V = EPS \times (8.5 + 2g) \times \frac{4.4}{Y}"
    STEP_2_TITLE = "#### Étape 2 : Conditions de Marché AAA"
    STEP_2_DESC = "Ajustement par rapport au rendement actuel des obligations de haute qualité."
    INP_BASE = "Bénéfice par action (EPS) normalisé"
    INP_YIELD = "Rendement actuel Obligations AAA (Y)"

class FCFETexts(SharedTexts):
    TITLE = "Terminal Expert : Flux Actionnaire (FCFE)"
    DESCRIPTION = "Valorisation directe des capitaux propres par les flux résiduels après dette."
    STEP_1_TITLE = "#### Étape 1 : Flux Actionnaire ($FCFE_0$)"
    STEP_1_DESC = "Reconstruction du flux résiduel après investissements et variations d'endettement."
    STEP_1_FORMULA = r"P = \sum \frac{FCFE_t}{(1+k_e)^t} + \frac{TV_n}{(1+k_e)^n}"
    STEP_2_TITLE = "#### Étape 2 : Projection des Flux de Distribution"
    STEP_2_DESC = "Capacité réelle de distribution aux actionnaires sur la phase explicite."
    INP_BASE = "Flux FCFE de référence"
    INP_NET_BORROWING = "Variation nette de l'endettement (Δ Dette)"

class DDMTexts(SharedTexts):
    TITLE = "Terminal Expert : Modèle de Dividendes (DDM)"
    DESCRIPTION = "Valeur actuelle des dividendes futurs actualisés au coût des fonds propres."
    STEP_1_TITLE = "#### Étape 1 : Dividende de Départ ($D_0$)"
    STEP_1_DESC = "Saisie du dividende annuel de référence pour la projection de croissance."
    STEP_1_FORMULA = r"P = \sum \frac{D_0(1+g)^t}{(1+k_e)^t} + \frac{TV_n}{(1+k_e)^n}"
    STEP_2_TITLE = "#### Étape 2 : Dynamique des Dividendes"
    STEP_2_DESC = "Hypothèses de croissance du coupon sur l'horizon de projection."
    INP_BASE = "Dernier dividende annuel ($D_0$)"