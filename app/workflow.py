"""
app/workflow.py

LOGICAL ORCHESTRATOR — Valuation Lifecycle Management.
======================================================
Role: Pilots the analysis lifecycle, multi-temporal orchestration, and risk scenarios.
Architecture: Segmented Smart Merge, Point-in-Time Isolation, and Enrichment Phases.
ST-4.2 Compliant.
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
    Parameters,
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
    Executes the logical analysis pipeline:
    Acquisition -> Consolidation -> Core (P1-3) -> Enrichment (P4-5).
    """
    status = st.status(WorkflowTexts.STATUS_MAIN_LABEL, expanded=True)
    _renderer = renderer or NullResultRenderer()

    try:
        # --- PHASE 1: DATA ACQUISITION (Foundations) ---
        status.write(WorkflowTexts.STATUS_DATA_ACQUISITION)
        provider = YahooFinanceProvider(YahooMacroProvider())

        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker,
            request.projection_years
        )

        # --- PHASE 2: CONSOLIDATION (SSOT Smart Merge) ---
        # Harmonizes all sources (Auto/Manual) into the unified Parameters object
        status.write(WorkflowTexts.STATUS_SMART_MERGE)
        final_params = map_request_to_params(request, auto_params)

        # --- PHASE 3: CORE EXECUTION (Pillars 1, 2, 3) ---
        # Strictly Deterministic: IV calculation, Step Trace, and Reliability Audit
        status.write(WorkflowTexts.STATUS_ENGINE_RUN.format(mode=request.mode.value))

        # Isolation: Ensure Monte Carlo internal logic is disabled for the base case
        base_run_params = final_params.model_copy(deep=True)
        base_run_params.monte_carlo.enabled = False

        result = run_valuation(request, financials, base_run_params)

        # --- PHASE 4: RISK ENGINEERING (Pillar 4) ---
        # 4.1 Monte Carlo Simulation (Vectorized Shocks)
        if final_params.monte_carlo.enabled:
            status.write(WorkflowTexts.STATUS_MC_RUN)
            from src.computation.statistics import MonteCarloEngine

            mc_data = MonteCarloEngine.simulate_from_result(result, final_params)
            result.simulation_results = mc_data.values
            result.quantiles = mc_data.quantiles

        # 4.2 Deterministic Scenario Analysis (Conviction Overrides)
        if final_params.scenarios.enabled:
            status.write(WorkflowTexts.STATUS_SCENARIOS_RUN)
            result.scenario_synthesis = compute_scenario_impact(
                request, financials, final_params, result
            )

        # 4.3 Historical Backtesting (Past Accuracy Audit)
        if final_params.backtest.enabled:
            status.write(WorkflowTexts.STATUS_BACKTEST_RUN)
            result.backtest_report = _orchestrate_backtesting(
                request=request,
                raw_data=provider.last_raw_data,
                params=final_params,
                price_history=provider.get_price_history(request.ticker),
                provider=provider
            )
            status.write(WorkflowTexts.STATUS_BACKTEST_COMPLETE)

        # --- PHASE 5: MARKET ANALYSIS (Pillar 5) ---
        # 5.1 Peer Discovery & Multiples Triangulation
        if final_params.peers.enabled:
            status.write(WorkflowTexts.STATUS_PEER_DISCOVERY)

            # 1. Fetch raw sectoral data
            raw_multiples = provider.get_peer_multiples(
                ticker=request.ticker,
                manual_peers=final_params.peers.manual_peers
            )

            # 2. Compute implied values using the specific Strategy
            # Senior: Call .execute() to match the strategy interface
            from src.valuation.strategies.multiples import MarketMultiplesStrategy
            multiples_engine = MarketMultiplesStrategy(multiples_data=raw_multiples)
            result.multiples_triangulation = multiples_engine.execute(financials, final_params)

        # 5.2 SOTP Breakdown (Structural Analysis)
        if final_params.sotp.enabled:
            # SOTP results are pre-populated in the params during UI entry
            result.sotp_results = final_params.sotp

        # --- PHASE 6: FINALIZATION & TELEMETRY ---
        status.update(label=WorkflowTexts.STATUS_COMPLETE, state="complete", expanded=False)

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
    """
    Streamlit-specific facade to run the workflow and render results.

    Parameters
    ----------
    request : ValuationRequest
        The validated request object from the UI.
    """
    from app.adapters import StreamlitResultRenderer

    renderer = StreamlitResultRenderer()
    result, provider = run_workflow(request, renderer)

    if result is not None and provider is not None:
        renderer.render_results(result, provider)


# ==============================================================================
# 2. ANALYTICAL HELPERS
# ==============================================================================

