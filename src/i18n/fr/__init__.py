"""
src/i18n/fr/__init__.py
"""
from src.i18n.fr.backend import (
    BenchmarkTexts,
    CalculationErrors,
    DiagnosticTexts,
    ModelTexts,
    KPITexts,
    SOTPTexts,
    RegistryTexts,
    StrategyFormulas,
    StrategyInterpretations,
    StrategySources,
    SharedTexts,
    WorkflowTexts
)

from src.i18n.fr.ui import (
    CommonTexts,
    ExpertTexts,
    ExtensionTexts,
    ResultsTexts,
    SidebarTexts
)

__all__ = [
    "BenchmarkTexts",
    "CalculationErrors",
    "DiagnosticTexts",
    "ModelTexts",
    "KPITexts",
    "SOTPTexts",
    "RegistryTexts",
    "StrategyFormulas",
    "StrategyInterpretations",
    "StrategySources",
    "SharedTexts",
    "WorkflowTexts",

    "CommonTexts",
    "ExpertTexts",
    "ExtensionTexts",
    "ResultsTexts",
    "SidebarTexts"
]