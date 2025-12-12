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


class CalculationError(BaseValuationError):
    """Erreur mathématique ou incohérence de modèle (ex: WACC <= g)."""
    pass


class WorkflowError(BaseValuationError):
    """Erreur d'orchestration ou d'état (ex: paramètres manquants)."""
    pass


class ApplicationStartupError(BaseValuationError):
    """Erreur critique au démarrage (config, environnement)."""
    pass


# --- DATA PROVIDER ERRORS (HIÉRARCHIE) ---

class DataProviderError(BaseValuationError):
    """Erreur générique liée à la récupération de données."""
    pass


class TickerNotFoundError(DataProviderError):
    """
    Le symbole est introuvable, radié ou mal orthographié.
    L'UI doit inviter l'utilisateur à corriger sa saisie.
    """
    pass


class DataInsufficientError(DataProviderError):
    """
    Le ticker existe, mais les données financières sont trop pauvres
    pour effectuer une valorisation (ex: Coquille vide, Holding obscure).
    """
    pass


class ExternalServiceError(DataProviderError):
    """
    Erreur technique du fournisseur (Timeout, Rate-limit, API Down).
    L'UI doit suggérer de réessayer plus tard.
    """
    pass