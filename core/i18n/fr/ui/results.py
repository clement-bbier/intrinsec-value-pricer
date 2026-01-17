"""
core/i18n/fr/ui/results.py
Textes des onglets de resultats.
"""


class KPITexts:
    """Labels et titres pour l'affichage des resultats (Glass Box)."""

    # === NOUVELLES CONSTANTES POUR RESULT TABS ===
    # Inputs Summary
    PARAM_RF = "Taux sans risque (R_f)"
    PARAM_MRP = "Prime de risque marché"
    PARAM_GROWTH_PHASE1 = "Croissance Phase 1"
    PARAM_GROWTH_PERP = "Croissance perpétuelle (g)"
    PARAM_TV_MULT = "Multiple de sortie"
    PARAM_LABEL = "Paramètre"
    PARAM_VALUE = "Valeur"

    # Peer Multiples
    COL_TICKER = "Ticker"
    COL_NAME = "Name"
    COL_MCAP = "Mcap"
    COL_PE_RATIO = "P/E"
    COL_EV_EBITDA = "EV/EBITDA"
    COL_EV_REVENUE = "EV/Rev"
    VAL_VIA_EV_EBITDA = "Via EV/EBITDA"
    VAL_VIA_PE = "Via P/E"
    VAL_IMPLIED_VALUES = "Valeurs Implicites par Action"

    # Monte Carlo
    METRIC_CV = "Coef. Variation"
    METRIC_P5 = "P5 (Bear)"
    METRIC_P50 = "P50 (Base)"
    METRIC_P95 = "P95 (Bull)"
    TITLE_CI = "Intervalles de Confiance"
    TITLE_PROBA_ANALYSIS = "Analyse de Probabilité"
    PROBA_ABOVE_CURRENT = "P(Valeur > Prix actuel)"
    PROBA_UPSIDE_20 = "P(Upside > 20%)"
    CHART_ANNOTATION_CURRENT = "Prix actuel"
    CHART_ANNOTATION_DCF = "Valeur DCF"
    CHART_TITLE_DISTRIBUTION = "Distribution des Valeurs Intrinsèques"

    # Historical Backtest
    COL_DATE = "Date"
    COL_PREDICTED = "Valeur Prédite"
    COL_ACTUAL = "Valeur Réelle"
    COL_ERROR = "Erreur"
    
    # Onglets
    TAB_INPUTS = "Donnees d'Entree"
    TAB_CALC = "Preuve de Calcul"
    TAB_AUDIT = "Audit de Fiabilite"
    TAB_MC = "Analyse de Risque (MC)"
    TAB_SCENARIOS = "Analyse de Scenarios"

    # Titres de sections (Inputs)
    SECTION_INPUTS_HEADER = "#### Recapitulatif des Donnees Utilisees"
    SECTION_INPUTS_CAPTION = "Ce tableau liste l'ensemble des inputs injectes dans le moteur de calcul."
    SEC_A_IDENTITY = "A. Identification de l'Entreprise"
    SEC_B_FINANCIALS = "B. Donnees Financieres (Source: Yahoo Finance)"
    SEC_C_MODEL = "C. Parametres du Modele de Valorisation"
    SEC_D_MC = "D. Configuration Monte Carlo"
    SEC_E_RELATIVE = "E. Valorisation Relative (Multiples de Marche)"

    # Labels Identification
    LABEL_TICKER = "Ticker"
    LABEL_NAME = "Nom"
    LABEL_SECTOR = "Secteur"
    LABEL_COUNTRY = "Pays"
    LABEL_INDUSTRY = "Industrie"
    LABEL_CURRENCY = "Devise"
    LABEL_BETA = "Beta"
    LABEL_SHARES = "Actions en circulation"

    # Labels Financiers
    SUB_MARKET = "Marche & Capitalisation"
    LABEL_PRICE = "Cours Actuel"
    LABEL_MCAP = "Capitalisation Boursiere"
    LABEL_BVPS = "Book Value / Action"

    SUB_CAPITAL = "Structure du Capital"
    LABEL_DEBT = "Dette Totale"
    LABEL_CASH = "Tresorerie"
    LABEL_NET_DEBT = "Dette Nette"
    LABEL_INTEREST = "Charges d'Interets"
    LABEL_MINORITIES = "Interets Minoritaires"
    LABEL_PENSIONS = "Provisions Pensions"

    SUB_PERF = "Performance Operationnelle (TTM)"
    LABEL_REV = "Chiffre d'Affaires"
    LABEL_EBIT = "EBIT"
    LABEL_NI = "Resultat Net"
    LABEL_EPS = "BPA (EPS)"

    SUB_CASH = "Flux de Tresorerie"
    LABEL_FCF_LAST = "FCF (Dernier)"
    LABEL_CAPEX = "CapEx"
    LABEL_DA = "D&A"

    # Parametres Modele
    SUB_RATES = "Taux et Primes de Risque"
    LABEL_RF = "Taux Sans Risque (Rf)"
    LABEL_MRP = "Prime de Risque (MRP)"
    LABEL_KD = "Cout de la Dette (Kd)"
    LABEL_TAX = "Taux d'Imposition"

    SUB_GROWTH = "Croissance et Horizon"
    LABEL_G = "Taux de Croissance (g)"
    LABEL_GN = "Croissance Perpetuelle (gn)"
    LABEL_HORIZON = "Horizon de Projection"
    UNIT_YEARS = "ans"

    SUB_CALCULATED = "Metriques Calculees"
    LABEL_WACC = "WACC"
    LABEL_KE = "Cout des Fonds Propres (Ke)"
    LABEL_METHOD = "Methode de Valorisation"

    SUB_TV = "Valeur Terminale"
    LABEL_TV_METHOD = "Methode TV"
    LABEL_EXIT_M = "Multiple de Sortie"

    # Preuve de Calcul
    STEP_LABEL = r"Etape {index}"
    FORMULA_THEORY = "Formule Theorique"
    FORMULA_DATA_SOURCE = "*Donnee source*"
    APP_NUMERIC = "Application Numerique"
    VALUE_UNIT = r"Valeur ({unit})"
    STEP_VALIDATED = "**Validee**"
    NOTE_ANALYSIS = "Note d'analyse"

    # Resume Executif
    EXEC_TITLE = "Dossier de Valorisation : {name} ({ticker})"
    EXEC_CONFIDENCE = "Indice de Confiance"
    LABEL_IV = "Valeur Intrinseque"
    LABEL_SIMULATIONS = "Simulations"

    # Triangulation
    FOOTBALL_FIELD_TITLE = "Synthese de Triangulation (Football Field)"
    RELATIVE_VAL_DESC = "Comparaison de la valeur intrinseque face aux multiples medians du secteur."
    LABEL_MULTIPLES_UNAVAILABLE = "Multiples de marche indisponibles (Cohorte insuffisante)"

    # Scenarios
    LABEL_EXPECTED_VALUE = "Valeur Esperee (Ponderee)"
    LABEL_SCENARIO_RANGE = "Fourchette de Valeur (Bear - Bull)"

    # Glass Box Substitutions (utilisees par les strategies)
    SUB_FCF_BASE = r"FCF_0 = {val:,.2f} ({src})"
    SUB_FCF_NORM = r"FCF_norm = {val:,.2f} ({src})"
    SUB_REV_BASE = r"Rev_0 = {val:,.0f}"
    SUB_MARGIN_CONV = r"{curr:.2%} -> {target:.2%} (sur {years} ans)"
    SUB_EPS_GRAHAM = r"EPS = {val:.2f} ({src})"
    SUB_GRAHAM_MULT = r"8.5 + 2 x {g:.2f}"
    SUB_BV_BASE = r"BV_0 = {val:,.2f} ({src})"
    SUB_SUM_RI = r"Sum PV(RI) = {val:,.2f}"
    SUB_RIM_TV = r"{sub_tv} x {factor:.4f}"
    SUB_RIM_FINAL = r"{bv:,.2f} + {ri:,.2f} + {tv:,.2f}"
    SUB_P50_VAL = r"P50 = {val:,.2f} {curr}"
    SUB_FCFE_CALC = r"FCFE = FCFF - Int(1-t) + DDette = {val:,.2f}"
    SUB_FCFE_WALK = r"FCFE = NI ({ni:,.0f}) + Adj ({adj:,.0f}) + NetBorrowing ({nb:,.0f}) = {total:,.2f}"
    SUB_DDM_BASE = r"D_0 = {val:,.2f} / action"
    SUB_KE_LABEL = r"Cost of Equity (Ke) = {val:.2%}"
    SUB_EQUITY_NPV = r"Equity Value = NPV(Equity Flows) = {val:,.2f}"
    SUB_PAYOUT = r"Payout Ratio = Div_TTM ({div:,.2f}) / EPS_TTM ({eps:,.2f}) = {total:.1%}"
    SUB_TV_PE = r"TV_n = NI_n ({ni:,.0f}) x P/E Target ({pe:.1f}x) = {total:,.2f}"

    # Monte Carlo
    LABEL_CORRELATION_BG = "Correlation (Beta, g)"
    LABEL_HORIZON_SUB = "Horizon : {years} ans"
    LABEL_FOOTBALL_FIELD_IV = "Modele Intrinseque"
    LABEL_FOOTBALL_FIELD_PE = "Multiple P/E"
    LABEL_FOOTBALL_FIELD_EBITDA = "Multiple EV/EBITDA"
    LABEL_FOOTBALL_FIELD_REV = "Multiple EV/Revenue"
    LABEL_FOOTBALL_FIELD_PRICE = "Prix de Marche"

    MC_CONFIG_SUB = r"Sims : {sims} | Beta: N({beta:.2f}, {sig_b:.1%}) | g: N({g:.1%}, {sig_g:.1%}) | Y0 Vol: {sig_y0:.1%} | rho: {rho:.2f}"
    MC_FILTER_SUB = r"{valid} valides / {total} iterations"
    MC_SENS_SUB = r"P50(rho=0) = {p50_n:,.2f} vs Base = {p50_b:,.2f}"

    # Scenarios Labels
    LBL_SCENARIO_NAME = "Scenario"
    LBL_SCENARIO_PROBA = "Probabilite"
    LBL_SCENARIO_G = "Croissance (g)"
    LBL_SCENARIO_MARGIN = "Marge FCF"
    LBL_SCENARIO_VAL = "Valeur par Action"

    # Labels additionnels
    LABEL_NET_BORROWING = "Variation Dette Nette"
    LABEL_FCFE_TTM = "FCFE (Dernier)"
    LABEL_DIVIDEND_D0 = "Dividende $D_0$"
    LABEL_PAYOUT_RATIO = "Ratio de Distribution"
    LABEL_PE_RATIO = "Multiple P/E (Cours / Benefice)"
    LABEL_EV_EBITDA = "Multiple EV/EBITDA"
    LABEL_EV_REVENUE = "Multiple EV/Revenue"


