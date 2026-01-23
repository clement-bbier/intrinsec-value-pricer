"""
core/i18n/fr/ui/common.py
Textes communs et generiques de l'interface.
"""


class CommonTexts:
    """Textes transverses et metadonnees de base."""
    APP_TITLE = "Analyse de la valeur intrinsèque"
    AUTHOR_NAME = "Clément Barbier"
    DEVELOPED_BY = "Développé par"
    RUN_BUTTON = "Lancer le calcul"
    DEFAULT_TICKER = "AAPL"


class OnboardingTexts:
    """Contenu pédagogique de la page d'accueil."""
    # Accroche
    INTRO_INFO = "Plateforme d'analyse fondamentale automatisée pour l'estimation de la valeur intrinsèque."
    COMPLIANCE_BODY = (
        "Les valorisations produites par cette application sont des projections basées sur des modèles de flux actualisés et de profits résiduels."
        "Elles constituent une d'analyse fondamentale et ne doivent pas être interprétées comme des recommandations d'investissement."
    )

    # Section : Méthodes de Valorisation
    TITLE_METHODS = "Méthode de valorisation"
    DESC_METHODS = (
        "Modélisation à partir de 4 approches :"
    )
    MODEL_DCF_TITLE = "**Approche Entité (DCF)**"
    MODEL_DCF_DESC = (
        "Valorisation de l'actif économique total. Flux opérationnels actualisés au coût moyen du capital."
    )
    MODEL_EQUITY_TITLE = "**Approche Actionnaire (FCFE/DDM)**"
    MODEL_EQUITY_DESC = (
        "Estimation directe des fonds propres. Actualise les flux résiduels ou dividendes au coût des fonds propres."
    )
    MODEL_RIM_TITLE = "**Revenu Résiduel (RIM)**"
    MODEL_RIM_DESC = (
        "Standard pour les Banques et Assurances. Valorise l'actif net augmenté des profits excédant le coût du capital."
    )
    MODEL_GRAHAM_TITLE = "**Valeur Intrinsèque de Graham**"
    MODEL_GRAHAM_DESC = (
        "Approche reliant la puissance bénéficiaire aux taux obligataires pour une marge de sécurité réelle."
    )

    # Section : Intelligence de Données (Processus)
    TITLE_PROCESS = "Flux de données selon le mode (Standard / Approfondi)"
    STRATEGY_ACQUISITION_TITLE = "**Paramétrage Automatique (Standard)**"
    STRATEGY_ACQUISITION_DESC = (
        "Extraction des données pour les chaînes de calculs à partir de Yahoo Finance "
        "(possibilité d'utiliser d'autres providers en modifiant le code)."
    )
    STRATEGY_MANUAL_TITLE = "**Paramétrage Manuel (Approfondi)**"
    STRATEGY_MANUAL_DESC = (
        "Possibilité de surcharger les données d'entrées avec ses propres hypothèses "
        "pour simuler des scénarios spécifiques à partir des chaînes de calcul."
    )
    STRATEGY_FALLBACK_TITLE = "**Continuité (Fallback)**"
    STRATEGY_FALLBACK_DESC = (
        "En cas de donnée manquante, l'application utilise des algorithmes de secours "
        "(moyennes sectorielles, valeurs par défaut, ...) pour garantir la production d'une valeur."
    )

    # Section : Résultats
    TITLE_RESULTS = "Architecture des Résultats"
    DESC_RESULTS = "Résultats segmentée en 5 piliers différents :"
    TAB_1_TITLE = "**1. Configuration**"
    TAB_1_DESC = "Audit des hypothèses sources et récapitulatif des données utilisées."
    TAB_2_TITLE = "**2. Trace Mathématique**"
    TAB_2_DESC = "Détail intégral de chaque étape de calculs intermédiaires."
    TAB_3_TITLE = "**3. Rapport d'Audit**"
    TAB_3_DESC = "Score de fiabilité et détection des anomalies de modélisation."
    TAB_4_TITLE = "**4. Analyse de Marché (mode Approfondi)**"
    TAB_4_DESC = "Triangulation par multiples sectoriels et comparaison directe par pairs."
    TAB_5_TITLE = "**5. Ingénierie du Risque (mode Approfondi)**"
    TAB_5_DESC = "Simulations de Monte Carlo et stress-tests pour quantifier l'incertitude."

    # Section : Diagnostics
    DIAGNOSTIC_HEADER = "**Système de Diagnostics**"
    DIAG_BLOQUANT = "**Bloquant** : Erreur de donnée ou paramètre manquant."
    DIAG_WARN = "**Avertissement** : Hypothèse divergente (ex: g > WACC)."
    DIAG_INFO = "**Information** : Note ou recommandation."


class FeedbackMessages:
    """Messages systeme et alertes de validation."""
    TICKER_REQUIRED_SIDEBAR = "Veuillez saisir un ticker dans la barre latérale."
    TICKER_INVALID = "Veuillez saisir un ticker valide."


class LegalTexts:
    """Textes juridiques, avertissements et notes de conformite."""
    COMPLIANCE_TITLE = "Note de conformité"

class TooltipsTexts:
    """Infobulles et aides contextuelles pour le mode Expert."""
    pass

class UIMessages:
    """Messages d'information et d'erreur de l'interface utilisateur."""

    # Messages d'information
    NO_VALID_PERIOD_DATA = "Aucune donnée de période valide trouvée."
    CHART_UNAVAILABLE = "Graphique non disponible (installer altair pour visualiser la distribution)."
    NO_CALCULATION_STEPS = "Aucune étape de calcul disponible."
    NO_DETAILED_TESTS = "Aucun test détaillé disponible."
    NO_TABS_TO_DISPLAY = "Aucun onglet à afficher."

    # Messages PDF
    DOWNLOAD_PDF_BTN = "Télécharger le Rapport Pitchbook (PDF)"
    GENERATING_PDF = "Génération du Pitchbook en cours..."
    PDF_SUCCESS = "Pitchbook généré avec succès !"
    PDF_UNAVAILABLE = "Export PDF indisponible (fpdf2 non installé)"
    PDF_ERROR = "Erreur lors de la génération du PDF :"
