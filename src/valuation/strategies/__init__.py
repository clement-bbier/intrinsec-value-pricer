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

from .ddm import DividendDiscountStrategy

# DCF Strategies (Equity-Level)
from .fcfe import FCFEStrategy
from .fundamental_fcff import FundamentalFCFFStrategy
from .graham_value import GrahamNumberStrategy

# The Contract (Interface)
from .interface import IValuationRunner
from .revenue_growth_fcff import RevenueGrowthFCFFStrategy

# Other Models (RIM, Graham)
from .rim_banks import RIMBankingStrategy

# DCF Strategies (Firm-Level)
from .standard_fcff import StandardFCFFStrategy

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
