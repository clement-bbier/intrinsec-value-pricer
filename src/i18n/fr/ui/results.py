"""
src/i18n/fr/ui/results.py

RÉFÉRENTIEL DES TEXTES DE RENDU — VERSION INSTITUTIONNELLE FUSIONNÉE (V22)
==========================================================================
Rôle : Centralise tous les textes, labels et formats utilisés dans les vues de résultats.
Portée : KPIs, Graphiques, Rapports d'Audit, SOTP, Backtest.
"""

class PillarLabels:
    """Labels officiels des 5 piliers de recherche."""
    PILLAR_1_CONF = "Configuration"
    PILLAR_2_TRACE = "Trace mathématique"
    PILLAR_3_AUDIT = "Rapport d'audit"
    PILLAR_4_RISK = "Ingénierie du risque"
    PILLAR_5_MARKET = "Analyse de marché & SOTP"
    PILLAR_0_SUMMARY = "Synthèse décisionnelle"


class KPITexts:
    """Labels et titres pour les indicateurs clés (Glass Box & Dashboard)."""

    # --- Navigation & Onglets ---
    TAB_INPUTS = "Données d'Entrée"
    TAB_CALC = "Preuve de calcul"
    TAB_AUDIT = "Audit de Fiabilité"
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

    # --- Formules de substitution (Templates) ---
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
    RELATIVE_VAL_DESC = "Positionnement du modèle intrinsèque face aux multiples du secteur."
    LABEL_MULTIPLES_UNAVAILABLE = "Données insuffisantes pour la triangulation relative."

    LABEL_FOOTBALL_FIELD_IV = "Modèle Intrinsèque"
    LABEL_FOOTBALL_FIELD_REV = "EV/Revenue"
    LABEL_FOOTBALL_FIELD_EBITDA = "EV/EBITDA"
    LABEL_FOOTBALL_FIELD_PE = "P/E Ratio"
    LABEL_FOOTBALL_FIELD_PRICE = "Prix de Marché"


class AuditTexts:
    """Textes Pillar 3 — Audit & Fiabilité."""
    COVERAGE = "Couverture d'audit"
    H_INDICATOR = "Tests exécutés"
    GLOBAL_SCORE = "Score de fiabilité global basé sur {score}% de conformité aux invariants."
    CRITICAL_VIOLATION_MSG = r"{count} invariants critiques violés"
    AUDIT_NOTES_EXPANDER = "Procès-verbal détaillé des tests"
    H_RULE = "Règle métier"
    H_EVIDENCE = "Preuve (Calcul)"
    H_VERDICT = "Résultat"
    DEFAULT_FORMULA = r"\text{Règle Standard}"
    INTERNAL_CALC = "Calcul interne"

    # Statuts
    STATUS_OK = "Conforme"
    STATUS_ALERT = "Alerte"

    # Niveaux de fiabilité
    RELIABILITY_HIGH = "Fiabilité élevée"
    RELIABILITY_MODERATE = "Fiabilité modérée"
    RELIABILITY_LOW = "Fiabilité faible"
    NO_REPORT = "Audit indisponible pour ce modèle."
    RATING_SCORE = "Notation Qualité"

    # Messages Spécifiques
    LBL_SOTP_REVENUE_CHECK = "Cohérence Revenus SOTP"
    LBL_SOTP_DISCOUNT_CHECK = "Prudence Décote Holding"
    CHECK_TABLE = "Vérification des règles normatives"

    # Codes de règles (pour mapping)
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


class QuantTexts:
    """Textes Pillar 4 — Ingénierie du Risque (Monte Carlo & Scenarios)."""
    # Monte Carlo
    MC_TITLE = "Simulation de Monte Carlo"
    MC_PROB_ANALYSIS = "Analyse des Probabilités de Marché"
    MC_DOWNSIDE = "Risque de Surévaluation"
    MC_PROB_UNDERVALUATION = "Probabilité de Sous-évaluation"
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
    MC_SENS_SUB = "P50 Neutre (rho=0) : {p50_n:,.2f} | P50 de Base (rho=-0.3) : {p50_b:,.2f}"
    CONFIDENCE_INTERVAL = "Intervalle de confiance"

    # Scenarios
    SCENARIO_TITLE = "Analyse des scénarios"
    METRIC_WEIGHTED_VALUE = "Valeur Pondérée"
    METRIC_WEIGHTED_UPSIDE = "Potentiel Pondéré"
    COL_SCENARIO = "SCÉNARIO"
    COL_PROBABILITY = "PROBABILITÉ"
    COL_GROWTH = "CROISSANCE"
    COL_MARGIN_FCF = "MARGE"
    COL_VALUE_PER_SHARE = "VALEUR"
    COL_UPSIDE = "UPSIDE"

    # Axes Heatmap (Sensibilité)
    AXIS_WACC = "WACC / Taux d'Actualisation"
    AXIS_GROWTH = "Taux de Croissance Terminale (g)"


class BacktestTexts:
    """Textes pour le module de Backtesting Historique."""
    TITLE = "Validation Historique (Backtest)"
    LABEL_HIST_IV = "Valeur Intrinsèque Calculée"
    LABEL_REAL_PRICE = "Prix Réel Historique"

    NO_BACKTEST_FOUND = "Données historiques insuffisantes pour générer un audit de performance."
    LABEL_HIT_RATE = "Taux de succès (Hit Rate)"
    LABEL_MAE = "Erreur Moyenne (MAE)"
    INTERPRETATION = "Une convergence historique élevée renforce la fiabilité des projections futures."


class MarketTexts:
    """Textes Pillar 5 — Analyse de Marché (Peers & Multiples)."""
    MARKET_TITLE = "Positionnement sectoriel & Multiples"

    # Tableaux Peers
    COL_PEER = "Comparable"
    COL_MULTIPLE = "Multiple"
    COL_IMPLIED_VALUE = "VALEUR IMPLICITE"

    LBL_RATIO = "Ratio"
    LBL_MEDIAN = "Médiane Pairs"
    LBL_TARGET = "Cible (Actuel)"
    IMPLIED_VAL_PREFIX = "Valeur induite via"


class SOTPTexts:
    """Textes spécifiques à la méthode Somme des Parties (SOTP)."""
    TITLE = "Analyse Somme des Parties (SOTP)"

    # Waterfall Chart
    LBL_ENTERPRISE_VALUE = "Valeur d'Entreprise (EV)"
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

    # Glass Box
    FORMULA_BRIDGE = "Equity = Σ(Segments) - Dette Nette - Décote"
    INTERP_CONSOLIDATION = "Agrégation des valorisations individuelles par Business Unit."
    FORMULA_CONSOLIDATION = r"EV_{SOTP} = (\sum V_{segment}) \times (1 - \text{Discount})"
    STEP_LABEL_CONSOLIDATION = "Consolidation des Parties"
    LBL_DISCOUNT = "Décote de Holding"
    LBL_RAW_EV_SUM = "Somme Brute des Segments"


class ChartTexts:
    """Libellés pour les graphiques (Plotly/Altair)."""
    PRICE_HISTORY_TITLE = "Historique : {ticker}"
    SIM_AXIS_X = r"Valeur Intrinsèque ({currency})"
    SIM_AXIS_Y = "Fréquence"
    SENS_TITLE = "Modèle Intrinsèque (DCF/RIM)"
    CORREL_CAPTION = "Matrice de Corrélation des Inputs"

class ResultsTexts:
    """Textes génériques de la page résultats."""
    TITLE = "Résultats de Valorisation"
    VALUATION_SUMMARY = "Synthèse"