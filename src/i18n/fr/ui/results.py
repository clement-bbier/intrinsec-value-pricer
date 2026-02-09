"""
src/i18n/fr/ui/results.py

RÉFÉRENTIEL DES TEXTES DE RENDU — VERSION INSTITUTIONNELLE FUSIONNÉE (V23)
==========================================================================
Rôle : Centralise tous les textes, labels et formats utilisés dans les vues de résultats.
Portée : KPIs, Graphiques, Benchmark, SOTP, Backtest, Inputs.
"""

class ResultsTexts:
    """Textes génériques de la page résultats."""
    TITLE = "Résultats de Valorisation"
    VALUATION_SUMMARY = "Synthèse Décisionnelle"
    NO_RATES_DATA = "Données de taux non disponibles"
    NO_FINANCIALS_PROVIDED = "Aucun état financier historique fourni"

class PillarLabels:
    """
    Labels officiels des onglets (Piliers).
    Séparation explicite entre la Synthèse (Output) et la Configuration (Input).
    """
    PILLAR_0_SUMMARY = "Synthèse & Dashboard"  # Output
    PILLAR_1_CONF = "Configuration & Inputs"   # Input
    PILLAR_2_TRACE = "Trace Mathématique"
    PILLAR_3_BENCHMARK = "Benchmark Sectoriel" # Ex-Audit
    PILLAR_4_RISK = "Ingénierie du Risque"
    PILLAR_5_MARKET = "Marché & SOTP"

class InputLabels:
    """
    Labels spécifiques au Pilier 1 (Configuration & Hypothèses).
    Détaille les paramètres entrés dans le modèle.
    """
    # Section Headers
    SECTION_STRUCTURE = "1. Structure & Marché"
    SECTION_WACC = "2. Paramètres de Taux (WACC)"
    SECTION_GROWTH = "3. Croissance & Terminal"
    SECTION_FINANCIALS = "4. Données Financières Brutes"

    # Metrics Structure
    TICKER = "Ticker"
    CURRENCY = "Devise"
    CURRENT_PRICE = "Prix Actuel"
    SHARES_OUT = "Actions en Circ."
    NET_DEBT = "Dette Nette"
    MINORITY_INTEREST = "Intérêts Minoritaires"
    IMPLIED_EV = "VE Implicite (Marché)"

    # Metrics Taux
    RISK_FREE_RATE = "Taux Sans Risque (Rf)"
    SOURCE_RF = "Source : Obligations 10 ans"
    BETA = "Beta"
    SOURCE_BETA = "Beta Levier"
    ERP = "Prime de Risque (ERP)"
    COST_OF_EQUITY = "Coût des Fonds Propres"
    COST_OF_DEBT_PRE_TAX = "Coût Dette (Pre-Tax)"
    TAX_RATE = "Taux d'IS"

    # Metrics WACC Detail
    WEIGHT_EQUITY = "Poids Fonds Propres"
    WEIGHT_DEBT = "Poids Dette"
    WACC_CALC = "WACC Calculé"
    WACC_DETAILS = "Détails du Calcul"

    # Metrics Growth
    TERMINAL_GROWTH = "Croissance Infinie (g)"
    PROJECTION_PERIOD = "Période Explicite"
    VALUATION_METHOD = "Méthode"

    # Données brutes
    VIEW_RAW_DATA = "Voir Compte de Résultat Historique"
    DATA_UNFORMATTED = "Formatage des données requis"

