import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BaseValuationError(Exception):
    """
    Classe de base abstraite pour toutes les exceptions spécifiques
    au domaine de la valorisation d'entreprise.
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context

        # Log l'erreur directement à l'instanciation
        log_message = f"[BaseValuationError] {message}"
        if context is not None:
            log_message += f" | Context: {context}"

        logger.error(log_message)

    def __repr__(self):
        return f"{self.__class__.__name__}(message={self.args[0]!r}, context={self.context})"


class CalculationError(BaseValuationError):
    """
    Erreur de Calcul Mathématique ou Incohérence Modèle.

    Exemples :
    - Dénominateur de Gordon-Shapiro nul (WACC <= g_perp).
    - Division par zéro (e.g., Shares Outstanding = 0).
    - Résultats intermédiaires absurdes (e.g., Valeur Nette Négative non gérable).
    """
    # Cette classe hérite de BaseValuationError, elle est prête.
    pass


class DataProviderError(BaseValuationError):
    """
    Erreur d'Infrastructure ou de Données Source (Input Data).

    Exemples :
    - Échec d'API (Yahoo Finance hors service).
    - Ticker non trouvé.
    - Données financières critiques manquantes (ex: FCF historique ou Beta).
    - Valeurs récupérées qui ne passent pas les contrôles de cohérence initiaux.
    """
    # Cette classe hérite de BaseValuationError, elle est prête.
    pass


class ConfigurationError(BaseValuationError):
    """
    Erreur de Configuration Utilisateur/Modèle.

    Cette erreur est typiquement levée par la couche MethodConfig ou UI Validation.
    Exemples :
    - La somme des poids D/E manuels n'est pas égale à 100%.
    - Taux d'impôt saisi est > 100%.
    """
    pass