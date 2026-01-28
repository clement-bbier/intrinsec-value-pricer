"""
app/workflow.py

LOGICAL ORCHESTRATOR — Valuation Lifecycle Management.
Role: Pilots the analysis lifecycle, multi-temporal orchestration, and risk scenarios.
Architecture: Segmented Smart Merge, Point-in-Time Isolation, and Historical Validation.
"""

from __future__ import annotations
import logging
import traceback
from datetime import datetime, date
from typing import Any, List, Optional, Tuple

import streamlit as st
import numpy as np

# Interface and i18n imports
from src.interfaces import IResultRenderer, NullResultRenderer
from src.i18n import WorkflowTexts, DiagnosticTexts
from src.diagnostics import DiagnosticDomain, DiagnosticEvent, SeverityLevel
from src.exceptions import ValuationException
from src.models import (
    DCFParameters,
    InputSource,
    ValuationRequest,
    ScenarioResult,
    ScenarioSynthesis,
    ValuationResult,
    BacktestResult,
    HistoricalPoint
)
from src.valuation.engines import run_valuation
from src.quant_logger import QuantLogger
from infra.auditing.backtester import BacktestEngine
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. MAIN ENTRY POINT
# ==============================================================================

def run_workflow(
    request: ValuationRequest,
    renderer: Optional[IResultRenderer] = None
) -> Tuple[Optional[ValuationResult], Optional[YahooFinanceProvider]]:
    """
    Executes the complete valuation workflow.

    Architecture: Decouples computation from rendering via renderer injection.
    """
    # UI-facing status initialization
    status = st.status(WorkflowTexts.STATUS_MAIN_LABEL, expanded=True)
    _renderer = renderer or NullResultRenderer()

    try:
        # --- STEP 1: INFRASTRUCTURE & DATA ACQUISITION ---
        status.write(WorkflowTexts.STATUS_DATA_ACQUISITION)
        provider = YahooFinanceProvider(YahooMacroProvider())

        # Deep Fetch for structural analysis and backtesting support
        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker,
            request.projection_years
        )

        # Sectoral triangulation
        status.write(WorkflowTexts.STATUS_PEER_DISCOVERY)
        multiples_data = provider.get_peer_multiples(
            ticker=request.ticker,
            manual_peers=request.options.get("manual_peers")
        )
        request.options["multiples_data"] = multiples_data

        # --- STEP 2: CONCILIATION (SMART MERGE) ---
        status.write(WorkflowTexts.STATUS_SMART_MERGE)
        final_params = map_request_to_params(request, auto_params)

        # --- STEP 3: PRESENT ANALYSIS (BASE CASE) ---
        status.write(WorkflowTexts.STATUS_ENGINE_RUN.format(mode=request.mode.value))
        if final_params.monte_carlo.enable_monte_carlo:
            status.write(WorkflowTexts.STATUS_MC_RUN)

        # Core engine execution (IV + Triangulation + Audit)
        result = run_valuation(request, financials, final_params)

        # --- STEP 4: DETERMINISTIC SCENARIO ANALYSIS ---
        if final_params.scenarios.enabled:
            status.write(WorkflowTexts.STATUS_SCENARIOS_RUN)
            result.scenario_synthesis = compute_scenario_impact(
                request, financials, final_params, result
            )

        # --- STEP 5: HISTORICAL VALIDATION (POINT-IN-TIME BACKTESTING) ---
        if request.options.get("enable_backtest", False):
            status.write(WorkflowTexts.STATUS_BACKTEST_RUN)

            # Orchestrate backtest on raw fiscal data
            result.backtest_report = _orchestrate_backtesting(
                request=request,
                raw_data=provider.last_raw_data,
                params=final_params,
                price_history=provider.get_price_history(request.ticker),
                provider=provider
            )
            status.write(WorkflowTexts.STATUS_BACKTEST_COMPLETE)

        # --- STEP 6: FINALIZATION ---
        status.update(label=WorkflowTexts.STATUS_COMPLETE, state="complete", expanded=False)

        # Quantitative logging for stochastic performance
        if result.simulation_results:
            _log_monte_carlo_performance(request.ticker, result, final_params)

        return result, provider

    except ValuationException as e:
        status.update(label=WorkflowTexts.STATUS_INTERRUPTED, state="error", expanded=True)
        _display_diagnostic_message(e.diagnostic)
        return None, None

    except Exception as e:
        status.update(label=WorkflowTexts.STATUS_CRITICAL_ERROR, state="error", expanded=True)
        logger.error(f"Critical workflow error: {str(e)}", exc_info=True)
        _display_diagnostic_message(_create_crash_diagnostic(e))
        return None, None


