"""
infra/data_providers/base_provider.py

ABSTRACT BASE INTERFACE — FINANCIAL DATA PROVIDERS
==================================================
Role: Strict contract for all micro-financial data providers.
Ensures that the Resolver remains decoupled from specific APIs (Yahoo, Bloomberg).

Architecture: Provider Pattern (Interface Segregation).
Style: Numpy docstrings.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from src.models.company import CompanySnapshot


class FinancialDataProvider(ABC):
    """
    Strict abstract interface for financial data acquisition.

    Implementing classes must return a CompanySnapshot DTO to ensure 
    compatibility with the Resolution Engine.
    """

    @abstractmethod
    def get_company_snapshot(self, ticker: str) -> Optional[CompanySnapshot]:
        """
        Retrieves a complete raw financial snapshot for a given ticker.

        Parameters
        ----------
        ticker : str
            The stock symbol to fetch.

        Returns
        -------
        Optional[CompanySnapshot]
            A transport object containing raw data, or None if the fetch fails.
        """
        raise NotImplementedError
