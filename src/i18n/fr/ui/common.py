"""
core/i18n/fr/ui/common.py
Textes transverses et métadonnées de base du système.
Note : Version Institutionnelle - Zéro émoji - Terminologie Finance de Marché.
"""
from src.models import VariableSource

class CommonTexts:
    """Référentiel des textes génériques et statuts institutionnels."""

    # --- Métadonnées Application ---
    PROJECT_BADGE = "QUANT ENGINE V1.0"
    APP_TITLE = "Terminal de Valorisation Intrinsèque"
    APP_SUBTITLE = "Ingénierie Financière & Analyse de Risque"
    AUTHOR_NAME = "Clément Barbier"
    DEVELOPED_BY = "Developpé par"

    # --- Boutons et Actions ---
    RUN_BUTTON = "Exécuter l'analyse"
    VALIDATE_BUTTON = "Confirmer les hypothèses"
    DEFAULT_TICKER = "AAPL"

    # --- Valeurs par défaut et Fallbacks ---
    VALUE_NOT_AVAILABLE = "N/A"
    VALUE_AUTO = "MODÈLE"
    UNIT_YEARS = "ans"

    # --- En-têtes de Tableaux ---
    TABLE_HEADER_METRIC = "Indicateur"
    TABLE_HEADER_VALUE = "Valeur"

    # --- Statuts de Calcul (Glass Box) ---
    STATUS_CALCULATED = "Calculé"
    STATUS_AUDITED = "Audité"
    STATUS_ADJUSTED = "Ajusté"

    # --- Labels de Composants Glass Box ---
    STEP_GENERIC_LABEL = "Calcul spécifique"
    DATA_ORIGIN_LABEL = "Provenance des données"
    AUTO_VALUE_IGNORED = "Valeur auto ignorée"
    INTERPRETATION_LABEL = "Note d'analyse"

    CURRENCY = "Devise"

    SOURCE_LABELS = {
        VariableSource.YAHOO_FINANCE: "Yahoo Finance",
        VariableSource.MACRO_PROVIDER: "Données Macro",
        VariableSource.CALCULATED: "Moteur Interne",
        VariableSource.MANUAL_OVERRIDE: "Saisie Manuelle",
    }


class OnboardingTexts:
    """Contenu structurel de la page d'accueil et des piliers."""
    INTRO_INFO = "Solution d'analyse fondamentale quantitative pour l'estimation de la valeur intrinsèque des capitaux propres."
    COMPLIANCE_BODY = (
        "Les modélisations produites reposent sur des algorithmes de flux actualisés (DCF) et de profits résiduels (RIM). "
        "Ces résultats constituent des outils d'aide à la décision et non des recommandations d'investissement."
    )

    # Section : Méthodes
    TITLE_METHODS = "Méthodologies de Valorisation"
    DESC_METHODS = "Architecture multi-modèles pour une triangulation de la valeur :"

    MODEL_DCF_TITLE = "Approche Entité (FCFF)"
    MODEL_DCF_DESC = "Valeur de l'actif économique. Flux opérationnels actualisés au coût moyen pondéré du capital (WACC)."

    MODEL_EQUITY_TITLE = "Approche Actionnaire (FCFE/DDM)"
    MODEL_EQUITY_DESC = "Valeur directe des fonds propres. Actualisation des flux nets de dette au coût des fonds propres (Ke)."

    MODEL_RIM_TITLE = "Revenu Résiduel (Residual Income)"
    MODEL_RIM_DESC = "Méthode comptable avancée. Valorisation basée sur la création de valeur excédentaire par rapport au coût du capital."

    MODEL_GRAHAM_TITLE = "Formule de Benjamin Graham"
    MODEL_GRAHAM_DESC = "Approche sécuritaire reliant la capacité bénéficiaire normalisée aux taux obligataires sans risque."

    # Section : Intelligence de Données
    TITLE_PROCESS = "Acquisition des données"
    STRATEGY_ACQUISITION_TITLE = "Extraction Automatisée"
    STRATEGY_ACQUISITION_DESC = "Récupération des états financiers et données macro via fournisseurs de données institutionnels."

    STRATEGY_MANUAL_TITLE = "Mode Ingénierie (Manual Override)"
    STRATEGY_MANUAL_DESC = "Permet l'ajustement granulaire des hypothèses de croissance, de marge et de structure du capital."

    STRATEGY_FALLBACK_TITLE = "Données de Substitution"
    STRATEGY_FALLBACK_DESC = "Recours aux benchmarks sectoriels par défaut en cas de données historiques incomplètes ou aberrantes. (Fallback)"

    # Section : Architecture des 5 Piliers
    TITLE_RESULTS = "Organisation des Résultats"
    DESC_RESULTS = "Les résultats sont segmentés par domaines d'analyse financière :"
    # Pilier 1 - Configuration
    TAB_1_TITLE = "Configuration & Macro"
    TAB_1_DESC = "Audit des variables d'entrée et synchronisation du contexte macroéconomique."
    # Pilier 2 - Glass Box
    TAB_2_TITLE = "Logique de Calcul"
    TAB_2_DESC = "Décomposition des étapes mathématiques et affichage des formules LaTeX."
    # Pilier 3 - Audit
    TAB_3_TITLE = "Audit des Données & Cohérence"
    TAB_3_DESC = "Évaluation de la fiabilité du modèle et détection d'anomalies."
    # Pilier 4 - Risque
    TAB_4_TITLE = "Ingénierie des Risques & Sensibilité"
    TAB_4_DESC = "Analyse stochastique (Monte Carlo), matrices de sensibilité et backtesting historique pour valider la précision du modèle."
    # Pilier 5 - Marché
    TAB_5_TITLE = "Triangulation de Marché & SOTP"
    TAB_5_DESC = "Étude comparative des multiples boursiers sectoriels et décomposition segmentée (SOTP) pour une validation extrinsèque."

    # Section : Diagnostics
    DIAGNOSTIC_HEADER = "Système de diagnostics"
    DIAGNOSTIC_BLOQUANT = "ERREUR : Données financières incomplètes ou incohérentes."
    DIAGNOSTIC_WARN = "AVERTISSEMENT : Hypothèses en dehors des normes historiques."
    DIAGNOSTIC_INFO = "INFORMATION : Moteurs de calcul opérationnels."


