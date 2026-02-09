"""
src/i18n/fr/ui/__init__.py
UI TRANSLATIONS (FRENCH)
"""

from src.i18n.fr.ui.common import CommonTexts, LegalTexts
from src.i18n.fr.ui.expert import ExpertTexts
from src.i18n.fr.ui.extensions import ExtensionTexts
from src.i18n.fr.ui.results import ResultsTexts, KPITexts, QuantTexts, ChartTexts, BacktestTexts
from src.i18n.fr.ui.sidebar import SidebarTexts

__all__ = [
    "CommonTexts",
    "ExpertTexts",
    "ExtensionTexts",
    "ResultsTexts",
    "SidebarTexts",
    "LegalTexts",
    "KPITexts",
    "QuantTexts",
    "BacktestTexts",
    "ChartTexts",
]