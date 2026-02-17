"""
src/i18n/fr/ui/terminals.py

Architecture Institutionnelle - Source de Vérité des Terminaux Experts (V2).
==============================================================================
Centralisation complète de tous les textes d'interface pour les terminaux experts.

Structure :
1. CommonTerminals : Socle commun partagé entre tous les modèles
2. Classes Spécialisées : Textes spécifiques par stratégie (FCFF, DDM, RIM, Graham, etc.)

Règles de rédaction strictes :
- INTERDICTION : Ne plus utiliser $M, M$ ou (M)
- STANDARD : Écrire "(Millions)" pour les montants
- Unités explicites : "(Millions)", "(%)", "($/action)"
- Help : Uniquement pour les concepts techniques complexes
- Format : "%.2f" systématiquement pour permettre les virgules

Maintenance :
- Ce fichier est la SEULE source de vérité pour les textes UI
- Toute modification doit être faite ici uniquement
- Les vues importent depuis ce fichier
"""


class CommonTerminals:
    """
    Socle commun - Constantes partagées par tous les terminaux experts.

    Centralise :
    - Les titres d'étapes standards (Step 1 à 5)
    - Les unités explicites
    - Les labels universels (Risk-free, Beta, MRP, etc.)
    - Les formules financières LaTeX communes
    - Les messages d'erreur
    """

    # ==========================================================================
    # 1. UNITÉS EXPLICITES (Standard Institutionnel)
    # ==========================================================================
    UNIT_MILLIONS = "(Millions)"
    UNIT_PERCENT = "(%)"
    UNIT_CURRENCY = "($/action)"
    UNIT_MULTIPLE = "(x)"

    # ==========================================================================
    # 2. ÉTAPES STANDARDS (Titres et Descriptions)
    # ==========================================================================
    # Étape 1 : Ancrage du Flux Opérationnel
    STEP_1_TITLE = "#### Étape 1 : Ancrage du Flux Opérationnel"
    STEP_1_DESC = "Définition du flux de référence servant de base à la projection."

    # Étape 2 : Trajectoire de Croissance
    STEP_2_TITLE = "#### Étape 2 : Trajectoire de Croissance"
    STEP_2_DESC = "Définition de la dynamique de croissance et de l'horizon temporel."

    # Étape 3 : Taux d'Actualisation
    # Note: Le titre est dynamique selon le type de modèle (Firm vs Equity)
    STEP_3_TITLE_WACC = "#### Étape 3 : Taux d'Actualisation (WACC)"
    STEP_3_TITLE_KE = "#### Étape 3 : Coût des Fonds Propres (Ke)"
    STEP_3_DESC = "Détermination du taux requis pour rémunérer le risque opérationnel et financier."

    # Étape 4 : Valeur de Continuation
    STEP_4_TITLE = "#### Étape 4 : Valeur de Continuation (Sortie)"
    STEP_4_DESC = "Estimation de la valeur de l'entreprise au-delà de l'horizon de projection explicite."

    # Étape 5 : Bridge de Valeur
    STEP_5_TITLE = "#### Étape 5 : Bridge de Valeur"
    STEP_5_DESC = "Passage de la valeur de l'actif économique (EV) à la valeur revenant aux actionnaires (Equity)."

    # ==========================================================================
    # 3. LABELS UNIVERSELS (Inputs Standards)
    # ==========================================================================
    # Horizon de Projection
    INP_PROJ_YEARS = "Années de projection"
    SLIDER_PROJ_YEARS = "Horizon explicite (années)"

    # Paramètres de Risque
    INP_RF = f"Taux Sans Risque (Rf) {UNIT_PERCENT}"
    INP_BETA = "Coefficient Bêta (β)"
    INP_MRP = f"Prime de Risque Marché (MRP) {UNIT_PERCENT}"
    INP_KD = f"Coût de la Dette Brut (kd) {UNIT_PERCENT}"
    INP_TAX = f"Taux d'Imposition Effectif (τ) {UNIT_PERCENT}"

    # Croissance et Sortie
    INP_GROWTH_G = f"Taux de croissance moyen (g) {UNIT_PERCENT}"
    INP_PERP_G = f"Croissance à l'Infini (g_n) {UNIT_PERCENT}"
    INP_EXIT_MULT = f"Multiple de Sortie (Terminal) {UNIT_MULTIPLE}"

    # Structure du Capital
    INP_DEBT = f"Dette Financière Totale {UNIT_MILLIONS}"
    INP_CASH = f"Trésorerie et Équivalents {UNIT_MILLIONS}"
    INP_SHARES = f"Actions en circulation {UNIT_MILLIONS}"
    INP_MINORITIES = f"Intérêts Minoritaires {UNIT_MILLIONS}"
    INP_PENSIONS = f"Provisions / Engagements Sociaux {UNIT_MILLIONS}"

    # Dilution et Prix
    INP_PRICE_WEIGHTS = f"Cours de l'action {UNIT_CURRENCY}"
    INP_SBC_DILUTION = f"Taux de dilution annuelle attendu {UNIT_PERCENT}"

    # Facteurs Spéciaux
    INP_OMEGA = "Facteur de persistance (ω)"

    # ==========================================================================
    # 4. TOOLTIPS (Concepts Techniques Uniquement)
    # ==========================================================================
    # Paramètres de projection
    HELP_PROJ_YEARS = "Durée de la phase de croissance explicite avant le calcul de la valeur terminale."
    HELP_GROWTH_RATE = "Taux annuel moyen de croissance des flux (g). Vide = Estimation via historique Yahoo."

    # Paramètres de risque (Concepts techniques)
    HELP_RF = "Rendement des obligations d'État à 10 ans. Vide = Taux actuel du marché (Auto)."
    HELP_BETA = "Sensibilité de l'action face au marché. Vide = Régression Yahoo Finance sur 5 ans."
    HELP_MRP = "Surprime historique exigée pour détenir des actions (Equity Risk Premium)."
    HELP_KD = "Coût moyen pondéré de la dette brute avant impact fiscal."
    HELP_TAX = "Taux réel d'imposition moyen attendu sur l'horizon de projection."

    # Sortie (Concepts techniques)
    HELP_PERP_G = "Taux de croissance à l'infini (gn). Doit être ≤ croissance du PIB nominal."
    HELP_EXIT_MULT = "Multiple de référence (EV/EBITDA ou P/E) appliqué au flux terminal."

    # Structure du Capital
    HELP_SHARES = "Nombre total d'actions ordinaires diluées (incluant stock-options exercibles)."
    HELP_DEBT = "Somme des dettes financières à court et long terme (Dette brute)."
    HELP_CASH = "Trésorerie disponible, équivalents de trésorerie et placements financiers."
    HELP_SBC_DILUTION = "Dilution annuelle moyenne liée à la rémunération en actions (Stock-Based Compensation)."
    HELP_PRICE_WEIGHTS = "Cours boursier de référence pour déterminer la pondération Equity/Dette dans le WACC."

    # Facteurs spéciaux (Concepts techniques)
    HELP_OMEGA = "Facteur de persistance des surprofits : 0 = érosion immédiate, 1 = rente perpétuelle."

    # ==========================================================================
    # 5. FORMULES FINANCIÈRES (LaTeX)
    # ==========================================================================
    # Capital
    FORMULA_CAPITAL_KE = r"k_e = R_f + \beta \times (E R P)"
    FORMULA_CAPITAL_WACC = r"WACC = \frac{E}{D+E} \times K_e + \frac{D}{D+E} \times K_d \times (1 - T)"

    # Equity Bridge
    FORMULA_BRIDGE = r"P = \frac{EV - \text{Dette} + \text{Trésorerie} - \text{Minorités}}{\text{Actions}}"
    FORMULA_BRIDGE_SIMPLE = r"P = \frac{\text{Valeur Actionnaire}}{\text{Actions}}"

    # Valeur Terminale (Générique)
    FORMULA_TV_GORDON = r"TV_n = \frac{FCF_n(1+g_n)}{WACC - g_n}"
    FORMULA_TV_EXIT = r"TV_n = FCF_{n} \cdot Multiple_{exit}"

    # Valeur Terminale (Spécifique par Modèle)
    FORMULA_TV_FCFF_STD = r"TV_n = \frac{FCF_n(1+g_n)}{WACC - g_n}"
    FORMULA_TV_FCFF_NORM = r"TV_n = \frac{FCF_{norm}(1+g_n)}{WACC - g_n}"
    FORMULA_TV_FCFF_GROWTH = r"TV_n = \frac{Rev_n \times Margin_{target} \times (1+g_n)}{WACC - g_n}"
    FORMULA_TV_FCFE = r"TV_n = \frac{FCFE_n(1+g_n)}{k_e - g_n}"
    FORMULA_TV_DDM = r"TV_n = \frac{D_n(1+g_n)}{k_e - g_n}"

    # ==========================================================================
    # 6. EXTENSIONS OPTIONNELLES (Sections 6 à 11)
    # ==========================================================================
    # Section 6 : Monte Carlo
    SEC_6_MC = "#### Option : Simulation Probabiliste (Incertitude)"
    SEC_6_DESC_MC = "Analyse de sensibilité par simulation stochastique de Monte Carlo pour quantifier la dispersion de la valeur."

    MC_CALIBRATION = "Activer la simulation stochastique"
    MC_ITERATIONS = "Nombre d'itérations"
    MC_VOL_INCERTITUDE = "**Calibration des volatilités (Écarts-types σ)**"
    MC_VOL_BASE_FLOW = f"Volatilité du flux de l'année 0"
    MC_VOL_BETA = "Incertitude coefficient Bêta (σ)"
    MC_VOL_G = f"Incertitude croissance g {UNIT_PERCENT}"
    LBL_VOL_OMEGA = f"Incertitude persistance ω {UNIT_PERCENT}"
    LBL_VOL_GN = f"Incertitude croissance perpétuelle gn {UNIT_PERCENT}"
    LBL_VOL_EXIT_M = "Volatilité du multiple terminal"

    # Volatilités spécifiques par modèle
    MC_VOL_EPS = "Incertitude sur le BPA (EPS)"
    MC_VOL_NI = "Incertitude sur le Résultat Net"
    MC_VOL_DIV = "Incertitude sur le Dividende"

    HELP_MC_ENABLE = "Simulation stochastique pour évaluer l'intervalle de confiance du prix intrinsèque."
    HELP_MC_SIMS = "Nombre de tirages aléatoires. 5000 itérations offrent un ratio précision/vitesse optimal."
    HELP_MC_VOL_FLOW = "Écart-type attendu sur le premier flux de trésorerie (Année 0)."
    HELP_MC_VOL_BETA = "Dispersion statistique possible du coefficient Bêta (Risque de marché)."
    HELP_MC_VOL_G = "Incertitude sur le taux de croissance moyen de la phase 1."
    HELP_MC_VOL_OMEGA = "Volatilité du facteur de persistance des profits (Modèle RIM)."
    HELP_MC_VOL_GN = "Incertitude sur la croissance à l'infini (gn)."

    # Section 7 : Peer Triangulation
    SEC_7_PEERS = "#### Option : Cohorte de Comparables (Triangulation)"
    SEC_7_DESC_PEERS = "Validation de la valeur intrinsèque par comparaison aux multiples boursiers du secteur."

    LBL_PEER_ENABLE = "Activer la triangulation sectorielle"
    INP_MANUAL_PEERS = "Tickers des comparables"
    PLACEHOLDER_PEERS = "ex: AAPL, MSFT, GOOGL"
    HELP_MANUAL_PEERS = "Séparez les tickers par une virgule. Les données seront extraites automatiquement."
    HELP_PEER_TRIANGULATION = "Compare la valeur intrinsèque calculée aux multiples de valorisation de sociétés comparables."
    PEERS_SELECTED = "*Pairs identifiés pour triangulation : {peers}*"

    # Section 8 : Scénarios
    SEC_8_SCENARIOS = "#### Option : Analyse de Scénarios (Convictions)"
    SEC_8_DESC_SCENARIOS = "Modélisation de variantes stratégiques (Bull/Bear) pour tester la robustesse de vos hypothèses."

    INP_SCENARIO_ENABLE = "Activer l'analyse de scénarios"
    INP_SCENARIO_PROBA = f"Probabilité de réalisation {UNIT_PERCENT}"
    INP_SCENARIO_GROWTH = f"Taux de croissance g {UNIT_PERCENT}"
    INP_SCENARIO_MARGIN = f"Marge FCF cible {UNIT_PERCENT}"

    LABEL_SCENARIO_BULL = "Scénario Optimiste (Bull Case)"
    LABEL_SCENARIO_BASE = "Scénario de Référence (Base Case)"
    LABEL_SCENARIO_BEAR = "Scénario Pessimiste (Bear Case)"

    LBL_BULL = "Bull"
    LBL_BASE = "Base"
    LBL_BEAR = "Bear"

    SCENARIO_HINT = "Définissez vos variantes. Laissez vide pour utiliser les données du modèle de base."
    ERR_SCENARIO_PROBA_SUM = "La somme des probabilités est de {sum}% (le total doit être 100%)."
    ERR_SCENARIO_INVALID = "Certains paramètres de scénarios sont incomplets ou invalides."
    HELP_SCENARIO_ENABLE = "Permet de tester des variantes Bull/Bear pour valider la robustesse opérationnelle."

    # Section 9 : SOTP
    SEC_9_SOTP = "#### Option : Somme des Parties (Segmentation SOTP)"
    SEC_9_DESC = "Décomposition de la valeur d'entreprise par segments métier ou actifs distincts."

    LBL_SOTP_ENABLE = "Activer la décomposition SOTP"
    HELP_SOTP_ENABLE = "Permet de ventiler la valeur d'entreprise globale entre différentes Business Units."
    HELP_SOTP = "Applique une décote de holding sur la somme des parties."
    WARN_SOTP_RELEVANCE = "L'analyse SOTP est recommandée pour les conglomérats. Pour une entreprise mono-segment, utilisez-la uniquement pour décomposer la valeur calculée."

    SEC_SOTP_SEGMENTS = "**Segmentation opérationnelle (Millions)**"
    SEC_SOTP_ADJUSTMENTS = "**Ajustements de holding / conglomérat**"

    LBL_SEGMENT_NAME = "Nom du Segment"
    LBL_SEGMENT_VALUE = f"Valeur d'Entreprise (EV) {UNIT_MILLIONS}"
    LBL_SEGMENT_METHOD = "Méthode de Valorisation"
    LBL_DISCOUNT = f"Décote de conglomérat {UNIT_PERCENT}"
    LBL_COMPARATIVE = "multiples comparatifs"
    DEFAULT_SEGMENT_NAME = "Segment A"

    # Section 10 : Backtest
    SEC_10_BACKTEST = "#### Option : Validation Historique (Backtest)"
    SEC_10_DESC_BACKTEST = "Analyse rétrospective comparant la valeur intrinsèque (IV) aux cours de clôture historiques pour tester la fiabilité du modèle."
    LBL_BACKTEST_ENABLE = "Activer le Backtesting temporel"
    HELP_BACKTEST_ENABLE = "Recalcule le modèle sur les 3 dernières années pour vérifier si le prix intrinsèque a historiquement anticipé les mouvements de marché."
    LBL_LOOKBACK = "Recul historique (années)"

    # Section 11 : Sensibilité
    SEC_11_SENSITIVITY = "#### Option : Analyse de Sensibilité (Stress Test)"
    LBL_SENSITIVITY_ENABLE = "Activer la matrice de sensibilité"
    MSG_SENSITIVITY_DESC = "Génère une matrice croisée (Heatmap) pour visualiser l'impact des variations du WACC et de la croissance (g) sur la valorisation finale."

    LBL_SENS_STEP = f"Amplitude du pas de variation (±) {UNIT_PERCENT}"
    LBL_SENS_RANGE = "Profondeur d'analyse (Nombre de pas)"

    HELP_SENS_STEP = "Amplitude de chaque saut (ex: 0.005 = 0.5%). Un pas plus petit donne une granularité plus fine."
    HELP_SENS_RANGE = "Nombre de colonnes/lignes de part et d'autre de la valeur centrale (ex: 2 signifie -2, -1, 0, +1, +2)."

    # ==========================================================================
    # 7. MÉTHODES DE CALCUL TERMINAL VALUE
    # ==========================================================================
    RADIO_TV_METHOD = "Méthode de calcul terminal (TV)"
    TV_GORDON = "Modèle de Gordon-Shapiro (gn)"
    TV_EXIT = "Multiples de Marché (Exit Multiple)"

    # ==========================================================================
    # 8. DILUTION & SBC
    # ==========================================================================
    LABEL_DILUTION_SBC = "Impact Dilutif (SBC)"
    WARN_SBC_TECH = "Pour les sociétés Tech, prévoyez un taux de 1% à 3% pour refléter la dilution future."

    # ==========================================================================
    # 9. MESSAGES D'ERREUR & VALIDATION
    # ==========================================================================
    ERR_CRITICAL = "Une erreur critique est survenue lors de l'assemblage de la valorisation. Veuillez vérifier vos saisies ou contacter le support."
    ERR_VALIDATION = "Erreur de validation"

    # ==========================================================================
    # 10. BOUTONS & ACTIONS
    # ==========================================================================
    BTN_CALCULATE = "Générer le Dossier de Valorisation"
    BTN_VALUATE_STD = "Valoriser {ticker} (Expert)"

    # ==========================================================================
    # 11. CATÉGORIES DE MODÈLES (Factory)
    # ==========================================================================
    CATEGORY_DEFENSIVE = "1. Approche Défensive (Screening)"
    CATEGORY_RELATIVE_SECTORIAL = "2. Approche Relative (Sectoriel)"
    CATEGORY_FUNDAMENTAL_DCF = "3. Approche Fondamentale (DCF)"
    CATEGORY_OTHER = "Autre"


