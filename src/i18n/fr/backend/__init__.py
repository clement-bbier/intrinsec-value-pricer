"""
src/i18n/fr/backend/__init__.py
"""

# 2. Core Modules (Les survivants)
from src.i18n.fr.backend.errors import CalculationErrors, DiagnosticTexts
from src.i18n.fr.backend.models import ModelTexts
from src.i18n.fr.backend.registry import RegistryTexts
from src.i18n.fr.backend.strategies import SharedTexts, StrategyFormulas, StrategyInterpretations, StrategySources
from src.i18n.fr.backend.workflow import WorkflowTexts

__all__ = [
    "CalculationErrors",
    "DiagnosticTexts",
    "ModelTexts",
    "RegistryTexts",
    "StrategyFormulas",
    "StrategyInterpretations",
    "StrategySources",
    "SharedTexts",
    "WorkflowTexts",
]
