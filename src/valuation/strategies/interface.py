"""
src/valuation/strategies/interface.py

VALUATION STRATEGY INTERFACE
============================
Role: Defines the contract that all Valuation Runners must implement.
Architecture: Abstract Base Class (ABC).
Scope: Core Engines (FCFF, RIM, Graham) and future extensions.
"""

from __future__ import annotations
from abc import ABC, abstractmethod

from src.models.parameters.base_parameter import Parameters
from src.models.company import Company
from src.models.valuation import ValuationResult


class IValuationRunner(ABC):
    """
    Contract for a Valuation Engine Runner.

    Every strategy (Standard DCF, Growth DCF, RIM, etc.) must implement
    this execute method to be compatible with the Orchestrator.
    """

    @abstractmethod
    def execute(self, financials: Company, params: Parameters) -> ValuationResult:
        """
        Runs the valuation logic.

        Parameters
        ----------
        financials : Company
            The static identity and market data of the target.
        params : Parameters
            The fully resolved configuration (Growth, Rates, Margins).

        Returns
        -------
        ValuationResult
            The complete valuation package (Price, Trace, Sensitivity).
        """
        pass

    @property
    @abstractmethod
    def glass_box_enabled(self) -> bool:
        """Indicates if the runner should generate detailed audit trails."""
        pass

    @glass_box_enabled.setter
    @abstractmethod
    def glass_box_enabled(self, value: bool) -> None:
        """Enables or disables audit trail generation (e.g. for Monte Carlo speed)."""
        pass