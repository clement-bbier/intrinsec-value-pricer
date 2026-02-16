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


class UISharedTexts:
    """
    SOCLE COMMUN - Centralise l'intégralité des labels, messages et formules
    utilisés par les terminaux experts et les widgets de saisie - UI Layer.
    """

    # ==========================================================================
    # 1. SÉQUENÇAGE DES ÉTAPES (3 à 9)
    # ==========================================================================
    # Titres de sections et descriptions pédagogiques
    ERR_CRITICAL = (
        "Une erreur critique est survenue lors de l'assemblage de la valorisation."
        " Veuillez vérifier vos saisies ou contacter le support."
    )
    LBL_LOOKBACK = "Recul historique (années)"
    FORMULA_TV_FCFF_STD = r"TV_n = \frac{FCF_n(1+g_n)}{WACC - g_n}"
    FORMULA_TV_FCFF_NORM = r"TV_n = \frac{FCF_{norm}(1+g_n)}{WACC - g_n}"
    FORMULA_TV_FCFF_GROWTH = r"TV_n = \frac{Rev_n \times Margin_{target} \times (1+g_n)}{WACC - g_n}"
    FORMULA_TV_FCFE = r"TV_n = \frac{FCFE_n(1+g_n)}{k_e - g_n}"
    FORMULA_TV_DDM = r"TV_n = \frac{D_n(1+g_n)}{k_e - g_n}"
    ERR_VALIDATION = "Erreur de validation"
    INP_EPS_NORM = "BPA (EPS) normalisé ($/action)"
    INP_YIELD_AAA = "Taux de croissance moyen (g) (%)"
    INP_BV_INITIAL = "Valeur Comptable (Equity) (M$)"
    FORMULA_TV_RIM = r"TV_{RI} = \frac{RI_n \times \omega}{1 + k_e - \omega}"
    DEFAULT_SEGMENT_NAME = "Segment A"
    MC_VOL_EPS = "Incertitude sur le BPA (EPS)"
    MC_VOL_NI = "Incertitude sur le Résultat Net"
    MC_VOL_DIV = "Incertitude sur le Dividende"
    HELP_VOL_BASE = "Écart-type attendu (σ) sur le premier flux (Year 0) du modèle."
    LBL_VOL_EXIT_M = "Volatilité du multiple terminal"
    SEC_3_CAPITAL = "#### Étape 3 : Profil de Risque (Actualisation)"
    SEC_3_DESC = "Détermination du taux requis pour rémunérer le risque opérationnel et financier (WACC ou Ke)."

    SEC_4_TERMINAL = "#### Étape 4 : Valeur de Continuation (Sortie)"
    SEC_4_DESC = "Estimation de la valeur de l'entreprise au-delà de l'horizon de projection explicite."

    SEC_5_BRIDGE = "#### Étape 5 : Ajustements de Structure (Equity Bridge)"
    SEC_5_DESC = "Passage de la valeur de l'actif économique (EV) à la valeur revenant aux actionnaires (Equity)."

    # Extensions optionnelles (Index 6 à 9)
    SEC_6_MC = "#### Option : Simulation Probabiliste (Incertitude)"
    SEC_6_DESC_MC = (
        "Analyse de sensibilité par simulation stochastique de Monte Carlo pour quantifier la dispersion de la valeur."
    )

    SEC_7_PEERS = "#### Option : Cohorte de Comparables (Triangulation)"
    SEC_7_DESC_PEERS = "Validation de la valeur intrinsèque par comparaison aux multiples boursiers du secteur."

    SEC_8_SCENARIOS = "#### Option : Analyse de Scénarios (Convictions)"
    SEC_8_DESC_SCENARIOS = (
        "Modélisation de variantes stratégiques (Bull/Bear) pour tester la robustesse de vos hypothèses."
    )

    SEC_9_SOTP = "#### Option : Somme des Parties (Segmentation SOTP)"
    SEC_9_DESC = "Décomposition de la valeur d'entreprise par segments métier ou actifs distincts."

    # ==========================================================================
    # 2. MODULE : ÉTAPE 5 - EQUITY BRIDGE
    # ==========================================================================
    BRIDGE_TITLE = "#### Equity Bridge"
    BRIDGE_SUBTITLE = "Réconciliation de la Valeur d'Entreprise vers la Valeur par Action"

    BRIDGE_COMPONENTS = "**1. Structure du Capital (M$)**"
    BRIDGE_ADJUSTMENTS = "**2. Ajustements de Valeur (M$)**"
    BRIDGE_DILUTION = "**3. Ajustements Dilutifs (SBC)**"

    INP_DEBT = "Dette Financière Totale (M$)"
    INP_CASH = "Trésorerie et Équivalents (M$)"
    INP_SHARES = "Actions en circulation (Millions)"
    INP_MINORITIES = "Intérêts Minoritaires (M$)"
    INP_PENSIONS = "Provisions / Engagements Sociaux (M$)"

    # ==========================================================================
    # 3. MODULE : ÉTAPE 6 - MONTE CARLO
    # ==========================================================================
    MC_CALIBRATION = "Activer la simulation stochastique"
    MC_ITERATIONS = "Nombre d'itérations"
    MC_VOL_INCERTITUDE = "**Calibration des volatilités (Écarts-types σ)**"
    MC_VOL_BASE_FLOW = "Incertitude flux d'ancrage (%)"
    MC_VOL_BETA = "Incertitude coefficient Bêta (σ)"
    MC_VOL_G = "Incertitude croissance g (%)"
    LBL_VOL_OMEGA = "Incertitude persistance ω (%)"
    LBL_VOL_GN = "Incertitude croissance perpétuelle gn (%)"

    # ==========================================================================
    # 4. MODULE : ÉTAPE 8 - SCÉNARIOS (Bull/Base/Bear)
    # ==========================================================================
    INP_SCENARIO_ENABLE = "Activer l'analyse de scénarios"
    INP_SCENARIO_PROBA = "Probabilité de réalisation (%)"
    INP_SCENARIO_GROWTH = "Taux de croissance g (%)"
    INP_SCENARIO_MARGIN = "Marge FCF cible (%)"

    LABEL_SCENARIO_BULL = "Scénario Optimiste (Bull Case)"
    LABEL_SCENARIO_BASE = "Scénario de Référence (Base Case)"
    LABEL_SCENARIO_BEAR = "Scénario Pessimiste (Bear Case)"

    LBL_BULL = "Bull"
    LBL_BASE = "Base"
    LBL_BEAR = "Bear"

    SCENARIO_HINT = "Définissez vos variantes. Laissez vide pour utiliser les données du modèle de base."
    ERR_SCENARIO_PROBA_SUM = "La somme des probabilités est de {sum}% (le total doit être 100%)."
    ERR_SCENARIO_INVALID = "Certains paramètres de scénarios sont incomplets ou invalides."

    # ==========================================================================
    # 5. MODULE : ÉTAPE 9 - SOTP (Sum-of-the-Parts)
    # ==========================================================================
    LBL_SOTP_ENABLE = "Activer la décomposition SOTP"
    HELP_SOTP_ENABLE = "Permet de ventiler la valeur d'entreprise globale entre différentes Business Units."
    WARN_SOTP_RELEVANCE = (
        "L'analyse SOTP est recommandée pour les conglomérats. Pour une entreprise"
        " mono-segment, utilisez-la uniquement pour decomposer la valeur calculée."
    )

    SEC_SOTP_SEGMENTS = "**Segmentation opérationnelle (M$)**"
    SEC_SOTP_ADJUSTMENTS = "**Ajustements de holding / conglomérat**"

    LBL_SEGMENT_NAME = "Nom du Segment"
    LBL_SEGMENT_VALUE = "Valeur d'Entreprise (EV) (Millions)"
    LBL_SEGMENT_METHOD = "Méthode de Valorisation"
    LBL_DISCOUNT = "Décote de conglomérat (%)"
    LBL_COMPARATIVE = "multiples comparatifs"

    # ==========================================================================
    # 6. LABELS D'INPUTS UNIVERSELS (Paramètres financiers)
    # ==========================================================================
    INP_PROJ_YEARS = "Années de projection"
    SLIDER_PROJ_YEARS = "Horizon explicite (t années)"

    INP_RF = "Taux Sans Risque (Rf) (%)"
    INP_BETA = "Coefficient Bêta (β)"
    INP_MRP = "Prime de Risque Marché (MRP) (%)"
    INP_KD = "Coût de la Dette Brut (kd) (%)"
    INP_TAX = "Taux d'Imposition Effectif (τ) (%)"
    INP_PERP_G = "Croissance Perpétuelle (gn) (%)"
    INP_EXIT_MULT = "Multiple de Sortie (Terminal) (x)"
    INP_GROWTH_G = "Taux de croissance moyen (g) (%)"
    INP_PRICE_WEIGHTS = "Cours de l'action ($/action)"
    INP_OMEGA = "Facteur de persistance (ω)"

    # ==========================================================================
    # 7. TOOLTIPS & TEXTES D'AIDE (Help Texts)
    # ==========================================================================
    HELP_PROJ_YEARS = "Durée de la phase de croissance explicite avant le calcul de la valeur terminale."
    HELP_GROWTH_RATE = "Taux annuel moyen de croissance des flux (g). Vide = Estimation via historique Yahoo."
    HELP_RF = "Rendement des obligations d'État à 10 ans. Vide = Taux actuel du marché (Auto)."
    HELP_BETA = "Sensibilité de l'action face au marché. Vide = Régression Yahoo Finance sur 5 ans."
    HELP_MRP = "Surprime historique exigée pour détenir des actions (Equity Risk Premium)."
    HELP_KD = "Coût moyen pondéré de la dette brute avant impact fiscal."
    HELP_TAX = "Taux réel d'imposition moyen attendu sur l'horizon de projection."
    HELP_PERP_G = "Taux de croissance à l'infini (gn). Doit être ≤ croissance du PIB nominal."
    HELP_EXIT_MULT = "Multiple de référence (EV/EBITDA ou P/E) appliqué au flux terminal."
    HELP_SBC_DILUTION = "Dilution annuelle moyenne liée à la rémunération en actions (Stock-Based Compensation)."
    HELP_PRICE_WEIGHTS = "Cours boursier de référence pour déterminer la pondération Equity/Dette dans le WACC."
    HELP_OMEGA = "Facteur de persistance des surprofits : 0 = érosion immédiate, 1 = rente perpétuelle."
    HELP_MC_ENABLE = "Simulation stochastique pour évaluer l'intervalle de confiance du prix intrinsèque."
    HELP_MC_SIMS = "Nombre de tirages aléatoires. 5000 itérations offrent un ratio précision/vitesse optimal."
    HELP_SCENARIO_ENABLE = "Permet de tester des variantes Bull/Bear pour valider la robustesse opérationnelle."
    HELP_PEER_TRIANGULATION = (
        "Compare la valeur intrinsèque calculée aux multiples de valorisation de sociétés comparables."
    )
    HELP_SHARES = "Nombre total d'actions ordinaires diluées (incluant stock-options exercibles)."
    HELP_DEBT = "Somme des dettes financières à court et long terme (Dette brute)."
    HELP_CASH = "Trésorerie disponible, équivalents de trésorerie et placements financiers."
    HELP_SOTP = "Applique une décote de holding sur la somme des parties."

    # Tooltips Monte Carlo (Incertitudes)
    HELP_MC_VOL_FLOW = "Écart-type attendu sur le premier flux de trésorerie (Année 0)."
    HELP_MC_VOL_BETA = "Dispersion statistique possible du coefficient Bêta (Risque de marché)."
    HELP_MC_VOL_G = "Incertitude sur le taux de croissance moyen de la phase 1."
    HELP_MC_VOL_OMEGA = "Volatilité du facteur de persistance des profits (Modèle RIM)."
    HELP_MC_VOL_GN = "Incertitude sur la croissance à l'infini (gn)."

    # ==========================================================================
    # 8. ÉLÉMENTS D'UI & NAVIGATION (Factory, Boutons, Méthodes)
    # ==========================================================================
    # Catégories de modèles
    CATEGORY_DEFENSIVE = "1. Approche Défensive (Screening)"
    CATEGORY_RELATIVE_SECTORIAL = "2. Approche Relative (Sectoriel)"
    CATEGORY_FUNDAMENTAL_DCF = "3. Approche Fondamentale (DCF)"
    CATEGORY_OTHER = "Autre"

    # Peer Triangulation
    LBL_PEER_ENABLE = "Activer la triangulation sectorielle"
    INP_MANUAL_PEERS = "Tickers des comparables"
    PLACEHOLDER_PEERS = "ex: AAPL, MSFT, GOOGL"
    HELP_MANUAL_PEERS = "Séparez les tickers par une virgule. Les données seront extraites automatiquement."
    PEERS_SELECTED = "*Pairs identifiés pour triangulation : {peers}*"

    # Terminal Value Methods
    RADIO_TV_METHOD = "Méthode de calcul terminal (TV)"
    TV_GORDON = "Modèle de Gordon-Shapiro (gn)"
    TV_EXIT = "Multiples de Marché (Exit Multiple)"

    # SBC & Dilution
    LABEL_DILUTION_SBC = "Impact Dilutif (SBC)"
    INP_SBC_DILUTION = "Taux de dilution annuelle attendu (%)"
    WARN_SBC_TECH = "Pour les sociétés Tech, prévoyez un taux de 1% à 3% pour refléter la dilution future."

    # Boutons
    BTN_CALCULATE = "Générer le Dossier de Valorisation"
    BTN_VALUATE_STD = "Valoriser {ticker} (Expert)"

    # ==========================================================================
    # 9. FORMULES FINANCIÈRES (LaTeX)
    # ==========================================================================
    # Bridge
    FORMULA_BRIDGE = r"P = \frac{EV - \text{Dette} + \text{Trésorerie} - \text{Minorités}}{\text{Actions}}"
    FORMULA_BRIDGE_SIMPLE = r"P = \frac{\text{Valeur Actionnaire}}{\text{Actions}}"

    # Capital
    FORMULA_CAPITAL_KE = r"k_e = R_f + \beta \times (E R P)"
    FORMULA_CAPITAL_WACC = r"WACC = \frac{E}{D+E} \times K_e + \frac{D}{D+E} \times K_d \times (1 - T)"

    # Valeur Terminale (Dynamique Étape 4)
    FORMULA_TV_GORDON = r"TV_n = \frac{FCF_n(1+g_n)}{WACC - g_n}"
    FORMULA_TV_EXIT = r"TV_n = FCF_{n} \cdot Multiple_{exit}"

    # Extensions optionnelles (Index 6 à 10)
    SEC_10_BACKTEST = "#### Option : Validation Historique (Backtest)"
    SEC_10_DESC_BACKTEST = (
        "Analyse rétrospective comparant la valeur intrinsèque (IV) aux cours de clôture"
        " historiques pour tester la fiabilité du modèle."
    )
    LBL_BACKTEST_ENABLE = "Activer le Backtesting temporel"
    HELP_BACKTEST_ENABLE = (
        "Recalcule le modèle sur les 3 dernières années pour vérifier si le prix"
        " intrinsèque a historiquement anticipé les mouvements de marché."
    )

    # ==========================================================================
    # 10. MODULE : ÉTAPE 11 - SENSIBILITÉ (WACC vs g)
    # ==========================================================================
    SEC_11_SENSITIVITY = "#### Option : Analyse de Sensibilité (Stress Test)"
    LBL_SENSITIVITY_ENABLE = "Activer la matrice de sensibilité"
    MSG_SENSITIVITY_DESC = (
        "Génère une matrice croisée (Heatmap) pour visualiser l'impact des variations"
        " du WACC et de la croissance (g) sur la valorisation finale."
    )

    LBL_SENS_STEP = "Pas de variation (%)"
    LBL_SENS_RANGE = "Profondeur d'analyse (Nombre de pas)"

    HELP_SENS_STEP = "Amplitude de chaque saut (ex: 0.005 = 0.5%). Un pas plus petit donne une granularité plus fine."
    HELP_SENS_RANGE = (
        "Nombre de colonnes/lignes de part et d'autre de la valeur centrale (ex: 2 signifie -2, -1, 0, +1, +2)."
    )


