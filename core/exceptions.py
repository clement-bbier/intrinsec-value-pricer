import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseValuationError(Exception):
    """
    Classe de base pour toutes les erreurs métier.
    Loggue automatiquement l'erreur à l'instanciation.
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.context = context

        # Log structuré automatique
        log_message = f"[{self.__class__.__name__}] {message}"
        if context:
            log_message += f" | context={context}"
        logger.error(log_message)

    @property
    def ui_user_message(self) -> str:
        """Message convivial pour l'interface utilisateur."""
        return str(self)


class CalculationError(BaseValuationError):
    @property
    def ui_user_message(self) -> str:
        # Correction du bug ici : on utilise self (le message) et non super().__init__
        return f"Erreur de calcul : {self}"


class WorkflowError(BaseValuationError):
    @property
    def ui_user_message(self) -> str:
        return "Erreur technique interne (Workflow). Veuillez réessayer."


class ApplicationStartupError(BaseValuationError):
    pass


# --- DATA PROVIDER ERRORS (HIÉRARCHIE) ---

class DataProviderError(BaseValuationError):
    """Erreur générique liée à la récupération de données."""
    pass


class TickerNotFoundError(DataProviderError):
    @property
    def ui_user_message(self) -> str:
        return "Symbole (Ticker) introuvable ou radié. Vérifiez l'orthographe sur Yahoo Finance."


class DataInsufficientError(DataProviderError):
    @property
    def ui_user_message(self) -> str:
        return "Données financières insuffisantes ou incomplètes pour ce symbole (ex: Holding, SPAC ou données manquantes)."


class ExternalServiceError(DataProviderError):
    @property
    def ui_user_message(self) -> str:
        return "Erreur de connexion au fournisseur de données (Timeout/Réseau). Veuillez réessayer dans quelques instants."