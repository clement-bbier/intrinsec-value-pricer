"""
app/ui_components/ui_texts.py
CENTRALISATION INTÉGRALE DES TEXTES — PROJET IVP 2026
Version : V10.0 — Sprint 3 : Expansion Analytique (DDM & FCFE)
Rôle : Source unique de vérité pour toutes les chaînes de caractères visibles.
"""

class CommonTexts:
    """Textes transverses et métadonnées de base."""
    APP_TITLE = "Intrinsic Value Pricer"
    PROJECT_BADGE = "Projet Personnel Public"
    AUTHOR_NAME = "Clément Barbier"
    DEVELOPED_BY = "Developed by"
    RUN_BUTTON = "Lancer le calcul"
    DEFAULT_TICKER = "AAPL"

class SidebarTexts:
    """Labels et en-têtes de la barre latérale."""
    SEC_1_COMPANY = "1. Choix de l'entreprise"
    SEC_2_METHODOLOGY = "2. Choix de la méthodologie"
    SEC_3_SOURCE = "3. Source des données"
    SEC_4_HORIZON = "4. Horizon"
    SEC_5_RISK = "5. Analyse de Risque"

    TICKER_LABEL = "Ticker (Yahoo Finance)"
    METHOD_LABEL = "Méthode de Valorisation"
    STRATEGY_LABEL = "Stratégie de pilotage"
    YEARS_LABEL = "Années de projection"
    MC_TOGGLE_LABEL = "Activer Monte Carlo"
    MC_SIMS_LABEL = "Simulations"

    SOURCE_AUTO = "Auto (Yahoo Finance)"
    SOURCE_EXPERT = "Expert (Surcharge Manuelle)"
    SOURCE_OPTIONS = [SOURCE_AUTO, SOURCE_EXPERT]

class OnboardingTexts:
    """Contenu pédagogique de la page d'accueil (Guide d'Onboarding)."""
    INTRO_INFO = "Estimez la valeur intrinsèque d'une entreprise et comparez-la à son prix de marché."

    TITLE_A = "A. Sélection de la Méthodologie"
    DESC_A = (
        "Chaque méthodologie vise à modéliser la réalité économique d'une entreprise à un instant donné, "
        "conditionnellement à un ensemble d'hypothèses financières, selon les principes de "
        "[l'évaluation intrinsèque](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm) :"
    )

    MODEL_DCF_TITLE = "**Modèles DCF (Approche Entité)**"
    MODEL_DCF_DESC = (
        "• <b>FCFF (Firm)</b> : Standard Damodaran actualisant les flux avant service de la dette via le WACC. <br>"
        "• <b>Standard</b> : Approche pour entreprises matures aux flux de trésorerie prévisibles. <br>"
        "• <b>Fundamental</b> : Adapté aux cycliques ; utilise des flux normalisés pour gommer la volatilité d'un cycle économique complet.<br>"
        "• <b>Growth</b> : Modèle \"Revenue-Driven\" pour la Tech ; simule la convergence des marges vers un profil normatif à l'équilibre."
    )

    # NOUVEAUTÉ SPRINT 3
    MODEL_EQUITY_TITLE = "**Modèles Direct Equity (Approche Actionnaire)**"
    MODEL_EQUITY_DESC = (
        "• <b>FCFE (Equity)</b> : Actualise le flux résiduel après service de la dette au coût des fonds propres (Ke). <br>"
        "• <b>DDM (Dividend Model)</b> : Standard académique pour les entreprises dont la politique de distribution est le principal vecteur de valeur."
    )

    MODEL_RIM_TITLE = "**Residual Income (RIM)**"
    MODEL_RIM_DESC = (
        "Standard académique (Penman/Ohlson) pour les <b>Banques et Assurances</b> dont la valeur repose sur l'actif net.<br>"
        "Additionne la valeur comptable actuelle et la valeur actuelle de la richesse créée au-delà du coût d'opportunité des fonds propres."
    )

    MODEL_GRAHAM_TITLE = "**Modèle de Graham**"
    MODEL_GRAHAM_DESC = (
        "Estimation \"Value\" (1974 Revised) liant la capacité bénéficiaire actuelle aux conditions de crédit de haute qualité (AAA).<br>"
        "Définit un prix de référence basé sur le multiple de croissance historique et l'ajustement au rendement obligataire actuel."
    )

    TITLE_B = "B. Pilotage & Gestion du Risque"
    PILOTAGE_TITLE = "**Pilotage des Données (Auto vs Expert)**"
    PILOTAGE_DESC = (
        "Le mode **Auto** extrait les données de Yahoo Finance...  "
        "Le mode **Expert** offre une autonomie totale..."
    )
    MC_TITLE = "**Analyse Probabiliste (Monte Carlo)**"
    MC_DESC = (
        "La valeur intrinsèque est présentée comme une distribution...  "
        "simule des variations sur la croissance et le risque..."
    )

    TITLE_C = "C.Gouvernance & Transparence"
    AUDIT_TITLE = "**Audit Reliability Score**"
    AUDIT_DESC = "Indicateur mesurant la cohérence des inputs..."
    TRACE_TITLE = "**Valuation Traceability**"
    TRACE_DESC = "Chaque étape est détaillé dans l'onglet 'Calcul'..."

    DIAGNOSTIC_HEADER = "Système de Diagnostic :"
    DIAG_BLOQUANT = "**Bloquant** : Erreur de donnée ou paramètre manquant."
    DIAG_WARN = "**Avertissement** : Hypothèse divergente (ex: g > WACC)."
    DIAG_INFO = "**Information** : Note ou recommandation."


