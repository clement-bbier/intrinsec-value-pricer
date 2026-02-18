"""
src/i18n/fr/backend/models.py
Backend constants for Data Models and Validation logic.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelValidationTexts:
    """Error messages related to model integrity and validation."""

    SCENARIO_PROBABILITIES_SUM_ERROR: str = "La somme des probabilités (Bull+Base+Bear) doit être égale à 1.0."


MODEL_VALIDATION_TEXTS = ModelValidationTexts()


class ModelTexts:
    """Labels used for internal data representation or logging."""

    DEFAULT_NAME = "Entité Inconnue"
    LABEL_DEBT = "Dette Totale"
    LABEL_CASH = "Trésorerie & Équivalents"
    LABEL_MINORITIES = "Intérêts Minoritaires"
    LABEL_PENSIONS = "Provisions pour Retraites"
    LABEL_EQUITY = "Valeur des Capitaux Propres"
    LABEL_COMPREHENSIVE_NET_DEBT = "Dette Nette Consolidée (IFRS 16)"
    LABEL_LEASE_LIABILITIES = "Engagements de Location (IFRS 16)"
    LABEL_PENSION_LIABILITIES = "Engagements de Retraite (IFRS 16)"

    # Variable descriptions for terminal value calculations
    VAR_DESC_EXIT_MULT_MANUAL = "Exit Multiple (Manuel)"
    VAR_DESC_EXIT_MULT_SECTOR = "Exit Multiple (Benchmark Sectoriel)"

    # Common variable descriptions used across strategies
    VAR_DESC_FCFE_BASE = "Flux de Trésorerie Libre pour les Actionnaires (Année de Base)"
    VAR_DESC_DIVIDEND_BASE = "Dividende par Action (Base)"
    VAR_DESC_FCF_NORM = "Flux de Trésorerie Normalisé"
    VAR_DESC_ROIC = "Rendement sur Capital Investi"
    VAR_DESC_REINVESTMENT_RATE = "Taux de Réinvestissement"
    VAR_DESC_GROWTH_DERIVED = "Taux de Croissance Calculé"
    VAR_DESC_GROWTH_OVERRIDE = "Taux de Croissance Manuel"

    # Common interpretations
    INTERP_CASH_ADDITION = "Ajout de la trésorerie non-opérationnelle à la valeur des capitaux propres."