class KPITexts:
    """Labels et titres pour les indicateurs clés (Glass Box & Dashboard - Pilier 0)."""

    # --- Navigation & Onglets ---
    NOTE_ANALYSIS = "Note d'Analyse"
    TAB_INPUTS = "Données d'Entrée"
    TAB_CALC = "Preuve de calcul"
    TAB_BENCHMARK = "Benchmark & Fiabilité" # Remplacement de Audit
    TAB_MC = "Monte Carlo"
    TAB_SCENARIOS = "Analyse de Scénarios"

    # --- Concepts Mathématiques ---
    FORMULA_THEORY = "Théorie"
    APP_NUMERIC = "Application numérique"

    # --- Métriques de Valorisation (Output) ---
    INTRINSIC_PRICE_LABEL = "Prix Intrinsèque"
    ESTIMATED_PRICE_L = "Prix Estimé"
    EQUITY_VALUE_LABEL = "Valeur des Capitaux Propres (Equity)"
    UPSIDE_LABEL = "Potentiel (Upside)"
    MARGIN_SAFETY_LABEL = "Marge de Sécurité (MoS)"
    MARKET_CAP_LABEL = "Capitalisation Boursière"

    # --- Métriques Techniques (Input/Intermediate) ---
    WACC_LABEL = "Coût du Capital (WACC)"
    KE_LABEL = "Coût des Fonds Propres (Ke)"
    GROWTH_G_LABEL = "Croissance Perpétuelle (gn)"
    LABEL_GA = "Croissance perpétuelle (g)"
    SBC_ADJUSTMENT_LABEL = "Ajustement Dilution SBC"

    # --- Composants du Pont (Equity Bridge) ---
    LABEL_DEBT = "Dette Financière Totale"
    LABEL_CASH = "Trésorerie & Équivalents"
    LABEL_MINORITIES = "Intérêts Minoritaires"
    LABEL_PENSIONS = "Engagements de Retraite"
    LABEL_EQUITY = "Valeur des Capitaux Propres"

    # --- Formules de substitution (Templates LaTeX) ---
    SUB_DILUTION = "{iv:.2f} / (1 + {rate:.2%})^{t}"
    SUB_FCF_BASE = r"FCF_0 = {val:,.2f} ({src})"
    SUB_FCF_NORM = r"FCF_norm = {val:,.2f} ({src})"
    SUB_REV_BASE = r"Rev_0 = {val:,.0f}"
    SUB_MARGIN_CONV = r"Marge : {curr:.2%} -> {target:.2%} ({years} ans)"
    SUB_EPS_GRAHAM = r"EPS = {val:.2f} ({src})"
    SUB_GRAHAM_MULT = r"Facteur : 8.5 + 2 x {g:.2f}"
    SUB_BV_BASE = r"BV_0 = {val:,.2f} ({src})"
    SUB_SUM_RI = r"Cumul PV(RI) = {val:,.2f}"
    SUB_RIM_TV = r"Sortie : {sub_tv} x {factor:.4f}"
    SUB_RIM_FINAL = r"P = {bv:,.2f} + {ri:,.2f} + {tv:,.2f}"
    SUB_P50_VAL = r"P50 = {val:,.2f} {curr}"
    SUB_FCFE_CALC = r"FCFE = FCFF - Int(1-t) + ΔDette = {val:,.2f}"
    SUB_FCFE_WALK = r"FCFE Walk : NI({ni:,.0f}) + Adj({adj:,.0f}) + ΔDebt({nb:,.0f}) = {total:,.2f}"
    SUB_DDM_BASE = r"D_0 = {val:,.2f} / action"
    SUB_KE_LABEL = r"k_e = {rf:.2%} + {beta:.2f}({mrp:.2%}) = {val:.2%}"
    SUB_EQUITY_NPV = r"Equity NPV = {val:,.2f}"
    SUB_PAYOUT = r"Payout = Div({div:,.2f}) / EPS({eps:,.2f}) = {total:.1%}"
    SUB_TV_PE = r"TV_n = NI_n({ni:,.0f}) x P/E({pe:.1f}x) = {total:,.2f}"
    SUB_HAMADA = "Bêta réendetté (Hamada) selon structure cible."
    SUB_SBC_DILUTION = r"Actions_{{t}} = Actions_{{0}} \times (1 + {rate:.1%})^{years}"
    SUB_CAPM_MATH = "{rf:.4f} + {beta:.2f} \times {mrp:.4f}"
    SUB_RIM_TV_MATH = "({ri:,.2f} \times {omega:.2f}) / (1 + {ke:.4f} - {omega:.2f})"
    SUB_PE_MULT = "({ni} × {mult:.1f}) / {shares}"
    SUB_EBITDA_MULT = "({ebitda} × {mult:.1f}) / {shares}"

    # --- Tooltips ---
    HELP_IV = "Valeur intrinsèque : prix théorique par action après actualisation des flux futurs."
    HELP_MOS = "Marge de sécurité : écart en pourcentage entre la valeur intrinsèque et le prix actuel."
    HELP_KE = "Coût de l'Equity : rendement minimal exigé par les actionnaires (CAPM)."
    HELP_WACC = "Coût moyen pondéré du capital (Dette + Equity)."
    HELP_VAR = "Value at Risk (VaR 95%) : Seuil de valeur pessimiste."
    HELP_OMEGA = "Coefficient de persistance des profits anormaux (0 = érosion immédiate, 1 = perpétuité)."
    HELP_EQUITY_VALUE = "Valeur totale revenant aux actionnaires après déduction de la dette nette."

    # --- Labels Synthèse & Football Field ---
    EXEC_TITLE = "DOSSIER DE VALORISATION : {name} ({ticker})"
    EXEC_CONFIDENCE = "Indice de Confiance"

    LABEL_PRICE = "Cours de Marché"
    LABEL_IV = "Valeur Intrinsèque"
    LABEL_MOS = "Marge de Sécurité (MoS)"
    LABEL_EXPECTED_VALUE = "Valeur Pondérée (Espérée)"
    LABEL_SIMULATIONS = "Simulations"
    LABEL_SCENARIO_RANGE = "Fourchette Bear - Bull"

    FOOTBALL_FIELD_TITLE = "Synthèse de Triangulation (Football Field)"
    RELATIVE_VAL_DESC = "Positionnement du modèle intrinsèque face aux métriques de marché."
    LABEL_MULTIPLES_UNAVAILABLE = "Données insuffisantes pour la triangulation relative."

    LABEL_FOOTBALL_FIELD_IV = "Modèle Intrinsèque"
    LABEL_FOOTBALL_FIELD_REV = "EV/Revenue"
    LABEL_FOOTBALL_FIELD_EBITDA = "EV/EBITDA"
    LABEL_FOOTBALL_FIELD_PE = "P/E Ratio"
    LABEL_FOOTBALL_FIELD_PRICE = "Prix de Marché"


