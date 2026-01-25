"""
core/i18n/fr/ui/expert.py

Architecture Modulaire des Textes pour Terminaux Experts (V18 - Nuances Méthodologiques).
==============================================================================
Structure :
1. SharedTexts : Socle commun (Labels WACC, Bridge, Monte Carlo, etc.)
2. Classes Narratives : Spécificités par modèle (Ancrage et Projections).

Règles de maintenance :
- Ne jamais supprimer de lignes existantes.
- Les titres (TITLE) doivent correspondre exactement aux labels de la sidebar.
"""


class SharedTexts:
    """
    SOCLE COMMUN - Centralise l'intégralité des labels, messages et formules
    utilisés par les terminaux experts et les widgets de saisie.
    """

    # ==========================================================================
    # 1. SÉQUENÇAGE DES ÉTAPES (3 à 9)
    # ==========================================================================
    # Titres de sections et descriptions pédagogiques
    SEC_3_CAPITAL = "#### Étape 3 : Profil de Risque (Actualisation)"
    SEC_3_DESC = "Détermination du taux requis pour rémunérer le risque opérationnel et financier (WACC ou Ke)."

    SEC_4_TERMINAL = "#### Étape 4 : Valeur de Continuation (Sortie)"
    SEC_4_DESC = "Estimation de la valeur de l'entreprise au-delà de l'horizon de projection explicite."

    SEC_5_BRIDGE = "#### Étape 5 : Ajustements de Structure (Equity Bridge)"
    SEC_5_DESC = "Passage de la valeur de l'actif économique (EV) à la valeur revenant aux actionnaires (Equity)."

    # Extensions optionnelles (Index 6 à 9)
    SEC_6_MC = "#### Option : Simulation Probabiliste (Incertitude)"
    SEC_6_DESC_MC = "Analyse de sensibilité par simulation de Monte Carlo pour quantifier la dispersion de la valeur."

    SEC_7_PEERS = "#### Option : Cohorte de Comparables (Triangulation)"
    SEC_7_DESC_PEERS = "Vérification de la cohérence du modèle intrinsèque via les multiples boursiers du secteur."

    SEC_8_SCENARIOS = "#### Option : Analyse de Scénarios (Convictions)"
    SEC_8_DESC_SCENARIOS = "Modélisation de variantes stratégiques (Bull/Bear) pour tester la robustesse de vos hypothèses."

    SEC_9_SOTP = "#### Option : Somme des Parties (Segmentation SOTP)"
    SEC_9_DESC = "Décomposition de la valeur d'entreprise par segments métier ou actifs distincts."

    # ==========================================================================
    # 2. MODULE : ÉTAPE 5 - EQUITY BRIDGE
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
    # 3. MODULE : ÉTAPE 6 - MONTE CARLO
    # ==========================================================================
    MC_CALIBRATION = "Activer Monte Carlo"
    MC_ITERATIONS = "Nombre d'itérations"
    MC_VOL_INCERTITUDE = "**Calibration des incertitudes (écarts-types)**"
    MC_VOL_BASE_FLOW = "Vol. Flux de Base (Y0)"
    MC_VOL_BETA = "Vol. du Bêta"
    MC_VOL_G = "Vol. du taux g"
    LBL_VOL_OMEGA = "Vol. de ω (Persistance)"
    LBL_VOL_GN = "Vol. de gn (Perp.)"

    # ==========================================================================
    # 4. MODULE : ÉTAPE 8 - SCÉNARIOS (Bull/Base/Bear)
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
    # 5. MODULE : ÉTAPE 9 - SOTP (Sum-of-the-Parts)
    # ==========================================================================
    LBL_SOTP_ENABLE = "Activer l'analyse SOTP"
    HELP_SOTP_ENABLE = "Permet de diviser la valeur totale entre différentes Business Units."
    WARN_SOTP_RELEVANCE = "L'analyse SOTP est recommandée pour les conglomérats. Pour une entreprise mono-segment, utilisez-la uniquement pour decomposer la valeur calculée."

    SEC_SOTP_SEGMENTS = "**Répartition par segments**"
    SEC_SOTP_ADJUSTMENTS = "**Ajustements de holding**"

    LBL_SEGMENT_NAME = "Nom du Segment"
    LBL_SEGMENT_VALUE = "Valeur d'Entreprise (EV)"
    LBL_SEGMENT_METHOD = "Méthode de Valorisation"
    LBL_DISCOUNT = "Décote de conglomérat (%)"

    # ==========================================================================
    # 6. LABELS D'INPUTS UNIVERSELS (Paramètres financiers)
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
    # 7. TOOLTIPS & TEXTES D'AIDE (Help Texts)
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
    HELP_SCENARIO_ENABLE = "Permet de tester des hypothèses de croissance et de marge différente."
    HELP_PEER_TRIANGULATION = "Compare la valeur intrinsèque aux multiples de trading des concurrents."
    HELP_SHARES = "Nombre total d'actions diluées en circulation."
    HELP_DEBT = "Dette financière brute totale."
    HELP_CASH = "Cash, équivalents et placements financiers."

    # Tooltips Monte Carlo (Incertitudes)
    HELP_MC_VOL_FLOW = "Incertitude sur le flux de trésorerie de l'année 0."
    HELP_MC_VOL_BETA = "Dispersion possible du coefficient de risque (Bêta)."
    HELP_MC_VOL_G = "Variabilité de la croissance sur la phase explicite."
    HELP_MC_VOL_OMEGA = "Incertitude sur la persistance des profits (modèle RIM)."
    HELP_MC_VOL_GN = "Incertitude sur le taux de croissance à l'infini."

    # ==========================================================================
    # 8. ÉLÉMENTS D'UI & NAVIGATION (Factory, Boutons, Méthodes)
    # ==========================================================================
    # Catégories de modèles
    CATEGORY_DEFENSIVE = "Défensif"
    CATEGORY_RELATIVE_SECTORIAL = "Relatif / Sectoriel"
    CATEGORY_FUNDAMENTAL_DCF = "Fondamental (DCF)"
    CATEGORY_OTHER = "Autre"

    # Peer Triangulation
    LBL_PEER_ENABLE = "Activer la triangulation"
    INP_MANUAL_PEERS = "Tickers des concurrents"
    PLACEHOLDER_PEERS = "ex: AAPL, MSFT, GOOG"
    HELP_MANUAL_PEERS = "Séparez les tickers par des virgules."
    PEERS_SELECTED = "*Concurrents sélectionnés : {peers}*"

    # Terminal Value Methods
    RADIO_TV_METHOD = "Modèle de sortie (TV)"
    TV_GORDON = "Croissance Perpétuelle (Gordon)"
    TV_EXIT = "Multiple de Sortie / P/E"

    # SBC & Dilution
    LABEL_DILUTION_SBC = "Dilution / SBC"
    INP_SBC_DILUTION = "Taux de dilution annuel attendu"
    WARN_SBC_TECH = "Le SBC impacte la valeur par action. Prévoyez 1-3% pour les entreprises technologiques."

    # Boutons
    BTN_CALCULATE = "Lancer la Valorisation"
    BTN_VALUATE_STD = "Lancer la Valorisation ({ticker})"

    # ==========================================================================
    # 9. FORMULES FINANCIÈRES (LaTeX)
    # ==========================================================================
    # Bridge
    FORMULA_BRIDGE = r"P = \frac{EV - \text{Dette} + \text{Cash} - \text{Minorités}}{\text{Actions}}"
    FORMULA_BRIDGE_SIMPLE = r"P = \frac{\text{Valeur Actionnaire}}{\text{Actions}}"

    # Capital
    FORMULA_CAPITAL_KE = r"k_e = R_f + \beta \times MRP"
    FORMULA_CAPITAL_WACC = r"WACC = w_e [R_f + \beta(MRP)] + w_d [k_d(1-\tau)]"

    # Valeur Terminale (Dynamique Étape 4)
    FORMULA_TV_GORDON = r"TV_n = \frac{FCF_n(1+g_n)}{WACC - g_n}"
    FORMULA_TV_EXIT = r"TV_n = FCF_{n+1} \times Multiple_{exit}"

