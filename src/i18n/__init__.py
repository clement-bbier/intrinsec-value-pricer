"""
src/i18n/__init__.py
"""
from src.i18n.fr import (
    # Backend (calculation/engine layer)
    CalculationErrors,
    DiagnosticTexts,
    ModelTexts,
    RegistryTexts,          # Backend registry labels (Glass Box)
    StrategyFormulas,        # Backend LaTeX formulas (computation)
    StrategyInterpretations,
    StrategySources,
    SharedTexts,             # Backend shared texts
    WorkflowTexts,

    # UI (presentation layer)
    CommonTexts,
    ExpertTexts,
    ExtensionTexts,
    ResultsTexts,
    SidebarTexts,
    LegalTexts,
    QuantTexts,
    ChartTexts,
    BacktestTexts,
    PillarLabels,
    SOTPTexts,
    InputLabels,
    BenchmarkTexts,
    MarketTexts,
    PeersTexts,
    KPITexts,
    
    # UI renamed (no conflict with backend)
    UIRegistryTexts,
    UIStrategyFormulas,
    UISharedTexts,
)

__all__ = [
    # Backend (calculation/engine layer)
    "CalculationErrors",
    "DiagnosticTexts",
    "ModelTexts",
    "RegistryTexts",          # Backend registry labels (Glass Box)
    "StrategyFormulas",        # Backend LaTeX formulas (computation)
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
    "QuantTexts",
    "ChartTexts",
    "BacktestTexts",
    "PillarLabels",
    "SOTPTexts",
    "InputLabels",
    "BenchmarkTexts",
    "MarketTexts",
    "PeersTexts",
    "KPITexts",
    
    # UI renamed (no conflict with backend)
    "UIRegistryTexts",
    "UIStrategyFormulas",
    "UISharedTexts",
]