class ExpertTerminalTexts:
    """Titres, Sections et Labels spécifiques aux Terminaux Experts (V10.1)."""

    # --- Titres des terminaux ---
    TITLE_FCFF_STD = "Terminal Expert : FCFF Standard"
    TITLE_FCFF_FUND = "Terminal Expert : FCFF Fundamental"
    TITLE_FCFF_GROWTH = "Terminal Expert : FCFF Growth"
    TITLE_FCFE = "Terminal Expert : FCFE (Direct Equity)"
    TITLE_DDM = "Terminal Expert : Dividend Discount Model"
    TITLE_RIM = "Terminal Expert : RIM"
    TITLE_GRAHAM = "Terminal Expert : Graham"

    # --- Sections communes (Standardisation de la numérotation) ---
    SEC_1_FCF_STD = "#### 1. Flux de trésorerie de base ($FCF_0$)"
    SEC_1_FCF_NORM = "#### 1. Flux normalisé de base ($FCF_{norm}$)"
    SEC_1_REV_BASE = "#### 1. Chiffre d'Affaires de base ($Rev_0$)"
    SEC_1_FCFE_BASE = "#### 1. Reconstruction du Flux Actionnaire (FCFE)"
    SEC_1_DDM_BASE = "#### 1. Dividende de départ ($D_0$)"
    SEC_1_RIM_BASE = "#### 1. Valeur Comptable ($BV_0$) & Profits ($NI_t$)"
    SEC_1_GRAHAM_BASE = "#### 1. Bénéfices ($EPS$) & Croissance attendue ($g$)"

    SEC_2_PROJ = "#### 2. Phase de croissance explicite"
    SEC_2_PROJ_FUND = "#### 2. Croissance moyenne de cycle"
    SEC_2_PROJ_GROWTH = "#### 2. Horizon & Convergence des Marges"
    SEC_2_PROJ_RIM = "#### 2. Horizon & Croissance des profits"
    SEC_2_GRAHAM = "#### 2. Conditions de Marché AAA & Fiscalité"

    SEC_3_CAPITAL = "#### 3. Coût du Capital (Actualisation)"
    SEC_4_TERMINAL = "#### 4. Valeur de continuation (Sortie)"
    SEC_5_BRIDGE = "#### 5. Ajustements de structure (Equity Bridge)"
    SEC_6_MC = "#### 6. Simulation Probabiliste (Incertitude)"
    SEC_7_PEERS = "#### 7. Cohorte de Comparables (Triangulation)"

    # --- Labels des Inputs (Standard & FCFF) ---
    INP_FCF_TTM = "Dernier flux TTM (devise entreprise, Vide = Auto Yahoo)"
    INP_FCF_SMOOTHED = "Flux lissé de cycle (devise entreprise, Vide = Auto Yahoo)"
    INP_REV_TTM = "Chiffre d'affaires TTM (devise entreprise, Vide = Auto Yahoo)"
    INP_GROWTH_G = "Croissance moyenne attendue g (décimal, Vide = Auto Yahoo)"
    INP_GROWTH_G_SIMPLE = "Croissance moyenne g (décimal, Vide = Auto Yahoo)"
    INP_REV_GROWTH = "Croissance CA g_rev (décimal, Vide = Auto Yahoo)"
    INP_MARGIN_TARGET = "Marge FCF cible (décimal, Vide = Auto Yahoo)"
    INP_BV_INITIAL = "Valeur comptable initiale BV₀ (Vide = Auto Yahoo)"
    INP_NI_TTM = "Résultat Net TTM NIₜ (Vide = Auto Yahoo)"
    INP_EPS_NORM = "BPA normalisé EPS (Vide = Auto Yahoo)"
    INP_YIELD_AAA = "Rendement Obligations AAA Y (décimal, Vide = Auto Yahoo)"
    INP_PRICE_WEIGHTS = "Prix de l'action pour calcul des poids (Vide = Auto Yahoo)"
    INP_RF = "Taux sans risque Rf (décimal, Vide = Auto Yahoo)"
    INP_BETA = "Coefficient Beta β (facteur x, Vide = Auto Yahoo)"
    INP_MRP = "Prime de risque marché MRP (décimal, Vide = Auto Yahoo)"
    INP_KD = "Coût de la dette brut kd (décimal, Vide = Auto Yahoo)"
    INP_TAX = "Taux d'imposition effectif τ (décimal, Vide = Auto Yahoo)"
    INP_TAX_SIMPLE = "Taux d'imposition τ (décimal, Vide = Auto Yahoo)"
    INP_GN = "Taux de croissance à l'infini gn (décimal, Vide = Auto Yahoo)"
    INP_EXIT_M = "Multiple de sortie (facteur x, Vide = Auto Yahoo)"
    INP_OMEGA = "Facteur de persistance ω (0 à 1, Vide = Auto 0.6)"

    # --- Equity Bridge (FCFF Standard) ---
    INP_DEBT = "Dette Totale (Vide = Auto Yahoo)"
    INP_CASH = "Trésorerie (Vide = Auto Yahoo)"
    INP_SHARES = "Actions en circulation (Vide = Auto Yahoo)"
    INP_MINORITIES = "Intérêts Minoritaires (Vide = Auto Yahoo)"
    INP_PENSIONS = "Provisions Pensions (Vide = Auto Yahoo)"

    # --- Spécificités FCFE (Clean Walk) ---
    INP_FCFE_NI = "Résultat Net (Net Income TTM)"
    INP_FCFE_ADJ = "Ajustements Cash (Amort - Capex - ΔBFR)"
    INP_FCFE_BASE = "Flux FCFE de base (Vide = Auto Yahoo)"
    INP_NET_BORROWING = "Variation nette de la dette ($Net Borrowing$)"
    INP_NET_BORROWING_HELP = "Montant net des émissions moins les remboursements de dette sur l'année."

    # --- Spécificités DDM ---
    INP_DIVIDEND_BASE = "Dernier dividende annuel payé ($D_0$)"
    INP_PAYOUT_TARGET = "Ratio de distribution cible (Payout %)"
    INP_PE_TARGET = "Multiple P/E Cible (Sortie)"
    INP_DIVIDEND_BASE_HELP = "Dividendes versés sur les 12 derniers mois (TTM)."

    INP_MANUAL_PEERS = "Tickers des concurrents (séparés par une virgule)"
    INP_MANUAL_PEERS_HELP = "Laissez vide pour utiliser l'algorithme de découverte automatique de Yahoo Finance."

    # --- Labels Interactifs & Monte Carlo ---
    RADIO_TV_METHOD = "Modèle de sortie (TV)"
    TV_GORDON = "Croissance Perpétuelle (Gordon)"
    TV_EXIT = "Multiple de Sortie / P/E"

    MC_CALIBRATION = "Calibration des Volatilités (Monte Carlo) :"
    MC_ITERATIONS = "Nombre d'itérations"
    MC_VOL_BASE_FLOW = "Vol. Flux Base (Y0)"
    MC_VOL_BASE_FLOW_HELP = "Simule l'incertitude sur la fiabilité du dernier flux reporté (Standard Error)."
    MC_VOL_BETA = "Vol. β"
    MC_VOL_G = "Vol. g"
    MC_VOL_OMEGA = "Vol. ω"
    MC_VOL_GN = "Vol. gn"

    # --- Sliders d'Horizon ---
    SLIDER_PROJ_YEARS = "Horizon de projection (t années)"
    SLIDER_CYCLE_YEARS = "Horizon du cycle (t années)"
    SLIDER_PROJ_T = "Années de projection (t)"
    SLIDER_PROJ_N = "Années de projection (n)"

    # --- Boutons de validation (Templates) ---
    BTN_VALUATE_STD = "Lancer la valorisation : {ticker}"
    BTN_VALUATE_FUND = "Lancer la valorisation Fondamentale : {ticker}"
    BTN_VALUATE_GROWTH = "Lancer l'analyse Growth : {ticker}"
    BTN_VALUATE_RIM = "Lancer la valorisation RIM : {ticker}"
    BTN_VALUATE_GRAHAM = "Calculer la valeur Graham : {ticker}"
    BTN_VALUATE_FCFE = "Calculer la valeur FCFE (Actionnaire) : {ticker}"
    BTN_VALUATE_DDM = "Calculer la valeur DDM (Dividendes) : {ticker}"

