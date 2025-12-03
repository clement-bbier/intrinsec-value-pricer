import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class CalculationError(Exception):
    """
    Raised when the DCF valuation cannot be computed
    due to invalid assumptions, mathematical inconsistencies,
    or structural model constraints.

    Accepts optional context for better debugging:
        raise CalculationError("WACC <= g", context={"wacc": wacc, "g": g})
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context

        if context is not None:
            logger.error("[CalculationError] %s | Context: %s", message, context)
        else:
            logger.error("[CalculationError] %s", message)

    def __repr__(self):
        return f"CalculationError(message={self.args[0]!r}, context={self.context})"


class DataProviderError(Exception):
    """
    Raised when the data provider fails to return valid financial information:
        - missing critical fields (price, shares, cash flow, etc.)
        - invalid ticker
        - API failure or malformed data
        - values inconsistent with model requirements

    Accepts optional context for traceability.
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context

        if context is not None:
            logger.error("[DataProviderError] %s | Context: %s", message, context)
        else:
            logger.error("[DataProviderError] %s", message)

    def __repr__(self):
        return f"DataProviderError(message={self.args[0]!r}, context={self.context})"
