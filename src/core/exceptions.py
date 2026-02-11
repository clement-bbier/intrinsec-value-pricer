"""
src/core/exceptions.py

TYPED EXCEPTIONS WITH STRUCTURED DIAGNOSTICS
============================================
Role: Provides type-safe domain exceptions carrying structured diagnostic metadata.
Pattern: Domain Exceptions / Diagnostic Transport.
Architecture: Decouples business failure logic from UI rendering.
Style: Numpy docstrings.
"""

from __future__ import annotations

import logging

from src.core.diagnostics import DiagnosticDomain, DiagnosticEvent, DiagnosticRegistry, SeverityLevel

logger = logging.getLogger(__name__)


class ValuationException(Exception):
    """
    Standardized root exception for the entire valuation engine.

    Attributes
    ----------
    diagnostic : DiagnosticEvent
        Structured metadata about the failure.
    """
    def __init__(self, diagnostic: DiagnosticEvent):
        self.diagnostic = diagnostic
        super().__init__(diagnostic.message)
        logger.error(
            f"[{diagnostic.code}] {diagnostic.message} "
            f"(Severity: {diagnostic.severity.value}, Domain: {diagnostic.domain.value})"
        )


# ==============================================================================
# 1. INFRASTRUCTURE & CONFIGURATION
# ==============================================================================

class ConfigurationError(ValuationException):
    """Raised when critical configuration files (YAML) are missing or invalid."""
    def __init__(self, file_path: str, details: str):
        event = DiagnosticEvent(
            code="CONFIG_LOAD_ERROR",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.CONFIG,
            message=f"Failed to load configuration: {file_path}",
            technical_detail=details,
            remediation_hint="Check file permissions and YAML syntax."
        )
        super().__init__(event)


class ExternalServiceError(ValuationException):
    """Raised when an external API (Yahoo, Macro) fails or times out."""
    def __init__(self, provider: str, error_detail: str):
        event = DiagnosticEvent(
            code="PROVIDER_CONNECTION_FAIL",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.PROVIDER,
            message=f"Connection failed to provider: {provider}",
            technical_detail=error_detail,
            remediation_hint="Check network connection or try again later."
        )
        super().__init__(event)


class TickerNotFoundError(ValuationException):
    """Raised when the financial provider cannot resolve a stock symbol."""
    def __init__(self, ticker: str):
        event = DiagnosticEvent(
            code="DATA_TICKER_NOT_FOUND",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.DATA,
            message=f"Ticker '{ticker}' not found.",
            technical_detail=f"Input symbol: {ticker}",
            remediation_hint="Verify the ticker symbol on Yahoo Finance."
        )
        super().__init__(event)


class DataMissingError(ValuationException):
    """Raised when a mandatory financial field is absent from the dataset."""
    def __init__(self, missing_field: str, ticker: str, year: int | None = None):
        if year:
            msg = f"Missing data for {ticker}: Field '{missing_field}' (Year: {year})."
        else:
            msg = f"Missing data for {ticker}: Field '{missing_field}'."

        event = DiagnosticEvent(
            code="DATA_MISSING_FIELD",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.DATA,
            message=msg,
            remediation_hint="Try 'Expert Mode' to manually input missing data."
        )
        super().__init__(event)


# ==============================================================================
# 2. MODELING AND CALCULATION ERRORS
# ==============================================================================

class ModelDivergenceError(ValuationException):
    """Raised when Gordon Growth parameters prevent model convergence (g >= WACC)."""
    def __init__(self, g: float, wacc: float):
        super().__init__(DiagnosticRegistry.model_g_divergence(g, wacc))


class MonteCarloInstabilityError(ValuationException):
    """Raised when the simulation fails to produce enough valid iterations."""
    def __init__(self, valid_ratio: float, threshold: float):
        super().__init__(DiagnosticRegistry.model_mc_instability(valid_ratio, threshold))


class CalculationError(ValuationException):
    """Raised for generic mathematical failures during model execution."""
    def __init__(self, message: str):
        event = DiagnosticEvent(
            code="CALCULATION_GENERIC_ERROR",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.MODEL,
            message=message,
            remediation_hint="Check inputs for zero-division or invalid ranges."
        )
        super().__init__(event)


class InvalidParameterError(ValuationException):
    """Raised when a user-provided parameter is outside allowed bounds."""
    def __init__(self, param_name: str, value: float, bounds: tuple[float, float]):
        event = DiagnosticEvent(
            code="CONFIG_INVALID_PARAM",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.CONFIG,
            message=f"Parameter '{param_name}' value {value} is out of bounds {bounds}.",
            remediation_hint="Adjust the parameter to be within the allowed range."
        )
        super().__init__(event)