class AuditTexts:
    """Textes lies au rapport d'audit et a la simulation Monte Carlo."""
    
    NO_REPORT = "Aucun rapport d'audit genere pour cette simulation."
    GLOBAL_SCORE = "Score d'Audit Global : {score:.1f} / 100"
    RATING_SCORE = "Rating Score"
    COVERAGE = "Couverture"
    CHECK_TABLE = "Table de Verification des Invariants"

    # Headers Table
    H_INDICATOR = "INDICATEUR"
    H_RULE = "REGLE NORMATIVE"
    H_EVIDENCE = "PREUVE NUMERIQUE"
    H_VERDICT = "VERDICT"

    # Verdicts
    STATUS_ALERT = "Alerte"
    STATUS_OK = "Conforme"
    AUDIT_NOTES_EXPANDER = "Consulter les notes d'audit detaillees"

    # Monte Carlo
    MC_FAILED = "La simulation n'a pas pu converger (Parametres instables)."
    MC_TITLE = "#### Analyse de Conviction Probabiliste"
    MC_DOWNSIDE = "Downside Risk (IV < Prix)"
    MC_MEDIAN = "Mediane (P50)"
    MC_TAIL_RISK = "Risque de Queue (P10)"
    MC_NO_DATA = "Donnees non disponibles."

    # SOTP
    LBL_SOTP_REVENUE_CHECK = "Reconciliation Revenus Groupe"
    LBL_SOTP_DISCOUNT_CHECK = "Prudence Decote SOTP"


