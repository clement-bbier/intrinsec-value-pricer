"""
src/i18n/__init__.py
"""

from src.i18n.fr import (
    BacktestTexts,
    BenchmarkTexts,
    # Backend (calculation/engine layer)
    CalculationErrors,
    ChartTexts,
    # UI (presentation layer)
    CommonTexts,
    DiagnosticTexts,
    ExpertTexts,
    ExtensionTexts,
    FeedbackMessages,
    InputLabels,
    KPITexts,
    LegalTexts,
    MarketTexts,
    ModelTexts,
    OnboardingTexts,
    PeersTexts,
    PillarLabels,
    QuantTexts,
    RegistryTexts,  # Backend registry labels (Glass Box)
    ResultsTexts,
    SharedTexts,  # Backend shared texts
    SidebarTexts,
    SOTPTexts,
    StrategyFormulas,  # Backend LaTeX formulas (computation)
    StrategyInterpretations,
    StrategySources,
    TooltipsTexts,
    UIMessages,
    # UI renamed (no conflict with backend)
    UIRegistryTexts,
    UISharedTexts,
    UIStrategyFormulas,
    WorkflowTexts,
)

__all__ = [
    # Backend (calculation/engine layer)
    "CalculationErrors",
    "DiagnosticTexts",
    "ModelTexts",
    "RegistryTexts",  # Backend registry labels (Glass Box)
    "StrategyFormulas",  # Backend LaTeX formulas (computation)
    "StrategyInterpretations",
    "StrategySources",
    "SharedTexts",  # Backend shared texts
    "WorkflowTexts",
    # UI (presentation layer)
    "CommonTexts",
    "ExpertTexts",
    "ExtensionTexts",
    "FeedbackMessages",
    "LegalTexts",
    "OnboardingTexts",
    "ResultsTexts",
    "SidebarTexts",
    "TooltipsTexts",
    "UIMessages",
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
