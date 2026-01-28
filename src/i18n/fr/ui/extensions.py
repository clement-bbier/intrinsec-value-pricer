"""
core/i18n/fr/ui/extensions.py
Textes des extensions (SOTP, Backtest).
"""


class SOTPTexts:
    """Labels pour la valorisation par somme des parties."""
    LABEL_HOLDING_DISCOUNT = "Décote holding"
    TITLE = "Analyse Sum-Of-The-Parts (SOTP)"
    SEC_SEGMENTS = "#### 1. Definition des Business Units (Segments)"
    SEC_ADJUSTMENTS = "#### 2. Ajustements de Conglomérat"

    LBL_SEGMENT_NAME = "Nom du Segment"
    LBL_SEGMENT_VALUE = "Valeur d'Entreprise (EV)"
    LBL_SEGMENT_METHOD = "Methode de Valorisation"
    LBL_DISCOUNT = "Décote de Conglomérat (%)"
    LBL_ENTERPRISE_VALUE = "Valeur d'Entreprise (EV)"
    LBL_EQUITY_VALUE = "Valeur des Fonds Propres"
    LBL_BU_DETAILS = "Detail des Business Units"
    LBL_SEGMENT_COUNT = "Nombre de segments"
    LBL_RAW_EV_SUM = "Somme brute EV"
    LBL_SEGMENT_REVENUE = "Revenu du Segment"

    METHOD_DCF = "DCF (Flux actualises)"
    METHOD_MULT = "Multiples sectoriels"
    METHOD_ASSET = "Valeur d'actif (Net Book Value)"

    HELP_SOTP = "La valeur totale est la somme des EV de chaque segment moins la dette nette globale."
    DESC_WATERFALL = "Decomposition de la valeur par Business Unit"
    INTERP_CONSOLIDATION = "Valeur d'entreprise consolidée pour {count} segments apres décote."
    STEP_LABEL_CONSOLIDATION = "Consolidation Sum-Of-The-Parts"
    DESC_SOTP_VALUATION = "Segmentation de la valeur d'entreprise par divisions opérationnelles."

class BacktestTexts:
    LABEL = "Backtest"
    TITLE = "Validation Historique (Backtest)"
    HELP_BACKTEST = "Analyse rétrospective comparant la valeur intrinsèque (IV) calculée par le modèle aux cours de clôture historiques."
    LBL_PERIODS = "Périodes testées"
    METRIC_ACCURACY = "Précision"
    SEC_RESULTS = "Détail des séquences historiques"
    LBL_DATE = "Période"
    LBL_HIST_IV = "IV Historique"
    LBL_REAL_PRICE = "Prix Réel"
    LBL_ERROR_GAP = "Écart (Gap)"
    GRADE_A = "Grade A"
    GRADE_B = "Grade B"


class SOTPResultTexts:
    """Textes pour l'affichage des résultats Sum-of-the-Parts (SOTP)."""

    # Titres et sous-titres
    TITLE_SEGMENTATION = "VALORISATION PAR SEGMENTS"
    CAPTION_SEGMENTATION = "Somme des parties avec multiples sectoriels"

    # En-têtes de colonnes du tableau
    COL_SEGMENT = "Segment"
    COL_REVENUE = "Revenu"
    COL_MULTIPLE = "Multiple"
    COL_VALUE = "Valeur"
    COL_CONTRIBUTION = "Contribution"

    # Métriques de synthèse
    METRIC_GROSS_VALUE = "Valeur Brute SOTP"
    METRIC_HOLDING_DISCOUNT = "Décote Holding"
    METRIC_NET_VALUE = "Valeur Nette SOTP"

    LBL_SEGMENT_NAME = "Nom du Segment"
    LBL_SEGMENT_VALUE = "Valeur d'Entreprise (EV)"
    LBL_SEGMENT_REVENUE = "Chiffre d'Affaires"
    LBL_SEGMENT_METHOD = "Méthode"
    LBL_SEGMENT_CONTRIBUTION = "Contribution"


class ScenarioTexts:
    """Textes pour l'affichage des scénarios déterministes."""

    # Titres et sous-titres
    TITLE_ANALYSIS = "ANALYSE DE SCÉNARIOS"
    CAPTION_ANALYSIS = "Valorisation sous différentes hypothèses de croissance"

    # En-têtes de colonnes du tableau
    COL_SCENARIO = "Scénario"
    COL_PROBABILITY = "Probabilité"
    COL_GROWTH = "Croissance"
    COL_MARGIN_FCF = "Marge FCF"
    COL_VALUE_PER_SHARE = "Valeur/Action"
    COL_UPSIDE = "Upside"

    # Métriques de synthèse
    METRIC_WEIGHTED_VALUE = "Valeur Pondérée"
    METRIC_WEIGHTED_UPSIDE = "Upside Pondéré"
