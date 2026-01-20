"""
core/i18n/fr/ui/
Textes visibles dans l'interface utilisateur (francais).
"""

from src.i18n.fr.ui.common import (
    CommonTexts,
    OnboardingTexts,
    FeedbackMessages,
    LegalTexts,
    TooltipsTexts,
    UIMessages,
)

from src.i18n.fr.ui.sidebar import SidebarTexts

from src.i18n.fr.ui.expert import ExpertTerminalTexts

from src.i18n.fr.ui.results import (
    KPITexts,
    AuditTexts,
    ChartTexts,
)

from src.i18n.fr.ui.extensions import (
    SOTPTexts,
    SOTPResultTexts,
    BacktestTexts,
    ScenarioTexts,
)

__all__ = [
    "CommonTexts",
    "OnboardingTexts",
    "FeedbackMessages",
    "LegalTexts",
    "TooltipsTexts",
    "UIMessages",
    "SidebarTexts",
    "ExpertTerminalTexts",
    "KPITexts",
    "AuditTexts",
    "ChartTexts",
    "SOTPTexts",
    "SOTPResultTexts",
    "BacktestTexts",
    "ScenarioTexts",
]