# ==============================================================================
# CLASSES NARRATIVES SPÉCIFIQUES (Héritage de SharedTexts)
# ==============================================================================


class FCFFStandardTexts(UISharedTexts):
    TITLE = "FCFF Standard (Modèle à deux étapes)"
    DESCRIPTION = (
        "Valorisation fondamentale de l'entreprise par l'actualisation des flux de trésorerie disponibles (FCFF)."
    )
    STEP_1_TITLE = "#### Étape 1 : Ancrage du Flux Opérationnel"
    STEP_1_DESC = "Définition du flux de trésorerie disponible pour la firme (FCFF) de référence pour l'année 0."
    STEP_1_FORMULA = r"FCFF = EBIT \times (1 - \tau) + DA - \Delta WCR - CapEx"
    INP_BASE = "Flux FCFF d'ancrage (M$)"
    HELP_BASE = "Flux de trésorerie opérationnel net, disponible pour tous les apporteurs de capitaux (Dette + Equity)."
    STEP_2_TITLE = "#### Étape 2 : Trajectoire de Croissance"
    STEP_2_DESC = "Définition de la croissance annuelle attendue et de l'horizon temporel explicite."
    INP_GROWTH_G = "Croissance annuelle phase 1 (%)"


class FCFFNormalizedTexts(UISharedTexts):
    LBL_GROWTH_G = "Taux de croissance (g)"
    TITLE = "Approche Entité (FCFF Normalisé)"
    DESCRIPTION = "DCF utilisant un flux lissé sur le cycle pour neutraliser la volatilité court terme."
    STEP_1_TITLE = "#### Étape 1 : Flux Normatif (FCF norm)"
    STEP_1_DESC = "Estimation d'un flux de croisière moyen sur 3 à 5 ans pour stabiliser la valorisation."
    STEP_1_FORMULA = r"V_0 = \sum_{t=1}^{n} \frac{FCF_{norm}(1+g)^t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}"
    INP_BASE = "Flux normatif de cycle (M$)"
    HELP_BASE = "Flux moyen lissé pour éviter de valoriser l'entreprise sur un pic ou un creux cyclique."
    STEP_2_TITLE = "#### Étape 2 : Croissance de Cycle"
    STEP_2_DESC = "Projection de la croissance moyenne stable attendue sur le cycle à venir."
    HELP_GROWTH = "Taux de croissance annuel moyen visé pour le flux normalisé."