def map_request_to_params(request: ValuationRequest, auto_params: Parameters) -> Parameters:
    """
    Merges automated financial data with manual expert overrides.

    Parameters
    ----------
    request : ValuationRequest
        The incoming request containing manual parameters.
    auto_params : Parameters
        Default parameters extracted from the data provider.

    Returns
    -------
    Parameters
        The final parameter set for engine execution.
    """
    if request.input_source == InputSource.MANUAL:
        final_params = auto_params.model_copy(deep=True)

        # Merge Rates and Growth sections
        for section in ['rates', 'growth']:
            manual_data = getattr(request.manual_params, section).model_dump(exclude_unset=True)
            for k, v in manual_data.items():
                if v is not None:
                    setattr(getattr(final_params, section), k, v)

        # Inject advanced analytical configurations
        final_params.monte_carlo = request.manual_params.monte_carlo.model_copy()
        final_params.scenarios = request.manual_params.scenarios.model_copy()
        final_params.sotp = request.manual_params.sotp.model_copy()
        return final_params

    # Standard Mode logic
    auto_params.monte_carlo.enabled = request.options.get("enable_mc", False)
    auto_params.monte_carlo.num_simulations = request.options.get("mc_sims", 5000)
    return auto_params


def compute_scenario_impact(
    request: ValuationRequest,
    financials: Any,
    params: Parameters,
    base_result: ValuationResult
) -> ScenarioSynthesis:
    """
    Computes Bull/Base/Bear impacts with deterministic variation.

    Parameters
    ----------
    request : ValuationRequest
        Request context.
    financials : Any
        Company financials object.
    params : Parameters
        The base parameter set.
    base_result : ValuationResult
        The result of the base case calculation.

    Returns
    -------
    ScenarioSynthesis
        Synthesis of the deterministic variations.
    """
    sc = params.scenarios
    results = []
    variants = [(sc.bull, "Bull"), (sc.base, "Base"), (sc.bear, "Bear")]

    for variant, label in variants:
        # Optimization: Reuse base result if variant metrics are identical
        if label == "Base" and variant.growth_rate is None and variant.target_fcf_margin is None:
            val = base_result.intrinsic_value_per_share
            g_used = params.growth.fcf_growth_rate
            m_used = params.growth.target_fcf_margin
        else:
            v_params = params.model_copy(deep=True)
            if variant.growth_rate is not None:
                v_params.growth.fcf_growth_rate = variant.growth_rate
            if variant.target_fcf_margin is not None:
                v_params.growth.target_fcf_margin = variant.target_fcf_margin

            # Engine lightweighting (Disable Monte Carlo for scenarios)
            v_params.monte_carlo.enabled = False
            v_res = run_valuation(request, financials, v_params)

            val = v_res.intrinsic_value_per_share
            g_used = v_params.growth.fcf_growth_rate
            m_used = v_params.growth.target_fcf_margin

        results.append(ScenarioResult(
            label=label, intrinsic_value=val, probability=variant.probability,
            growth_used=g_used or 0.0, margin_used=m_used or 0.0
        ))

    return ScenarioSynthesis(
        variants=results,
        expected_value=sum(r.intrinsic_value * r.probability for r in results),
        max_upside=max(r.intrinsic_value for r in results),
        max_downside=min(r.intrinsic_value for r in results)
    )


def _orchestrate_backtesting(
    request: ValuationRequest,
    raw_data: Any,
    params: Parameters,
    price_history: Any,
    provider: YahooFinanceProvider
) -> BacktestResult:
    """
    Executes historical point-in-time validation.

    Returns
    -------
    BacktestResult
        Aggregated historical performance metrics.
    """
    points: List[HistoricalPoint] = []
    current_year = datetime.now().year
    years_to_test = [current_year - 1, current_year - 2, current_year - 3]

    for yr in years_to_test:
        try:
            frozen_raw = BacktestEngine.freeze_data_at_fiscal_year(raw_data, yr)
            if not frozen_raw: continue

            hist_financials = provider.map_raw_to_financials(frozen_raw)

            v_params = params.model_copy(deep=True)
            v_params.monte_carlo.enabled = False
            hist_res = run_valuation(request, hist_financials, v_params)

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
# 3. TELEMETRY & DIAGNOSTICS
# ==============================================================================

def _log_monte_carlo_performance(ticker: str, result: ValuationResult, params: Parameters) -> None:
    """
    Forwards stochastic execution metrics to the institutional logger.
    """
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
    """
    Renders standardized error alerts in the Streamlit UI.
    """
    level_fn = st.error if diag.severity in [SeverityLevel.CRITICAL, SeverityLevel.ERROR] else st.warning
    level_fn(f"**{diag.code}** : {diag.message}")

    with st.expander(WorkflowTexts.DIAG_EXPANDER_TITLE):
        st.markdown(f"**Action :** {diag.remediation_hint}")
        if diag.technical_detail:
            st.code(diag.technical_detail)


def _create_crash_diagnostic(error: Exception) -> DiagnosticEvent:
    """
    Generates a fallback diagnostic event for unhandled system exceptions.
    """
    return DiagnosticEvent(
        code="SYSTEM_CRASH",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message=DiagnosticTexts.SYSTEM_CRASH_MSG,
        technical_detail=f"{str(error)}\n{traceback.format_exc()}",
        remediation_hint=DiagnosticTexts.SYSTEM_CRASH_HINT
    )