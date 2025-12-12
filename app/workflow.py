import logging
from typing import Optional, List
import streamlit as st
import pandas as pd

from core.models import (
    ValuationMode,
    DCFParameters,
    CompanyFinancials,
    DCFResult,
    ConfigFactory,
    InputSource
)
from core.valuation.engines import run_deterministic_dcf, run_monte_carlo_dcf, run_reverse_dcf
from core.valuation.historical import YahooMacroHistoricalParamsStrategy, build_intrinsic_value_time_series
from core.exceptions import CalculationError, DataProviderError
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.auditing.audit_engine import AuditEngine
from app.ui_components.ui_kpis import display_results
from app.ui_components.ui_charts import display_price_chart, _get_sample_dates, display_simulation_chart

logger = logging.getLogger(__name__)
PROVIDER = YahooFinanceProvider()
MACRO_PROVIDER = YahooMacroProvider()
FORBIDDEN_SECTORS = ["Financial Services", "Real Estate", "Banks", "Insurance"]


def run_workflow_and_display(
        ticker: str,
        projection_years: int,
        mode: ValuationMode,
        input_source: InputSource = InputSource.AUTO,
        manual_params: Optional[DCFParameters] = None,
        manual_beta: Optional[float] = None
) -> None:
    logger.info(f"WORKFLOW START : {ticker} | Mode: {mode.value} | Source: {input_source.value}")
    status = st.status("Calcul en cours...", expanded=False)

    try:
        financials, auto_params = PROVIDER.get_company_financials_and_parameters(ticker, projection_years)

        if input_source == InputSource.MANUAL:
            if manual_params is None: raise ValueError("Paramètres manuels manquants.")
            params = manual_params
            if manual_beta is not None: financials.beta = manual_beta

            params.beta_volatility = auto_params.beta_volatility
            params.growth_volatility = auto_params.growth_volatility
            params.terminal_growth_volatility = auto_params.terminal_growth_volatility

            if params.manual_fcf_base is not None:
                financials.fcf_last = params.manual_fcf_base
                financials.fcf_fundamental_smoothed = params.manual_fcf_base

            financials.source_growth = "manual"
            financials.source_debt = "manual"
            financials.source_fcf = "manual"
        else:
            params = auto_params

        try:
            ConfigFactory.get_config(mode, params).validate(context_beta=financials.beta)
        except ValueError as ve:
            status.update(label="Erreur Config", state="error");
            st.error(f"Configuration : {ve}");
            return

        if financials.sector in FORBIDDEN_SECTORS:
            status.update(label="Secteur non supporté", state="error");
            st.error(f"Secteur '{financials.sector}' non géré.");
            return

        if mode == ValuationMode.MONTE_CARLO and financials.audit_score < 40 and input_source == InputSource.AUTO:
            status.update(label="Mode Bloqué", state="error");
            st.error("Qualité données insuffisante pour Monte Carlo Auto.");
            return

        if mode == ValuationMode.MONTE_CARLO:
            dcf_result = run_monte_carlo_dcf(financials, params)
        else:
            dcf_result = run_deterministic_dcf(financials, params, mode)

        try:
            financials.implied_growth_rate = run_reverse_dcf(financials, params, financials.current_price)
        except:
            financials.implied_growth_rate = None

        price_history, hist_iv_df = None, None
        try:
            price_history = PROVIDER.get_price_history(ticker)
            if not price_history.empty:
                dates = _get_sample_dates(price_history.reset_index())
                if dates:
                    macro_strat = YahooMacroHistoricalParamsStrategy(MACRO_PROVIDER, financials.currency)
                    hist_iv_df, _ = build_intrinsic_value_time_series(ticker, financials, params, mode, PROVIDER,
                                                                      macro_strat, dates)
        except Exception as e:
            logger.warning(f"History Skip: {e}")

        tv_ev_ratio = 0.0
        if dcf_result.enterprise_value > 0:
            tv_ev_ratio = dcf_result.discounted_terminal_value / dcf_result.enterprise_value

        final_audit = AuditEngine.compute_audit(financials, params, dcf_result.simulation_results, None, mode,
                                                tv_ev_ratio, input_source)

        financials.audit_score = final_audit.global_score
        financials.audit_rating = final_audit.rating
        financials.audit_details = final_audit.ui_details
        financials.audit_breakdown = final_audit.breakdown
        financials.audit_logs = [final_audit.audit_mode_description]

        status.update(label="Terminé", state="complete", expanded=False)

        # Affichage avec pays
        c_val = getattr(financials, 'country', 'Unknown')
        country_display = f" | {c_val}" if c_val != "Unknown" else ""
        st.caption(f"Secteur : {financials.sector}{country_display} | Devise : {financials.currency}")

        # APPEL CORRIGÉ
        display_results(financials, params, dcf_result, mode, input_source)

        if mode == ValuationMode.MONTE_CARLO:
            display_simulation_chart(dcf_result.simulation_results, financials.current_price, financials.currency)
            st.caption("*Note : Historique calculé en méthode Analytique (performance).*")

        display_price_chart(ticker, price_history, hist_iv_df, dcf_result.intrinsic_value_per_share)

    except (DataProviderError, CalculationError) as e:
        status.update(label="Erreur Analytique", state="error");
        st.error(f"Echec : {e}")
    except Exception as e:
        status.update(label="Erreur Système", state="error");
        st.error("Erreur inattendue.");
        st.exception(e)