class FCFFGrowthTexts(UISharedTexts):
    TITLE = "FCFF : Modèle de Croissance & Marges"
    DESCRIPTION = "Valorisation par projection du chiffre d'affaires et convergence vers une marge cible."
    STEP_1_TITLE = "#### Étape 1 : Assiette de Revenus"
    STEP_1_DESC = "Saisie du Chiffre d'Affaires TTM (Derniers 12 mois) servant de base à la projection."
    STEP_1_FORMULA = r"FCF_t = Revenue_0 \times (1+g)^t \times Marge_{cible}"
    INP_BASE = "Chiffre d'Affaires TTM (M$)"
    HELP_REV_TTM = "Total des revenus générés au cours des 12 derniers mois."
    STEP_2_TITLE = "#### Étape 2 : Convergence des Marges"
    STEP_2_DESC = "Hypothèses de croissance top-line et de marge FCF cible à terme."
    INP_REV_GROWTH = "Croissance annuelle du CA (%)"
    HELP_REV_GROWTH = "Taux de croissance annuel projeté pour les ventes."
    INP_MARGIN_TARGET = "Marge FCF cible (%)"
    HELP_MARGIN_TARGET = "Marge de flux de trésorerie disponible visée à la fin de l'horizon de projection."

    # Disclaimer about margin simplification
    MARGIN_DISCLAIMER = """ATTENTION - Approche simplifiée : La formule FCF_t = Revenue_t × Marge_cible
suppose que le CapEx, la variation du BFR et les impôts sont implicitement intégrés dans la marge.

Formule complète professionnelle :
FCFF = Revenue × Marge_EBIT × (1-T) - Réinvestissements

Cette simplification est appropriée pour les analyses rapides ou lorsque les données détaillées
ne sont pas disponibles."""


