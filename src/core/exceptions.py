"""
src/exceptions.py

TYPED EXCEPTIONS WITH STRUCTURED DIAGNOSTICS
============================================
Role: Provides type-safe domain exceptions carrying structured diagnostic metadata.
Pattern: Domain Exceptions / Diagnostic Transport.
Architecture: Decouples business failure logic from UI rendering.

Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.core.diagnostics import (
    DiagnosticEvent,
    SeverityLevel,
    DiagnosticDomain,
    DiagnosticRegistry
)
# Centralized i18n mapping
from src.i18n import DiagnosticTexts, MODEL_VALIDATION_TEXTS



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
        # Institutional Developer Logging
        logger.error(
            f"[{diagnostic.code}] {diagnostic.message} "
            f"(Severity: {diagnostic.severity.value}, Domain: {diagnostic.domain.value})"
        )

# ==============================================================================
# 1. DATA ADAPTERS AND INFRASTRUCTURE
# ==============================================================================

class TickerNotFoundError(ValuationException):
    """Raised when the financial provider cannot resolve a stock symbol."""
    def __init__(self, ticker: str):
        event = DiagnosticEvent(
            code="DATA_TICKER_NOT_FOUND",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.DATA,
            message=DiagnosticTexts.TICKER_NOT_FOUND_MSG.format(ticker=ticker),
            technical_detail=f"Input symbol: {ticker}",
            remediation_hint=DiagnosticTexts.TICKER_NOT_FOUND_HINT
        )
        super().__init__(event)

class DataMissingError(ValuationException):
    """Raised when a mandatory financial field is absent from the dataset."""
    def __init__(self, missing_field: str, ticker: str, year: Optional[int] = None):
        if year:
            msg = DiagnosticTexts.DATA_FIELD_MISSING_YEAR.format(ticker=ticker, field=missing_field, year=year)
        else:
            msg = DiagnosticTexts.DATA_FIELD_MISSING_GENERIC.format(ticker=ticker, field=missing_field)

        event = DiagnosticEvent(
            code="DATA_MISSING_FIELD",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.DATA,
            message=msg,
            remediation_hint=DiagnosticTexts.DATA_FIELD_HINT
        )
        super().__init__(event)

class ExternalServiceError(ValuationException):
    """Raised when an external API (Yahoo, Macro) fails or times out."""
    def __init__(self, provider: str, error_detail: str):
        event = DiagnosticEvent(
            code="PROVIDER_CONNECTION_FAIL",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.PROVIDER,
            message=DiagnosticTexts.PROVIDER_FAIL_MSG.format(provider=provider),
            technical_detail=error_detail,
            remediation_hint=DiagnosticTexts.PROVIDER_FAIL_HINT
        )
        super().__init__(event)

# ==============================================================================
# 2. MODELING AND CALCULATION ERRORS
# ==============================================================================

class ModelIncoherenceError(ValuationException):
    """Raised when model inputs violate fundamental economic principles."""
    def __init__(self, model_name: str, issue: str, values_context: str):
        event = DiagnosticEvent(
            code="MODEL_LOGIC_ERROR",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.MODEL,
            message=DiagnosticTexts.MODEL_LOGIC_MSG.format(model=model_name, issue=issue),
            technical_detail=f"Context: {values_context}",
            remediation_hint=DiagnosticTexts.MODEL_LOGIC_HINT
        )
        super().__init__(event)

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
            remediation_hint=DiagnosticTexts.CALC_GENERIC_HINT
        )
        super().__init__(event)

# ==============================================================================
# 3. USER INPUT AND CONFIGURATION ERRORS (NEW)
# ==============================================================================

class InvalidParameterError(ValuationException):
    """Raised when a user-provided parameter is outside allowed bounds."""
    def __init__(self, param_name: str, value: float, bounds: tuple[float, float]):
        event = DiagnosticEvent(
            code="CONFIG_INVALID_PARAM",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.CONFIG,
            message=MODEL_VALIDATION_TEXTS.INVALID_PARAM.format(
                name=param_name, val=value, min=bounds[0], max=bounds[1]
            ),
            remediation_hint=DiagnosticTexts.CALC_GENERIC_HINT
        )
        super().__init__(event)

class UnsupportedModelError(ValuationException):
    """Raised when a requested valuation mode is not implemented for the ticker."""
    def __init__(self, mode: str, sector: str):
        event = DiagnosticEvent(
            code="REGISTRY_UNSUPPORTED_MODE",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.ENGINE,
            message=f"Model '{mode}' is not compatible with sector '{sector}'.",
            remediation_hint="Please switch to a model suitable for this industry."
        )
        super().__init__(event)