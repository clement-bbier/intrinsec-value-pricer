"""
src/i18n/fr/ui/__init__.py
Point d'entrée des traductions de l'interface utilisateur.
"""

from .common import CommonTexts, LegalTexts
from .results import (
    ResultsTexts,
    KPITexts,
    QuantTexts,
    ChartTexts,
    BacktestTexts,
    PillarLabels,
    InputLabels,
    SOTPTexts,
    MarketTexts,
    RegistryTexts,
    StrategyFormulas,
    BenchmarkTexts
)
from .expert import ExpertTexts
from .extensions import ExtensionTexts, PeersTexts
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
    "RegistryTexts",
    "StrategyFormulas",
    "BenchmarkTexts"
]