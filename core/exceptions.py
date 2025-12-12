import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseValuationError(Exception):
    """
    Base class for all domain-specific errors.
    Carries an optional context dict for diagnostics and UI surfacing.
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.context = context

        log_message = f"[{self.__class__.__name__}] {message}"
        if context:
            log_message += f" | context={context}"
        logger.error(log_message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.args[0]!r}, context={self.context})"


class CalculationError(BaseValuationError):
    """Mathematical/model inconsistency errors."""
    pass


class DataProviderError(BaseValuationError):
    """Provider / source data errors (Yahoo, missing fields, rate-limit, etc.)."""
    pass


class ConfigurationError(BaseValuationError):
    """Invalid user/model configuration (weights, bounds, etc.)."""
    pass


class WorkflowError(BaseValuationError):
    """Orchestration errors (invalid state, missing manual inputs, etc.)."""
    pass


class ApplicationStartupError(BaseValuationError):
    """Raised when application cannot safely start (environment/import/config)."""
    pass
