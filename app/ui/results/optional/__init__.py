"""
app/ui/result_tabs/optional/
Onglets conditionnels — affichés selon la configuration.

Chaque onglet implémente is_visible() pour définir ses conditions.
"""

from app.ui.results.optional.peer_multiples import PeerMultiplesTab
from app.ui.results.optional.sotp_breakdown import SOTPBreakdownTab
from app.ui.results.optional.scenario_analysis import ScenarioAnalysisTab
from app.ui.results.optional.historical_backtest import HistoricalBacktestTab
from app.ui.results.optional.monte_carlo_distribution import MonteCarloDistributionTab

__all__ = [
    "PeerMultiplesTab",
    "SOTPBreakdownTab",
    "ScenarioAnalysisTab",
    "HistoricalBacktestTab",
    "MonteCarloDistributionTab",
]