class TooltipsTexts:
    """Infobulles et aides contextuelles pour le mode Expert."""
    # Note: On pourra ici centraliser les aides DAMODARAN plus tard
    pass

class FeedbackMessages:
    """Messages système et alertes de validation."""
    TICKER_REQUIRED_SIDEBAR = "Veuillez saisir un ticker dans la barre latérale."
    TICKER_INVALID = "Veuillez saisir un ticker valide."

class LegalTexts:
    """Textes juridiques, avertissements et notes de conformité."""
    COMPLIANCE_TITLE = "Note de conformité"
    COMPLIANCE_BODY = (
        "Ces estimations constituent des simulations prospectives basées sur des modèles d’analyse intrinsèque. "
        "La précision du prix théorique dépend strictement de la qualité des entrées fournies et des paramètres de risque sélectionnés. "
        "Ce travail à visée pédagogique ne constitue pas un conseil en investissement."
    )


class KPITexts:
    """Labels et titres pour l'affichage des résultats (Glass Box)."""
    # Onglets
    TAB_INPUTS = "Données d'Entrée"
    TAB_CALC = "Preuve de Calcul"
    TAB_AUDIT = "Audit de Fiabilité"
    TAB_MC = "Analyse de Risque (MC)"

    # Titres de sections (Inputs)
    SECTION_INPUTS_HEADER = "#### Récapitulatif des Données Utilisées"
    SECTION_INPUTS_CAPTION = "Ce tableau liste l'ensemble des inputs injectés dans le moteur de calcul."
    SEC_A_IDENTITY = "A. Identification de l'Entreprise"
    SEC_B_FINANCIALS = "B. Données Financières (Source: Yahoo Finance)"
    SEC_C_MODEL = "C. Paramètres du Modèle de Valorisation"
    SEC_D_MC = "D. Configuration Monte Carlo"

    # Labels Identification
    LABEL_TICKER = "Ticker"
    LABEL_NAME = "Nom"
    LABEL_SECTOR = "Secteur"
    LABEL_COUNTRY = "Pays"
    LABEL_INDUSTRY = "Industrie"
    LABEL_CURRENCY = "Devise"
    LABEL_BETA = "Beta (β)"
    LABEL_SHARES = "Actions en circulation"

    # Labels Financiers
    SUB_MARKET = "Marché & Capitalisation"
    LABEL_PRICE = "Cours Actuel"
    LABEL_MCAP = "Capitalisation Boursière"
    LABEL_BVPS = "Book Value / Action"

    SUB_CAPITAL = "Structure du Capital"
    LABEL_DEBT = "Dette Totale"
    LABEL_CASH = "Trésorerie"
    LABEL_NET_DEBT = "Dette Nette"
    LABEL_INTEREST = "Charges d'Intérêts"

    SUB_PERF = "Performance Opérationnelle (TTM)"
    LABEL_REV = "Chiffre d'Affaires"
    LABEL_EBIT = "EBIT"
    LABEL_NI = "Résultat Net"
    LABEL_EPS = "BPA (EPS)"

    SUB_CASH = "Flux de Trésorerie"
    LABEL_FCF_LAST = "FCF (Dernier)"
    LABEL_CAPEX = "CapEx"
    LABEL_DA = "D&A"

    # Nouveaux Labels Financiers Sprint 3
    LABEL_NET_BORROWING = "Variation Dette Nette"
    LABEL_FCFE_TTM = "FCFE (Dernier)"
    LABEL_DIVIDEND_D0 = "Dividende $D_0$"
    LABEL_PAYOUT_RATIO = "Ratio de Distribution"

    # Paramètres Modèle
    SUB_RATES = "Taux et Primes de Risque"
    LABEL_RF = "Taux Sans Risque (Rf)"
    LABEL_MRP = "Prime de Risque (MRP)"
    LABEL_KD = "Coût de la Dette (Kd)"
    LABEL_TAX = "Taux d'Imposition (τ)"

    SUB_GROWTH = "Croissance et Horizon"
    LABEL_G = "Taux de Croissance (g)"
    LABEL_GN = "Croissance Perpétuelle (gn)"
    LABEL_HORIZON = "Horizon de Projection"
    UNIT_YEARS = "ans"

    SUB_CALCULATED = "Métriques Calculées"
    LABEL_WACC = "WACC"
    LABEL_KE = "Coût des Fonds Propres (Ke)"
    LABEL_METHOD = "Méthode de Valorisation"

    SUB_TV = "Valeur Terminale"
    LABEL_TV_METHOD = "Méthode TV"
    LABEL_EXIT_M = "Multiple de Sortie"

    # Preuve de Calcul
    STEP_LABEL = r"Étape {index}"
    FORMULA_THEORY = "Formule Théorique"
    FORMULA_DATA_SOURCE = "*Donnée source*"
    APP_NUMERIC = "Application Numérique"
    VALUE_UNIT = r"Valeur ({unit})"
    STEP_VALIDATED = "**Validée**"
    NOTE_ANALYSIS = "Note d'analyse"

    # Résumé Exécutif
    EXEC_TITLE = "Dossier de Valorisation : {name} ({ticker})"
    EXEC_CONFIDENCE = "Indice de Confiance"

    # Labels
    LABEL_IV = "Valeur Intrinsèque"
    LABEL_SIMULATIONS = "Simulations"
    LABEL_CORRELATION_BG = "Corrélation (β, g)"
    LABEL_HORIZON_SUB = "Horizon : {years} ans"

    LABEL_FOOTBALL_FIELD_IV = "Modèle Intrinsèque"
    LABEL_FOOTBALL_FIELD_PE = "Multiple P/E"
    LABEL_FOOTBALL_FIELD_EBITDA = "Multiple EV/EBITDA"
    LABEL_FOOTBALL_FIELD_REV = "Multiple EV/Revenue"
    LABEL_FOOTBALL_FIELD_PRICE = "Prix de Marché"

    MC_CONFIG_SUB = r"Sims : {sims} | β: 𝒩({beta:.2f}, {sig_b:.1%}) | g: 𝒩({g:.1%}, {sig_g:.1%}) | Y₀ Vol: {sig_y0:.1%} | ρ: {rho:.2f}"
    MC_FILTER_SUB = r"{valid} valides / {total} itérations"
    MC_SENS_SUB = r"P50(rho=0) = {p50_n:,.2f} vs Base = {p50_b:,.2f}"

    SUB_FCF_BASE = r"FCF_0 = {val:,.2f} ({src})"
    SUB_FCF_NORM = r"FCF_norm = {val:,.2f} ({src})"
    SUB_REV_BASE = r"Rev_0 = {val:,.0f}"
    SUB_MARGIN_CONV = r"{curr:.2%} -> {target:.2%} (sur {years} ans)"
    SUB_EPS_GRAHAM = r"EPS = {val:.2f} ({src})"
    SUB_GRAHAM_MULT = r"8.5 + 2 × {g:.2f}"
    SUB_BV_BASE = r"BV_0 = {val:,.2f} ({src})"
    SUB_SUM_RI = r"Σ PV(RI) = {val:,.2f}"
    SUB_RIM_TV = r"{sub_tv} × {factor:.4f}"
    SUB_RIM_FINAL = r"{bv:,.2f} + {ri:,.2f} + {tv:,.2f}"
    SUB_P50_VAL = r"P50 = {val:,.2f} {curr}"

    SUB_FCFE_CALC = r"FCFE = FCFF - Int(1-τ) + ΔDette = {val:,.2f}"
    SUB_FCFE_WALK = r"FCFE = NI ({ni:,.0f}) + Adj ({adj:,.0f}) + NetBorrowing ({nb:,.0f}) = {total:,.2f}"

    SUB_DDM_BASE = r"D_0 = {val:,.2f} / action"
    SUB_KE_LABEL = r"Cost of Equity (Ke) = {val:.2%}"
    SUB_EQUITY_NPV = r"Equity Value = NPV(Equity Flows) = {val:,.2f}"
    SUB_PAYOUT = r"Payout Ratio = Div_TTM ({div:,.2f}) / EPS_TTM ({eps:,.2f}) = {total:.1%}"
    SUB_TV_PE = r"TV_n = NI_n ({ni:,.0f}) × P/E Target ({pe:.1f}x) = {total:,.2f}"

    # Titres de sections (Relative Valuation)
    SEC_E_RELATIVE = "E. Valorisation Relative (Multiples de Marché)"
    LABEL_PE_RATIO = "Multiple P/E (Cours / Bénéfice)"
    LABEL_EV_EBITDA = "Multiple EV/EBITDA"
    LABEL_EV_REVENUE = "Multiple EV/Revenue"

    # Triangulation
    FOOTBALL_FIELD_TITLE = "Synthèse de Triangulation (Football Field)"
    RELATIVE_VAL_DESC = "Comparaison de la valeur intrinsèque face aux multiples médians du secteur."
    LABEL_MULTIPLES_UNAVAILABLE = "Multiples de marché indisponibles (Cohorte insuffisante)" # NOUVEAU

