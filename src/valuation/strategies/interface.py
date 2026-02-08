"""
src/valuation/strategies/interface.py

STRATEGY INTERFACE CONTRACT
===========================
Role: Defines the strict blueprint for all valuation strategies (DCF, Graham, etc.).
Architecture: Strategy Pattern.
"""

from abc import ABC, abstractmethod
from src.models.valuation import ValuationResult, ValuationRequest

class IValuationStrategy(ABC):
    """
    Abstract Base Class enforcing the structure of a Valuation Strategy.
    """

    @abstractmethod
    def execute(self, request: ValuationRequest) -> ValuationResult:
        """
        Runs the full valuation logic for a specific strategy.

        Parameters
        ----------
        request : ValuationRequest
            The input container with Parameters and Company data.

        Returns
        -------
        ValuationResult
            The fully computed result with audit trails.
        """
        pass