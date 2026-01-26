"""
src/i18n/fr/ui/
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

from src.i18n.fr.ui.expert import SharedTexts, DDMTexts

from src.i18n.fr.ui.results import (
    KPITexts,
    AuditTexts,
    ChartTexts,
    PillarLabels,
    QuantTexts,
    MarketTexts
)

from src.i18n.fr.ui.extensions import (
    SOTPTexts,
    SOTPResultTexts,
    BacktestTexts,
    ScenarioTexts,
)

__all__ = [
    "CommonTexts",
    "PillarLabels",
    "OnboardingTexts",
    "FeedbackMessages",
    "LegalTexts",
    "TooltipsTexts",
    "UIMessages",
    "SidebarTexts",
    "SharedTexts",
    "KPITexts",
    "QuantTexts",
    "MarketTexts",
    "AuditTexts",
    "ChartTexts",
    "SOTPTexts",
    "SOTPResultTexts",
    "BacktestTexts",
    "ScenarioTexts",
    "DDMTexts"
]