class AuditTexts:
    """Textes liés au rapport d'audit et à la simulation Monte Carlo."""
    # Rapport d'Audit
    NO_REPORT = "Aucun rapport d'audit généré pour cette simulation."
    GLOBAL_SCORE = "Score d'Audit Global : {score:.1f} / 100"
    RATING_SCORE = "Rating Score"
    COVERAGE = "Couverture"
    CHECK_TABLE = "Table de Vérification des Invariants"

    # Headers Table
    H_INDICATOR = "INDICATEUR"
    H_RULE = "RÈGLE NORMATIVE"
    H_EVIDENCE = "PREUVE NUMÉRIQUE"
    H_VERDICT = "VERDICT"

    # Verdicts
    STATUS_ALERT = "Alerte"
    STATUS_OK = "Conforme"
    AUDIT_NOTES_EXPANDER = "Consulter les notes d'audit détaillées"

    # Monte Carlo
    MC_FAILED = "La simulation n'a pas pu converger (Paramètres instables)."
    MC_TITLE = "#### Analyse de Conviction Probabiliste"
    MC_DOWNSIDE = "Downside Risk (IV < Prix)"
    MC_MEDIAN = "Médiane (P50)"
    MC_TAIL_RISK = "Risque de Queue (P10)"

    MC_SENS_RHO = "**Sensibilité Corrélation (ρ)**"
    MC_SCENARIO = "Scénario"
    MC_IV_P50 = "IV (P50)"
    MC_NO_DATA = "Données non disponibles."

    MC_STRESS_TITLE = "**Scénario de Stress (Bear Case)**"
    MC_FLOOR_VAL = "**Valeur Plancher : {val:,.2f} {curr}**"
    MC_STRESS_DESC = "Paramètres : g=0%, β=1.5. Simulation de rupture des fondamentaux."

    MC_AUDIT_HYP = "Audit des Hypothèses Statistiques"
    MC_AUDIT_STOCH = "Détail du traitement stochastique (Audit)"
    MC_VOL_BETA = "Volatilité Beta"
    MC_VOL_G = "Volatilité Croissance"
    MC_CORREL_INFO = "La corrélation négative standard prévient les scénarios financiers incohérents."

    # Evidence mapping (internes)
    EVIDENCE_ERROR = "Erreur source"
    EVIDENCE_OK = "Vérification OK"


class ChartTexts:
    """Libellés et textes pour les graphiques (ui_charts.py)."""
    # Graphique de Prix
    PRICE_HISTORY_TITLE = "Historique de marché : {ticker}"
    PRICE_UNAVAILABLE = "Historique de prix indisponible pour {ticker}."
    PRICE_AXIS_Y = "Prix"
    TOOLTIP_DATE = "Date"
    TOOLTIP_PRICE = "Prix"
    DATE_FORMAT = "%d %b %Y"

    # Monte Carlo
    SIM_UNAVAILABLE = "Pas de données de simulation disponibles."
    SIM_AXIS_X = "Valeur Intrinsèque ({currency})"
    SIM_AXIS_Y = "Fréquence"
    SIM_SUMMARY_TITLE = "**Synthèse de la distribution ({count} scénarios) :**"
    SIM_SUMMARY_P50 = "Valeur centrale (P50)"
    SIM_SUMMARY_PRICE = "Prix de marché"
    SIM_SUMMARY_CI = "Intervalle de confiance (P10-P90)"
    SIM_SUMMARY_PROB = "({prob}% de probabilité)"

    # Sensibilité
    SENS_TITLE = "Sensibilité (WACC / Croissance)"
    SENS_UNAVAILABLE = "Matrice impossible (WACC trop proche de g)."
    SENS_AXIS_X = "Croissance (g)"
    SENS_AXIS_Y = "WACC / Ke"
    SENS_TOOLTIP_WACC = "Taux (WACC)"
    SENS_TOOLTIP_GROWTH = "Croissance"
    SENS_TOOLTIP_VAL = "Valeur ({currency})"

    # Corrélation
    CORREL_CAPTION = "Matrice de Corrélation des Inputs (Stochastique)"

