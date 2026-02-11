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
    FeedbackMessages,
    InputLabels,
    KPITexts,
    LegalTexts,
    MarketTexts,
    OnboardingTexts,
    PeersTexts,
    PillarLabels,
    QuantTexts,
    ResultsTexts,
    SidebarTexts,
    SOTPTexts,
    TooltipsTexts,
    UIMessages,
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
    "FeedbackMessages",
    "LegalTexts",
    "OnboardingTexts",
    "ResultsTexts",
    "SidebarTexts",
    "TooltipsTexts",
    "UIMessages",
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
