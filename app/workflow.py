import logging
import uuid
from typing import Optional, Tuple
import pandas as pd
import streamlit as st

# Imports UI
from app.ui_components.ui_charts import _get_sample_dates, display_price_chart, display_simulation_chart
from app.ui_components.ui_kpis import display_results

# Imports Core
from core.exceptions import (
    BaseValuationError,
    TickerNotFoundError,
    DataInsufficientError,
    ExternalServiceError,
    WorkflowError
)
from core.models import (
    CompanyFinancials,
    DCFParameters,
    ValuationMode,
    ValuationRequest,
    ValuationResult,
    InputSource,
    AuditReport
)
from core.valuation.engines import run_valuation, run_reverse_dcf
from core.valuation.historical import YahooMacroHistoricalParamsStrategy, build_intrinsic_value_time_series
from infra.auditing.audit_engine import AuditEngine
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

logger = logging.getLogger("app.workflow")


# --- FACTORY PROVIDERS ---
@st.cache_resource
def _get_provider() -> YahooFinanceProvider:
    return YahooFinanceProvider()


@st.cache_resource
def _get_macro_provider() -> YahooMacroProvider:
    return YahooMacroProvider()


# --- WORKFLOW STEPS ---

def _step_fetch_and_build(
        provider: YahooFinanceProvider,
        request: ValuationRequest
) -> Tuple[CompanyFinancials, DCFParameters]:
    try:
        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker,
            request.projection_years
        )
        return financials, auto_params
    except BaseValuationError:
        raise
    except Exception as e:
        raise WorkflowError(f"Echec récupération données: {str(e)}")


def _step_run_engine(
        request: ValuationRequest,
        financials: CompanyFinancials,
        auto_params: DCFParameters
) -> Tuple[DCFParameters, "DCFResult"]:
    if request.input_source == InputSource.MANUAL:
        effective_g = request.manual_params.fcf_growth_rate
        source_label = "MANUAL"
    else:
        effective_g = auto_params.fcf_growth_rate
        source_label = "AUTO"

    logger.info(
        "EFFECTIVE ASSUMPTIONS | ticker=%s | source=%s | g=%.2f%%",
        request.ticker, source_label, effective_g * 100
    )

    return run_valuation(request, financials, auto_params)


def _step_compute_history(
        run_id: str,
        request: ValuationRequest,
        financials: CompanyFinancials,
        params: DCFParameters,
        provider: YahooFinanceProvider
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Calcule l'historique de valorisation (Best Effort).
    """
    try:
        price_history = provider.get_price_history(request.ticker)
        if price_history.empty: return None, None

        dates = _get_sample_dates(price_history)
        if not dates: return price_history, None

        macro_provider = _get_macro_provider()
        macro_strat = YahooMacroHistoricalParamsStrategy(macro_provider, financials.currency)

        hist_iv_df, errors = build_intrinsic_value_time_series(
            request.ticker,
            financials,
            params,
            request.mode,
            provider,
            macro_strat,
            dates
        )

        if errors:
            # [CORRECTION] INFO au lieu de WARNING pour les trous de données attendus
            logger.info("HISTORY[%s] partial data gaps (expected): %s", run_id, errors[:3])

        return price_history, hist_iv_df

    except Exception as e:
        # Warning maintenu pour crash complet inattendu
        logger.warning("HISTORY[%s] failed: %s", run_id, e)
        return None, None


def _step_audit(
        request: ValuationRequest,
        financials: CompanyFinancials,
        params: DCFParameters,
        dcf_result: "DCFResult"
) -> AuditReport:
    """
    Exécute l'audit complet et retourne le rapport structuré.
    Met à jour financials pour compatibilité legacy, mais le rapport est la source de vérité.
    """
    tv_ev_ratio = 0.0
    if dcf_result.enterprise_value > 0:
        tv_ev_ratio = dcf_result.discounted_terminal_value / dcf_result.enterprise_value

    report = AuditEngine.compute_audit(
        financials=financials,
        params=params,
        simulation_results=dcf_result.simulation_results,
        tv_ev_ratio=tv_ev_ratio,
        mode=request.mode,
        input_source=request.input_source
    )

    # Retro-propagation pour affichage simple
    financials.audit_score = int(report.global_score)
    financials.audit_rating = report.rating

    return report


# --- MAIN ORCHESTRATOR ---

def run_workflow_and_display(request: ValuationRequest) -> None:
    run_id = uuid.uuid4().hex[:8]
    logger.info("WORKFLOW[%s] START | ticker=%s", run_id, request.ticker)

    status_container = st.status("Analyse en cours...", expanded=True)

    try:
        provider = _get_provider()

        status_container.write("1/5 Récupération des données financières...")
        financials, auto_params = _step_fetch_and_build(provider, request)

        status_container.write(f"2/5 Exécution du modèle {request.mode.value}...")
        params, dcf_result = _step_run_engine(request, financials, auto_params)

        if financials.current_price > 0:
            try:
                financials.implied_growth_rate = run_reverse_dcf(
                    financials, params, financials.current_price
                )
            except Exception:
                pass

        status_container.write("3/5 Analyse historique...")
        price_history, hist_iv_df = _step_compute_history(
            run_id, request, financials, params, provider
        )

        status_container.write("4/5 Audit de confiance...")
        audit_report = _step_audit(request, financials, params, dcf_result)

        status_container.update(label="Analyse Terminée", state="complete", expanded=False)

        # Construction du Résultat Final
        result_obj = ValuationResult(
            request=request,
            financials=financials,
            params=params,
            dcf=dcf_result,
            audit_report=audit_report
        )

        # Affichage
        display_results(result_obj)

        if request.mode == ValuationMode.MONTE_CARLO and dcf_result.simulation_results:
            display_simulation_chart(
                dcf_result.simulation_results,
                financials.current_price,
                financials.currency
            )

        display_price_chart(
            request.ticker,
            price_history,
            hist_iv_df,
            dcf_result.intrinsic_value_per_share
        )

        logger.info("WORKFLOW[%s] SUCCESS", run_id)

    except BaseValuationError as e:
        status_container.update(label="Erreur Analyse", state="error", expanded=False)
        st.error(f"⛔ {e.ui_user_message}")
        logger.warning("WORKFLOW[%s] Domain Error: %s", run_id, str(e))

    except Exception as e:
        status_container.update(label="Erreur Système", state="error", expanded=False)
        st.error("Une erreur inattendue est survenue.")
        logger.exception("WORKFLOW[%s] CRITICAL UNHANDLED ERROR", run_id)