class RegistryTexts:
    """Labels et descriptions pédagogiques du registre Glass Box (ui_glass_box_registry.py)."""

    # --- DCF (Approche Entité - FCFF) ---
    DCF_FCF_BASE_L = "Ancrage du Flux d'Exploitation (FCF₀)"
    DCF_FCF_BASE_D = "Flux de trésorerie disponible pour l'entreprise (Firm) avant service de la dette."

    DCF_FCF_NORM_L = "Ancrage du Flux Normalisé"
    DCF_FCF_NORM_D = "Flux lissé sur un cycle complet pour neutraliser la volatilité opérationnelle."

    DCF_STABILITY_L = "Contrôle de Viabilité Financière"
    DCF_STABILITY_D = "Validation de la capacité de l'actif économique à générer des flux positifs."

    DCF_WACC_L = "Coût Moyen Pondéré du Capital (WACC)"
    DCF_WACC_D = "Taux d'actualisation reflétant le coût global du capital (Dette + Fonds Propres)."

    DCF_KE_L = "Coût des Fonds Propres (Ke)"
    DCF_KE_D = "Taux de rendement exigé par les actionnaires, calculé via le modèle CAPM."

    DCF_PROJ_L = "Projection des Flux Futurs"
    DCF_PROJ_D = "Modélisation de la croissance des flux sur l'horizon explicite de projection."

    DCF_TV_GORDON_L = "Valeur Terminale (Gordon Growth)"
    DCF_TV_GORDON_D = r"Estimation de la valeur de perpétuité basée sur un taux de croissance stable ($g_n$)."

    DCF_TV_MULT_L = "Valeur Terminale (Multiple de Sortie)"
    DCF_TV_MULT_D = "Estimation de la valeur de revente théorique basée sur un multiple (EBITDA ou P/E)."

    DCF_EV_L = "Valeur de l'Outil de Production (EV)"
    DCF_EV_D = "Somme actualisée des flux d'exploitation et de la valeur terminale."

    DCF_BRIDGE_L = "Pont de Valeur (Equity Bridge)"
    DCF_BRIDGE_D = "Passage de la Valeur d'Entreprise à la Valeur Actionnariale (Retrait Dette, Minoritaires, Pensions)."

    DCF_IV_L = "Valeur Intrinsèque par Action"
    DCF_IV_D = "Prix théorique final estimé pour un titre ordinaire."

    # --- FCFE (Approche Actionnaire - Clean Walk) ---
    FCFE_BASE_L = "Reconstruction du Flux Actionnaire (FCFE₀)"
    FCFE_BASE_D = "Calcul du flux résiduel : Résultat Net + Amortissements - CapEx - ΔBFR + Net Borrowing."

    FCFE_DEBT_ADJ_L = "Audit du Levier Actionnaire"
    FCFE_DEBT_ADJ_D = "Analyse de la contribution de l'endettement net à la génération du flux actionnaire."

    # --- DDM (Dividend Discount Model) ---
    DDM_BASE_L = r"Ancrage du Dividende de Référence ($D_0$)"
    DDM_BASE_D = "Somme des dividendes versés sur les 12 derniers mois (Base de projection)."

    DDM_GROWTH_L = "Dynamique de Distribution"
    DDM_GROWTH_D = "Modélisation de la croissance des dividendes basée sur le taux de rétention et le ROE."

    # --- GROWTH (Convergence des Marges) ---
    GROWTH_REV_BASE_L = "Chiffre d'Affaires d'Ancrage"
    GROWTH_REV_BASE_D = "Revenu TTM utilisé comme socle pour la projection de croissance du volume."

    GROWTH_MARGIN_L = "Convergence des Marges Opérationnelles"
    GROWTH_MARGIN_D = "Simulation de l'évolution des marges vers un profil normatif de maturité."

    # --- RIM (Residual Income Model) ---
    RIM_BV_L = "Actif Net Comptable d'Ouverture"
    RIM_BV_D = "Valeur des capitaux propres au bilan au départ du modèle."

    RIM_KE_L = "Coût d'Opportunité des Fonds Propres"
    RIM_KE_D = "Seuil de rentabilité minimum pour justifier la création de valeur actionnariale."

    RIM_RI_L = "Calcul du Profit Résiduel (Surprofit)"
    RIM_RI_D = r"Richesse créée au-delà du coût du capital immobilisé ($NI - k_e \times BV_{t-1}$)."

    RIM_TV_L = "Valeur Terminale de Persistance (ω)"
    RIM_TV_D = "Estimation de la vitesse de dégradation du surprofit vers la moyenne du marché."

    RIM_IV_L = "Valeur Intrinsèque RIM (Ohlson)"
    RIM_IV_D = "Somme de la Valeur Comptable et de la valeur actuelle des surprofits futurs."

    RIM_PAYOUT_L = "Politique de Rétention des Profits"
    RIM_PAYOUT_D = "Impact de la distribution sur la croissance future de la valeur comptable."

    RIM_EPS_PROJ_L = "Projection des Bénéfices Net (NI)"
    RIM_EPS_PROJ_D = "Trajectoire attendue du résultat net par action sur l'horizon choisi."

    # --- GRAHAM (Valuation Historique) ---
    GRAHAM_EPS_L = "Capacité Bénéficiaire Normalisée (EPS)"
    GRAHAM_EPS_D = "Bénéfice par action ajusté pour refléter la rentabilité récurrente."

    GRAHAM_MULT_L = "Multiplicateur de Croissance Graham"
    GRAHAM_MULT_D = "Prime de croissance théorique basée sur la formule révisée de 1974."

    GRAHAM_IV_L = "Valeur Graham AAA"
    GRAHAM_IV_D = "Prix de référence ajusté par le rendement actuel des obligations d'entreprises AAA."

    # --- MC (Moteur Stochastique) ---
    MC_INIT_L = "Initialisation & Lois de Probabilité"
    MC_INIT_D = r"Paramétrage des distributions normales pour les variables critiques ($k_e, g, gn$)."

    MC_SAMP_L = "Simulation Multivariée (Cholesky)"
    MC_SAMP_D = "Génération de scénarios corrélés pour respecter la cohérence économique."

    MC_FILT_L = "Contrôle de Convergence Statistique"
    MC_FILT_D = r"Filtrage des scénarios mathématiquement divergents ($g \geq r$)."

    MC_MED_L = "Valeur Centrale Probabiliste (P50)"
    MC_MED_D = "Point médian de la distribution des valeurs intrinsèques simulées."

    MC_SENS_L = "Analyse de Corrélation des Risques"
    MC_SENS_D = "Mesure de la sensibilité de la valeur au couple Risque/Croissance."

    MC_STRESS_L = "Test de Résistance (Stress Test)"
    MC_STRESS_D = "Scénario extrême simulant une rupture de croissance et une hausse du risque."

    # --- NOUVEAUTÉ MONTE CARLO ---
    MC_Y0_UNCERTAINTY_L = r"Incertitude sur le Flux d'Ancrage ($Y_0$)"
    MC_Y0_UNCERTAINTY_D = "Intégration de l'erreur type sur le dernier flux reporté (Standard Error)."

    # --- AUDIT (Système Expert) ---
    AUDIT_BETA_L = "Validation du Risque Systématique (β)"
    AUDIT_BETA_D = "Vérifie que le Beta utilisé est cohérent avec le profil sectoriel."

    AUDIT_ICR_L = "Couverture des Intérêts (Solvabilité)"
    AUDIT_ICR_D = "Capacité de l'entreprise à honorer sa dette via son résultat opérationnel."

    AUDIT_CASH_L = "Position Net-Net"
    AUDIT_CASH_D = "Alerte si la trésorerie nette dépasse la valeur de marché (Opportunité Value)."

    AUDIT_LIQ_L = "Risque de Liquidité de Marché"
    AUDIT_LIQ_D = "Analyse de la profondeur de marché pour les capitalisations réduites."

    AUDIT_LEV_L = "Intensité du Levier Financier"
    AUDIT_LEV_D = "Évaluation du poids de la dette par rapport à la capacité de remboursement."

    AUDIT_MACRO_L = "Alignement Macro-économique"
    AUDIT_MACRO_D = "Vérifie que la croissance perpétuelle ($gn$) ne dépasse pas le PIB nominal attendu."

    AUDIT_RF_L = "Cohérence du Taux Sans Risque ($R_f$)"
    AUDIT_RF_D = "Alerte si le taux sans risque est déconnecté des réalités monétaires."

    AUDIT_REINV_L = "Taux de Réinvestissement Industriel"
    AUDIT_REINV_D = "Vérifie si le CapEx est suffisant pour maintenir l'outil de production."

    AUDIT_GLIM_L = "Plafond de Croissance soutenable"
    AUDIT_GLIM_D = "Alerte sur les hypothèses de croissance dépassant les standards historiques."

    AUDIT_PAY_L = "Soutenabilité du Dividende"
    AUDIT_PAY_D = "Vérifie que le Payout Ratio ne compromet pas le réinvestissement nécessaire."

    AUDIT_WACC_L = "Validation du Plancher d'Actualisation"
    AUDIT_WACC_D = "Alerte si le coût du capital est anormalement bas (Survalorisation)."

    AUDIT_TVC_L = "Poids de la Valeur Terminale"
    AUDIT_TVC_D = "Mesure la dépendance de la valorisation à l'hypothèse d'éternité."

    AUDIT_G_WACC_L = "Divergence Gordon-Shapiro"
    AUDIT_G_WACC_D = "Vérifie la condition critique d'existence du modèle ($r > g$)."

    AUDIT_SPREAD_L = "Spread de Création de Valeur ($ROE - k_e$)"
    AUDIT_SPREAD_D = "Mesure l'écart de rentabilité par rapport au coût d'opportunité."

    AUDIT_PB_L = "Pertinence du Modèle RIM (P/B Ratio)"
    AUDIT_PB_D = "Analyse si la valeur boursière est trop déconnectée de la valeur comptable."

    AUDIT_UNK_L = "Test de Fiabilité Spécifique"
    AUDIT_UNK_D = "Diagnostic technique non référencé dans le catalogue standard."