# ==============================================================================
# CLASSES NARRATIVES SPÉCIFIQUES (Héritage de SharedTexts)
# ==============================================================================

class FCFFStandardTexts(SharedTexts):
    TITLE = "Approche Entité (FCFF Standard)"
    DESCRIPTION = "Modèle DCF classique : flux opérationnels actualisés au coût moyen du capital (WACC)."
    STEP_1_TITLE = "#### Étape 1 : Flux d'Ancrage ($FCFF_0$)"
    STEP_1_DESC = "Définition du Free Cash Flow to Firm de référence (TTM) pour initier les projections."
    STEP_1_FORMULA = r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}"
    STEP_2_TITLE = "#### Étape 2 : Projection de la Croissance"
    STEP_2_DESC = "Hypothèses de croissance des flux durant la phase explicite de projection."
    INP_BASE = "Flux de trésorerie disponible (TTM)"
    HELP_BASE = "Dernier flux de trésorerie disponible généré par l'exploitation (Y0) servant d'ancrage."
    HELP_GROWTH = "Taux d'expansion annuel moyen des flux de trésorerie sur l'horizon explicite."

class FCFFNormalizedTexts(SharedTexts):
    TITLE = "Approche Entité (FCFF Normalisé)"
    DESCRIPTION = "DCF utilisant un flux lissé sur le cycle pour neutraliser la volatilité court terme."
    STEP_1_TITLE = "#### Étape 1 : Flux Normatif ($FCF_{norm}$)"
    STEP_1_DESC = "Estimation d'un flux de croisière lissé sur 3 à 5 ans pour stabiliser la base."
    STEP_1_FORMULA = r"V_0 = \sum \frac{FCF_{norm}(1+g)^t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}"
    STEP_2_TITLE = "#### Étape 2 : Dynamique de Croissance"
    STEP_2_DESC = "Projection de la croissance moyenne attendue sur le cycle à venir."
    INP_BASE = "Flux normalisé de cycle"
    HELP_BASE = "Flux moyen lissé sur le cycle économique complet (3-5 ans) pour neutraliser la cyclicité."
    HELP_GROWTH = "Taux de croissance de croisière projeté pour le flux normalisé de cycle."

