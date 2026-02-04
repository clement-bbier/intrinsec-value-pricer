"""
infra/macro/base_macro_provider.py

ABSTRACT BASE INTERFACE — MACRO DATA PROVIDERS
==============================================
Role: Contract for fetching regional economic indicators (Rf, MRP, Tax).
"""

from abc import ABC, abstractmethod
from src.models.company import CompanySnapshot

class MacroDataProvider(ABC):
    @abstractmethod
    def hydrate_macro_data(self, snapshot: CompanySnapshot) -> CompanySnapshot:
        """
        Populates a CompanySnapshot with macro-economic data based on its country.

        Parameters
        ----------
        snapshot : CompanySnapshot
            The snapshot containing at least a 'country' field.

        Returns
        -------
        CompanySnapshot
            The snapshot enriched with macro data.
        """
        pass