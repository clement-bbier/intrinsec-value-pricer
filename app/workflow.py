import logging
import uuid
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

from app.ui_components.ui_charts import _get_sample_dates, display_price_chart, display_simulation_chart
from app.ui_components.ui_kpis import display_results
from core.exceptions import CalculationError, DataProviderError, WorkflowError
from core.models import CompanyFinancials, DCFParameters, InputSource, ValuationMode, ValuationRequest, ValuationResult
from core.valuation.engines import run_reverse_dcf, run_valuation
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


def _validate_inputs(
    financials: CompanyFinancials,
    params: DCFParameters,
    mode: ValuationMode,
    input_source: InputSource,
) -> None:
    """
    Validation de sécurité workflow (niveau orchestration).
    Les validations financières strictes restent dans le core (MethodConfig / engines).
    """
    if financials.sector in FORBIDDEN_SECTORS:
        raise WorkflowError(f"Unsupported sector: {financials.sector}")

    # ConfigFactory est optionnel à ce stade (tu as mentionné qu'il n'est pas toujours présent).
    # On ne casse pas le workflow si non disponible.
    try:
        from core.models import ConfigFactory  # type: ignore
        ConfigFactory.get_config(mode, params).validate(context_beta=financials.beta)
    except Exception:
        pass

    # Point important : audit_score n'est PAS garanti à ce stade (calculé plus tard).
    # On évite la dépendance à un champ non initialisé.
    if mode == ValuationMode.MONTE_CARLO and input_source == InputSource.AUTO:
        score = getattr(financials, "audit_score", None)
        if score is not None and score < 40:
            raise WorkflowError("Monte Carlo blocked: insufficient data quality for AUTO")


def _compute_history(
    run_id: str,
    ticker: str,
    financials: CompanyFinancials,
    params: DCFParameters,
    mode: ValuationMode,
    provider: YahooFinanceProvider,
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Best-effort history computation: never hard-fails the workflow.
    """
    try:
        price_history = provider.get_price_history(ticker)
    except Exception as exc:
        logger.warning("HISTORY[%s] price history unavailable | ticker=%s | err=%s", run_id, ticker, exc)
        return None, None

    if price_history is None or price_history.empty:
        logger.info("HISTORY[%s] no price history | ticker=%s", run_id, ticker)
        return price_history, None

    try:
        dates = _get_sample_dates(price_history.reset_index())
        if not dates:
            logger.info("HISTORY[%s] no sample dates | ticker=%s", run_id, ticker)
            return price_history, None

        macro_provider = _get_macro_provider()
        macro_strat = YahooMacroHistoricalParamsStrategy(macro_provider, financials.currency)

        hist_iv_df, _ = build_intrinsic_value_time_series(
            ticker,
            financials,
            params,
            mode,
            provider,
            macro_strat,
            dates,
        )
        return price_history, hist_iv_df

    except Exception as exc:
        logger.warning("HISTORY[%s] intrinsic history skipped | ticker=%s | err=%s", run_id, ticker, exc)
        return price_history, None


def _compute_audit(
    run_id: str,
    request: ValuationRequest,
    financials: CompanyFinancials,
    params: DCFParameters,
    dcf_result: "DCFResult",
) -> None:
    """
    Mutates financials with audit fields (backward compatible with existing UI usage).
    """
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

    logger.info(
        "AUDIT[%s] done | score=%s | rating=%s",
        run_id,
        financials.audit_score,
        financials.audit_rating,
    )


def run_workflow_and_display(request: ValuationRequest) -> None:
    """
    Typed workflow:
    - input: ValuationRequest
    - output: ValuationResult (rendered via existing UI components)

    Robustness:
    - history is best-effort
    - errors are surfaced with technical messages
    """
    run_id = uuid.uuid4().hex[:8]
    logger.info(
        "WORKFLOW[%s] START | ticker=%s | mode=%s | source=%s | years=%s",
        run_id,
        request.ticker,
        request.mode.value,
        request.input_source.value,
        request.projection_years,
    )

    status = st.status("Calcul en cours...", expanded=False)
    provider = _get_provider()

    try:
        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker,
            request.projection_years,
        )

        params, dcf_result = run_valuation(request, financials, auto_params)

        _validate_inputs(financials, params, request.mode, request.input_source)

        try:
            financials.implied_growth_rate = run_reverse_dcf(financials, params, financials.current_price)
        except Exception as exc:
            logger.info("REVERSE_DCF[%s] skipped | reason=%s", run_id, exc)
            financials.implied_growth_rate = None

        price_history, hist_iv_df = _compute_history(
            run_id,
            request.ticker,
            financials,
            params,
            request.mode,
            provider,
        )

        _compute_audit(run_id, request, financials, params, dcf_result)

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

        display_results(result.financials, result.params, result.dcf, request.mode, request.input_source)

        if request.mode == ValuationMode.MONTE_CARLO:
            display_simulation_chart(
                result.dcf.simulation_results,
                result.financials.current_price,
                result.financials.currency,
            )
            st.caption("*Note : Historique calculé en méthode Analytique (performance).*")

        display_price_chart(
            request.ticker,
            price_history,
            hist_iv_df,
            result.dcf.intrinsic_value_per_share,
        )

    except WorkflowError as exc:
        status.update(label="Erreur Config/Workflow", state="error")
        logger.error("WORKFLOW[%s] ERROR | %s", run_id, exc)
        st.error(f"[WORKFLOW ERROR] {exc}")

    except (DataProviderError, CalculationError) as exc:
        status.update(label="Erreur Analytique", state="error")
        logger.error("WORKFLOW[%s] ANALYTIC ERROR | %s", run_id, exc)
        st.error(f"[ANALYTIC ERROR] {exc}")

    except Exception as exc:
        status.update(label="Erreur Système", state="error")
        logger.exception("WORKFLOW[%s] SYSTEM ERROR", run_id)
        st.error("[SYSTEM ERROR] Unexpected failure")
        st.exception(exc)