class RIMTexts(UISharedTexts):
    """
    Textes spécifiques pour le Modèle à Revenu Résiduel (RIM / Ohlson).
    Idéal pour les financières (Banques, Assurances) où la Book Value est centrale.
    """

    TITLE = "Revenu Résiduel (RIM)"
    DESCRIPTION = (
        "Modèle d'Ohlson : Valorisation par la Valeur Comptable et la persistance de la création de valeur (ROE > Ke)."
    )

    # --- ÉTAPE 1 : ANCRAGE BILANCIEL ---
    STEP_1_TITLE = "#### Étape 1 : Ancrage Bilanciel (Book Value)"
    STEP_1_DESC = "Définition du socle de capitaux propres et de la capacité bénéficiaire actuelle."

    # Formule RIM canonique
    STEP_1_FORMULA = r"V_0 = BV_0 + \sum_{t=1}^{n} \frac{NI_t - (k_e \times BV_{t-1})}{(1+k_e)^t} + TV"

    # Inputs Principaux (Utilisés par rim_bank_view.py)
    INP_BV_BASE = "Valeur Comptable (Book Value) (M$)"
    HELP_BV_BASE = (
        "Capitaux propres part du groupe (Equity) au dernier bilan publié. Point de départ de la valorisation."
    )

    # Inputs Secondaires (Pour d'éventuelles variantes ou affichages détaillés)
    INP_BV_INITIAL = "Valeur Comptable Initiale (BV₀)"
    HELP_BV_INITIAL = "Montant des capitaux propres comptables servant d'ancrage fondamental au modèle."

    INP_NI_TTM = "Résultat Net Normatif (M$)"
    HELP_NI_TTM = "Bénéfice net récurrent (Net Income) servant à déterminer le profit résiduel initial."

    INP_EPS_ANCHOR = "EPS (Bénéfice par action)"
    HELP_EPS_ANCHOR = "Bénéfice par action normalisé ou TTM. Sert d'ancrage pour la projection des profits résiduels."

    # --- ÉTAPE 2 : DYNAMIQUE & PERSISTANCE ---
    STEP_2_TITLE = "#### Étape 2 : Persistance des Profits Anormaux"
    STEP_2_DESC = (
        "Estimation de la durée pendant laquelle l'entreprise génère un rendement"
        " supérieur à son coût du capital (Facteur Omega)."
    )

    HELP_GROWTH = "Taux de croissance des fonds propres (via mise en réserve) avant l'atténuation par le facteur Omega."

    # Omega (persistence factor) explanation
    HELP_OMEGA = """Facteur de persistance des profits anormaux : ω (0 < ω < 1), issu du modèle Ohlson (1995) AR(1).
- ω = 1 : les profits anormaux persistent indéfiniment (scénario agressif, avantage compétitif durable)
- ω = 0 : les profits anormaux disparaissent immédiatement (scénario conservateur, forte concurrence)
- Valeurs typiques : 0.5-0.7 pour entreprises matures
Modélisation : RI_{t+1} = ω × RI_t (processus autorégressif AR(1), Ohlson 1995)"""

    # Sections Logiques (Headers de regroupement)
    SEC_1_RIM_BASE = "1. Ancrage Comptable"
    SEC_2_PROJ_RIM = "2. Projection & Atténuation (Omega)"


