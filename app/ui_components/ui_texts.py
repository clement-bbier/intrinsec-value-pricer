"""
app/ui_components/ui_texts.py
CENTRALISATION INTÉGRALE DES TEXTES — PROJET IVP 2026
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

    MODEL_DCF_TITLE = "**Modèles DCF (FCFF)**"
    MODEL_DCF_DESC = (
        "• <b>Standard</b> : Approche de Damodaran pour entreprises matures aux flux de trésorerie prévisibles. <br>"
        "• <b>Fundamental</b> : Adapté aux cycliques ; utilise des flux normalisés pour gommer la volatilité d'un cycle économique complet.<br>"
        "• <b>Growth</b> : Modèle \"Revenue-Driven\" pour la Tech ; simule la convergence des marges vers un profil normatif à l'équilibre."
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
    """Titres, Sections et Labels spécifiques aux Terminaux Experts."""
    # Titres des terminaux
    TITLE_FCFF_STD = "Terminal Expert : FCFF Standard"
    TITLE_FCFF_FUND = "Terminal Expert : FCFF Fundamental"
    TITLE_FCFF_GROWTH = "Terminal Expert : FCFF Growth"
    TITLE_RIM = "Terminal Expert : RIM"
    TITLE_GRAHAM = "Terminal Expert : Graham"

    # Sections communes
    SEC_1_FCF_STD = "#### 1. Flux de trésorerie de base ($FCF_0$)"
    SEC_1_FCF_NORM = "#### 1. Flux normalisé de base ($FCF_{norm}$)"
    SEC_1_REV_BASE = "#### 1. Chiffre d'Affaires de base ($Rev_0$)"
    SEC_1_RIM_BASE = "#### 1. Valeur Comptable ($BV_0$) & Profits ($NI_t$)"
    SEC_1_GRAHAM_BASE = "#### 1. Bénéfices ($EPS$) & Croissance attendue ($g$)"

    SEC_2_PROJ = "#### 2. Phase de croissance explicite"
    SEC_2_PROJ_FUND = "#### 2. Croissance moyenne de cycle"
    SEC_2_PROJ_GROWTH = "#### 2. Horizon & Convergence des Marges"
    SEC_2_PROJ_RIM = "#### 2. Horizon & Croissance des profits"
    SEC_2_GRAHAM = "#### 2. Conditions de Marché AAA & Fiscalité"

    SEC_3_CAPITAL = "#### 3. Coût du Capital"
    SEC_4_TERMINAL = "#### 4. Valeur de continuation"
    SEC_5_BRIDGE = "#### 5. Ajustements de structure (Equity Bridge)"
    SEC_6_MC = "#### 6. Simulation Probabiliste (Incertitude)"

    # Labels des Inputs
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
    INP_DEBT = "Dette Totale (Vide = Auto Yahoo)"
    INP_CASH = "Trésorerie (Vide = Auto Yahoo)"
    INP_SHARES = "Actions en circulation (Vide = Auto Yahoo)"
    INP_MINORITIES = "Intérêts Minoritaires (Vide = Auto Yahoo)"
    INP_PENSIONS = "Provisions Pensions (Vide = Auto Yahoo)"

    # Labels Interactifs
    RADIO_TV_METHOD = "Modèle de sortie"
    TV_GORDON = "Croissance Perpétuelle (Gordon)"
    TV_EXIT = "Multiple de Sortie"
    MC_CALIBRATION = "Calibration des Volatilités (Décimales, Vide = Auto Yahoo) :"
    MC_ITERATIONS = "Itérations"
    MC_VOL_BETA = "Vol. β"
    MC_VOL_G = "Vol. g"
    MC_VOL_OMEGA = "Vol. ω"
    MC_VOL_GN = "Vol. gn"

    # Horizon Sliders
    SLIDER_PROJ_YEARS = "Horizon de projection (t années)"
    SLIDER_CYCLE_YEARS = "Horizon du cycle (t années)"
    SLIDER_PROJ_T = "Années de projection (t)"
    SLIDER_PROJ_N = "Années de projection (n)"

    # Boutons (Templates)
    BTN_VALUATE_STD = "Lancer la valorisation {ticker}"
    BTN_VALUATE_FUND = "Lancer la valorisation Fondamentale ({ticker})"
    BTN_VALUATE_GROWTH = "Lancer l'analyse Growth : {ticker}"
    BTN_VALUATE_RIM = "Lancer la valorisation RIM : {ticker}"
    BTN_VALUATE_GRAHAM = "Calculer la valeur Graham : {ticker}"

class TooltipsTexts:
    """Infobulles et aides contextuelles pour le mode Expert."""
    # Note: On pourra ici centraliser les aides DAMODARAN plus tard
    pass

class FeedbackMessages:
    """Messages système et alertes de validation."""
    TICKER_REQUIRED_SIDEBAR = "Veuillez saisir un ticker dans la barre latérale."
    TICKER_INVALID = "Veuillez saisir un ticker valide."

# --- NOUVELLE CLASSE POUR LE DESIGN SYSTEM (EXTRACTION style_system.py) ---

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
    SUB_MARKET = "##### Marché & Capitalisation"
    LABEL_PRICE = "Cours Actuel"
    LABEL_MCAP = "Capitalisation Boursière"
    LABEL_BVPS = "Book Value / Action"

    SUB_CAPITAL = "##### Structure du Capital"
    LABEL_DEBT = "Dette Totale"
    LABEL_CASH = "Trésorerie"
    LABEL_NET_DEBT = "Dette Nette"
    LABEL_INTEREST = "Charges d'Intérêts"

    SUB_PERF = "##### Performance Opérationnelle (TTM)"
    LABEL_REV = "Chiffre d'Affaires"
    LABEL_EBIT = "EBIT"
    LABEL_NI = "Résultat Net"
    LABEL_EPS = "BPA (EPS)"

    SUB_CASH = "##### Flux de Trésorerie"
    LABEL_FCF_LAST = "FCF (Dernier)"
    LABEL_CAPEX = "CapEx"
    LABEL_DA = "D&A"

    # Paramètres Modèle
    SUB_RATES = "##### Taux et Primes de Risque"
    LABEL_RF = "Taux Sans Risque (Rf)"
    LABEL_MRP = "Prime de Risque (MRP)"
    LABEL_KD = "Coût de la Dette (Kd)"
    LABEL_TAX = "Taux d'Imposition (τ)"

    SUB_GROWTH = "##### Croissance et Horizon"
    LABEL_G = "Taux de Croissance (g)"
    LABEL_GN = "Croissance Perpétuelle (gn)"
    LABEL_HORIZON = "Horizon de Projection"
    UNIT_YEARS = "ans"

    SUB_CALCULATED = "##### Métriques Calculées"
    LABEL_WACC = "WACC"
    LABEL_KE = "Coût des Fonds Propres (Ke)"
    LABEL_METHOD = "Méthode de Valorisation"

    SUB_TV = "##### Valeur Terminale"
    LABEL_TV_METHOD = "Méthode TV"
    LABEL_EXIT_M = "Multiple de Sortie"

    # Preuve de Calcul
    STEP_LABEL = "Étape {index}"
    FORMULA_THEORY = "Formule Théorique"
    FORMULA_DATA_SOURCE = "*Donnée source*"
    APP_NUMERIC = "Application Numérique"
    VALUE_UNIT = "Valeur ({unit})"
    STEP_VALIDATED = "**Validée**"
    NOTE_ANALYSIS = "Note d'analyse"

    # Résumé Exécutif
    EXEC_TITLE = "Dossier de Valorisation : {name} ({ticker})"
    EXEC_CONFIDENCE = "Indice de Confiance"


class AuditTexts:
    """Textes liés au rapport d'audit et à la simulation Monte Carlo."""
    # Rapport d'Audit
    NO_REPORT = "Aucun rapport d'audit généré pour cette simulation."
    GLOBAL_SCORE = "### Score d'Audit Global : {score:.1f} / 100"
    RATING_SCORE = "Rating Score"
    COVERAGE = "Couverture"
    CHECK_TABLE = "#### Table de Vérification des Invariants"

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

    # --- DCF ---
    DCF_FCF_BASE_L = "Ancrage FCF₀"
    DCF_FCF_BASE_D = "Flux de trésorerie disponible de départ pour la projection."

    DCF_FCF_NORM_L = "Ancrage FCF Normalisé"
    DCF_FCF_NORM_D = "Flux lissé sur un cycle complet pour neutraliser la volatilité."

    DCF_STABILITY_L = "Contrôle de Viabilité Financière"
    DCF_STABILITY_D = "Validation de la capacité à générer des flux positifs."

    DCF_WACC_L = "Coût Moyen Pondéré du Capital"
    DCF_WACC_D = "Taux d'actualisation reflétant le coût du capital de l'entreprise."

    DCF_PROJ_L = "Projection des Flux"
    DCF_PROJ_D = "Projection des flux sur l'horizon explicite."

    DCF_TV_GORDON_L = "Valeur Terminale (Gordon)"
    DCF_TV_GORDON_D = "Valeur de l'entreprise au-delà de la période explicite (modèle de Gordon)."

    DCF_TV_MULT_L = "Valeur Terminale (Multiple)"
    DCF_TV_MULT_D = "Valeur terminale basée sur un multiple de sortie."

    DCF_EV_L = "Valeur d'Entreprise (EV)"
    DCF_EV_D = "Somme actualisée des flux et de la valeur terminale."

    DCF_BRIDGE_L = "Pont de Valeur (Equity Bridge)"
    DCF_BRIDGE_D = "Ajustement de la structure financière pour obtenir la valeur des fonds propres."

    DCF_IV_L = "Valeur Intrinsèque par Action"
    DCF_IV_D = "Estimation de la valeur réelle d'une action."

    # --- GROWTH ---
    GROWTH_REV_BASE_L = "Chiffre d'Affaires de Base"
    GROWTH_REV_BASE_D = "Point de départ du modèle basé sur le chiffre d'affaires TTM."

    GROWTH_MARGIN_L = "Convergence des Marges"
    GROWTH_MARGIN_D = "Modélisation de l'amélioration opérationnelle vers une marge FCF normative."

    # --- RIM ---
    RIM_BV_L = "Actif Net Comptable Initial"
    RIM_BV_D = "Valeur comptable par action au départ du modèle."

    RIM_KE_L = "Coût des Fonds Propres (Ke)"
    RIM_KE_D = "Coût des capitaux propres via le CAPM."

    RIM_RI_L = "Calcul des Surprofits (RI)"
    RIM_RI_D = "Profit résiduel après rémunération des fonds propres."

    RIM_TV_L = "Valeur Terminale (Persistance ω)"
    RIM_TV_D = "Estimation de la persistance des surprofits selon le modèle d'Ohlson."

    RIM_IV_L = "Valeur Intrinsèque RIM"
    RIM_IV_D = "Valeur totale issue du modèle Residual Income."

    RIM_PAYOUT_L = "Politique de Distribution"
    RIM_PAYOUT_D = "Ratio de distribution des dividendes."

    RIM_EPS_PROJ_L = "Projection des Bénéfices"
    RIM_EPS_PROJ_D = "Projection des bénéfices par action."

    # --- GRAHAM ---
    GRAHAM_EPS_L = "BPA Normalisé (EPS)"
    GRAHAM_EPS_D = "Bénéfice par action utilisé comme socle de rentabilité."

    GRAHAM_MULT_L = "Multiplicateur de Croissance"
    GRAHAM_MULT_D = "Prime de croissance appliquée selon le barème révisé de Graham."

    GRAHAM_IV_L = "Valeur Graham 1974"
    GRAHAM_IV_D = "Estimation de la valeur intrinsèque ajustée par le rendement AAA."

    # --- MC ---
    MC_INIT_L = "Initialisation du Moteur Stochastique"
    MC_INIT_D = "Calibration des lois normales multivariées."

    MC_SAMP_L = "Simulation Multivariée"
    MC_SAMP_D = "Génération des vecteurs d'inputs via décomposition de Cholesky."

    MC_FILT_L = "Contrôle de Convergence"
    MC_FILT_D = "Élimination des scénarios de divergence."

    MC_MED_L = "Valeur Probabiliste Centrale (P50)"
    MC_MED_D = "Valeur intrinsèque centrale de la distribution stochastique."

    MC_SENS_L = "Sensibilité à la Corrélation (ρ)"
    MC_SENS_D = "Impact de la corrélation sur la stabilité de la valeur médiane."

    MC_STRESS_L = "Stress Test (Bear Case)"
    MC_STRESS_D = "Scénario de stress avec croissance nulle et risque élevé."

    # --- AUDIT ---
    AUDIT_BETA_L = "Cohérence du Beta"
    AUDIT_BETA_D = "Vérifie que le beta est dans une plage économiquement réaliste."

    AUDIT_ICR_L = "Solvabilité (ICR)"
    AUDIT_ICR_D = "Évalue la capacité à honorer la charge de la dette."

    AUDIT_CASH_L = "Position Net-Net"
    AUDIT_CASH_D = "Vérifie si la trésorerie excède la valorisation boursière."

    AUDIT_LIQ_L = "Taille de Marché"
    AUDIT_LIQ_D = "Identifie les risques de liquidité sur les small-caps."

    AUDIT_LEV_L = "Levier Financier"
    AUDIT_LEV_D = "Mesure l'endettement relatif à la capacité bénéficiaire."

    AUDIT_MACRO_L = "Convergence Macro"
    AUDIT_MACRO_D = "Vérifie la cohérence entre croissance perpétuelle et taux sans risque."

    AUDIT_RF_L = "Plancher du Taux Sans Risque"
    AUDIT_RF_D = "Alerte si le Rf est anormalement bas."

    AUDIT_REINV_L = "Taux de Renouvellement Industriel"
    AUDIT_REINV_D = "Mesure la capacité à maintenir l'outil de production."

    AUDIT_GLIM_L = "Borne de Croissance"
    AUDIT_GLIM_D = "Alerte si le taux de croissance est hors normes."

    AUDIT_PAY_L = "Soutenabilité de la Distribution"
    AUDIT_PAY_D = "Vérifie que la politique de dividende ne décapitalise pas l'entreprise."

    AUDIT_WACC_L = "Plancher du WACC"
    AUDIT_WACC_D = "Alerte si le taux d'actualisation est excessivement bas."

    AUDIT_TVC_L = "Concentration Valeur Terminale"
    AUDIT_TVC_D = "Mesure la dépendance du modèle à la valeur terminale."

    AUDIT_G_WACC_L = "Stabilité de Convergence Gordon"
    AUDIT_G_WACC_D = "Assure la convergence mathématique du modèle de Gordon."

    AUDIT_SPREAD_L = "Spread de Création de Valeur"
    AUDIT_SPREAD_D = "Mesure la création de richesse additionnelle."

    AUDIT_PB_L = "Pertinence RIM (P/B)"
    AUDIT_PB_D = "Indicateur de pertinence pour le modèle Residual Income."

    AUDIT_UNK_L = "Test Spécifique"
    AUDIT_UNK_D = "Test non référencé dans le registre."