class WorkflowTexts:
    """Messages d'état du cycle de vie de l'analyse (workflow.py)."""
    STATUS_MAIN_LABEL = "Initialisation de l'analyse..."
    STATUS_DATA_ACQUISITION = "Acquisition des données de marché et macro-économiques..."
    STATUS_SMART_MERGE = "Conciliation des hypothèses (Smart Merge)..."
    STATUS_ENGINE_RUN = "Exécution du moteur de calcul : {mode}..."
    STATUS_MC_RUN = "Simulation stochastique, tests de sensibilité et stress-testing en cours..."
    STATUS_AUDIT_GEN = "Génération du rapport d'audit et score de confiance..."
    STATUS_PEER_DISCOVERY = "Identification des pairs et concurrents sectoriels..."
    STATUS_PEER_FETCHING = r"Extraction des multiples de marché ({current}/{total})..."
    STATUS_COMPLETE = "Analyse finalisée avec succès"
    STATUS_INTERRUPTED = "Analyse interrompue"
    STATUS_CRITICAL_ERROR = "Erreur système critique"

    DIAG_EXPANDER_TITLE = "Détails techniques et remédiation"
    DIAG_ACTION_LABEL = "Action recommandée :"

    PREFIX_CRITICAL = "**ARRÊT CRITIQUE :**"
    PREFIX_WARNING = "**AVERTISSEMENT :**"
    PREFIX_INFO = "**INFORMATION :**"

