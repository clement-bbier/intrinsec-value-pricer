"""
src/core/__init__.py

CORE MODULE EXPORTS
===================
Exposes the foundational building blocks of the Valuation Engine.
Centralizes technical cross-cutting concerns (Logging, Error Handling, Formatting).
"""

from src.core.diagnostics import DiagnosticDomain, DiagnosticEvent, SeverityLevel
from src.core.exceptions import (
    CalculationError,
    ConfigurationError,
    DataMissingError,
    ExternalServiceError,
    InvalidParameterError,
    TickerNotFoundError,
    ValuationError,
)
from src.core.formatting import COLOR_NEGATIVE, COLOR_NEUTRAL, COLOR_POSITIVE, format_smart_number, get_delta_color
from src.core.interfaces import DataProviderProtocol, IResultRenderer, IUIProgressHandler, NullProgressHandler
from src.core.quant_logger import QuantLogger, log_valuation

__all__ = [
    # Diagnostics
    "DiagnosticEvent",
    "SeverityLevel",
    "DiagnosticDomain",
    # Exceptions
    "ValuationError",
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
