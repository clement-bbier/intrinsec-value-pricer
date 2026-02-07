"""
src/core/__init__.py

CORE MODULE EXPORTS
===================
Exposes the foundational building blocks of the Valuation Engine.
Centralizes technical cross-cutting concerns (Logging, Error Handling, Formatting).
"""

from src.core.diagnostics import (
    DiagnosticEvent,
    SeverityLevel,
    DiagnosticDomain
)

from src.core.exceptions import (
    ValuationException,
    ConfigurationError,
    ExternalServiceError,
    TickerNotFoundError,
    DataMissingError,
    CalculationError,
    InvalidParameterError
)

from src.core.formatting import (
    format_smart_number,
    get_delta_color,
    COLOR_POSITIVE,
    COLOR_NEGATIVE,
    COLOR_NEUTRAL
)

from src.core.interfaces import (
    IUIProgressHandler,
    IResultRenderer,
    DataProviderProtocol,
    NullProgressHandler
)

from src.core.quant_logger import (
    QuantLogger,
    log_valuation
)

__all__ = [
    # Diagnostics
    "DiagnosticEvent",
    "SeverityLevel",
    "DiagnosticDomain",

    # Exceptions
    "ValuationException",
    "ConfigurationError",
    "ExternalServiceError",
    "TickerNotFoundError",
    "DataMissingError",
    "CalculationError",
    "InvalidParameterError",

    # Formatting
    "format_smart_number",
    "get_delta_color",
    "COLOR_POSITIVE",
    "COLOR_NEGATIVE",
    "COLOR_NEUTRAL",

    # Interfaces
    "IUIProgressHandler",
    "IResultRenderer",
    "DataProviderProtocol",
    "NullProgressHandler",

    # Logger
    "QuantLogger",
    "log_valuation",
]