class DiagnosticTexts:
    """Messages du registre de diagnostic et des exceptions (diagnostics.py & exceptions.py)."""

    # Registre : Divergence Gordon
    MODEL_G_DIV_MSG = r"ERREUR DE CONVERGENCE : Le taux de croissance g ({g:.2%}) est $\geq$ au Ke/WACC ({wacc:.2%})."
    MODEL_G_DIV_HINT = "Une entreprise ne peut croître plus vite que son coût du capital à l'infini. Réduisez 'gn' ou révisez le taux d'actualisation."

    # Registre : Instabilité Monte Carlo
    MODEL_MC_INST_MSG = "INSTABILITÉ CRITIQUE : Seuls {valid_ratio:.1%} des scénarios sont valides."
    MODEL_MC_INST_HINT = r"Le modèle diverge trop souvent ($g \geq r$). Diminuez la 'Vol. gn' ou augmentez la marge de sécurité entre gn et le taux d'actualisation."

    # Registre : Métriques manquantes
    DATA_MISSING_CORE_MSG = "Métrique critique manquante : {metric_name}."
    DATA_MISSING_CORE_HINT = "Utilisez le mode 'Expert' pour saisir manuellement cette donnée."
    DATA_PEER_SKIP_MSG = r"Pair '{ticker}' ignoré : Multiples aberrants ou données incomplètes."

    # Registre : Risques
    RISK_EXCESSIVE_GROWTH_MSG = "Croissance projetée agressive ({g:.2%})."
    RISK_EXCESSIVE_GROWTH_HINT = "Vérifiez si ce taux est soutenable face à la moyenne du secteur."

    DATA_NEGATIVE_BETA_MSG = "Beta atypique détecté ({beta:.2f})."
    DATA_NEGATIVE_BETA_HINT = "Un Beta négatif est rare ; vérifiez la source ou saisissez un Beta sectoriel."

    # Erreurs Système (Crash)
    SYSTEM_CRASH_MSG = "Une défaillance technique inattendue a été détectée lors de l'exécution."
    SYSTEM_CRASH_HINT = "Veuillez vérifier votre connexion internet ou tenter une requête simplifiée (Mode Auto)."

    # Exceptions : Ticker & Données
    TICKER_NOT_FOUND_MSG = "Le ticker '{ticker}' est introuvable sur Yahoo Finance."
    TICKER_NOT_FOUND_HINT = "Vérifiez l'orthographe (ex: 'AIR.PA' pour Airbus) ou si l'entreprise est radiée."

    DATA_FIELD_MISSING_YEAR = "Donnée manquante pour {ticker} : '{field}' pour l'année {year}."
    DATA_FIELD_MISSING_GENERIC = "Donnée fondamentale manquante pour {ticker} : '{field}' est vide ou invalide."
    DATA_FIELD_HINT = "Cette entreprise ne publie peut-être pas cette donnée, ou l'historique est trop court."

    # Exceptions : Infrastructure
    PROVIDER_FAIL_MSG = "Échec de connexion au fournisseur {provider}."
    PROVIDER_FAIL_HINT = "Veuillez vérifier votre connexion internet. L'API est peut-être temporairement indisponible."

    # Exceptions : Logique Modèle
    MODEL_LOGIC_MSG = "Incohérence dans le modèle {model} : {issue}"
    MODEL_LOGIC_HINT = "Vérifiez vos hypothèses de croissance ou de taux d'actualisation."
    CALC_GENERIC_HINT = "Vérifiez les données d'entrée ou les paramètres du modèle dans le Terminal Expert."

    UNKNOWN_STRATEGY_MSG = "La stratégie pour {mode} n'est pas enregistrée."
    UNKNOWN_STRATEGY_HINT = "Vérifiez le registre des stratégies dans le moteur central."
    STRATEGY_CRASH_MSG = "Échec critique du moteur : {error}"
    STRATEGY_CRASH_HINT = "Redémarrez l'analyse ou contactez le support technique."

    # FCFE & DDM (Sprint 3)
    FCFE_NEGATIVE_MSG = "FLUX ACTIONNAIRE NÉGATIF ({val:,.0f}) : Modèle inapplicable."
    FCFE_NEGATIVE_HINT = "Le remboursement de la dette excède la génération de cash. Le modèle DCF ne peut valoriser des flux négatifs perpétuels."

    DDM_PAYOUT_MSG = "DÉCAPITALISATION : Le taux de distribution ({payout:.1%}) dépasse 100%."
    DDM_PAYOUT_HINT = "L'entreprise distribue plus que ses bénéfices. Vérifiez si cette politique est soutenable."

    MODEL_SGR_DIV_MSG = r"CROISSANCE INSOUTENABLE : $g$ ({g:.1%}) est supérieur au SGR ({sgr:.1%})."
    MODEL_SGR_DIV_HINT = "La croissance dépasse la capacité d'autofinancement. Réduisez 'gn' ou justifiez un apport de capital externe."



class StrategySources:
    """Descriptions des sources de données utilisées dans les calculs (strategies/)."""
    WACC_TARGET = "Structure Cible"
    WACC_MARKET = "Structure de Marché"
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

class StrategyInterpretations:
    """Notes pédagogiques dynamiques générées par les stratégies (Glass Box)."""
    # DCF & Abstract
    WACC = "Taux d'actualisation cible (WACC) de {wacc:.2%}, basé sur la structure de capital actuelle."
    PROJ = "Projection sur {years} ans à un taux de croissance annuel moyen de {g:.2%}"
    TV = "Estimation de la valeur de l'entreprise au-delà de la période explicite."
    EV = "Valeur totale de l'outil de production actualisée."
    BRIDGE = "Ajustement de la structure financière."
    IV = "Estimation de la valeur réelle d'une action pour {ticker}."

    # RIM
    RIM_TV = "Estimation de la persistance des surprofits."

    # Growth
    GROWTH_REV = "Point de départ du modèle basé sur le chiffre d'affaires TTM."
    GROWTH_MARGIN = "Modélisation de l'amélioration opérationnelle vers une marge FCF normative."
    GROWTH_TV = "Valeur de l'entreprise à l'infini basée sur la dernière marge convergée."
    GROWTH_EV = "Somme actualisée des flux et de la valeur terminale."
    GROWTH_IV = "Estimation finale du prix théorique par titre."

    # Fundamental
    FUND_NORM = "Le modèle utilise un flux lissé sur un cycle complet pour neutraliser la volatilité des bénéfices industriels ou cycliques."
    FUND_VIABILITY = "Validation de la capacité de l'entreprise à générer des flux de trésorerie positifs sur un cycle."

    # Graham
    GRAHAM_EPS = "Bénéfice par action utilisé comme socle de rentabilité."
    GRAHAM_MULT = "Prime de croissance appliquée selon le barème révisé de Graham."
    GRAHAM_IV = "Estimation de la valeur intrinsèque ajustée par le rendement des obligations AAA."

    # Monte Carlo
    MC_CLAMP_NOTE = " (Écrêté de {g_raw:.1%} pour cohérence WACC)"
    MC_INIT = "Calibration des lois normales multivariées.{note}"
    MC_SAMPLING_SUB = "Génération de {count} vecteurs d'inputs via Décomposition de Cholesky."
    MC_SAMPLING_INTERP = "Application des corrélations pour garantir la cohérence économique des scénarios tirés."
    MC_FILTERING = "Élimination des scénarios de divergence pour stabiliser la distribution."
    MC_SENS_NEUTRAL = "Neutre (rho=0)"
    MC_SENS_BASE = "Base (rho=-0.3)"
    MC_SENS_INTERP = "Audit de l'impact de la corrélation sur la stabilité de la valeur médiane."
    MC_STRESS_SUB = "Bear Case = {val:,.2f} {curr}"
    MC_STRESS_INTERP = "Scénario de stress : croissance nulle et risque élevé (Point de rupture)."

    FCFE_LOGIC = (
        "Le modèle FCFE valorise les fonds propres après service de la dette."
        "L'actualisation est effectuée via le coût des fonds propres (Ke)."
    )

    DDM_LOGIC = (
        "Le modèle DDM repose sur la distribution future. Nous utilisons le dividende annuel "
        r"total ($D_0$) comme base, en s'assurant qu'il est couvert par les bénéfices réels."
    )

    RELATIVE_PE = r"Valeur basée sur le multiple P/E médian du secteur ({val:.1f}x)."
    RELATIVE_EBITDA = r"Valeur basée sur le multiple EV/EBITDA médian ({val:.1f}x) après Equity Bridge."
    TRIANGULATION_FINAL = "Valeur hybride obtenue par la moyenne des méthodes relatives."