# ==============================================================================
# CLASSES SPÉCIALISÉES PAR STRATÉGIE
# ==============================================================================


class FCFFStandardTexts(CommonTerminals):
    """
    Textes spécifiques pour le modèle FCFF Standard (Modèle à deux étapes).
    Valorisation fondamentale par actualisation des flux de trésorerie disponibles.
    """

    TITLE = "DCF : Standard"
    DESCRIPTION = "L'approche par l'entité. Le moteur calcule la Valeur d'Entreprise en actualisant les flux de trésorerie disponibles (FCFF) au WACC."

    # Formule globale du modèle
    FORMULA_GLOBAL = r"EV = \sum_{t=1}^{n} \frac{FCFF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}"

    # Étape 1 : Ancrage spécifique
    STEP_1_TITLE = "#### Étape 1 : Ancrage du Flux Opérationnel"
    STEP_1_DESC = "Définition du flux de trésorerie disponible pour la firme (FCFF) de référence pour l'année 0."
    # DA = Depreciation & Amortization (Dotations aux Amortissements)
    # BFR = Besoin en Fonds de Roulement (Working Capital Requirement)
    STEP_1_FORMULA = r"FCFF_0 = EBIT \times (1 - \tau) + DA - \Delta BFR - CapEx"

    INP_BASE = f"FCFF de référence (Année 0) {CommonTerminals.UNIT_MILLIONS}"

    # Étape 2 : Croissance spécifique
    STEP_2_TITLE = "#### Étape 2 : Trajectoire de Croissance"
    STEP_2_DESC = "Définition de la croissance annuelle attendue et de l'horizon temporel explicite."

    # Formule TV spécifique
    FORMULA_TV = r"TV_n = \frac{FCF_n(1+g_n)}{WACC - g_n}"


