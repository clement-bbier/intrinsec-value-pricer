"""
src/models/results/__init__.py

RESULTS MODULE EXPORTS
======================
Exposes the output data structures for all valuation engines.
"""

from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedCapital, ResolvedRates
from src.models.results.options import (
    BacktestResults,
    ExtensionBundleResults,
    MCResults,
    PeersResults,
    ScenariosResults,
    SensitivityResults,
    SOTPResults,
)
from src.models.results.strategies import (
    BaseFlowResults,
    DDMResults,
    FCFEResults,
    FCFFGrowthResults,
    FCFFNormalizedResults,
    FCFFStandardResults,
    GrahamResults,
    RIMResults,
    StrategyUnionResults,
)

__all__ = [
    # Root
    "Results",
    # Common
    "CommonResults",
    "ResolvedRates",
    "ResolvedCapital",
    # Strategies
    "StrategyUnionResults",
    "BaseFlowResults",
    "FCFFStandardResults",
    "FCFFNormalizedResults",
    "FCFFGrowthResults",
    "FCFEResults",
    "DDMResults",
    "RIMResults",
    "GrahamResults",
    # Options
    "ExtensionBundleResults",
    "MCResults",
    "SensitivityResults",
    "ScenariosResults",
    "BacktestResults",
    "PeersResults",
    "SOTPResults",
]
