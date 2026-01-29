"""
Package des stratégies de valorisation.

Ce package regroupe toutes les stratégies de valorisation disponibles,
organisées par approche économique : DCF, modèles actionnariaux,
modèles spécifiques sectoriels et méthodes relatives.

Usage recommandé:
    from src.valuation.strategies import StandardFCFFStrategy, FCFEStrategy
"""

from __future__ import annotations

# Stratégies DCF (Firm-Level)
from .standard_fcff import StandardFCFFStrategy
from .fundamental_fcff import FundamentalFCFFStrategy
from .revenue_growth import RevenueBasedStrategy

# Stratégies DCF (Equity-Level)
from .fcfe import FCFEStrategy
from .ddm import DividendDiscountStrategy

# Autres modèles
from .rim_banks import RIMBankingStrategy
from .graham_value import GrahamNumberStrategy

# Multiples (pour triangulation)
from .multiples import MarketMultiplesStrategy

# Classe de base (pour extension)
from .abstract import ValuationStrategy

# Monte Carlo wrapper (usage interne principalement)
from .monte_carlo import MonteCarloGenericStrategy

# API publique garantie
__all__ = [
    # Stratégies principales (Firm-Level DCF)
    "StandardFCFFStrategy",
    "FundamentalFCFFStrategy",
    "RevenueBasedStrategy",
    # Stratégies Equity-Level
    "FCFEStrategy",
    "DividendDiscountStrategy",
    # Autres modèles
    "RIMBankingStrategy",
    "GrahamNumberStrategy",
    # Multiples
    "MarketMultiplesStrategy",
    # Base class (pour héritage)
    "ValuationStrategy",
]
