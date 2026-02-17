"""
core/i18n/fr/ui/sidebar.py
Textes de la barre latérale.
"""


class SidebarTexts:
    """Labels et en-têtes de la barre latérale."""

    ANALYSIS = "Niveau d'analyse"
    LANGUAGE = "Langues"
    TITLE = "Paramétrage de l'analyse"

    SEC_1_COMPANY = "Séléction de la cible"
    SEC_2_METHODOLOGY = "Moteur de valorisation"
    SEC_3_SOURCE = "Source des données"
    SEC_4_HORIZON = "Paramètres temporels"

    HELP_TICKER_LABEL = "Saisissez un code ticker Yahoo Finance valide (par exemple AAPL, MSFT, ^GSPC)"

    BTN_TICKER_CONFIRM = "Confirmer le ticker"

    TICKER_LABEL = "Ticker (Yahoo Finance)"
    METHOD_LABEL = "Sélection du modèle"
    STRATEGY_LABEL = "Mode d'analyse"
    YEARS_LABEL = "Période de projection (n)"

    SOURCE_AUTO = "Standard (via Yahoo Finance)"
    SOURCE_EXPERT = "Approfondi (Paramétrage Manuel)"
    SOURCE_OPTIONS = [SOURCE_AUTO, SOURCE_EXPERT]

    SETTINGS = "Mode"
    DATA_SOURCE = "Source de données"
