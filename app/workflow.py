"""
app/workflow.py
ORCHESTRATEUR LOGIQUE (DT-016 Resolution)
=========================================
Rôle : Pilotage du cycle de vie de l'analyse, orchestration multi-temporelle et scénarios.
Architecture : Smart Merge segmenté, Isolation Point-in-Time et Validation Historique.
"""

from __future__ import annotations
import logging
import traceback
from datetime import datetime, date
from typing import Any, List, Optional, Tuple

import streamlit as st
import numpy as np

# Import de l'interface et i18n
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
# 1. POINT D'ENTRÉE PRINCIPAL
# ==============================================================================

def run_workflow(
    request: ValuationRequest,
    renderer: Optional[IResultRenderer] = None
) -> Tuple[Optional[ValuationResult], Optional[YahooFinanceProvider]]:
    """
    Exécute le workflow complet de valorisation.
    DT-016 Resolution : Séparation calcul/affichage via injection de renderer.
    """
    status = st.status(WorkflowTexts.STATUS_MAIN_LABEL, expanded=True)
    _renderer = renderer or NullResultRenderer()

    try:
        # --- ÉTAPE 1 : ACQUISITION & INFRASTRUCTURE ---
        status.write(WorkflowTexts.STATUS_DATA_ACQUISITION)
        provider = YahooFinanceProvider(YahooMacroProvider())

        # Deep Fetch pour supporter l'analyse et le backtesting
        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker,
            request.projection_years
        )

        # Triangulation sectorielle
        status.write(WorkflowTexts.STATUS_PEER_DISCOVERY)
        multiples_data = provider.get_peer_multiples(
            ticker=request.ticker,
            manual_peers=request.options.get("manual_peers")
        )
        request.options["multiples_data"] = multiples_data

        # --- ÉTAPE 2 : CONCILIATION (SMART MERGE) ---
        status.write(WorkflowTexts.STATUS_SMART_MERGE)
        final_params = map_request_to_params(request, auto_params)

        # --- ÉTAPE 3 : ANALYSE DU PRÉSENT (BASE CASE) ---
        status.write(WorkflowTexts.STATUS_ENGINE_RUN.format(mode=request.mode.value))
        if final_params.monte_carlo.enable_monte_carlo:
            status.write(WorkflowTexts.STATUS_MC_RUN)

        # Exécution du moteur (IV + Triangulation + Audit)
        result = run_valuation(request, financials, final_params)

        # --- ÉTAPE 4 : ANALYSE DE SCÉNARIOS DÉTERMINISTES ---
        if final_params.scenarios.enabled:
            status.write(WorkflowTexts.STATUS_SCENARIOS_RUN)
            result.scenario_synthesis = compute_scenario_impact(
                request, financials, final_params, result
            )

        # --- ÉTAPE 5 : VALIDATION HISTORIQUE (BACKTESTING RÉEL) ---
        if request.options.get("enable_backtest", False):
            status.write(WorkflowTexts.STATUS_BACKTEST_RUN)

            # Orchestration du backtest sur les données brutes
            result.backtest_report = _orchestrate_backtesting(
                request=request,
                raw_data=provider.last_raw_data,
                params=final_params,
                price_history=provider.get_price_history(request.ticker),
                provider=provider
            )
            status.write(WorkflowTexts.STATUS_BACKTEST_COMPLETE)

        # --- ÉTAPE 6 : FINALISATION ---
        status.update(label=WorkflowTexts.STATUS_COMPLETE, state="complete", expanded=False)

        # Log Monte Carlo (ST-4.2)
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
    """Facade de compatibilité Streamlit pour le workflow."""
    from app.adapters import StreamlitResultRenderer

    renderer = StreamlitResultRenderer()
    result, provider = run_workflow(request, renderer)

    if result is not None and provider is not None:
        renderer.render_results(result, provider)


# ==============================================================================
# 2. LOGIQUE DU BACKTESTING (ISOLATION TEMPORELLE)
# ==============================================================================

def _orchestrate_backtesting(
    request: ValuationRequest,
    raw_data: Any,
    params: DCFParameters,
    price_history: Any,
    provider: YahooFinanceProvider
) -> BacktestResult:
    """Simule la valorisation sur les trois dernières années avec isolation Point-in-Time."""
    points: List[HistoricalPoint] = []
    current_year = datetime.now().year
    years_to_test = [current_year - 1, current_year - 2, current_year - 3]

    for yr in years_to_test:
        try:
            # 1. Congélation des données à l'année N
            frozen_raw = BacktestEngine.freeze_data_at_fiscal_year(raw_data, yr)
            if not frozen_raw: continue

            # 2. Mapping financier rétrograde
            hist_financials = provider.map_raw_to_financials(frozen_raw)

            # 3. Calcul IV (MC désactivé pour performance backtest)
            v_params = params.model_copy(deep=True)
            v_params.monte_carlo.enable_monte_carlo = False
            hist_res = run_valuation(request, hist_financials, v_params)

            # 4. Récupération du prix de clôture réel
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
# 3. ANALYSE DE SCÉNARIOS
# ==============================================================================