class BenchmarkTexts:
    """
        Textes Pillar 3 — Benchmark & Fiabilité.
        Vocabulaire de comparaison sectorielle et de scoring.
        """
    # Titres & Sections
    TITLE_MACRO = "Contexte Macroéconomique"
    SUBTITLE_VALUATION = "1. Positionnement Valorisation (Multiples)"
    DESC_VALUATION = "Comparaison des multiples de valorisation actuels vs moyenne sectorielle."
    SUBTITLE_PERFORMANCE = "2. Performance Opérationnelle"
    DESC_PERFORMANCE = "Analyse de la qualité financière relative."

    # Cartes d'Identité
    LBL_SECTOR_REF = "SECTEUR DE RÉFÉRENCE"
    LBL_BENCHMARK_ID = "Benchmark ETF/Indice"
    LBL_RF = "TAUX SANS RISQUE (Rf)"
    LBL_ERP = "PRIME DE RISQUE (ERP)"

    # Statuts de comparaison (Badges)
    STATUS_PREMIUM = "PREMIUM"  # Plus cher que le secteur
    STATUS_DISCOUNT = "DISCOUNT"  # Moins cher que le secteur
    STATUS_LEADER = "LEADER"  # Meilleure perf que le secteur
    STATUS_LAGGING = "RETARD"  # Moins bonne perf que le secteur

    # Labels Graphiques
    CHART_TITLE_VALUATION = "Visualisation des écarts de valorisation"
    LBL_ENTITY_COMPANY = "Entreprise"
    LBL_ENTITY_SECTOR = "Moyenne Secteur"

    # Messages génériques
    NO_REPORT = "Données sectorielles indisponibles pour générer le rapport de benchmark."

    COVERAGE = "Couverture des tests"
    H_INDICATOR = "Indicateurs vérifiés"
    GLOBAL_SCORE = "Score de fiabilité global basé sur {score}% de conformité aux standards du secteur."
    CRITICAL_VIOLATION_MSG = r"{count} écarts critiques détectés par rapport aux normes."
    NOTES_EXPANDER = "Détail des analyses de cohérence" # Anciennement Procès-verbal...

    H_RULE = "Standard analysé"
    H_EVIDENCE = "Valeur Modèle"
    H_VERDICT = "Statut"

    DEFAULT_FORMULA = r"\text{Standard de Marché}"
    INTERNAL_CALC = "Calcul interne"

    # Statuts
    STATUS_OK = "Aligné"
    STATUS_ALERT = "Écart Significatif"

    # Niveaux de fiabilité
    RELIABILITY_HIGH = "Fiabilité : Élevée"
    RELIABILITY_MODERATE = "Fiabilité : Modérée"
    RELIABILITY_LOW = "Fiabilité : Faible"
    RATING_SCORE = "Score Qualité"

    # Messages Spécifiques
    LBL_SOTP_REVENUE_CHECK = "Cohérence Revenus SOTP"
    LBL_SOTP_DISCOUNT_CHECK = "Prudence Décote Holding"
    CHECK_TABLE = "Tableau de conformité sectorielle"

    # Codes de règles (pour mapping - inchangés pour compatibilité backend)
    KEY_BETA_VALIDITY = "BETA_VALIDITY"
    KEY_DATA_FRESHNESS = "DATA_FRESHNESS"
    KEY_ICR_WARNING = "DCF_ICR_WARNING"
    KEY_WACC_G_SPREAD = "DCF_WACC_G_SPREAD"
    KEY_REINVESTMENT_DEFICIT = "DCF_REINVESTMENT_DEFICIT"
    KEY_PAYOUT_UNSUSTAINABLE = "DDM_PAYOUT_UNSUSTAINABLE"
    KEY_ROE_KE_NEGATIVE = "RIM_SPREAD_ROE_KE_NEGATIVE"
    KEY_OMEGA_BOUNDS = "RIM_OMEGA_OUT_OF_BOUNDS"
    KEY_GRAHAM_MULTIPLIER = "GRAHAM_MULTIPLIER_EXCEEDED"
    KEY_COHORT_SMALL = "MULTIPLES_COHORT_SMALL"
    KEY_HIGH_DISPERSION = "MULTIPLES_HIGH_DISPERSION"

    PIOTROSKI_TITLE = "Santé Financière (F-Score Piotroski)"
    PIOTROSKI_DESC = "Analyse de la solidité financière selon 9 critères comptables (Rentabilité, Levier, Efficacité)."
    PIOTROSKI_LBL_SCORE = "Score F"
    PIOTROSKI_LBL_STATUS = "Statut"
    PIOTROSKI_LBL_HEALTH = "Santé Fondamentale : {score} sur 9 points"

    # Status
    PIOTROSKI_STATUS_STRONG = "Solide"
    PIOTROSKI_STATUS_STABLE = "Moyen"
    PIOTROSKI_STATUS_WEAK = "Fragile"

    # Interpretations (Sans smileys)
    PIOTROSKI_MSG_STRONG = "Fondamentaux de haute qualité. Profil défensif."
    PIOTROSKI_MSG_STABLE = "Fondamentaux moyens. Profil standard."
    PIOTROSKI_MSG_WEAK = "Fondamentaux de faible qualité. Profil risqué."


