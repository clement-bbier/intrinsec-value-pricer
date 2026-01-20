"""
core/i18n/
Module de centralisation des textes et labels (i18n-ready).

Structure :
- fr/          : Textes en francais
  - ui/        : Textes visibles dans l'interface
  - backend/   : Textes internes (logs, erreurs, audit)
- en/          : Textes en anglais (a creer)

Ce module est la source unique de verite pour toutes les chaines de caracteres.
L'architecture respecte le principe de Clean Architecture.

Usage :
    from src.i18n import CommonTexts, KPITexts, DiagnosticTexts
"""

# Import depuis la langue par defaut (francais)
from src.i18n.fr import (
    # UI
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
    # Backend
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