class FCFFNormalizedTexts(CommonTerminals):
    """
    Textes spécifiques pour le modèle FCFF Normalisé.
    DCF utilisant un flux lissé sur le cycle pour neutraliser la volatilité court terme.
    """

    TITLE = "DCF : Fondamental"
    DESCRIPTION = (
        "Logique Damodaran pour entreprises cycliques : utilise un flux FCF lissé (Normalisé) pour neutraliser la "
        "volatilité court terme."
    )

    # Formule globale
    FORMULA_GLOBAL = r"EV = \sum_{t=1}^{n} \frac{FCFF_{norm} \times (1+g)^t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}"

    # Étape 1 : Flux Normatif
    STEP_1_TITLE = "#### Étape 1 : Flux Normatif (FCF norm)"
    STEP_1_DESC = "Estimation d'un flux de croisière moyen sur 3 à 5 ans pour stabiliser la valorisation."
    STEP_1_FORMULA = r"FCFF_{norm} = \text{EBIT}_{norm} \times (1 - \tau) - \text{Réinvestissement Net}"

    INP_BASE = f"Flux FCFF Normalisé {CommonTerminals.UNIT_MILLIONS}"

    # Étape 2 : Croissance de Cycle
    STEP_2_TITLE = "#### Étape 2 : Croissance de Cycle"
    STEP_2_DESC = "Projection de la croissance moyenne stable attendue sur le cycle à venir."
    HELP_GROWTH = "Taux de croissance annuel moyen visé pour le flux normalisé."
    LBL_GROWTH_G = f"Taux de croissance (g) {CommonTerminals.UNIT_PERCENT}"

    # Formule TV
    FORMULA_TV = r"TV_n = \frac{FCF_{norm}(1+g_n)}{WACC - g_n}"