def run_workflow_and_display(request: ValuationRequest) -> None:
    """Streamlit-specific facade for workflow orchestration."""
    from app.adapters import StreamlitResultRenderer

    renderer = StreamlitResultRenderer()
    result, provider = run_workflow(request, renderer)

    if result is not None and provider is not None:
        renderer.render_results(result, provider)


# ==============================================================================
# 2. BACKTESTING LOGIC (TEMPORAL ISOLATION)
# ==============================================================================

def _orchestrate_backtesting(
    request: ValuationRequest,
    raw_data: Any,
    params: DCFParameters,
    price_history: Any,
    provider: YahooFinanceProvider
) -> BacktestResult:
    """
    Simulates valuation over the last 3 fiscal years with Point-in-Time isolation.

    Ensures that historical calculations only use data available at that specific time.
    """
    points: List[HistoricalPoint] = []
    current_year = datetime.now().year
    years_to_test = [current_year - 1, current_year - 2, current_year - 3]

    for yr in years_to_test:
        try:
            # 1. Freeze raw data at fiscal year N
            frozen_raw = BacktestEngine.freeze_data_at_fiscal_year(raw_data, yr)
            if not frozen_raw: continue

            # 2. Retrograde financial mapping
            hist_financials = provider.map_raw_to_financials(frozen_raw)

            # 3. IV Calculation (Monte Carlo disabled for backtest throughput)
            v_params = params.model_copy(deep=True)
            v_params.monte_carlo.enable_monte_carlo = False
            hist_res = run_valuation(request, hist_financials, v_params)

            # 4. Fetch actual historical closing price
            market_price = BacktestEngine.get_historical_price_at(price_history, yr)

            if market_price > 0:
                points.append(HistoricalPoint(
                    valuation_date=date(yr, 12, 31),
                    intrinsic_value=hist_res.intrinsic_value_per_share,
                    market_price=market_price,
                    error_pct=(hist_res.intrinsic_value_per_share / market_price) - 1.0,
                    was_undervalued=(hist_res.intrinsic_value_per_share > market_price)
                ))
        except Exception as e:
            logger.warning(f"Backtest failed for year {yr}: {str(e)}")
            continue

    if not points: return BacktestResult()

    mae = sum(abs(p.error_pct) for p in points) / len(points)
    return BacktestResult(
        points=points,
        mean_absolute_error=mae,
        model_accuracy_score=max(0.0, 100.0 * (1.0 - mae))
    )


# ==============================================================================
# 3. SCENARIO ANALYSIS
# ==============================================================================

