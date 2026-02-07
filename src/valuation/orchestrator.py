"""
src/valuation/orchestrator.py

UNIFIED VALUATION ENGINE — STRATEGY ORCHESTRATOR
================================================
Role: Orchestrates financial strategies, Risk Analysis, and Market Extensions.
Architecture: Strategy Pattern with Extension Hooks (V19 - Stable).
Resiliency: Strict boundary for mathematical and system exceptions.

Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
import traceback
from typing import Optional

# Config & Constants
from src.config.constants import ValuationEngineDefaults
from src.i18n import DiagnosticTexts

# Exceptions
from src.core.exceptions import (
    ValuationException,
    DiagnosticEvent,
    SeverityLevel,
    DiagnosticDomain,
    CalculationError,
    ModelDivergenceError
)

# Models (Imports explicites pour éviter les erreurs de résolution Pylance)
from src.models.valuation import ValuationResult, ValuationRequest
from src.models.company import Company
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.strategies import FCFFStandardParameters
from src.models.enums import ValuationMethodology

# Core Interfaces & Registry
from src.valuation.strategies.interface import IValuationRunner
from src.valuation.registry import StrategyRegistry

# Extension Runners
from src.valuation.options.monte_carlo import MonteCarloRunner
from src.valuation.options.sensitivity import SensitivityRunner
from src.valuation.options.sotp import SOTPRunner
from src.valuation.options.peers import PeersRunner

# Logging
from src.core.quant_logger import QuantLogger, LogDomain

logger = logging.getLogger(__name__)

# Targeted mathematical error boundary
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
    financials: Company,
    params: Parameters
) -> ValuationResult:
    """
    Executes the unified valuation lifecycle.

    Flow:
    1. Resolve Strategy Runner (Factory).
    2. Execute Main Deterministic Valuation (Core Intrinsic Value).
    3. Execute Extensions (Risk, SOTP, Peers).
    4. Log and Return.

    Parameters
    ----------
    request : ValuationRequest
        The formal analyst request specifying mode and ticker.
    financials : Company
        Unified financial data container.
    params : Parameters
        Validated parameters.

    Returns
    -------
    ValuationResult
        The final result including core value and optional extension outputs.
    """
    logger.info(f"[Engine] Initializing {request.mode.value} for {request.ticker}")

    # A. Strategy Resolution via Registry
    # -----------------------------------
    strategy_cls = StrategyRegistry.get_strategy_cls(request.mode)
    if not strategy_cls:
        raise _raise_unknown_strategy(request.mode)

    # Instantiate the stateless runner
    runner: IValuationRunner = strategy_cls()

    try:
        # B. Financial Algorithm Execution (Deterministic Base Case)
        # ----------------------------------------------------------
        result = runner.execute(financials, params)

        # C. Inject Context (Traceability)
        # --------------------------------
        _inject_context(result, request)

        # D. Execute Extensions (Pillars 4 & 5 + New Pillar 3 Benchmarking)
        # -----------------------------------------------------------------
        _run_extensions(runner, result, financials, params, request)

        # E. Final Validation & Logging
        # -----------------------------
        _log_final_status(request, result, financials)

        return result

    except CalculationError as ce:
        raise _handle_calculation_error(ce)
    except ValuationException:
        raise
    except Exception as e:
        logger.error(f"[Engine] Critical System Failure: {str(e)}")
        QuantLogger.log_error(ticker=request.ticker, error=str(e), domain=LogDomain.VALUATION)
        raise _handle_system_crash(e)


# ==============================================================================
# 2. EXTENSION ORCHESTRATION
# ==============================================================================

def _run_extensions(
    runner: IValuationRunner,
    result: ValuationResult,
    financials: Company,
    params: Parameters,
    request: ValuationRequest
) -> None:
    """
    Orchestrates the execution of optional modules.
    """
    ext_params = params.extensions
    ext_results = result.results.extensions

    # 1. Sum-of-the-Parts (SOTP)
    if ext_params.sotp.enabled:
        ext_results.sotp = SOTPRunner.execute(params)

    # 2. Peers Triangulation (Relative Valuation)
    multiples_data = request.options.get("multiples_data") if request.options else None

    if ext_params.peers.enabled and multiples_data:
        try:
            ext_results.peers = PeersRunner.execute(financials, multiples_data)
        except Exception as e:
            logger.warning(f"[Engine] Peers triangulation skipped: {e}")

    # 3. Monte Carlo Simulation
    if ext_params.monte_carlo.enabled:
        original_gb_state = runner.glass_box_enabled
        runner.glass_box_enabled = False
        try:
            mc_engine = MonteCarloRunner(strategy=runner)
            ext_results.monte_carlo = mc_engine.execute(params, financials)
        finally:
            runner.glass_box_enabled = original_gb_state

    # 4. Sensitivity Analysis
    if ext_params.sensitivity.enabled:
        original_gb_state = runner.glass_box_enabled
        runner.glass_box_enabled = False
        try:
            sensi_engine = SensitivityRunner(strategy=runner)
            # Appel explicite avec les bons arguments nommés
            ext_results.sensitivity = sensi_engine.execute(base_params=params, financials=financials)
        finally:
            runner.glass_box_enabled = original_gb_state


# ==============================================================================
# 3. QUANT SOLVERS (REVERSE DCF)
# ==============================================================================

def run_reverse_dcf(
    financials: Company,
    params: Parameters,
    market_price: float,
    max_iterations: int = ValuationEngineDefaults.MAX_ITERATIONS
) -> Optional[float]:
    """
    Calculates the Implied Growth Rate (g).
    """
    if market_price <= 0:
        return None

    # Use Standard FCFF Strategy via local import to verify contract
    from src.valuation.strategies.standard_fcff import StandardFCFFStrategy

    strategy = StandardFCFFStrategy()
    strategy.glass_box_enabled = False

    test_params = params.model_copy(deep=True)

    if not isinstance(test_params.strategy, FCFFStandardParameters):
        return None

    low = ValuationEngineDefaults.REVERSE_DCF_LOW_BOUND
    high = ValuationEngineDefaults.REVERSE_DCF_HIGH_BOUND

    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        test_params.strategy.growth_rate_p1 = mid

        try:
            res = strategy.execute(financials, test_params)
            iv = res.results.common.intrinsic_value_per_share

            if abs(iv - market_price) < ValuationEngineDefaults.CONVERGENCE_TOLERANCE:
                return mid

            if iv < market_price:
                low = mid
            else:
                high = mid
        except VALUATION_ERRORS:
            high = mid

    return None


# ==============================================================================
# 4. INTERNAL HELPERS & ERROR HANDLING
# ==============================================================================

def _inject_context(result: ValuationResult, request: ValuationRequest) -> None:
    result.request = request

def _log_final_status(
    request: ValuationRequest,
    result: ValuationResult,
    financials: Company
) -> None:
    """Signals successful completion to the QuantLogger."""
    logger.info(f"[Engine] Valuation Complete for {request.ticker}")

    iv = result.results.common.intrinsic_value_per_share
    upside = result.results.common.upside_pct
    market_price = financials.current_price or 0.0

    QuantLogger.log_success(
        ticker=request.ticker,
        mode=request.mode.value,
        iv=iv,
        audit_score=0.0,
        market_price=market_price,
        upside=upside
    )

def _raise_unknown_strategy(mode: ValuationMethodology) -> ValuationException:
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