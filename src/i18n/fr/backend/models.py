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
