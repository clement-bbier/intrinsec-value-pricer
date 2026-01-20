"""
src/i18n/fr/backend/models.py
Textes i18n pour les modèles de données du domaine financier.

Centralise toutes les chaînes de caractères utilisées dans les modèles Pydantic
(labels, messages de validation, descriptions) pour faciliter l'internationalisation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelValidationTexts:
    """Messages de validation pour les modèles de données."""

    SCENARIO_PROBABILITIES_SUM_ERROR: str = (
        "La somme des probabilités (Bull+Base+Bear) doit être égale à 1.0."
    )


# Instance globale pour faciliter les imports
MODEL_VALIDATION_TEXTS = ModelValidationTexts()

__all__ = ["ModelValidationTexts", "MODEL_VALIDATION_TEXTS"]