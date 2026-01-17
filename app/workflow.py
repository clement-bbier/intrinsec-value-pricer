"""
app/workflow.py

ORCHESTRATEUR LOGIQUE — VERSION V14.0 (DT-016 Resolution)
Rôle : Pilotage du cycle de vie de l'analyse, orchestration multi-temporelle et scénarios.
Architecture : Smart Merge segmenté, Isolation Point-in-Time et Validation Historique.

DT-016 Resolution :
- L'affichage UI est délégué à IResultRenderer (injection de dépendances)
- Compatibilité ascendante maintenue via run_workflow_and_display()
"""

from __future__ import annotations

import logging
import traceback
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

# Import de l'interface (DT-016)
from core.interfaces import IResultRenderer, NullResultRenderer
from core.i18n import WorkflowTexts, DiagnosticTexts
from core.diagnostics import DiagnosticDomain, DiagnosticEvent, SeverityLevel
from core.exceptions import ValuationException
from core.models import (
    DCFParameters,
    InputSource,
    ValuationRequest,
    ScenarioResult,
    ScenarioSynthesis,
    ValuationResult,
    BacktestResult,
    HistoricalPoint
)
from core.valuation.engines import run_valuation
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
    Exécute le workflow de valorisation et retourne le résultat.
    
    DT-016 Resolution : Séparation calcul/affichage.
    
    Parameters
    ----------
    request : ValuationRequest
        La requête de valorisation.
    renderer : IResultRenderer, optional
        Le renderer pour l'affichage. Si None, NullResultRenderer est utilisé.
    
    Returns
    -------
    Tuple[Optional[ValuationResult], Optional[YahooFinanceProvider]]
        Le résultat de valorisation et le provider de données.
    """
    status = st.status(WorkflowTexts.STATUS_MAIN_LABEL, expanded=True)
    
    # Utilisation du NullResultRenderer si aucun renderer n'est fourni
    _renderer = renderer or NullResultRenderer()

    try:
        # --- ÉTAPE 1 : ACQUISITION & INFRASTRUCTURE ---
        status.write(WorkflowTexts.STATUS_DATA_ACQUISITION)
        provider = _create_data_provider()

        # Acquisition profonde (Deep Fetch) pour supporter le backtesting potentiel
        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker,
            request.projection_years
        )

        # Triangulation sectorielle (Multiples de marché)
        status.write(WorkflowTexts.STATUS_PEER_DISCOVERY)
        multiples_data = provider.get_peer_multiples(
            ticker=request.ticker,
            manual_peers=request.options.get("manual_peers")
        )
        request.options["multiples_data"] = multiples_data

        # --- ÉTAPE 2 : CONCILIATION (SMART MERGE) ---
        status.write(WorkflowTexts.STATUS_SMART_MERGE)
        final_params = _merge_parameters(request, auto_params)

        # --- ÉTAPE 3 : ANALYSE DU PRÉSENT (BASE CASE) ---
        status.write(WorkflowTexts.STATUS_ENGINE_RUN.format(mode=request.mode.value))
        if final_params.monte_carlo.enable_monte_carlo:
            status.write(WorkflowTexts.STATUS_MC_RUN)

        # Exécution du moteur principal (IV + Triangulation + Audit)
        result = run_valuation(request, financials, final_params)

        # --- ÉTAPE 4 : ANALYSE DE SCÉNARIOS DÉTERMINISTES (SPRINT 5) ---
        if final_params.scenarios.enabled:
            status.write(WorkflowTexts.STATUS_SCENARIOS_RUN)
            result.scenario_synthesis = _orchestrate_scenarios(
                request, financials, final_params, result
            )

        # --- ÉTAPE 5 : VALIDATION HISTORIQUE (BACKTESTING - SPRINT 6) ---
        if request.options.get("enable_backtest", False):
            status.write(WorkflowTexts.STATUS_BACKTEST_RUN)

            # Injection du rapport de backtesting dans le résultat final
            result.backtest_report = _orchestrate_backtesting(
                request=request,
                raw_data=provider.last_raw_data,  # Accès aux données brutes non filtrées
                params=final_params,
                price_history=provider.fetch_price_history(request.ticker),
                provider=provider
            )
            status.write(WorkflowTexts.STATUS_BACKTEST_COMPLETE)

        # --- ÉTAPE 6 : FINALISATION ---
        status.update(label=WorkflowTexts.STATUS_COMPLETE, state="complete", expanded=False)
        
        return result, provider

    except ValuationException as e:
        status.update(label=WorkflowTexts.STATUS_INTERRUPTED, state="error", expanded=True)
        _display_diagnostic_message(e.diagnostic)
        st.session_state.active_request = None
        return None, None

    except Exception as e:
        status.update(label=WorkflowTexts.STATUS_CRITICAL_ERROR, state="error", expanded=True)
        logger.error("Critical workflow error: %s", str(e), exc_info=True)
        _display_diagnostic_message(_create_crash_diagnostic(e))
        return None, None


def run_workflow_and_display(request: ValuationRequest) -> None:
    """
    Facade de compatibilité : Exécute le workflow ET affiche les résultats.
    
    DEPRECATION NOTICE :
    - Cette fonction maintient la compatibilité ascendante
    - Pour les nouveaux usages, préférer run_workflow() + injection de renderer
    """
    # Migration progressive : support des deux systèmes (legacy + nouveau)
    # TODO: Une fois testé, basculer définitivement vers ResultTabOrchestrator

    result, provider = run_workflow(request, NullResultRenderer())

    # Affichage des résultats
    if result is not None and provider is not None:
        # Nouveau système (enrichissement)
        try:
            from app.ui.result_tabs.orchestrator import ResultTabOrchestrator
            orchestrator = ResultTabOrchestrator()
            orchestrator.render(result, provider=provider)
            logger.info("[Workflow] Nouveau système ResultTabOrchestrator utilisé avec succès")
        except Exception as e:
            # Fallback vers l'ancien système (compatibilité)
            logger.warning(f"[Workflow] Fallback vers ancien système: {str(e)}")
            from app.adapters import StreamlitResultRenderer
            renderer = StreamlitResultRenderer()
            renderer.render_executive_summary(result)
            renderer.display_valuation_details(result, provider)


# ==============================================================================
# 2. LOGIQUE DU BACKTESTING
# ==============================================================================

def _orchestrate_backtesting(
    request: ValuationRequest,
    raw_data: Any,
    params: DCFParameters,
    price_history: Any,
    provider: YahooFinanceProvider
) -> BacktestResult:
    """
    Exécute N simulations sur les années fiscales passées avec isolation temporelle.
    """
    points: List[HistoricalPoint] = []

    # On cible les 3 dernières années fiscales closes
    current_year = datetime.now().year
    years_to_test = [current_year - 1, current_year - 2, current_year - 3]

    for target_year in years_to_test:
        try:
            # 1. Isolation Point-in-Time (On fige les données au passé)
            frozen_raw = BacktestEngine.freeze_data_at_fiscal_year(raw_data, target_year)
            if not frozen_raw:
                continue

            # 2. Re-mapping vers le modèle financier de l'époque
            hist_financials = provider.map_raw_to_financials(frozen_raw)

            # 3. Calcul de l'IV historique (Désactivation MC pour la performance)
            v_params = params.model_copy(deep=True)
            v_params.monte_carlo.enable_monte_carlo = False

            hist_res = run_valuation(request, hist_financials, v_params)

            # 4. Confrontation à la vérité terrain (Prix réel fin d'année)
            market_price = BacktestEngine.get_historical_price_at(price_history, target_year)

            if market_price > 0:
                error_pct = (hist_res.intrinsic_value_per_share / market_price) - 1.0
                points.append(HistoricalPoint(
                    valuation_date=date(target_year, 12, 31),
                    intrinsic_value=hist_res.intrinsic_value_per_share,
                    market_price=market_price,
                    error_pct=error_pct,
                    was_undervalued=(hist_res.intrinsic_value_per_share > market_price)
                ))
        except Exception as e:
            logger.warning("Backtest failed for year %s: %s", target_year, str(e))
            continue

    if not points:
        return BacktestResult()

    # Calcul des métriques de fiabilité du modèle (Hedge Fund Grade)
    mae = sum(abs(p.error_pct) for p in points) / len(points)

    return BacktestResult(
        points=points,
        mean_absolute_error=mae,
        model_accuracy_score=max(0.0, 100.0 * (1.0 - mae))
    )


# ==============================================================================
# 3. LOGIQUE DES SCÉNARIOS (OPTIMISÉE)
# ==============================================================================

def _orchestrate_scenarios(
    request: ValuationRequest,
    financials: Any,
    params: DCFParameters,
    base_result: ValuationResult
) -> ScenarioSynthesis:
    """
    Exécute les variantes stratégiques Bull/Bear sans recalculer le superflu.
    """
    sc = params.scenarios
    results = []
    variants = [(sc.bull, "Bull"), (sc.base, "Base"), (sc.bear, "Bear")]

    for variant, label in variants:
        # Optimisation : Réutilisation directe du résultat de référence si inchangé
        if label == "Base" and variant.growth_rate is None and variant.target_fcf_margin is None:
            val, g_used, m_used = base_result.intrinsic_value_per_share, params.growth.fcf_growth_rate, params.growth.target_fcf_margin
        else:
            v_params = params.model_copy(deep=True)
            if variant.growth_rate is not None: v_params.growth.fcf_growth_rate = variant.growth_rate
            if variant.target_fcf_margin is not None: v_params.growth.target_fcf_margin = variant.target_fcf_margin

            # Désactivation des modules lourds pour les variantes
            v_params.monte_carlo.enable_monte_carlo = False
            v_request = request.model_copy(deep=True)
            v_request.options["multiples_data"] = None

            v_res = run_valuation(v_request, financials, v_params)
            val, g_used, m_used = v_res.intrinsic_value_per_share, v_params.growth.fcf_growth_rate, v_params.growth.target_fcf_margin

        results.append(ScenarioResult(
            label=label, intrinsic_value=val, probability=variant.probability,
            growth_used=g_used or 0.0, margin_used=m_used or 0.0
        ))

    expected_val = sum(r.intrinsic_value * r.probability for r in results)
    ivs = [r.intrinsic_value for r in results]

    return ScenarioSynthesis(
        variants=results, expected_value=expected_val,
        max_upside=max(ivs), max_downside=min(ivs)
    )


# ==============================================================================
# 4. HELPERS DE FUSION & DIAGNOSTIC
# ==============================================================================

def _create_data_provider() -> YahooFinanceProvider:
    return YahooFinanceProvider(YahooMacroProvider())


def _merge_parameters(request: ValuationRequest, auto_params: DCFParameters) -> DCFParameters:
    if request.input_source == InputSource.MANUAL:
        final_params = auto_params.model_copy(deep=True)

        # Surcharges explicites et typées (Standard SOLID)
        expert_rates = request.manual_params.rates.model_dump(exclude_unset=True)
        expert_growth = request.manual_params.growth.model_dump(exclude_unset=True)

        for k, v in expert_rates.items():
            if v is not None: setattr(final_params.rates, k, v)
        for k, v in expert_growth.items():
            if v is not None: setattr(final_params.growth, k, v)

        # Segments directs
        final_params.monte_carlo = request.manual_params.monte_carlo.model_copy()
        final_params.scenarios = request.manual_params.scenarios.model_copy()
        final_params.sotp = request.manual_params.sotp.model_copy()
        return final_params

    auto_params.monte_carlo.enable_monte_carlo = request.options.get("enable_mc", False)
    auto_params.monte_carlo.num_simulations = request.options.get("mc_sims", 5000)
    auto_params.scenarios.enabled = False
    return auto_params


def _display_diagnostic_message(diag: DiagnosticEvent) -> None:
    level_map = {SeverityLevel.CRITICAL: st.error, SeverityLevel.ERROR: st.error, SeverityLevel.WARNING: st.warning}
    prefix_map = {SeverityLevel.CRITICAL: WorkflowTexts.PREFIX_CRITICAL, SeverityLevel.WARNING: WorkflowTexts.PREFIX_WARNING}

    level_map.get(diag.severity, st.info)(f"{prefix_map.get(diag.severity, WorkflowTexts.PREFIX_INFO)} {diag.message}")
    with st.expander(WorkflowTexts.DIAG_EXPANDER_TITLE, expanded=True):
        st.markdown(f"**{WorkflowTexts.DIAG_ACTION_LABEL}** {diag.remediation_hint}")
        if diag.technical_detail: st.code(diag.technical_detail, language="text")


def _create_crash_diagnostic(error: Exception) -> DiagnosticEvent:
    return DiagnosticEvent(
        code="SYSTEM_CRASH", severity=SeverityLevel.CRITICAL, domain=DiagnosticDomain.SYSTEM,
        message=DiagnosticTexts.SYSTEM_CRASH_MSG,
        technical_detail=f"{str(error)}\n{traceback.format_exc()}",
        remediation_hint=DiagnosticTexts.SYSTEM_CRASH_HINT
    )