class FCFFGrowthTexts(CommonTerminals):
    """
    Textes spécifiques pour le modèle FCFF Croissance & Marges.
    Valorisation par projection du chiffre d'affaires et convergence vers une marge cible.
    """

    TITLE = "DCF : Croissance"
    DESCRIPTION = (
        "Variante dynamique projetant les revenus avec une convergence linéaire vers une marge opérationnelle cible."
    )

    # Formule globale
    FORMULA_GLOBAL = r"FCFF_t = (Revenue_{t-1} \times (1+g_{rev})) \times \text{Marge}_t"

    # Étape 1 : Assiette de Revenus
    STEP_1_TITLE = "#### Étape 1 : Assiette de Revenus"
    STEP_1_DESC = "Saisie du Chiffre d'Affaires TTM (Derniers 12 mois) servant de base à la projection."
    STEP_1_FORMULA = r"Revenue_t = Revenue_{t-1} \times (1 + g_{sales})"

    INP_BASE = f"Chiffre d'Affaires TTM {CommonTerminals.UNIT_MILLIONS}"
    HELP_REV_TTM = "Total des revenus générés au cours des 12 derniers mois."

    # Étape 2 : Convergence des Marges
    STEP_2_TITLE = "#### Étape 2 : Convergence des Marges"
    STEP_2_DESC = "Convergence linéaire de la marge opérationnelle vers la cible normative."

    INP_REV_GROWTH = f"Croissance annuelle du CA {CommonTerminals.UNIT_PERCENT}"
    HELP_REV_GROWTH = "Taux de croissance annuel projeté pour les ventes."

    INP_MARGIN_TARGET = f"Marge FCF Normative (Cible) {CommonTerminals.UNIT_PERCENT}"
    HELP_MARGIN_TARGET = "Marge de flux de trésorerie disponible visée à la fin de l'horizon de projection."

    # Disclaimer
    MARGIN_DISCLAIMER = """ATTENTION - Approche simplifiée : La formule FCF_t = Revenue_t × Marge_cible
suppose que le CapEx, la variation du BFR et les impôts sont implicitement intégrés dans la marge.

Formule complète professionnelle :
FCFF = Revenue × Marge_EBIT × (1-T) - Réinvestissements

Cette simplification est appropriée pour les analyses rapides ou lorsque les données détaillées
ne sont pas disponibles."""

    # Formule TV
    FORMULA_TV = r"TV_n = \frac{Rev_n \times Margin_{target} \times (1+g_n)}{WACC - g_n}"