class GrahamTexts(UISharedTexts):
    """
    Textes spécifiques pour la méthode de Valorisation Intrinsèque de Graham.
    """

    TITLE = "Nombre de Graham (Screening)"
    DESCRIPTION = "Formule de Benjamin Graham révisée (1974) pour l'évaluation sécuritaire des bénéfices."

    # --- ÉTAPE 1 : CAPACITÉ BÉNÉFICIAIRE ---
    STEP_1_TITLE = "#### Étape 1 : Capacité Bénéficiaire & Croissance"
    STEP_1_DESC = "Saisie du bénéfice par action normalisé et de la croissance prévisionnelle conservatrice."
    STEP_1_FORMULA = r"V = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}"

    # Inputs EPS
    INP_EPS = "BPA (EPS) Normalisé ($)"
    HELP_EPS = (
        "Bénéfice par action lissé (moyenne 3-5 ans) ou TTM ajusté des éléments"
        " exceptionnels pour refléter la capacité bénéficiaire réelle."
    )

    # Alias pour compatibilité interne (si utilisé ailleurs)
    INP_EPS_NORM = "BPA (EPS) normalisé ($/action)"
    HELP_EPS_NORM = "Bénéfice par action moyen ou TTM ajusté des éléments exceptionnels."

    # Inputs Croissance
    INP_GROWTH = "Croissance Attendue (g) (%)"
    INP_GROWTH_G = "Croissance attendue g (%)"
    HELP_GROWTH_LT = (
        "Taux de croissance annuel moyen estimé pour les 7 à 10 prochaines années (doit rester conservateur)."
    )

    # --- ÉTAPE 2 : CONDITIONS DE MARCHÉ ---
    STEP_2_TITLE = "#### Étape 2 : Conditions de Marché"
    STEP_2_DESC = "Paramètres du rendement obligataire corporate et de la fiscalité."

    INP_YIELD_AAA = "Rendement Obligataire AAA (Y) (%)"
    HELP_YIELD_AAA = "Rendement actuel des obligations d'entreprises de haute qualité (référence vs 4.4% historique)."

    INP_TAX = "Taux d'imposition Effectif (%)"
    HELP_TAX = "Taux effectif moyen d'imposition attendu pour la société."

    NOTE_GRAHAM = (
        "Note : Le facteur 8.5 correspond au P/E d'une entreprise à croissance nulle."
        " Le facteur 4.4 représente le rendement AAA historique de référence."
    )