class ChartTexts:
    """Libelles et textes pour les graphiques."""
    
    # Graphique de Prix
    PRICE_HISTORY_TITLE = "Historique de marche : {ticker}"
    PRICE_UNAVAILABLE = "Historique de prix indisponible pour {ticker}."
    PRICE_AXIS_Y = "Prix"

    # Monte Carlo
    SIM_UNAVAILABLE = "Pas de donnees de simulation disponibles."
    SIM_AXIS_X = "Valeur Intrinseque ({currency})"
    SIM_AXIS_Y = "Frequence"
    SIM_SUMMARY_TITLE = "**Synthese de la distribution ({count} scenarios) :**"
    SIM_SUMMARY_P50 = "Valeur centrale (P50)"
    SIM_SUMMARY_PRICE = "Prix de marche"
    SIM_SUMMARY_CI = "Intervalle de confiance (P10-P90)"

    # Sensibilite
    SENS_TITLE = "Sensibilite (WACC / Croissance)"
    SENS_UNAVAILABLE = "Matrice impossible (WACC trop proche de g)."
    SENS_AXIS_X = "Croissance (g)"
    SENS_AXIS_Y = "WACC / Ke"

    # Correlation
    CORREL_CAPTION = "Matrice de Correlation des Inputs (Stochastique)"
