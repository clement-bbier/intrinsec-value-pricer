"""
src/valuation/orchestrator.py

UNIFIED VALUATION ENGINE — STRATEGY ORCHESTRATOR
================================================
Role: Orchestrates financial strategies, Risk Analysis, and Market Extensions.
Architecture: Strategy Pattern with Extension Hooks (V18).
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
from src.exceptions import (
    ValuationException,
    DiagnosticEvent,
    SeverityLevel,
    DiagnosticDomain,
    CalculationError,
    ModelDivergenceError
)

# Models (Explicit imports to avoid circular dependency issues)
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
from src.quant_logger import QuantLogger, LogDomain

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

    # Instantiate the stateless runner (Must implement IValuationRunner)
    runner: IValuationRunner = strategy_cls()

    try:
        # B. Financial Algorithm Execution (Deterministic Base Case)
        # ----------------------------------------------------------
        # This computes the "Intrinsic Value" (Pillar 1 & 2)
        result = runner.execute(financials, params)

        # C. Inject Context (Traceability)
        # --------------------------------
        _inject_context(result, request)

        # D. Execute Extensions (Pillars 4 & 5 + New Pillar 3 Benchmarking)
        # -----------------------------------------------------------------
        # Includes Monte Carlo, Sensitivity, SOTP, and Peers Triangulation
        _run_extensions(runner, result, financials, params, request)

        # E. Final Validation & Logging
        # -----------------------------
        # No more "Audit Score". We validate the calculation integrity only.
        _log_final_status(request, result, financials)

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
    Orchestrates the execution of optional modules based on Parameters.
    Populates the 'result.results.extensions' bundle.

    Parameters
    ----------
    runner : IValuationRunner
        The active strategy runner (needed for MC/Sensitivity).
    result : ValuationResult
        The result object to populate with extensions.
    financials : Company
        Financial data.
    params : Parameters
        Configuration parameters.
    request : ValuationRequest
        Original request (for accessing option payloads like Peers Data).
    """
    ext_params = params.extensions
    ext_results = result.results.extensions

    # 1. Sum-of-the-Parts (SOTP) - Pillar 5
    if ext_params.sotp.enabled:
        # SOTPRunner.execute is static and standalone
        ext_results.sotp = SOTPRunner.execute(params)

    # 2. Peers Triangulation (Market Positioning - Pillar 3/5)
    # This runs the relative valuation logic to populate the benchmark view.
    # We retrieve the multiples data that was fetched alongside the financials.
    multiples_data = request.options.get("multiples_data") if request.options else None

    if ext_params.peers.enabled and multiples_data:
        try:
            # PeersRunner compares Target vs Competitors
            ext_results.peers = PeersRunner.execute(financials, multiples_data)
        except Exception as e:
            logger.warning(f"[Engine] Peers triangulation skipped: {e}")

    # 3. Monte Carlo Simulation (Risk Analysis - Pillar 4)
    if ext_params.monte_carlo.enabled:
        # We disable Glass Box for the simulation to improve performance
        original_gb_state = runner.glass_box_enabled
        runner.glass_box_enabled = False

        try:
            # MonteCarloRunner is instantiated with the runner strategy
            mc_engine = MonteCarloRunner(strategy=runner)
            ext_results.monte_carlo = mc_engine.execute(params, financials)
        finally:
            # Restore state
            runner.glass_box_enabled = original_gb_state

    # 4. Sensitivity Analysis (Risk Analysis - Pillar 4)
    if ext_params.sensitivity.enabled:
        original_gb_state = runner.glass_box_enabled
        runner.glass_box_enabled = False

        try:
            # SensitivityRunner must be instantiated with the strategy runner
            sensi_engine = SensitivityRunner(strategy=runner)
            # Call execute with named parameters matching definition
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
    Calculates the Implied Growth Rate (g) using the Bisection method.
    Solves for g such that IV(g) ~= Price_market.

    Parameters
    ----------
    financials : Company
        Financial data.
    params : Parameters
        Base parameters to solve from.
    market_price : float
        The target price to match.
    max_iterations : int, optional
        Solver limit, by default ValuationEngineDefaults.MAX_ITERATIONS.

    Returns
    -------
    Optional[float]
        The implied growth rate, or None if convergence fails.
    """
    if market_price <= 0:
        return None

    # Use the Standard FCFF Strategy for solving
    # Explicit import to avoid circular dependency at top level
    from src.valuation.strategies.standard_fcff import StandardFCFFStrategy

    strategy = StandardFCFFStrategy()
    strategy.glass_box_enabled = False

    # Create a working copy of parameters
    test_params = params.model_copy(deep=True)

    # Ensure we are modifying the right parameter type
    if not isinstance(test_params.strategy, FCFFStandardParameters):
        return None

    low = ValuationEngineDefaults.REVERSE_DCF_LOW_BOUND
    high = ValuationEngineDefaults.REVERSE_DCF_HIGH_BOUND

    for _ in range(max_iterations):
        mid = (low + high) / 2.0

        # Inject test growth
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
            # Convergence failure protection (e.g. infinite growth)
            high = mid

    return None


# ==============================================================================
# 4. INTERNAL HELPERS & ERROR HANDLING
# ==============================================================================

def _inject_context(result: ValuationResult, request: ValuationRequest) -> None:
    """Injects the original request into the result."""
    result.request = request

def _log_final_status(
    request: ValuationRequest,
    result: ValuationResult,
    financials: Company
) -> None:
    """Signals successful completion to the QuantLogger."""
    logger.info(f"[Engine] Valuation Complete for {request.ticker}")

    # Extract computed values for logging
    iv = result.results.common.intrinsic_value_per_share
    upside = result.results.common.upside_pct
    market_price = financials.current_price or 0.0

    # Log Success.
    QuantLogger.log_success(
        ticker=request.ticker,
        mode=request.mode.value,
        iv=iv,
        audit_score=0.0, # Placeholder, legacy field kept for logger compatibility
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