class RIMTexts(CommonTerminals):
    """
    Textes spécifiques pour le Modèle à Revenu Résiduel (RIM / Ohlson).
    Idéal pour les financières (Banques, Assurances) où la Book Value est centrale.
    """

    TITLE = "Modèle RIM"
    DESCRIPTION = (
        "Dédié au secteur financier. Somme de la Valeur Comptable actuelle et de la valeur actuelle des bénéfices "
        "excédentaires (Profit - K_e)."
    )

    # Formule globale (canonique RIM)
    FORMULA_GLOBAL = r"V_0 = BV_0 + \sum_{t=1}^{n} \frac{RI_t}{(1+K_e)^t} + \frac{TV_{RI}}{(1+K_e)^n}"

    # Étape 1 : Ancrage Bilanciel
    STEP_1_TITLE = "#### Étape 1 : Ancrage Bilanciel (Book Value)"
    STEP_1_DESC = "Définition du socle de capitaux propres et de la capacité bénéficiaire actuelle."
    STEP_1_FORMULA = r"RI_t = NetIncome_t - (BV_{t-1} \times K_e)"

    INP_BASE = f"Valeur Comptable d'Ancrage (Book Value) {CommonTerminals.UNIT_MILLIONS}"
    INP_BV_BASE = f"Valeur Comptable (Book Value) {CommonTerminals.UNIT_MILLIONS}"
    HELP_BV_BASE = "Capitaux propres part du groupe (Equity) au dernier bilan publié. Point de départ de la valorisation."

    INP_NI_TTM = f"Résultat Net Normatif {CommonTerminals.UNIT_MILLIONS}"
    HELP_NI_TTM = "Bénéfice net récurrent (Net Income) servant à déterminer le profit résiduel initial."

    INP_EPS_ANCHOR = f"EPS (Bénéfice par action) {CommonTerminals.UNIT_CURRENCY}"
    HELP_EPS_ANCHOR = "Bénéfice par action normalisé ou TTM. Sert d'ancrage pour la projection des profits résiduels."

    # Étape 2 : Persistance
    STEP_2_TITLE = "#### Étape 2 : Persistance des Profits Anormaux"
    STEP_2_DESC = "Estimation de la durée pendant laquelle l'entreprise génère un rendement supérieur à son coût du capital (Facteur Omega)."
    STEP_2_FORMULA = r"BV_t = BV_{t-1} + NetIncome_t - Dividendes_t"

    HELP_GROWTH = "Taux de croissance des fonds propres (via mise en réserve) avant l'atténuation par le facteur Omega."

    # Omega (persistence factor) explanation
    HELP_OMEGA = """Facteur de persistance des profits anormaux : ω (0 < ω < 1), issu du modèle Ohlson (1995) AR(1).
- ω = 1 : les profits anormaux persistent indéfiniment (scénario agressif, avantage compétitif durable)
- ω = 0 : les profits anormaux disparaissent immédiatement (scénario conservateur, forte concurrence)
- Valeurs typiques : 0.5-0.7 pour entreprises matures
Modélisation : RI_{t+1} = ω × RI_t (processus autorégressif AR(1), Ohlson 1995)"""

    # Formule TV RIM
    FORMULA_TV_RIM = r"TV_{RI} = \frac{RI_n \times \omega}{1 + k_e - \omega}"

    # Sections
    SEC_1_RIM_BASE = "1. Ancrage Comptable"
    SEC_2_PROJ_RIM = "2. Projection & Atténuation (Omega)"