class FCFFGrowthTexts(SharedTexts):
    TITLE = "Approche Entité (Revenue-Driven)"
    DESCRIPTION = "Projection pilotée par le CA avec convergence progressive vers une marge cible."
    STEP_1_TITLE = "#### Étape 1 : Assiette de Revenus ($Rev_0$)"
    STEP_1_DESC = "Ancrage sur le Chiffre d'Affaires actuel pour modéliser l'expansion du business."
    STEP_1_FORMULA = r"V_0 = \sum \frac{Rev_t \times \text{Marge}_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}"
    STEP_2_TITLE = "#### Étape 2 : Convergence des Marges"
    STEP_2_DESC = "Évolution attendue de la rentabilité opérationnelle vers une marge de maturité."
    INP_BASE = "Chiffre d'Affaires (TTM)"
    INP_REV_GROWTH = "Croissance annuelle des revenus (g)"
    INP_MARGIN_TARGET = "Marge FCF cible (%)"
    HELP_REV_TTM = "Chiffre d'affaires consolidé des 12 derniers mois."
    HELP_REV_GROWTH = "Taux d'expansion annuel projeté pour le Chiffre d'Affaires (Top-line)."
    HELP_MARGIN_TARGET = "Marge de flux de trésorerie disponible visée en fin de période de convergence."

class RIMTexts(SharedTexts):
    TITLE = "Revenu Résiduel (RIM)"
    DESCRIPTION = "Valorisation par la Valeur Comptable brute et les profits anormaux."
    STEP_1_TITLE = "#### Étape 1 : Ancrage Bilan ($BV_0$)"
    STEP_1_DESC = "Saisie de la Valeur Comptable initiale (Equity) servant de socle au modèle."
    STEP_1_FORMULA = r"P = BV_0 + \sum_{t=1}^{n} \frac{NI_t - (k_e \cdot BV_{t-1})}{(1+k_e)^t} + TV_{RI}"
    STEP_2_TITLE = "#### Étape 2 : Profits Résiduels & Persistance"
    STEP_2_DESC = "Estimation des résultats nets futurs et de leur facteur de persistance (ω)."
    INP_BASE = "Valeur comptable initiale (Book Value)"
    INP_NI = "Résultat Net normatif (Net Income)"
    INP_NI_TTM = "Net Income (TTM)"
    INP_BV_INITIAL = "Book Value (BV_0)"
    HELP_NI_TTM = "Bénéfice net consolidé servant à déterminer le profit résiduel de départ."
    HELP_BV_INITIAL = "Capitaux propres comptables (Equity) constituant le socle de la valeur d'ancrage."
    HELP_GROWTH = "Croissance projetée des profits anormaux avant application du facteur de persistance ω."
    SEC_1_RIM_BASE = "#### 1. Ancrage Comptable"
    SEC_2_PROJ_RIM = "#### 2. Projection du RI"

