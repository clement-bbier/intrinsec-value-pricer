"""
src/i18n/fr/__init__.py
"""
from src.i18n.fr.backend import (
    CalculationErrors,
    DiagnosticTexts,
    ModelTexts,
    RegistryTexts,
    SharedTexts,
    StrategyFormulas,
    StrategyInterpretations,
    StrategySources,
    WorkflowTexts,
)
from src.i18n.fr.ui import (
    BacktestTexts,
    BenchmarkTexts,
    ChartTexts,
    CommonTexts,
    ExpertTexts,
    ExtensionTexts,
    InputLabels,
    KPITexts,
    LegalTexts,
    MarketTexts,
    PeersTexts,
    PillarLabels,
    QuantTexts,
    ResultsTexts,
    SidebarTexts,
    SOTPTexts,
    UIRegistryTexts,
    UISharedTexts,
    UIStrategyFormulas,
)

__all__ = [
    # Backend (calculation/engine layer)
    "CalculationErrors",
    "DiagnosticTexts",
    "ModelTexts",
    "RegistryTexts",          # Backend registry labels
    "StrategyFormulas",        # Backend LaTeX formulas
    "StrategyInterpretations",
    "StrategySources",
    "SharedTexts",             # Backend shared texts
    "WorkflowTexts",

    # UI (presentation layer)
    "CommonTexts",
    "ExpertTexts",
    "ExtensionTexts",
    "ResultsTexts",
    "SidebarTexts",
    "LegalTexts",
    "KPITexts",
    "BacktestTexts",
    "QuantTexts",
    "ChartTexts",
    "PillarLabels",
    "InputLabels",
    "SOTPTexts",
    "BenchmarkTexts",
    "MarketTexts",
    "PeersTexts",

    # UI renamed (no conflict with backend)
    "UIRegistryTexts",
    "UIStrategyFormulas",
    "UISharedTexts"
]
