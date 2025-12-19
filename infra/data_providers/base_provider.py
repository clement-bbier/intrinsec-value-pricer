from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, Tuple, List, Any

from core.models import CompanyFinancials, DCFParameters


class DataProvider(ABC):
    """
    Interface abstraite stricte pour les fournisseurs de données.
    """

    @abstractmethod
    def get_company_financials(self, ticker: str) -> CompanyFinancials:
        """Récupère les données financières actuelles (Snapshot)."""
        raise NotImplementedError

    @abstractmethod
    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """Récupère l'historique de prix (Close)."""
        raise NotImplementedError

    @abstractmethod
    def get_company_financials_and_parameters(
            self, ticker: str, projection_years: int
    ) -> Tuple[CompanyFinancials, DCFParameters]:
        """
        Méthode "Tout-en-un" pour le mode Automatique.
        Récupère à la fois les données entreprise et les paramètres macro.
        """
        raise NotImplementedError