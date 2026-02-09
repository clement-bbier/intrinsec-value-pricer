"""
src/i18n/fr/backend/__init__.py
"""
# 1. Benchmark (Le remplaçant)
from src.i18n.fr.backend.benchmark import BenchmarkTexts

# 2. Core Modules (Les survivants)
from src.i18n.fr.backend.errors import CalculationErrors, DiagnosticTexts
from src.i18n.fr.backend.models import ModelTexts, SOTPTexts
from src.i18n.fr.backend.registry import RegistryTexts
from src.i18n.fr.backend.strategies import (
    StrategyFormulas,
    StrategyInterpretations,
    StrategySources,
    SharedTexts
)
from src.i18n.fr.backend.workflow import WorkflowTexts

__all__ = [
    "BenchmarkTexts",
    "CalculationErrors",
    "DiagnosticTexts",
    "ModelTexts",
    "SOTPTexts",
    "RegistryTexts",
    "StrategyFormulas",
    "StrategyInterpretations",
    "StrategySources",
    "SharedTexts",
    "WorkflowTexts"
]