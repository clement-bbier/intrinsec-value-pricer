from abc import ABC, abstractmethod
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, Tuple, TYPE_CHECKING, Any, List

from core.models import CompanyFinancials

# TYPE_CHECKING permet d'éviter les importations circulaires pour les modèles non critiques
if TYPE_CHECKING:
    from core.models import DCFParameters

logger = logging.getLogger(__name__)


class DataProvider(ABC):
    """
    Interface abstraite pour les fournisseurs de données (marché et fondamentaux).
    """

    @abstractmethod
    def get_company_financials(self, ticker: str) -> CompanyFinancials:
        """
        Récupère les données financières ACTUELLES pour la valorisation immédiate.
        Doit lever DataProviderError si des données critiques manquent.
        """
        raise NotImplementedError

    @abstractmethod
    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """
        Récupère l'historique de prix (Close) sous forme de DataFrame.
        Index: Datetime, Colonne: 'Close'.
        """
        raise NotImplementedError

    @abstractmethod
    def get_historical_fundamentals_for_date(
            self,
            ticker: str,
            date: datetime,
    ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Récupère les fondamentaux (FCF TTM, Dette, Cash, Beta, Shares) tels qu'ils étaient connus
        JUSTE AVANT la date donnée (basé sur la publication des rapports).

        Retourne un tuple :
          1. Dictionnaire des valeurs trouvées (ou None si échec total).
             Clés OBLIGATOIRES: 'fcf_last', 'total_debt', 'cash_and_equivalents', 'beta', 'shares_outstanding'.
          2. Liste de chaînes décrivant les erreurs/manques précis (ex: "Dette introuvable").
        """
        raise NotImplementedError

    @abstractmethod
    def get_company_financials_and_parameters(self, ticker: str, projection_years: int):
        """
        Point d'entrée unifié pour l'application pour obtenir les deux modèles principaux (financials et params).
        Implémenté dans les fournisseurs concrets.
        """
        raise NotImplementedError