class QuantTexts:
    """Textes Pillar 4 — Ingénierie du Risque (Monte Carlo & Scenarios)."""

    # --- Analyse de Sensibilité (Heatmap) ---
    SENS_TITLE = "Matrice de Sensibilité"
    LBL_SENS_SCORE = "Score de Stabilité"
    HELP_SENS_SCORE = (
        "Indicateur de robustesse (0-100). Mesure l'impact des variations "
        "d'inputs sur la valorisation. < 15 : Stable | > 30 : Critique."
    )

    # Statuts du score
    SENS_STABLE = "Modèle Robuste"
    SENS_VOLATILE = "Volatilité Modérée"
    SENS_CRITICAL = "Instabilité Critique"

    # --- Monte Carlo ---
    MC_TITLE = "Simulation de Monte Carlo"
    MC_PROB_ANALYSIS = "Analyse des Probabilités de Marché"
    MC_DOWNSIDE = "Risque de Surévaluation"
    MC_PROB_UNDERVALUATION = "Probabilité de Sous-évaluation"
    MC_PROB_OVERVALUATION = "Probabilité de Sur-évaluation"
    MC_MEDIAN = "Valeur Médiane"
    MC_VAR = "VaR (95%)"
    MC_VOLATILITY = "Écart-type (σ)"
    MC_TAIL_RISK = "Coeff. de Variation"
    MC_ITERATIONS_L = "Nombre de simulations"
    MC_FAILED = "Convergence impossible : volatilités trop élevées ou données insuffisantes."
    MC_AUDIT_STOCH = "Audit des Paramètres Stochastiques"

    # Phrases dynamiques
    MC_CONFIG_SUB = r"Moteur stochastique : {sims} itérations | σ(β): {sig_b:.1%} | σ(g): {sig_g:.1%} | ρ: {rho:.2f}"
    MC_FILTER_SUB = r"Intervalle de confiance 80% ({valid}/{total} valides)"
    MC_SENS_SUB = r"P50 Neutre (rho=0) : {p50_n:,.2f} | P50 de Base (rho=-0.3) : {p50_b:,.2f}"
    CONFIDENCE_INTERVAL = "Intervalle de confiance"

    # --- Scenarios ---
    SCENARIO_TITLE = "Analyse des Scénarios"
    METRIC_WEIGHTED_VALUE = "Valeur Pondérée"
    METRIC_WEIGHTED_UPSIDE = "Potentiel Pondéré"
    COL_SCENARIO = "SCÉNARIO"
    COL_PROBABILITY = "PROBABILITÉ"
    COL_GROWTH = "CROISSANCE (g)"
    COL_MARGIN_FCF = "MARGE FCF"
    COL_VALUE_PER_SHARE = "VALEUR / ACTION"
    COL_UPSIDE = "POTENTIEL"

    # Axes Heatmap (Référence textuelle)
    AXIS_WACC = "WACC / Taux d'Actualisation"
    AXIS_GROWTH = "Taux de Croissance Terminale (g)"

    # Backtest Metrics (Ajout pour cohérence si manquant)
    LABEL_HIT_RATE = "Taux de Succès"
    LABEL_MAE = "Erreur Absolue Moyenne"
    BACKTEST_INTERPRETATION = "Comparaison de la valeur intrinsèque historique vs prix réel."
    MSG_SENS_NO_DATA = "Données de sensibilité insuffisantes pour l'affichage."


