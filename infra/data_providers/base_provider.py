from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, Tuple, List, Any

from core.models import CompanyFinancials, DCFParameters


class DataProvider(ABC):
    """
    Interface abstraite stricte pour les fournisseurs de données.

    Responsabilités :
    - Abstraire la source (Yahoo, Bloomberg, API...).
    - Normaliser les erreurs via core.exceptions.
    """

    @abstractmethod
    def get_company_financials(self, ticker: str) -> CompanyFinancials:
        """
        Récupère les données financières actuelles.

        Raises:
            TickerNotFoundError: Si le ticker est invalide.
            DataInsufficientError: Si les données sont vides.
            ExternalServiceError: Si le service est inaccessible.
        """
        raise NotImplementedError

    @abstractmethod
    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """
        Récupère l'historique de prix (Close).
        Retourne un DataFrame vide en cas d'erreur (Best Effort).
        """
        raise NotImplementedError

    @abstractmethod
    def get_historical_fundamentals_for_date(
            self, ticker: str, date: datetime
    ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Récupère un snapshot des fondamentaux à une date passée.
        Retourne (Dict Données, Liste Erreurs).
        """
        raise NotImplementedError

    @abstractmethod
    def get_company_financials_and_parameters(
            self, ticker: str, projection_years: int
    ) -> Tuple[CompanyFinancials, DCFParameters]:
        """
        Point d'entrée workflow unifié : Financials + Auto-Params.
        """
        raise NotImplementedError