def compute_scenario_impact(
    request: ValuationRequest,
    financials: Any,
    params: DCFParameters,
    base_result: ValuationResult
) -> ScenarioSynthesis:
    """
    Computes Bull/Base/Bear impacts with resource optimization.

    Reuses base calculation if the 'Base' scenario variant is unchanged.
    """
    sc = params.scenarios
    results = []
    variants = [(sc.bull, "Bull"), (sc.base, "Base"), (sc.bear, "Bear")]

    for variant, label in variants:
        # Optimization: Reuse base result if variant metrics are null
        if label == "Base" and variant.growth_rate is None and variant.target_fcf_margin is None:
            val = base_result.intrinsic_value_per_share
            g_used, m_used = params.growth.fcf_growth_rate, params.growth.target_fcf_margin
        else:
            v_params = params.model_copy(deep=True)
            if variant.growth_rate is not None: v_params.growth.fcf_growth_rate = variant.growth_rate
            if variant.target_fcf_margin is not None: v_params.growth.target_fcf_margin = variant.target_fcf_margin

            # Engine lightweighting for variants
            v_params.monte_carlo.enable_monte_carlo = False
            v_res = run_valuation(request, financials, v_params)
            val, g_used, m_used = v_res.intrinsic_value_per_share, v_params.growth.fcf_growth_rate, v_params.growth.target_fcf_margin

        results.append(ScenarioResult(
            label=label, intrinsic_value=val, probability=variant.probability,
            growth_used=g_used or 0.0, margin_used=m_used or 0.0
        ))

    # Calculate mathematical expectation (Expected Value)
    expected_val = sum(r.intrinsic_value * r.probability for r in results)
    return ScenarioSynthesis(
        variants=results, expected_value=expected_val,
        max_upside=max(r.intrinsic_value for r in results),
        max_downside=min(r.intrinsic_value for r in results)
    )


# ==============================================================================
# 4. HELPERS & DIAGNOSTICS
# ==============================================================================

def map_request_to_params(request: ValuationRequest, auto_params: DCFParameters) -> DCFParameters:
    """
    Merges automated data with manual overrides (Expert mode).
    """
    if request.input_source == InputSource.MANUAL:
        final_params = auto_params.model_copy(deep=True)
        # Rates and growth overrides
        for section in ['rates', 'growth']:
            manual_data = getattr(request.manual_params, section).model_dump(exclude_unset=True)
            for k, v in manual_data.items():
                if v is not None: setattr(getattr(final_params, section), k, v)

        # Advanced configuration injection
        final_params.monte_carlo = request.manual_params.monte_carlo.model_copy()
        final_params.scenarios = request.manual_params.scenarios.model_copy()
        final_params.sotp = request.manual_params.sotp.model_copy()
        return final_params

    # Standard mode: Monte Carlo controlled by UI options
    auto_params.monte_carlo.enable_monte_carlo = request.options.get("enable_mc", False)
    auto_params.monte_carlo.num_simulations = request.options.get("mc_sims", 5000)
    return auto_params


def _log_monte_carlo_performance(ticker: str, result: ValuationResult, params: DCFParameters) -> None:
    """Logs stochastic metrics to quantitative logs."""
    vals = result.simulation_results
    QuantLogger.log_monte_carlo(
        ticker=ticker,
        simulations=len(vals),
        valid_ratio=len(vals) / params.monte_carlo.num_simulations,
        p50=float(np.median(vals)),
        p10=float(np.percentile(vals, 10)),
        p90=float(np.percentile(vals, 90))
    )


def _display_diagnostic_message(diag: DiagnosticEvent) -> None:
    """Displays a stylized UI alert for business errors."""
    level_fn = st.error if diag.severity in [SeverityLevel.CRITICAL, SeverityLevel.ERROR] else st.warning
    level_fn(f"**{diag.code}** : {diag.message}")
    with st.expander(WorkflowTexts.DIAG_EXPANDER_TITLE):
        st.markdown(f"**Action :** {diag.remediation_hint}")
        if diag.technical_detail: st.code(diag.technical_detail)


def _create_crash_diagnostic(error: Exception) -> DiagnosticEvent:
    """Generates a critical system crash diagnostic event."""
    return DiagnosticEvent(
        code="SYSTEM_CRASH", severity=SeverityLevel.CRITICAL, domain=DiagnosticDomain.SYSTEM,
        message=DiagnosticTexts.SYSTEM_CRASH_MSG,
        technical_detail=f"{str(error)}\n{traceback.format_exc()}",
        remediation_hint=DiagnosticTexts.SYSTEM_CRASH_HINT
    )