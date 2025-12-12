import logging
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

from app.ui_components.ui_charts import _get_sample_dates, display_price_chart, display_simulation_chart
from app.ui_components.ui_kpis import display_results
from core.exceptions import CalculationError, DataProviderError, WorkflowError
from core.models import CompanyFinancials, DCFParameters, InputSource, ValuationMode
from core.valuation.engines import run_deterministic_dcf, run_monte_carlo_dcf, run_reverse_dcf
from core.valuation.historical import YahooMacroHistoricalParamsStrategy, build_intrinsic_value_time_series
from infra.auditing.audit_engine import AuditEngine
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

logger = logging.getLogger(__name__)

FORBIDDEN_SECTORS = {"Financial Services", "Real Estate", "Banks", "Insurance"}


@st.cache_resource(show_spinner=False)
def _get_provider() -> YahooFinanceProvider:
    """
    Returns a cached provider instance.
    Must not be created at module import time.
    """
    return YahooFinanceProvider()


@st.cache_resource(show_spinner=False)
def _get_macro_provider() -> YahooMacroProvider:
    """
    Returns a cached macro provider instance.
    Must not be created at module import time.
    """
    return YahooMacroProvider()


def _apply_manual_overrides(
    financials: CompanyFinancials,
    auto_params: DCFParameters,
    manual_params: DCFParameters,
    manual_beta: Optional[float],
) -> Tuple[CompanyFinancials, DCFParameters]:
    """
    Apply manual parameters while preserving required stochastic parameters from auto.
    """
    params = manual_params

    if manual_beta is not None:
        financials.beta = manual_beta

    params.beta_volatility = auto_params.beta_volatility
    params.growth_volatility = auto_params.growth_volatility
    params.terminal_growth_volatility = auto_params.terminal_growth_volatility

    if params.manual_fcf_base is not None:
        financials.fcf_last = params.manual_fcf_base
        financials.fcf_fundamental_smoothed = params.manual_fcf_base

    financials.source_growth = "manual"
    financials.source_debt = "manual"
    financials.source_fcf = "manual"

    return financials, params


def _validate_inputs(
    financials: CompanyFinancials,
    params: DCFParameters,
    mode: ValuationMode,
    input_source: InputSource,
) -> None:
    """
    Validates method configuration and business exclusions.
    Raises WorkflowError on validation failure.
    """
    try:
        from core.models import ConfigFactory  # local import to keep startup deterministic
        ConfigFactory.get_config(mode, params).validate(context_beta=financials.beta)
    except ValueError as exc:
        raise WorkflowError(f"Invalid configuration: {exc}") from exc

    if financials.sector in FORBIDDEN_SECTORS:
        raise WorkflowError(f"Unsupported sector: {financials.sector}")

    if mode == ValuationMode.MONTE_CARLO and input_source == InputSource.AUTO and financials.audit_score < 40:
        raise WorkflowError("Monte Carlo blocked: insufficient data quality for AUTO")


def _compute_history(
    ticker: str,
    financials: CompanyFinancials,
    params: DCFParameters,
    mode: ValuationMode,
    provider: YahooFinanceProvider,
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Computes price history and optional intrinsic value time series.
    Never raises: history is best-effort.
    """
    try:
        price_history = provider.get_price_history(ticker)
    except Exception as exc:
        logger.warning("Price history unavailable: %s", exc)
        return None, None

    if price_history is None or price_history.empty:
        return price_history, None

    try:
        dates = _get_sample_dates(price_history.reset_index())
        if not dates:
            return price_history, None

        macro_provider = _get_macro_provider()
        macro_strat = YahooMacroHistoricalParamsStrategy(macro_provider, financials.currency)
        hist_iv_df, _ = build_intrinsic_value_time_series(
            ticker, financials, params, mode, provider, macro_strat, dates
        )
        return price_history, hist_iv_df
    except Exception as exc:
        logger.warning("Intrinsic history skipped: %s", exc)
        return price_history, None


def run_workflow_and_display(
    ticker: str,
    projection_years: int,
    mode: ValuationMode,
    input_source: InputSource = InputSource.AUTO,
    manual_params: Optional[DCFParameters] = None,
    manual_beta: Optional[float] = None,
) -> None:
    """
    Orchestrates provider fetch, valuation, audit, and UI rendering.
    CH01 constraints:
    - provider instances are created at runtime only (cached)
    - module import must not trigger network calls or instantiation
    """
    logger.info("WORKFLOW START | ticker=%s | mode=%s | source=%s", ticker, mode.value, input_source.value)
    status = st.status("Calcul en cours...", expanded=False)

    provider = _get_provider()

    try:
        financials, auto_params = provider.get_company_financials_and_parameters(ticker, projection_years)

        if input_source == InputSource.MANUAL:
            if manual_params is None:
                raise WorkflowError("Manual parameters are missing")
            financials, params = _apply_manual_overrides(financials, auto_params, manual_params, manual_beta)
        else:
            params = auto_params

        _validate_inputs(financials, params, mode, input_source)

        if mode == ValuationMode.MONTE_CARLO:
            dcf_result = run_monte_carlo_dcf(financials, params)
        else:
            dcf_result = run_deterministic_dcf(financials, params, mode)

        try:
            financials.implied_growth_rate = run_reverse_dcf(financials, params, financials.current_price)
        except Exception:
            financials.implied_growth_rate = None

        price_history, hist_iv_df = _compute_history(ticker, financials, params, mode, provider)

        tv_ev_ratio = 0.0
        if dcf_result.enterprise_value > 0:
            tv_ev_ratio = dcf_result.discounted_terminal_value / dcf_result.enterprise_value

        final_audit = AuditEngine.compute_audit(
            financials,
            params,
            dcf_result.simulation_results,
            None,
            mode,
            tv_ev_ratio,
            input_source,
        )

        financials.audit_score = final_audit.global_score
        financials.audit_rating = final_audit.rating
        financials.audit_details = final_audit.ui_details
        financials.audit_breakdown = final_audit.breakdown
        financials.audit_logs = [final_audit.audit_mode_description]

        status.update(label="Terminé", state="complete", expanded=False)

        country = getattr(financials, "country", "Unknown")
        country_display = f" | {country}" if country != "Unknown" else ""
        st.caption(f"Secteur : {financials.sector}{country_display} | Devise : {financials.currency}")

        display_results(financials, params, dcf_result, mode, input_source)

        if mode == ValuationMode.MONTE_CARLO:
            display_simulation_chart(dcf_result.simulation_results, financials.current_price, financials.currency)
            st.caption("*Note : Historique calculé en méthode Analytique (performance).*")

        display_price_chart(ticker, price_history, hist_iv_df, dcf_result.intrinsic_value_per_share)

    except WorkflowError as exc:
        status.update(label="Erreur Config/Workflow", state="error")
        st.error(f"[WORKFLOW ERROR] {exc}")

    except (DataProviderError, CalculationError) as exc:
        status.update(label="Erreur Analytique", state="error")
        st.error(f"[ANALYTIC ERROR] {exc}")

    except Exception as exc:
        status.update(label="Erreur Système", state="error")
        st.error("[SYSTEM ERROR] Unexpected failure")
        st.exception(exc)
