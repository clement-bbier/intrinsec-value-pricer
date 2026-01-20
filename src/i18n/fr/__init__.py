"""
core/i18n/fr/
Textes en francais.

Structure :
- ui/       : Textes visibles dans l'interface
- backend/  : Textes internes (logs, erreurs, audit)
"""

# UI
from src.i18n.fr.ui import (
    CommonTexts,
    SidebarTexts,
    OnboardingTexts,
    FeedbackMessages,
    LegalTexts,
    TooltipsTexts,
    UIMessages,
    ExpertTerminalTexts,
    KPITexts,
    AuditTexts,
    ChartTexts,
    SOTPTexts,
    SOTPResultTexts,
    BacktestTexts,
    ScenarioTexts,
)

# Backend
from src.i18n.fr.backend import (
    WorkflowTexts,
    DiagnosticTexts,
    StrategySources,
    StrategyInterpretations,
    StrategyFormulas,
    CalculationErrors,
    AuditCategories,
    AuditMessages,
    AuditEngineTexts,
    RegistryTexts,
)

__all__ = [
    # UI
    "CommonTexts",
    "SidebarTexts",
    "OnboardingTexts",
    "FeedbackMessages",
    "LegalTexts",
    "TooltipsTexts",
    "UIMessages",
    "ExpertTerminalTexts",
    "KPITexts",
    "AuditTexts",
    "ChartTexts",
    "SOTPTexts",
    "SOTPResultTexts",
    "BacktestTexts",
    "ScenarioTexts",
    # Backend
    "WorkflowTexts",
    "DiagnosticTexts",
    "StrategySources",
    "StrategyInterpretations",
    "StrategyFormulas",
    "CalculationErrors",
    "AuditCategories",
    "AuditMessages",
    "AuditEngineTexts",
    "RegistryTexts",
]
