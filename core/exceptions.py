"""
core/exceptions.py
Exceptions typées transportant des diagnostics structurés.

Version : V2.0 — DT-001/002/020/021 Resolution
- Migration des imports vers core.i18n
- Amélioration des messages d'erreur pédagogiques
"""

import logging
from typing import Optional
from core.diagnostics import (
    DiagnosticEvent,
    SeverityLevel,
    DiagnosticDomain,
    DiagnosticRegistry
)
# DT-001/002: Import depuis core.i18n au lieu de app.ui_components
from core.i18n import DiagnosticTexts

logger = logging.getLogger(__name__)

class ValuationException(Exception):
    """Exception racine standardisée."""
    def __init__(self, diagnostic: DiagnosticEvent):
        self.diagnostic = diagnostic
        super().__init__(diagnostic.message)
        logger.error(
            f"[{diagnostic.code}] {diagnostic.message} "
            f"(Severity: {diagnostic.severity.value}, Domain: {diagnostic.domain.value})"
        )

# ==============================================================================
# 1. ADAPTATEURS DE DONNÉES ET INFRASTRUCTURE
# ==============================================================================

class TickerNotFoundError(ValuationException):
    def __init__(self, ticker: str):
        event = DiagnosticEvent(
            code="DATA_TICKER_NOT_FOUND",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.DATA,
            message=DiagnosticTexts.TICKER_NOT_FOUND_MSG.format(ticker=ticker),
            technical_detail=f"Symbole reçu : {ticker}",
            remediation_hint=DiagnosticTexts.TICKER_NOT_FOUND_HINT
        )
        super().__init__(event)

class DataMissingError(ValuationException):
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
# 2. ERREURS DE MODÉLISATION ET CALCULS
# ==============================================================================

class ModelIncoherenceError(ValuationException):
    def __init__(self, model_name: str, issue: str, values_context: str):
        event = DiagnosticEvent(
            code="MODEL_LOGIC_ERROR",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.MODEL,
            message=DiagnosticTexts.MODEL_LOGIC_MSG.format(model=model_name, issue=issue),
            technical_detail=f"Valeurs : {values_context}",
            remediation_hint=DiagnosticTexts.MODEL_LOGIC_HINT
        )
        super().__init__(event)

class ModelDivergenceError(ValuationException):
    def __init__(self, g: float, wacc: float):
        super().__init__(DiagnosticRegistry.model_g_divergence(g, wacc))

class MonteCarloInstabilityError(ValuationException):
    def __init__(self, valid_ratio: float, threshold: float):
        super().__init__(DiagnosticRegistry.model_mc_instability(valid_ratio, threshold))

class CalculationError(ValuationException):
    def __init__(self, message: str):
        event = DiagnosticEvent(
            code="CALCULATION_GENERIC_ERROR",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.MODEL,
            message=message,
            remediation_hint=DiagnosticTexts.CALC_GENERIC_HINT
        )
        super().__init__(event)
