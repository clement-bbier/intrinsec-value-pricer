"""
core/i18n/fr/backend/
Textes internes (logs, erreurs, audit).
"""

from src.i18n.fr.backend.workflow import WorkflowTexts

from src.i18n.fr.backend.errors import (
    DiagnosticTexts,
    CalculationErrors,
)

from src.i18n.fr.backend.audit import (
    AuditCategories,
    AuditMessages,
    AuditEngineTexts,
)

from src.i18n.fr.backend.strategies import (
    StrategySources,
    StrategyInterpretations,
    StrategyFormulas,
)

from src.i18n.fr.backend.registry import RegistryTexts
from src.i18n.fr.backend.models import ModelValidationTexts, MODEL_VALIDATION_TEXTS

__all__ = [
    "WorkflowTexts",
    "DiagnosticTexts",
    "CalculationErrors",
    "AuditCategories",
    "AuditMessages",
    "AuditEngineTexts",
    "StrategySources",
    "StrategyInterpretations",
    "StrategyFormulas",
    "RegistryTexts",
    "ModelValidationTexts",
    "MODEL_VALIDATION_TEXTS",
]
