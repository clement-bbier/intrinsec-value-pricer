"""
core/i18n/fr/ui/sidebar.py
Textes de la barre laterale.
"""


class SidebarTexts:
    """Labels et en-tetes de la barre laterale."""
    SEC_1_COMPANY = "1. Choix de l'entreprise"
    SEC_2_METHODOLOGY = "2. Choix de la methodologie"
    SEC_3_SOURCE = "3. Source des donnees"
    SEC_4_HORIZON = "4. Horizon"
    SEC_5_RISK = "5. Analyse de Risque"

    TICKER_LABEL = "Ticker (Yahoo Finance)"
    METHOD_LABEL = "Methode de Valorisation"
    STRATEGY_LABEL = "Strategie de pilotage"
    YEARS_LABEL = "Annees de projection"
    MC_TOGGLE_LABEL = "Activer Monte Carlo"
    MC_SIMS_LABEL = "Simulations"

    SOURCE_AUTO = "Auto (Yahoo Finance)"
    SOURCE_EXPERT = "Expert (Surcharge Manuelle)"
    SOURCE_OPTIONS = [SOURCE_AUTO, SOURCE_EXPERT]
