"""
src/i18n/fr/ui/__init__.py
Point d'entrée des traductions de l'interface utilisateur.
"""

from .common import CommonTexts, LegalTexts
from .expert import ExpertTexts, UISharedTexts
from .extensions import ExtensionTexts, PeersTexts
from .results import (
    BacktestTexts,
    BenchmarkTexts,
    ChartTexts,
    InputLabels,
    KPITexts,
    MarketTexts,
    PillarLabels,
    QuantTexts,
    ResultsTexts,
    SOTPTexts,
    UIRegistryTexts,
    UIStrategyFormulas,
)
from .sidebar import SidebarTexts

__all__ = [
    "CommonTexts",
    "LegalTexts",
    "ResultsTexts",
    "KPITexts",
    "QuantTexts",
    "ChartTexts",
    "BacktestTexts",
    "PillarLabels",
    "InputLabels",
    "SOTPTexts",
    "MarketTexts",
    "ExpertTexts",
    "ExtensionTexts",
    "PeersTexts",
    "SidebarTexts",
    "BenchmarkTexts",
    "UIRegistryTexts",
    "UIStrategyFormulas",
    "UISharedTexts"
]
