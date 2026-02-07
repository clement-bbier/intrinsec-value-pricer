"""
src/models/results/__init__.py

RESULTS MODULE EXPORTS
======================
Exposes the output data structures for all valuation engines.
"""

from src.models.results.base_result import Results
from src.models.results.common import (
    CommonResults,
    ResolvedRates,
    ResolvedCapital
)
from src.models.results.strategies import (
    StrategyUnionResults,
    BaseFlowResults,
    FCFFStandardResults,
    FCFFNormalizedResults,
    FCFFGrowthResults,
    FCFEResults,
    DDMResults,
    RIMResults,
    GrahamResults
)
from src.models.results.options import (
    ExtensionBundleResults,
    MCResults,
    SensitivityResults,
    ScenariosResults,
    BacktestResults,
    PeersResults,
    SOTPResults
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