class FCFETexts(UISharedTexts):
    TITLE = "Flux de Trésorerie Actionnaires (FCFE)"
    DESCRIPTION = "Valorisation directe des fonds propres via les flux résiduels après service de la dette."
    STEP_1_TITLE = "#### Étape 1 : Ancrage Actionnaire"
    STEP_1_DESC = "Définition du flux FCFE disponible pour l'actionnaire et de la politique d'endettement."
    STEP_1_FORMULA = r"FCFE = OCF - Capex + \Delta \text{Net Borrowing}"
    INP_BASE = "Flux FCFE d'ancrage (M$)"
    HELP_FCFE_BASE = (
        "Flux de trésorerie disponible pour les actionnaires après réinvestissement et service de la dette."
    )
    INP_NET_BORROWING = "Variation de l'endettement (M$)"
    HELP_NET_BORROWING = "Montant net des nouvelles émissions de dette moins les remboursements de principal."
    STEP_2_TITLE = "#### Étape 2 : Horizon de Projection"
    STEP_2_DESC = "Définition de la trajectoire de croissance et de l'horizon temporel."


class DDMTexts(UISharedTexts):
    TITLE = "Modèle d'Actualisation des Dividendes (DDM)"
    DESCRIPTION = "Valorisation basée sur la distribution future de dividendes aux actionnaires."
    STEP_1_TITLE = "#### Étape 1 : Flux de Dividendes"
    STEP_1_DESC = "Ancrage du dividende par action (DPA) de référence pour le calcul de départ."
    STEP_1_FORMULA = r"V_0 = \sum_{t=1}^{n} \frac{D_t}{(1+k_e)^t} + \frac{TV_n}{(1+k_e)^n}"
    INP_BASE = "Dividende par action ($/action)"
    INP_DIVIDEND_BASE = "Dividende par action ($/action)"
    HELP_DIVIDEND_BASE = "Dividende brut annuel versé (TTM) ou annoncé pour l'exercice en cours."
    STEP_2_TITLE = "#### Étape 2 : Dynamique de Croissance"
    STEP_2_DESC = "Projection de la croissance du dividende (g) sur l'horizon explicite."
    NOTE_DDM_SGR = "Note : Le taux de croissance soutenable (SGR) peut être estimé par : ROE × (1 - Payout)."


class ExpertTexts:
    TITLE = "Mode Expert"
    SUBTITLE = "Configuration avancée des paramètres"
