"""
app/ui/result_tabs/optional/
Onglets conditionnels — affichés selon la configuration.

Chaque onglet implémente is_visible() pour définir ses conditions.
"""

from app.ui.result_tabs.optional.peer_multiples import PeerMultiplesTab
from app.ui.result_tabs.optional.sotp_breakdown import SOTPBreakdownTab
from app.ui.result_tabs.optional.scenario_analysis import ScenarioAnalysisTab
from app.ui.result_tabs.optional.historical_backtest import HistoricalBacktestTab
from app.ui.result_tabs.optional.monte_carlo_distribution import MonteCarloDistributionTab

__all__ = [
    "PeerMultiplesTab",
    "SOTPBreakdownTab",
    "ScenarioAnalysisTab",
    "HistoricalBacktestTab",
    "MonteCarloDistributionTab",
]