class GrahamTexts(SharedTexts):
    TITLE = "Valeur de Graham"
    DESCRIPTION = "Formule défensive liant BPA, croissance et rendement obligataire AAA."
    STEP_1_TITLE = "#### Étape 1 : Bénéfices & Croissance ($EPS$)"
    STEP_1_DESC = "Ancrage sur le bénéfice par action normalisé pour un screening prudent."
    STEP_1_FORMULA = r"V = EPS \times (8.5 + 2g) \times \frac{4.4}{Y}"
    STEP_2_TITLE = "#### Étape 2 : Conditions de Marché AAA"
    STEP_2_DESC = "Ajustement par rapport au rendement actuel des obligations de haute qualité."
    INP_BASE = "Bénéfice par action (EPS) normalisé"
    INP_YIELD = "Rendement actuel Obligations AAA (Y)"
    INP_EPS_NORM = "EPS Normalisé (TTM)"
    INP_YIELD_AAA = "Yield Corporate AAA"
    HELP_EPS_NORM = "Bénéfice Par Action ajusté des éléments exceptionnels et lissé."
    HELP_GROWTH_LT = "Croissance LT (7-10 ans) pondérée pour le calcul du multiple Graham."
    HELP_YIELD_AAA = "Taux de rendement actuel des obligations corporate de haute qualité."
    SEC_1_GRAHAM_BASE = "#### 1. Paramètres de Screening"
    SEC_2_GRAHAM = "#### 2. Conditions Monétaires"
    NOTE_GRAHAM = "Note : Le facteur 8.5 correspond au multiple d'une entreprise sans croissance."

class FCFETexts(SharedTexts):
    TITLE = "Approche Actionnaire (FCFE)"
    DESCRIPTION = "Valorisation directe des capitaux propres par les flux résiduels après dette."
    STEP_1_TITLE = "#### Étape 1 : Flux Actionnaire ($FCFE_0$)"
    STEP_1_DESC = "Reconstruction du flux résiduel après investissements et variations d'endettement."
    STEP_1_FORMULA = r"P = \sum_{t=1}^{n} \frac{FCFE_t}{(1+k_e)^t} + \frac{TV_n}{(1+k_e)^n}"
    STEP_2_TITLE = "#### Étape 2 : Projection des Flux de Distribution"
    STEP_2_DESC = "Capacité réelle de distribution aux actionnaires sur la phase explicite."
    INP_BASE = "Flux FCFE de référence"
    INP_NET_BORROWING = "Variation nette de l'endettement (Δ Dette)"
    HELP_FCFE_BASE = "Flux résiduel revenant aux actionnaires après service de la dette (intérêts et capital)."
    HELP_NET_BORROWING = "Estimation des nouveaux emprunts nets des remboursements sur la période."
    HELP_GROWTH = "Taux de croissance annuel projeté de la capacité de distribution (FCFE)."
    SEC_1_FCFE_BASE = "#### 1. Ancrage Actionnaire"
    SEC_2_PROJ = "#### 2. Horizon de Projection"

class DDMTexts(SharedTexts):
    TITLE = "Approche Actionnaire (DDM)"
    DESCRIPTION = "Valeur actuelle des dividendes futurs actualisés au coût des fonds propres."
    STEP_1_TITLE = "#### Étape 1 : Dividende de Départ ($D_0$)"
    STEP_1_DESC = "Saisie du dividende annuel de référence pour la projection de croissance."
    STEP_1_FORMULA = r"P = \sum \frac{D_0(1+g)^t}{(1+k_e)^t} + \frac{TV_n}{(1+k_e)^n}"
    STEP_2_TITLE = "#### Étape 2 : Dynamique des Dividendes"
    STEP_2_DESC = "Hypothèses de croissance du coupon sur l'horizon de projection."
    INP_BASE = "Dernier dividende annuel ($D_0$)"
    INP_DIVIDEND_BASE = "Dividende par action ($D_0$)"
    HELP_DIVIDEND_BASE = "Somme des dividendes ordinaires versés (TTM) servant de base à la projection."
    HELP_GROWTH = "Taux de croissance annuel attendu pour le versement du coupon par action."
    NOTE_DDM_SGR = "Le modèle suppose que le dividende croît à un taux constant g à perpétuité."
    SEC_1_DDM_BASE = "#### 1. Flux de Dividendes"