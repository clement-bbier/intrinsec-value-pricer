"""
src/valuation/strategies/__init__.py

Package des stratégies de valorisation.

Version : V2.0 — ST-1.3 Encapsulation Resolution
Pattern : Strategy (GoF)
Style : Numpy Style docstrings

Ce package expose uniquement les stratégies publiques via __all__.
Les classes internes (MonteCarloGenericStrategy, ValuationStrategy) sont
accessibles mais ne font pas partie de l'API garantie.

Usage recommandé:
    from src.valuation.strategies import StandardFCFFStrategy, FCFEStrategy

Note: Les stratégies sont généralement accédées via le registre centralisé
      (src.valuation.registry) plutôt que par import direct.

RISQUES FINANCIERS:
- Chaque stratégie implémente un modèle de valorisation différent
- Un changement d'API peut casser les imports existants
"""

from __future__ import annotations

# Stratégies DCF (Firm-Level)
from .dcf_standard import StandardFCFFStrategy
from .dcf_fundamental import FundamentalFCFFStrategy
from .dcf_growth import RevenueBasedStrategy

# Stratégies DCF (Equity-Level)
from .dcf_equity import FCFEStrategy
from .dcf_dividend import DividendDiscountStrategy

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
