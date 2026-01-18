"""
core/i18n/fr/backend/
Textes internes (logs, erreurs, audit).
"""

from core.i18n.fr.backend.workflow import WorkflowTexts

from core.i18n.fr.backend.errors import (
    DiagnosticTexts,
    CalculationErrors,
)

from core.i18n.fr.backend.audit import (
    AuditCategories,
    AuditMessages,
    AuditEngineTexts,
)

from core.i18n.fr.backend.strategies import (
    StrategySources,
    StrategyInterpretations,
    StrategyFormulas,
)

from core.i18n.fr.backend.registry import RegistryTexts

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
]
