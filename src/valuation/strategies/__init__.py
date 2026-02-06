"""
src/valuation/strategies/__init__.py

VALUATION STRATEGIES PACKAGE
============================
Exposes the concrete implementations of the IValuationRunner interface.
Organized by economic approach: Firm-Level DCF, Equity-Level DCF, and Specific Models.

Usage:
    from src.valuation.strategies import StandardFCFFStrategy, IValuationRunner
"""

from __future__ import annotations

# The Contract (Interface)
from .interface import IValuationRunner

# DCF Strategies (Firm-Level)
from .standard_fcff import StandardFCFFStrategy
from .fundamental_fcff import FundamentalFCFFStrategy
from .revenue_growth_fcff import RevenueGrowthFCFFStrategy

# DCF Strategies (Equity-Level)
from .fcfe import FCFEStrategy
from .ddm import DividendDiscountStrategy

# Other Models (RIM, Graham)
from .rim_banks import RIMBankingStrategy
from .graham_value import GrahamNumberStrategy

# Public API
__all__ = [
    # Interface
    "IValuationRunner",

    # Firm-Level DCF
    "StandardFCFFStrategy",
    "FundamentalFCFFStrategy",
    "RevenueGrowthFCFFStrategy",

    # Equity-Level
    "FCFEStrategy",
    "DividendDiscountStrategy",

    # Specific Models
    "RIMBankingStrategy",
    "GrahamNumberStrategy",
]