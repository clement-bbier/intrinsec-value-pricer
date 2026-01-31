"""
app/ui/results/optional/__init__.py
Initialisation des composants optionnels.
"""

from .peer_multiples import PeerMultiples
from .sotp_breakdown import SOTPBreakdownTab
from .monte_carlo_distribution import MonteCarloDistributionTab
from .scenario_analysis import ScenarioAnalysisTab
from .historical_backtest import HistoricalBacktestTab

__all__ = [
    "PeerMultiples",
    "SOTPBreakdownTab",
    "ScenarioAnalysisTab",
    "HistoricalBacktestTab",
    "MonteCarloDistributionTab",
]