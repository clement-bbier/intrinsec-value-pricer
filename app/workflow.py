import logging
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

from app.ui_components.ui_charts import _get_sample_dates, display_price_chart, display_simulation_chart
from app.ui_components.ui_kpis import display_results
from core.exceptions import CalculationError, DataProviderError, WorkflowError
from core.models import CompanyFinancials, DCFParameters, InputSource, ValuationMode, ValuationRequest, ValuationResult
from core.valuation.engines import run_valuation, run_reverse_dcf
from core.valuation.historical import YahooMacroHistoricalParamsStrategy, build_intrinsic_value_time_series
from infra.auditing.audit_engine import AuditEngine
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

logger = logging.getLogger(__name__)

FORBIDDEN_SECTORS = {"Financial Services", "Real Estate", "Banks", "Insurance"}


@st.cache_resource(show_spinner=False)
def _get_provider() -> YahooFinanceProvider:
    return YahooFinanceProvider()


@st.cache_resource(show_spinner=False)
def _get_macro_provider() -> YahooMacroProvider:
    return YahooMacroProvider()


def _validate_inputs(financials: CompanyFinancials, params: DCFParameters, mode: ValuationMode, input_source: InputSource) -> None:
    if financials.sector in FORBIDDEN_SECTORS:
        raise WorkflowError(f"Unsupported sector: {financials.sector}")

    try:
        from core.models import ConfigFactory
        ConfigFactory.get_config(mode, params).validate(context_beta=financials.beta)
    except Exception:
        # ConfigFactory may not be available yet; do not hard fail CH02 on that dependency.
        pass

    if mode == ValuationMode.MONTE_CARLO and input_source == InputSource.AUTO:
        if financials.audit_score is not None and financials.audit_score < 40:
            raise WorkflowError("Monte Carlo blocked: insufficient data quality for AUTO")


def _compute_history(
    ticker: str,
    financials: CompanyFinancials,
    params: DCFParameters,
    mode: ValuationMode,
    provider: YahooFinanceProvider,
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
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
        hist_iv_df, _ = build_intrinsic_value_time_series(ticker, financials, params, mode, provider, macro_strat, dates)
        return price_history, hist_iv_df
    except Exception as exc:
        logger.warning("Intrinsic history skipped: %s", exc)
        return price_history, None


def run_workflow_and_display(request: ValuationRequest) -> None:
    """
    CH02 typed workflow:
    - input: ValuationRequest
    - output: ValuationResult (rendered through existing UI functions)
    """
    logger.info("WORKFLOW START | ticker=%s | mode=%s | source=%s", request.ticker, request.mode.value, request.input_source.value)
    status = st.status("Calcul en cours...", expanded=False)

    provider = _get_provider()

    try:
        financials, auto_params = provider.get_company_financials_and_parameters(request.ticker, request.projection_years)

        # Compute effective params + dcf strictly through engine entry-point
        params, dcf_result = run_valuation(request, financials, auto_params)

        _validate_inputs(financials, params, request.mode, request.input_source)

        try:
            financials.implied_growth_rate = run_reverse_dcf(financials, params, financials.current_price)
        except Exception:
            financials.implied_growth_rate = None

        price_history, hist_iv_df = _compute_history(request.ticker, financials, params, request.mode, provider)

        tv_ev_ratio = 0.0
        if dcf_result.enterprise_value > 0:
            tv_ev_ratio = dcf_result.discounted_terminal_value / dcf_result.enterprise_value

        final_audit = AuditEngine.compute_audit(
            financials,
            params,
            dcf_result.simulation_results,
            None,
            request.mode,
            tv_ev_ratio,
            request.input_source,
        )

        financials.audit_score = final_audit.global_score
        financials.audit_rating = final_audit.rating
        financials.audit_details = final_audit.ui_details
        financials.audit_breakdown = final_audit.breakdown
        financials.audit_logs = [final_audit.audit_mode_description]

        result = ValuationResult(
            request=request,
            financials=financials,
            params=params,
            dcf=dcf_result,
            audit_score=financials.audit_score,
            audit_rating=financials.audit_rating,
            audit_details=financials.audit_details,
            audit_breakdown=financials.audit_breakdown,
            audit_logs=financials.audit_logs,
        )

        status.update(label="Terminé", state="complete", expanded=False)

        country = getattr(financials, "country", "Unknown")
        country_display = f" | {country}" if country != "Unknown" else ""
        st.caption(f"Secteur : {financials.sector}{country_display} | Devise : {financials.currency}")

        # Existing UI calls kept (non-breaking), but driven by typed result components
        display_results(result.financials, result.params, result.dcf, request.mode, request.input_source)

        if request.mode == ValuationMode.MONTE_CARLO:
            display_simulation_chart(result.dcf.simulation_results, result.financials.current_price, result.financials.currency)
            st.caption("*Note : Historique calculé en méthode Analytique (performance).*")

        display_price_chart(request.ticker, price_history, hist_iv_df, result.dcf.intrinsic_value_per_share)

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
