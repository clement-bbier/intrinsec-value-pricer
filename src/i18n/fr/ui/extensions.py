"""
core/i18n/fr/ui/extensions.py
Textes des extensions (SOTP, Backtest).
"""


class SOTPTexts:
    """Labels pour la valorisation par somme des parties."""
    TITLE = "Analyse Sum-Of-The-Parts (SOTP)"
    SEC_SEGMENTS = "#### 1. Definition des Business Units (Segments)"
    SEC_ADJUSTMENTS = "#### 2. Ajustements de Conglomerat"

    LBL_SEGMENT_NAME = "Nom du Segment"
    LBL_SEGMENT_VALUE = "Valeur d'Entreprise (EV)"
    LBL_SEGMENT_METHOD = "Methode de Valorisation"
    LBL_DISCOUNT = "Decote de Conglomerat (%)"
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
    INTERP_CONSOLIDATION = "Valeur d'entreprise consolidee pour {count} segments apres decote."
    STEP_LABEL_CONSOLIDATION = "Consolidation Sum-Of-The-Parts"


class BacktestTexts:
    """Labels pour le module de validation historique."""
    TITLE = "Backtesting & Validation Historique"
    SEC_CONFIG = "#### Configuration de la simulation temporelle"
    SEC_RESULTS = "#### Analyse de la Performance du Modele"

    LBL_PERIODS = "Nombre d'annees a remonter"
    LBL_HIST_IV = "Valeur Intrinseque Historique"
    LBL_REAL_PRICE = "Prix de Marche Reel"
    LBL_ERROR_GAP = "Ecart (Erreur %)"

    METRIC_ALPHA = "Alpha genere (vs Marche)"
    METRIC_ACCURACY = "Precision directionnelle"
    METRIC_MAE = "Erreur Moyenne Absolue (MAE)"

    HELP_BACKTEST = "Compare l'IV calculee sur les bilans passes avec les cours reels de l'epoque."
