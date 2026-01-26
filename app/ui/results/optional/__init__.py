"""
app/ui/results/optional/__init__.py
Initialisation des composants optionnels.
"""

from .peer_multiples import MarketAnalysisTab
from .risk_engineering import RiskEngineeringTab
from .sotp_breakdown import SOTPBreakdownTab
from .scenario_analysis import ScenarioAnalysisTab
from .historical_backtest import HistoricalBacktestTab
from .monte_carlo_distribution import MonteCarloDistributionTab

__all__ = [
    "MarketAnalysisTab",
    "RiskEngineeringTab",
    "SOTPBreakdownTab",
    "ScenarioAnalysisTab",
    "HistoricalBacktestTab",
    "MonteCarloDistributionTab",
]