class FeedbackMessages:
    """Messages système et alertes de validation."""
    TICKER_REQUIRED_SIDEBAR = "Identifiant (Ticker) requis pour initialiser l'analyse."
    TICKER_INVALID = "Symbole boursier non identifié par le fournisseur de données."
    CALCULATION_SUCCESS = "Valorisation terminée avec succès."


class LegalTexts:
    """Textes juridiques et conformité."""
    COMPLIANCE_BODY = "Les simulations générées par ce terminal reposent sur des modèles mathématiques automatisés et ne constituent pas un conseil en investissement professionnel."
    COMPLIANCE_TITLE = "Avertissement Légal"
    DISCLAIMER = "Document à usage strictement professionnel et analytique."


class TooltipsTexts:
    """Aide contextuelle pour les concepts financiers (Indispensable pour corriger l'ImportError)."""
    MARKET_CAP_HELP = "Capitalisation boursière à la date d'analyse."
    WACC_HELP = "Coût Moyen Pondéré du Capital (WACC) utilisé pour actualiser les flux FCFF."
    KE_HELP = "Coût des fonds propres (Ke) utilisé pour actualiser les flux FCFE ou DDM."
    GROWTH_G = "Taux de croissance perpétuelle (g) utilisé pour la valeur terminale."
    SBC_HELP = "Stock-Based Compensation : ajustement de la dilution liée aux attributions d'actions au management."
    TERMINAL_VALUE = "Valeur de l'entreprise au-delà de l'horizon de prévision explicite (Modèle de Gordon-Shapiro)."
    MARGIN_SAFETY = "Décote appliquée entre la valeur intrinsèque et le cours actuel pour absorber l'incertitude."


class UIMessages:
    """Messages d'information et d'erreur de l'interface utilisateur."""
    BACKTEST_INSUFFICIENT_DATA = "Données historiques insuffisantes pour le backtesting."
    TECHNICAL_DETAILS = "Détails techniques"
    NO_VALID_PERIOD_DATA = "Historique financier insuffisant pour établir une tendance robuste."
    CHART_UNAVAILABLE = "Données insuffisantes pour la génération graphique."
    NO_CALCULATION_STEPS = "Aucune trace de calcul disponible pour ce modèle."
    NO_DETAILED_TESTS = "Aucun test d'intégrité supplémentaire requis."
    NO_TABS_TO_DISPLAY = "Initialisation de l'orchestrateur..."

    # PDF / Export
    DOWNLOAD_PDF_BTN = "Générer le Rapport d'Analyse (PDF)"
    GENERATING_PDF = "Compilation du rapport institutionnel..."
    PDF_SUCCESS = "Le rapport est prêt pour l'archivage."
    PDF_UNAVAILABLE = "Module d'exportation non détecté sur l'instance courante."
    PDF_ERROR = "Erreur lors de la génération du flux PDF."