class BacktestTexts:
    """Textes pour le module de Backtesting Historique (Pillar 4 extension)."""

    # Titres & Descriptions
    TITLE = "Validation Historique (Backtest)"
    HELP_BACKTEST = (
        "Simulation rétrospective du modèle sur les exercices passés pour vérifier sa capacité prédictive. "
        "Compare la valeur intrinsèque théorique calculée (IV) face au prix réel du marché à cette date."
    )

    # Messages
    NO_BACKTEST_FOUND = "Données historiques insuffisantes pour générer un audit de performance."
    INTERPRETATION = "Une convergence historique élevée renforce la fiabilité des projections futures."

    # Labels Graphiques (Longs - pour Altair/Plotly)
    LABEL_HIST_IV = "Valeur Intrinsèque Calculée"
    LABEL_REAL_PRICE = "Prix Réel Historique"

    # Labels Tableaux (Courts - pour Column Config)
    LBL_HIST_IV = "Valeur Calc."
    LBL_REAL_PRICE = "Prix Réel"
    LBL_PERIODS = "Périodes Testées"
    LBL_DATE = "Date Val."
    LBL_ERROR_GAP = "Écart (%)"

    # KPIs & Métriques
    METRIC_ACCURACY = "Précision du Modèle"
    LABEL_HIT_RATE = "Taux de Succès (Hit Rate)"
    LABEL_MAE = "Erreur Moyenne (MAE)"

    # Grades & Résultats
    GRADE_A = "Excellente"
    GRADE_B = "Moyenne"

    # Section
    SEC_RESULTS = "Détail des Écarts Historiques"