def compute_scenario_impact(
    request: ValuationRequest,
    financials: Any,
    params: DCFParameters,
    base_result: ValuationResult
) -> ScenarioSynthesis:
    """Calcule l'impact Bull/Base/Bear avec optimisation des ressources."""
    sc = params.scenarios
    results = []
    variants = [(sc.bull, "Bull"), (sc.base, "Base"), (sc.bear, "Bear")]

    for variant, label in variants:
        # Optimisation : réutilisation si Base est inchangé
        if label == "Base" and variant.growth_rate is None and variant.target_fcf_margin is None:
            val = base_result.intrinsic_value_per_share
            g_used, m_used = params.growth.fcf_growth_rate, params.growth.target_fcf_margin
        else:
            v_params = params.model_copy(deep=True)
            if variant.growth_rate is not None: v_params.growth.fcf_growth_rate = variant.growth_rate
            if variant.target_fcf_margin is not None: v_params.growth.target_fcf_margin = variant.target_fcf_margin

            # Allègement du moteur pour les variantes
            v_params.monte_carlo.enable_monte_carlo = False
            v_res = run_valuation(request, financials, v_params)
            val, g_used, m_used = v_res.intrinsic_value_per_share, v_params.growth.fcf_growth_rate, v_params.growth.target_fcf_margin

        results.append(ScenarioResult(
            label=label, intrinsic_value=val, probability=variant.probability,
            growth_used=g_used or 0.0, margin_used=m_used or 0.0
        ))

    expected_val = sum(r.intrinsic_value * r.probability for r in results)
    return ScenarioSynthesis(
        variants=results, expected_value=expected_val,
        max_upside=max(r.intrinsic_value for r in results),
        max_downside=min(r.intrinsic_value for r in results)
    )


# ==============================================================================
# 4. HELPERS ET DIAGNOSTICS
# ==============================================================================

def map_request_to_params(request: ValuationRequest, auto_params: DCFParameters) -> DCFParameters:
    """Fusionne les données automatiques avec les surcharges manuelles (Expert)."""
    if request.input_source == InputSource.MANUAL:
        final_params = auto_params.model_copy(deep=True)
        # Surcharges taux et croissance
        for section in ['rates', 'growth']:
            manual_data = getattr(request.manual_params, section).model_dump(exclude_unset=True)
            for k, v in manual_data.items():
                if v is not None: setattr(getattr(final_params, section), k, v)

        # Injection des configurations avancées
        final_params.monte_carlo = request.manual_params.monte_carlo.model_copy()
        final_params.scenarios = request.manual_params.scenarios.model_copy()
        final_params.sotp = request.manual_params.sotp.model_copy()
        return final_params

    # Mode Standard : MC piloté par les options de requête
    auto_params.monte_carlo.enable_monte_carlo = request.options.get("enable_mc", False)
    auto_params.monte_carlo.num_simulations = request.options.get("mc_sims", 5000)
    return auto_params


def _log_monte_carlo_performance(ticker: str, result: ValuationResult, params: DCFParameters) -> None:
    """Enregistre les métriques stochastiques dans les logs quantitatifs."""
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
    """Affiche une alerte UI stylisée pour les erreurs métier."""
    level_fn = st.error if diag.severity in [SeverityLevel.CRITICAL, SeverityLevel.ERROR] else st.warning
    level_fn(f"**{diag.code}** : {diag.message}")
    with st.expander(WorkflowTexts.DIAG_EXPANDER_TITLE):
        st.markdown(f"**Action :** {diag.remediation_hint}")
        if diag.technical_detail: st.code(diag.technical_detail)


def _create_crash_diagnostic(error: Exception) -> DiagnosticEvent:
    return DiagnosticEvent(
        code="SYSTEM_CRASH", severity=SeverityLevel.CRITICAL, domain=DiagnosticDomain.SYSTEM,
        message=DiagnosticTexts.SYSTEM_CRASH_MSG,
        technical_detail=f"{str(error)}\n{traceback.format_exc()}",
        remediation_hint=DiagnosticTexts.SYSTEM_CRASH_HINT
    )