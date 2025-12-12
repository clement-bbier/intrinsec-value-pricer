import logging
import uuid
import sys
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
    InputSource
)
from core.valuation.engines import run_valuation, run_reverse_dcf
from core.valuation.historical import YahooMacroHistoricalParamsStrategy, build_intrinsic_value_time_series
from infra.auditing.audit_engine import AuditEngine
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

logger = logging.getLogger("app.workflow")


# --- FACTORY PROVIDERS ---
# (Cachés au niveau resource pour éviter réinstanciation)

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
    """
    Étape 1 & 2 : Fetch Data + Build Parameters
    Gère la logique Auto vs Manuel pour la construction initiale.
    """
    try:
        # En mode Manuel, on récupère quand même les financials pour avoir le prix, la dette, etc.
        # En mode Auto, cela récupère aussi les paramètres calculés.
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
    """
    Étape 3 : Run Valuation Engine
    Combine Request + Financials + AutoParams -> Result
    """
    # Log des hypothèses effectives avant le calcul
    if request.input_source == InputSource.MANUAL:
        effective_g = request.manual_params.fcf_growth_rate
        effective_wacc = "Manuel/Calculé"
        source_label = "MANUAL"
    else:
        effective_g = auto_params.fcf_growth_rate
        effective_wacc = "Auto"
        source_label = "AUTO"

    logger.info(
        "EFFECTIVE ASSUMPTIONS | ticker=%s | source=%s | g=%.2f%% | wacc_mode=%s",
        request.ticker, source_label, effective_g * 100, effective_wacc
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
    Étape 4 : Historique & Backtest (Best Effort)
    Ne lève pas d'exception bloquante.
    """
    try:
        # 1. Historique Prix
        price_history = provider.get_price_history(request.ticker)
        if price_history.empty:
            return None, None

        # 2. Dates d'échantillonnage
        dates = _get_sample_dates(price_history)
        if not dates:
            return price_history, None

        # 3. Calcul VI Historique
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
            logger.warning("HISTORY[%s] partial errors: %s", run_id, errors[:3])

        return price_history, hist_iv_df

    except Exception as e:
        logger.warning("HISTORY[%s] failed: %s", run_id, e)
        return None, None


def _step_audit(
        request: ValuationRequest,
        financials: CompanyFinancials,
        params: DCFParameters,
        dcf_result: "DCFResult"
) -> None:
    """
    Étape 5 : Audit & Scoring
    Met à jour l'objet financials in-place.
    """
    # Ratio TV/EV pour vérifier la dépendance à l'infini
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

    financials.audit_score = report.global_score
    financials.audit_rating = report.rating
    financials.audit_details = report.ui_details
    financials.audit_breakdown = report.breakdown
    financials.audit_logs = report.terminal_logs


# --- MAIN ORCHESTRATOR ---

def run_workflow_and_display(request: ValuationRequest) -> None:
    """
    Orchestrateur Principal.
    Gère le cycle de vie, les erreurs UI et l'affichage.
    """
    run_id = uuid.uuid4().hex[:8]
    logger.info(
        "WORKFLOW[%s] START | ticker=%s | mode=%s | source=%s",
        run_id, request.ticker, request.mode.value, request.input_source.value
    )

    # Conteneur de statut UI pour feedback utilisateur
    status_container = st.status("Analyse en cours...", expanded=True)

    try:
        provider = _get_provider()

        # 1. FETCH & BUILD
        status_container.write("Récupération des données financières...")
        financials, auto_params = _step_fetch_and_build(provider, request)

        # 2. RUN VALUATION
        status_container.write(f"Exécution du modèle {request.mode.value}...")
        params, dcf_result = _step_run_engine(request, financials, auto_params)

        # 3. REVERSE DCF (Optionnel / Informatif)
        if financials.current_price > 0:
            try:
                financials.implied_growth_rate = run_reverse_dcf(
                    financials, params, financials.current_price
                )
            except Exception:
                pass

        # 4. HISTORY (Async-like / Best Effort)
        status_container.write("Analyse historique & Backtesting...")
        price_history, hist_iv_df = _step_compute_history(
            run_id, request, financials, params, provider
        )

        # 5. AUDIT
        status_container.write("Audit de cohérence et scoring...")
        _step_audit(request, financials, params, dcf_result)

        # Fin du processing
        status_container.update(label="Analyse Terminée", state="complete", expanded=False)

        # 6. RENDER RESULTS
        # Construction de l'objet résultat final pour l'UI
        result_obj = ValuationResult(
            request=request,
            financials=financials,
            params=params,
            dcf=dcf_result,
            audit_score=financials.audit_score,
            audit_rating=financials.audit_rating
        )

        # Affichage KPIs Principaux
        display_results(
            financials=financials,
            params=params,
            result=dcf_result,
            mode=request.mode,
            input_source=request.input_source
        )

        # Affichage Graphiques
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

    except TickerNotFoundError as e:
        status_container.update(label="Erreur Ticker", state="error", expanded=False)
        st.error(f"❌ {e.ui_user_message}")
        logger.warning("WORKFLOW[%s] Ticker Not Found: %s", run_id, str(e))

    except DataInsufficientError as e:
        status_container.update(label="Données Insuffisantes", state="error", expanded=False)
        st.error(f"⚠️ {e.ui_user_message}")
        logger.warning("WORKFLOW[%s] Data Insufficient: %s", run_id, str(e))

    except ExternalServiceError as e:
        status_container.update(label="Erreur Connexion", state="error", expanded=False)
        st.warning(f"🌐 {e.ui_user_message}")
        logger.error("WORKFLOW[%s] External Service Error: %s", run_id, str(e))

    except BaseValuationError as e:
        status_container.update(label="Erreur Calcul", state="error", expanded=False)
        st.error(f"⛔ {e.ui_user_message}")
        logger.error("WORKFLOW[%s] Domain Error: %s", run_id, str(e))

    except Exception as e:
        status_container.update(label="Erreur Système", state="error", expanded=False)
        st.error("Une erreur inattendue est survenue. Consultez les logs.")
        logger.exception("WORKFLOW[%s] CRITICAL UNHANDLED ERROR", run_id)
        # En mode debug seulement
        # st.exception(e)