class MarketTexts:
    """Textes Pillar 5 — Analyse de Marché (Peers & Multiples)."""

    # --- Titres & Sections ---
    MARKET_TITLE = "Triangulation par les Comparables"
    TITLE_SEGMENTATION = "Analyse Somme des Parties (SOTP)"  # Utilisé comme LABEL dans SOTPBreakdownTab

    # --- SOTP (Somme des Parties) ---
    METRIC_GROSS_VALUE = "Valeur Brute Cumulée (Gross EV)"
    COL_SEGMENT = "Segment / Business Unit"
    COL_VALUE = "Valeur d'Entreprise (EV)"
    COL_CONTRIBUTION = "Contribution (%)"
    CAPTION_SEGMENTATION = "Décomposition de la valeur d'entreprise par segments opérationnels (Sum-of-the-Parts)."

    # --- Peers (Comparables) ---
    # Colonnes
    COL_PEER = "Pair / Comparable"
    COL_MULTIPLE = "Multiple"
    COL_IMPLIED_VALUE = "VALEUR IMPLICITE"

    # Labels de lignes/entités
    LBL_RATIO = "Ratio"
    LBL_TARGET = "Cible (Target)"
    LBL_PEER_ENTITY = "Pair Sectoriel"
    LBL_MEDIAN = "Médiane"
    LBL_SECTOR_MEDIAN = "Médiane Sectorielle"

    # Métriques
    IMPLIED_VAL_PREFIX = "Valeur Implicite"

    # Sources & Messages Système
    SOURCE_DEFAULT = "Données de Marché"
    NO_MARKET_DATA = "Aucune donnée de marché (Comparables ou Segments) disponible pour cette valorisation."

    # --- Phrases Dynamiques (Format Strings) ---
    # Note: Le préfixe 'r' est utilisé pour sécuriser les chaînes de formatage

    # Usage : "Basé sur une médiane de 12.5x"
    HELP_IMPLIED_METHOD = r"Calculé sur la base d'une médiane sectorielle de {multiple}"

    # Légende nombre de pairs + source
    # Usage : "15 Pairs | Source : Bloomberg"
    CAPTION_PEERS_COUNT = r"{count} {label} | Source : {source}"

    # Résumé footer tableau
    CAPTION_MEDIAN_SUMMARY = r"**{label}** : EV/EBITDA = {ebitda} | P/E = {pe}"