class GrahamTexts(CommonTerminals):
    """
    Textes spécifiques pour la méthode de Valorisation Intrinsèque de Graham.
    Formule de Benjamin Graham révisée (1974).
    """

    TITLE = "Formule de Graham"
    DESCRIPTION = (
        "Implémentation révisée (1974). Valeur pivot basée sur l'EPS et la croissance, ajustée par le rendement "
        "obligataire AAA."
    )

    # Formule globale
    FORMULA_GLOBAL = r"V = \frac{EPS \times (8.5 + 2 \times g) \times 4.4}{Y_{AAA}}"

    # Étape 1 : Capacité Bénéficiaire
    STEP_1_TITLE = "#### Étape 1 : Capacité Bénéficiaire & Croissance"
    STEP_1_DESC = "Saisie du bénéfice par action normalisé et de la croissance prévisionnelle conservatrice."
    STEP_1_FORMULA = r"Multiplier = 8.5 + 2 \times (g \times 100)"

    INP_EPS = f"BPA (EPS) Normalisé {CommonTerminals.UNIT_CURRENCY}"
    INP_EPS_NORM = f"BPA (EPS) normalisé {CommonTerminals.UNIT_CURRENCY}"
    HELP_EPS = "Bénéfice par action lissé (moyenne 3-5 ans) ou TTM ajusté des éléments exceptionnels pour refléter la capacité bénéficiaire réelle."
    HELP_EPS_NORM = "Bénéfice par action moyen ou TTM ajusté des éléments exceptionnels."

    INP_GROWTH = f"Croissance Attendue (g) {CommonTerminals.UNIT_PERCENT}"
    INP_GROWTH_G = f"Croissance attendue g {CommonTerminals.UNIT_PERCENT}"
    HELP_GROWTH_LT = "Taux de croissance annuel moyen estimé pour les 7 à 10 prochaines années (doit rester conservateur)."

    # Étape 2 : Conditions de Marché
    STEP_2_TITLE = "#### Étape 2 : Conditions de Marché"
    STEP_2_DESC = "Paramètres du rendement obligataire corporate et de la fiscalité."

    INP_YIELD_AAA = f"Rendement Corporate AAA (Y) {CommonTerminals.UNIT_PERCENT}"
    HELP_YIELD_AAA = "Rendement actuel des obligations d'entreprises de haute qualité (référence vs 4.4% historique)."

    NOTE_GRAHAM = "Note : Le facteur 8.5 correspond au P/E d'une entreprise à croissance nulle. Le facteur 4.4 représente le rendement AAA historique de référence."


