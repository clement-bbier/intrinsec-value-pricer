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

class FeedbackMessages:
    """Messages système et alertes de validation."""
    TICKER_REQUIRED_SIDEBAR = "Veuillez saisir un ticker dans la barre latérale."
    TICKER_INVALID = "Veuillez saisir un ticker valide."