class SOTPTexts:
    """Textes spécifiques à la méthode Somme des Parties (SOTP) - Pillar 5."""
    HELP_SOTP = (
        "Cette méthodologie valorise chaque division indépendamment pour capturer "
        "la réalité économique des conglomérats, souvent masquée par une approche consolidée."
    )
    NO_SOTP_FOUND = (
        "Aucune segmentation détectée. Veuillez configurer les segments (Business Units) "
        "dans les paramètres pour activer la valorisation SOTP."
    )
    TITLE = "Analyse Somme des Parties (SOTP)"

    # Waterfall Chart
    LBL_ENTERPRISE_VALUE = "Valeur d'Entreprise Nette"
    LABEL_HOLDING_DISCOUNT = "Décote de Holding"

    # Tableaux
    SEGMENT_VALUATION = "Valorisation par Segment"
    IMPLIED_EV = "Valeur d'Entreprise Implicite"
    CONGLOMERATE_DISCOUNT = "Décote de Conglomérat"
    SUM_OF_PARTS = "Somme des Parties"
    COL_SEGMENT = "UNITÉ COMMERCIALE"
    COL_VALUE = "VALEUR"
    COL_CONTRIBUTION = "CONTRIBUTION (%)"
    METRIC_GROSS_VALUE = "Valeur Brute (Somme)"
    METRIC_HOLDING_DISCOUNT = "Décote de Holding"
    METRIC_NET_VALUE = "Valeur Nette"

    # Glass Box UI
    FORMULA_BRIDGE = "Equity = Σ(Segments) - Dette Nette - Décote"
    INTERP_CONSOLIDATION = "Agrégation des valorisations individuelles par Business Unit."
    FORMULA_CONSOLIDATION = r"EV_{SOTP} = (\sum V_{segment}) \times (1 - \text{Discount})"
    STEP_LABEL_CONSOLIDATION = "Consolidation des Parties"
    LBL_DISCOUNT = "Décote Appliquée"
    LBL_RAW_EV_SUM = "Somme Brute des Segments"


class ChartTexts:
    """Libellés pour les graphiques (Plotly/Altair)."""

    # Axes Standards
    AXIS_WACC = "WACC / Coût du Capital (%)"
    AXIS_GROWTH = "Croissance Terminale - g (%)"

    # Titres & Légendes
    PRICE_HISTORY_TITLE = r"Historique : {ticker}"
    SIM_AXIS_X = r"Valeur Intrinsèque ({currency})"
    SIM_AXIS_Y = "Fréquence (Densité)"
    SENS_TITLE = "Modèle Intrinsèque (DCF/RIM)"
    CORREL_CAPTION = "Matrice de Corrélation des Inputs (WACC vs Growth)"
    TOOLTIP_VALUATION = "Valorisation"

class RegistryTexts:
    """Textes pour les métadonnées du Glass Box (Registry)."""
    # DCF
    DCF_WACC_L = "Coût du Capital (WACC)"
    DCF_WACC_D = "Taux d'actualisation pondéré par la structure du capital cible."
    DCF_KE_L = "Coût des Fonds Propres (Ke)"
    DCF_KE_D = "Rendement exigé par les actionnaires (Modèle CAPM)."
    DCF_FCF_BASE_L = "Flux de Trésorerie de Base"
    DCF_FCF_BASE_D = "Point de départ des projections (Année 0 ou N-1)."
    DCF_PROJ_L = "Somme des Flux Actualisés"
    DCF_PROJ_D = "Valeur présente des flux de trésorerie sur la période explicite."
    DCF_TV_GORDON_L = "Valeur Terminale (Gordon)"
    DCF_TV_GORDON_D = "Valeur à l'infini selon le modèle de croissance perpétuelle."
    DCF_TV_MULT_L = "Valeur Terminale (Multiple)"
    DCF_TV_MULT_D = "Valeur de sortie basée sur un multiple d'EBITDA/Revenus."
    DCF_EV_L = "Valeur d'Entreprise (EV)"
    DCF_EV_D = "Somme des flux actualisés et de la valeur terminale."
    DCF_BRIDGE_L = "Pont vers l'Equity"
    DCF_BRIDGE_D = "Ajustement de la Dette Nette et autres passifs."
    DCF_IV_L = "Valeur par Action"
    DCF_IV_D = "Valeur finale des capitaux propres divisée par le nombre d'actions."

    # FCFE / DDM
    FCFE_BASE_L = "FCFE de Base"
    FCFE_BASE_D = "Flux de trésorerie disponible pour les actionnaires (après dette)."
    DDM_BASE_L = "Dividende de Base"
    DDM_BASE_D = "Dernier dividende versé ou projeté."
    EQUITY_DIRECT_D = "Calcul direct de la valeur des capitaux propres (pas de pont dette)."

    # RIM / Graham
    RIM_BV_L = "Valeur Comptable (Book Value)"
    RIM_BV_D = "Capitaux propres comptables initiaux."
    RIM_KE_L = "Coût des Fonds Propres"
    RIM_KE_D = "Taux d'actualisation appliqué aux revenus résiduels."
    RIM_PAYOUT_L = "Taux de Distribution"
    RIM_PAYOUT_D = "Part du résultat net reversée en dividendes."
    RIM_RI_L = "Revenus Résiduels Cumulés"
    RIM_RI_D = "Somme actualisée des profits excédentaires futurs."
    RIM_TV_L = "Valeur Terminale (Ohlson)"
    RIM_TV_D = "Valeur des profits anormaux perpétuels avec facteur de persistance."
    RIM_IV_L = "Valeur Intrinsèque RIM"
    RIM_IV_D = "Somme : BV + RI + TV."

    GRAHAM_EPS_L = "Bénéfice par Action (EPS)"
    GRAHAM_EPS_D = "Moyenne lissée ou dernier EPS connu."
    GRAHAM_MULT_L = "Multiplicateur de Graham"
    GRAHAM_MULT_D = "Facteur basé sur la croissance (8.5 + 2g)."
    GRAHAM_IV_L = "Valeur Intrinsèque Graham"
    GRAHAM_IV_D = "Formule classique de Benjamin Graham."

    # Ajustements
    HAMADA_L = "Ajustement Hamada"
    HAMADA_D = "Désendettement et réendettement du Bêta."
    SBC_L = "Dilution SBC"
    SBC_D = "Impact des rémunérations en actions (Stock-Based Compensation)."