class FCFETexts(CommonTerminals):
    """
    Textes spécifiques pour le modèle FCFE (Free Cash Flow to Equity).
    Valorisation directe des fonds propres via les flux résiduels après service de la dette.
    """

    TITLE = "DCF : FCFE"
    DESCRIPTION = (
        "Calcul direct de la valeur des capitaux propres en actualisant les flux résiduels (post-dette) au coût des "
        "fonds propres (K_e)."
    )

    # Formule globale
    FORMULA_GLOBAL = r"EquityValue = \sum_{t=1}^{n} \frac{FCFE_t}{(1+K_e)^t} + \frac{TV_n}{(1+K_e)^n}"

    # Étape 1 : Ancrage Actionnaire
    STEP_1_TITLE = "#### Étape 1 : Ancrage Actionnaire"
    STEP_1_DESC = "Définition du flux FCFE disponible pour l'actionnaire et de la politique d'endettement."
    STEP_1_FORMULA = r"FCFE = \text{Résultat Net} + DA - \Delta BFR - CapEx + \Delta \text{Endettement Net}"

    INP_BASE = f"Flux FCFE d'ancrage {CommonTerminals.UNIT_MILLIONS}"
    HELP_FCFE_BASE = "Flux de trésorerie disponible pour les actionnaires après réinvestissement et service de la dette."

    INP_NET_BORROWING = f"Variation Nette de la Dette {CommonTerminals.UNIT_MILLIONS}"
    HELP_NET_BORROWING = "Montant net des nouvelles émissions de dette moins les remboursements de principal."

    # Étape 2 : Horizon de Projection
    STEP_2_TITLE = "#### Étape 2 : Horizon de Projection"
    STEP_2_DESC = "Définition de la trajectoire de croissance et de l'horizon temporel."

    # Formule TV
    FORMULA_TV = r"TV_n = \frac{FCFE_n(1+g_n)}{k_e - g_n}"


