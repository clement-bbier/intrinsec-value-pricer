"""
infra/data_providers/base_provider.py

INTERFACE ABSTRAITE — FOURNISSEURS DE DONNÉES — VERSION V11.0 (Sprint 4)
Rôle : Contrat strict pour tous les providers de données financières et sectorielles.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

import pandas as pd

from core.models import CompanyFinancials, DCFParameters, MultiplesData


class DataProvider(ABC):
    """Interface abstraite stricte pour les fournisseurs de données."""

    @abstractmethod
    def get_company_financials(self, ticker: str) -> CompanyFinancials:
        """Récupère les données financières actuelles (Snapshot) d'une entreprise."""
        raise NotImplementedError

    @abstractmethod
    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """Récupère l'historique de prix (Close) pour l'analyse technique ou graphique."""
        raise NotImplementedError

    @abstractmethod
    def get_peer_multiples(self, ticker: str) -> MultiplesData:
        """
        NOUVEAUTÉ SPRINT 4 (Phase 3) :
        Découvre les concurrents et retourne leurs multiples normalisés.
        """
        raise NotImplementedError

    @abstractmethod
    def get_company_financials_and_parameters(
        self,
        ticker: str,
        projection_years: int
    ) -> Tuple[CompanyFinancials, DCFParameters]:
        """
        Méthode "Tout-en-un" pour le mode Automatique.
        Récupère les données fondamentales et résout les paramètres macro localisés.
        """
        raise NotImplementedError