"""
src/valuation/strategies/interface.py

STRATEGY INTERFACE CONTRACT
===========================
Role: Defines the strict blueprint for all valuation strategies.
Architecture: Strategy Pattern.
"""

from abc import ABC, abstractmethod
from src.models.company import Company
from src.models.parameters.base_parameter import Parameters
from src.models.valuation import ValuationResult

class IValuationRunner(ABC):
    """
    Abstract Base Class enforcing the structure of a Valuation Strategy.
    Renamed to IValuationRunner to match strategy implementations.
    """

    @abstractmethod
    def execute(self, financials: Company, params: Parameters) -> ValuationResult:
        """
        Runs the full valuation logic for a specific strategy.

        Parameters
        ----------
        financials : Company
            The raw financial data (Pillar 1).
        params : Parameters
            The fully resolved input parameters (Pillars 2, 3, 4).

        Returns
        -------
        ValuationResult
            The fully computed result containing the nested Results object.
        """
        pass