class DDMTexts(CommonTerminals):
    """
    Textes spécifiques pour le modèle DDM (Dividend Discount Model).
    Valorisation basée sur la distribution future de dividendes aux actionnaires.
    """

    TITLE = "Modèle DDM"
    DESCRIPTION = "Approche par le rendement pur. Il évalue l'action en actualisant uniquement les dividendes futurs attendus au coût des fonds propres (K_e)."

    # Formule globale
    FORMULA_GLOBAL = r"V_0 = \sum_{t=1}^{n} \frac{D_t}{(1+K_e)^t} + \frac{TV_n}{(1+K_e)^n}"

    # Étape 1 : Flux de Dividendes
    STEP_1_TITLE = "#### Étape 1 : Flux de Dividendes"
    STEP_1_DESC = "Ancrage du dividende par action (DPA) de référence pour le calcul de départ."
    STEP_1_FORMULA = r"D_0 = \text{Dividende par action (TTM)}"

    INP_BASE = f"Dividende par action {CommonTerminals.UNIT_CURRENCY}"
    INP_DIVIDEND_BASE = f"Dividende par action {CommonTerminals.UNIT_CURRENCY}"
    HELP_DIVIDEND_BASE = "Dividende brut annuel versé (TTM) ou annoncé pour l'exercice en cours."

    # Étape 2 : Dynamique de Croissance
    STEP_2_TITLE = "#### Étape 2 : Dynamique de Croissance"
    STEP_2_DESC = "Projection de la croissance du dividende (g) sur l'horizon explicite."

    NOTE_DDM_SGR = "Note : Le taux de croissance soutenable (SGR) peut être estimé par : ROE × (1 - Payout)."

    # Formule TV
    FORMULA_TV = r"TV_n = \frac{D_n(1+g_n)}{k_e - g_n}"
