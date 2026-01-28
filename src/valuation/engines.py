"""
src/valuation/engines.py

UNIFIED VALUATION ENGINE — STRATEGY ORCHESTRATOR
===============================================
Role: Orchestrates financial strategies, Monte Carlo injection, and institutional auditing.
Architecture: Strategy Pattern with Dynamic Wrapping (ST-1.2 Compliance).
Resiliency: Strict boundary for mathematical and system exceptions.

Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
import traceback
from typing import Optional, Dict, Type

from src.i18n import DiagnosticTexts
from src.config.constants import TechnicalDefaults
from src.exceptions import (
    ValuationException,
    DiagnosticEvent,
    SeverityLevel,
    DiagnosticDomain,
    CalculationError,
    ModelDivergenceError
)
from src.models import (
    ValuationRequest,
    ValuationMode,
    CompanyFinancials,
    DCFParameters,
    ValuationResult
)
from src.valuation.strategies import ValuationStrategy
from src.valuation.strategies.monte_carlo import MonteCarloGenericStrategy
from src.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy

# Registry and Telemetry
from src.valuation.registry import get_strategy
from src.quant_logger import QuantLogger, LogDomain

logger = logging.getLogger(__name__)

# Targeted mathematical error boundary for stochastic stability
VALUATION_ERRORS = (
    CalculationError,
    ModelDivergenceError,
    ValueError,
    ZeroDivisionError
)


# ==============================================================================
# 1. ENGINE ORCHESTRATION
# ==============================================================================

def run_valuation(
    request: ValuationRequest,
    financials: CompanyFinancials,
    params: DCFParameters
) -> ValuationResult:
    """
    Executes the unified valuation lifecycle and triggers the institutional audit.

    This function acts as the Strategy Router, determining whether to run a
    deterministic model or a probabilistic Monte Carlo simulation.

    Parameters
    ----------
    request : ValuationRequest
        The formal analyst request specifying mode and ticker.
    financials : CompanyFinancials
        Unified financial data container.
    params : DCFParameters
        Validated parameters (Rates, Growth, Monte Carlo).

    Returns
    -------
    ValuationResult
        The final audited result, including Glass Box traces and audit scores.
    """
    logger.info(f"[Engine] Initializing {request.mode.value} for {request.ticker}")

    # A. Strategy Resolution via Registry
    strategy_cls = get_strategy(request.mode)
    if not strategy_cls:
        raise _raise_unknown_strategy(request.mode)

    # B. Monte Carlo Injection (Stochastic Wrapping)
    # Checks if MC is enabled in params AND supported by the specific mode
    use_mc = params.monte_carlo.enable_monte_carlo and request.mode.supports_monte_carlo
    strategy = (
        MonteCarloGenericStrategy(strategy_cls=strategy_cls, glass_box_enabled=True)
        if use_mc else strategy_cls()
    )

    try:
        # C. Financial Algorithm Execution
        result = strategy.execute(financials, params)

        # D. Lineage Traceability: Context Injection
        _inject_context(result, request)

        # E. Relative Analysis: Market Multiples Triangulation (Pillar 5)
        _apply_triangulation(result, request, financials, params)

        # F. Institutional Audit Engine (Lazy Import to prevent circularity)
        from infra.auditing.audit_engine import AuditEngine
        result.audit_report = AuditEngine.compute_audit(result)

        # G. SOLID Contract Validation
        strategy.verify_output_contract(result)

        _log_final_status(request, result)

        return result

    except CalculationError as ce:
        # Managed business error (e.g., negative FCF in auto mode)
        raise _handle_calculation_error(ce)
    except ValuationException:
        # Propagation of already typed domain exceptions
        raise
    except Exception as e:
        # Critical System Failure (Glass Box catch-all)
        logger.error(f"[Engine] Critical System Failure: {str(e)}")
        QuantLogger.log_error(ticker=request.ticker, error=str(e), domain=LogDomain.VALUATION)
        raise _handle_system_crash(e)


# ==============================================================================
# 2. QUANT SOLVERS (REVERSE DCF)
# ==============================================================================

def run_reverse_dcf(
    financials: CompanyFinancials,
    params: DCFParameters,
    market_price: float,
    max_iterations: int = 50
) -> Optional[float]:
    """
    Calculates the Implied Growth Rate (g) using the Bisection method.

    Solves for $g$ such that $IV(g) \approx Price_{market}$.
    """
    if market_price <= 0:
        return None

    # Search bounds from technical constants
    low = TechnicalDefaults.REVERSE_DCF_LOW_BOUND
    high = TechnicalDefaults.REVERSE_DCF_HIGH_BOUND
    strategy = FundamentalFCFFStrategy(glass_box_enabled=False)

    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        test_params = params.model_copy(deep=True)
        test_params.growth.fcf_growth_rate = mid

        try:
            res = strategy.execute(financials, test_params)
            iv = res.intrinsic_value_per_share

            # Check for convergence threshold
            if abs(iv - market_price) < TechnicalDefaults.VALUATION_CONVERGENCE_THRESHOLD:
                return mid

            if iv < market_price:
                low = mid
            else:
                high = mid
        except VALUATION_ERRORS:
            # If a bound creates mathematical divergence, tighten the search
            high = mid

    return None



# ==============================================================================
# 3. INTERNAL HELPERS
# ==============================================================================

def _inject_context(result: ValuationResult, request: ValuationRequest) -> None:
    """Injects the original request into the result for i18n and audit traceability."""
    try:
        result.request = request
    except (AttributeError, TypeError):
        # Fallback for frozen/read-only models
        object.__setattr__(result, "request", request)

def _apply_triangulation(
    result: ValuationResult,
    request: ValuationRequest,
    financials: CompanyFinancials,
    params: DCFParameters
) -> None:
    """Handles optional Pillar 5 triangulation via market peer multiples."""
    multiples_data = request.options.get("multiples_data")

    if multiples_data and hasattr(multiples_data, "peers") and len(multiples_data.peers) > 0:
        try:
            from src.valuation.strategies.multiples import MarketMultiplesStrategy
            rel_strategy = MarketMultiplesStrategy(multiples_data=multiples_data)
            result.multiples_triangulation = rel_strategy.execute(financials, params)
            logger.info(f"[Engine] Triangulation Complete | n={len(multiples_data.peers)}")
        except VALUATION_ERRORS as e:
            logger.warning(f"[Engine] Triangulation failed (non-critical): {str(e)}")
            result.multiples_triangulation = None

def _log_final_status(request: ValuationRequest, result: ValuationResult) -> None:
    """Signals successful completion to the QuantLogger."""
    score = result.audit_report.global_score if result.audit_report else 0.0
    logger.info(f"[Engine] Valuation Complete | audit_score={score:.1f}")

    QuantLogger.log_success(
        ticker=request.ticker,
        mode=request.mode.value,
        iv=result.intrinsic_value_per_share,
        audit_score=score,
        market_price=result.market_price,
        upside=result.upside_pct
    )

def _raise_unknown_strategy(mode: ValuationMode) -> ValuationException:
    return ValuationException(DiagnosticEvent(
        code="UNKNOWN_STRATEGY",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message=DiagnosticTexts.UNKNOWN_STRATEGY_MSG.format(mode=mode),
        remediation_hint=DiagnosticTexts.UNKNOWN_STRATEGY_HINT
    ))

def _handle_calculation_error(ce: CalculationError) -> ValuationException:
    return ValuationException(DiagnosticEvent(
        code="CALCULATION_ERROR",
        severity=SeverityLevel.ERROR,
        domain=DiagnosticDomain.MODEL,
        message=str(ce),
        remediation_hint=DiagnosticTexts.CALC_GENERIC_HINT
    ))

def _handle_system_crash(e: Exception) -> ValuationException:
    return ValuationException(DiagnosticEvent(
        code="STRATEGY_CRASH",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message=DiagnosticTexts.STRATEGY_CRASH_MSG.format(error=str(e)),
        technical_detail=traceback.format_exc(),
        remediation_hint=DiagnosticTexts.STRATEGY_CRASH_HINT
    ))

def _build_legacy_registry() -> Dict[ValuationMode, Type[ValuationStrategy]]:
    """
    Builds the correspondence table for backward compatibility.
    Required for unit tests.
    """
    from src.valuation.registry import StrategyRegistry
    return {
        mode: meta.strategy_cls
        for mode, meta in StrategyRegistry.get_all_modes().items()
    }

# Used by router
STRATEGY_REGISTRY = _build_legacy_registry()