class CalculationErrors:
    """Messages d'erreurs levés lors des phases de calcul (CalculationError)."""
    CONTRACT_VIOLATION = "Le contrat de sortie n'est pas respecté pour {cls}."
    INVALID_SHARES = "Nombre d'actions en circulation invalide (<= 0)."
    MISSING_BV = "Book Value par action requise et > 0."
    MISSING_EPS_RIM = "EPS requis pour projeter les profits résiduels."
    MISSING_REV = "Chiffre d'affaires (Revenue) requis pour ce modèle."
    INVALID_SHARES_SIMPLE = "Nombre d'actions invalide."
    MISSING_FCF_NORM = "FCF normalisé indisponible (fcf_fundamental_smoothed manquant)."
    NEGATIVE_FCF_NORM = "Flux normalisé négatif : l'entreprise ne génère pas de valeur sur son cycle. La méthode DCF est mathématiquement inapplicable ici."
    MISSING_EPS_GRAHAM = "EPS strictement positif requis pour le modèle de Graham."
    INVALID_AAA = "Le rendement obligataire AAA (Y) doit être > 0."
    MISSING_FCF_STD = "FCF de base indisponible (fcf_last manquant ou nul)."
    INVALID_DISCOUNT_RATE = "Taux d'actualisation invalide : {rate:.2%}"
    CONVERGENCE_IMPOSSIBLE = "Convergence impossible : Taux ({rate:.2%}) <= Croissance ({g:.2%})"
    MANUAL_OVERRIDE_LABEL = "Surcharge manuelle : {wacc:.2%}"
    NEGATIVE_EXIT_MULTIPLE = "Le multiple de sortie ne peut pas être négatif."

    # Sprint 3
    NEGATIVE_FCFE = "Le flux FCFE est négatif. Le modèle est inapplicable ou l'entreprise sur-endettée."
    MISSING_NET_BORROWING = "Donnée de variation de dette (Net Borrowing) manquante pour le FCFE."
    INVALID_DIVIDEND = "Dividende de base nul ou invalide pour le modèle DDM."


class AuditCategories:
    """Catégories de logs d'audit (infra/auditing/)."""
    DATA = "Données"
    MACRO = "Macro"
    SYSTEM = "Système"
    MODEL = "Modèle"


class AuditMessages:
    """Verdicts et diagnostics générés par l'auditeur institutionnel (auditors.py)."""
    # --- Base Auditor (Data & Macro) ---
    BETA_MISSING = "Beta manquant."
    BETA_ATYPICAL = "Beta atypique ({beta:.2f})"
    SOLVENCY_FRAGILE = "Solvabilité fragile (ICR: {icr:.2f} < 1.5)"
    NET_NET_ANOMALY = "Anomalie : Trésorerie > Capitalisation (Situation Net-Net)"
    LIQUIDITY_SMALL_CAP = "Segment Small-Cap : Risque de liquidité et volatilité."

    MACRO_G_RF_DIV = "Divergence macro : g perpétuel ({g:.1%}) > Taux sans risque ({rf:.1%})."
    MACRO_RF_FLOOR = "Paramétrage Rf < 1% : Risque de survalorisation mécanique."

    # --- DCF Auditor ---
    DCF_LEVERAGE_EXCESSIVE = "Levier financier excessif (> 4x EBIT)."
    DCF_REINVESTMENT_DEFICIT = "Déficit de réinvestissement : Capex < 80% des dotations aux amortissements."
    DCF_GROWTH_OUTSIDE_NORMS = "Taux de croissance g ({g:.1%}) hors normes normatives."
    DCF_WACC_FLOOR = "Taux d'actualisation WACC ({wacc:.1%}) excessivement bas."
    DCF_TV_CONCENTRATION = "Concentration de valeur critique : {weight:.1%} repose sur la TV."
    DCF_MATH_INSTABILITY = "Instabilité mathématique : Taux g >= WACC."

    # --- RIM Auditor ---
    RIM_CASH_SECTOR_NOTE = "Note sectorielle : Trésorerie élevée (Standard Bancaire)."
    RIM_PERSISTENCE_EXTREME = "Hypothèse de persistance des surprofits (ω) statistiquement extrême."
    RIM_PAYOUT_EROSION = "Payout Ratio ({payout:.1%}) > 100% : risque d'érosion des fonds propres."
    RIM_SPREAD_ROE_KE_NULL = "Spread ROE-Ke quasi nul : absence de création de richesse additionnelle."
    RIM_PB_RATIO_HIGH = "Ratio P/B élevé ({pb:.1f}x) : le modèle RIM perd en pertinence."

    # --- Graham Auditor ---
    GRAHAM_GROWTH_PRUDENCE = "Taux de croissance g Graham ({g:.1%}) hors périmètre de prudence."

    # --- Sprint 3 ---
    FCFE_HIGH_BORROWING = "Attention : La valorisation repose sur un fort endettement (Net Borrowing élevé)."
    DDM_PAYOUT_UNSUSTAINABLE = "Alerte : Le Payout Ratio > 100% indique un dividende non soutenable."


class AuditEngineTexts:
    """Messages techniques et fallbacks du moteur d'audit (audit_engine.py)."""
    NO_REQUEST_WARNING = "[AuditEngine] ValuationResult sans requête, utilisation du fallback."
    ENGINE_FAILURE_PREFIX = "Audit Engine Failure: {error}"
    AGGREGATION_FORMULA = "Somme(Score * Poids) * Couverture"
    FALLBACK_RATING = "Erreur"