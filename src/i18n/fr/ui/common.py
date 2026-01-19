"""
core/i18n/fr/ui/common.py
Textes communs et generiques de l'interface.
"""


class CommonTexts:
    """Textes transverses et metadonnees de base."""
    APP_TITLE = "Analyse de la valeur intrinsèque"
    PROJECT_BADGE = "Projet Personnel Public"
    AUTHOR_NAME = "Clement Barbier"
    DEVELOPED_BY = "Developed by"
    RUN_BUTTON = "Lancer le calcul"
    DEFAULT_TICKER = "AAPL"


class OnboardingTexts:
    """Contenu pedagogique de la page d'accueil."""
    INTRO_INFO = "Estimez la valeur intrinseque d'une entreprise et comparez-la a son prix de marche."

    TITLE_A = "A. Selection de la Methodologie"
    DESC_A = (
        "Chaque methodologie vise a modeliser la realite economique d'une entreprise a un instant donne, "
        "conditionnellement a un ensemble d'hypotheses financieres."
    )

    MODEL_DCF_TITLE = "**Modeles DCF (Approche Entite)**"
    MODEL_DCF_DESC = (
        "FCFF (Firm) : Standard Damodaran actualisant les flux avant service de la dette via le WACC."
    )

    MODEL_EQUITY_TITLE = "**Modeles Direct Equity (Approche Actionnaire)**"
    MODEL_EQUITY_DESC = (
        "FCFE (Equity) : Actualise le flux residuel apres service de la dette au cout des fonds propres (Ke)."
    )

    MODEL_RIM_TITLE = "**Residual Income (RIM)**"
    MODEL_RIM_DESC = (
        "Standard academique (Penman/Ohlson) pour les Banques et Assurances dont la valeur repose sur l'actif net."
    )

    MODEL_GRAHAM_TITLE = "**Modele de Graham**"
    MODEL_GRAHAM_DESC = (
        "Estimation Value (1974 Revised) liant la capacite beneficiaire actuelle aux conditions de credit AAA."
    )

    TITLE_B = "B. Pilotage & Gestion du Risque"
    PILOTAGE_TITLE = "**Pilotage des Donnees (Auto vs Expert)**"
    PILOTAGE_DESC = "Le mode Auto extrait les donnees de Yahoo Finance. Le mode Expert offre une autonomie totale."
    MC_TITLE = "**Analyse de Risque Hybride**"
    MC_DESC = "Combinez l'analyse Probabiliste (Monte Carlo) et l'analyse Deterministe (Bull/Base/Bear)."

    TITLE_C = "C. Gouvernance & Transparence"
    AUDIT_TITLE = "**Audit Reliability Score**"
    AUDIT_DESC = "Indicateur mesurant la coherence des inputs."
    TRACE_TITLE = "**Valuation Traceability**"
    TRACE_DESC = "Chaque etape est detaillee dans l'onglet Calcul."

    DIAGNOSTIC_HEADER = "Systeme de Diagnostic :"
    DIAG_BLOQUANT = "**Bloquant** : Erreur de donnee ou parametre manquant."
    DIAG_WARN = "**Avertissement** : Hypothese divergente (ex: g > WACC)."
    DIAG_INFO = "**Information** : Note ou recommandation."


class FeedbackMessages:
    """Messages systeme et alertes de validation."""
    TICKER_REQUIRED_SIDEBAR = "Veuillez saisir un ticker dans la barre laterale."
    TICKER_INVALID = "Veuillez saisir un ticker valide."


class LegalTexts:
    """Textes juridiques, avertissements et notes de conformite."""
    COMPLIANCE_TITLE = "Note de conformité"
    COMPLIANCE_BODY = (
        "Les valorisations produites par cette application sont des projections basées sur des modèles de flux actualisés et de profits résiduels." 
        "Elles constituent un cadre d'analyse fondamentale et ne doivent pas être interprétées comme des recommandations d'investissement."
    )


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