class StrategyFormulas:
    """Formules LaTeX pour le Glass Box."""
    WACC = r"WACC = K_e \times \frac{E}{V} + K_d(1-t) \times \frac{D}{V}"
    CAPM = r"K_e = R_f + \beta \times ERP"
    FCF_BASE = r"FCF = EBIT(1-t) + D\&A - \Delta WCR - Capex"
    FCFE_RECONSTRUCTION = r"FCFE = FCF - Int(1-t) + \Delta Dette"
    DIVIDEND_BASE = r"Div_0"

    FCF_PROJECTION = r"\sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t}"
    GORDON = r"TV = \frac{FCF_n \times (1+g)}{WACC - g}"
    TERMINAL_EXIT_MULTIPLE = r"TV = Metric_n \times Multiple"

    NPV = r"EV = \sum PV(FCF) + PV(TV)"
    EQUITY_BRIDGE = r"Equity = EV - Dette_{net} - Minoritaires + Cash"
    FCFE_EQUITY_VALUE = r"Equity = \sum PV(FCFE) + PV(TV_{FCFE})"
    VALUE_PER_SHARE = r"Prix = \frac{Equity}{Actions}"

    BV_BASE = r"B_0"
    PAYOUT_RATIO = r"Payout = \frac{Div}{NI}"
    RI_SUM = r"\sum \frac{(ROE_t - K_e) \times B_{t-1}}{(1+K_e)^t}"
    RIM_PERSISTENCE = r"TV = \frac{RI_n \times \omega}{1 + K_e - \omega}"
    RIM_FINAL = r"V_0 = B_0 + \sum PV(RI) + PV(TV)"
    RIM_RESIDUAL_INCOME = r"RI_t = NI_t - (K_e \times B_{t-1})"

    EPS_BASE = r"EPS_{norm}"
    GRAHAM_MULTIPLIER = r"M = 8.5 + 2g"
    GRAHAM_VALUE = r"V = EPS \times (8.5 + 2g) \times \frac{4.4}{Y_{AAA}}"

    HAMADA = r"\beta_L = \beta_U \times [1 + (1-t)\frac{D}{E}]"
    SBC_DILUTION = r"Actions_{adj} = Actions \times (1+dilution)^t"