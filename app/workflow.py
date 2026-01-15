"""
app/workflow.py

ORCHESTRATEUR LOGIQUE — VERSION V12.0 (Sprint 5 : Scénarios & Triangulation)
Rôle : Pilotage du cycle de vie de l'analyse, fusion des paramètres et calculs parallèles.
Architecture : Smart Merge segmenté et orchestration multi-trajectoires.
"""

from __future__ import annotations

import logging
import traceback
from typing import Dict, Any

import streamlit as st

from core.diagnostics import DiagnosticDomain, DiagnosticEvent, SeverityLevel
from core.exceptions import ValuationException
from core.models import (
    DCFParameters,
    InputSource,
    ValuationRequest,
    ScenarioResult,
    ScenarioSynthesis,
    ValuationResult
)
from core.valuation.engines import run_valuation
from infra.auditing.audit_engine import AuditEngine
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

import app.ui_components.ui_kpis as ui_kpis
from app.ui_components.ui_texts import WorkflowTexts, DiagnosticTexts

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. POINT D'ENTRÉE PRINCIPAL
# ==============================================================================

def run_workflow_and_display(request: ValuationRequest) -> None:
    """
    Point d'entrée unique pilotant le cycle de vie complet de l'analyse financière.
    Orchestre les scénarios stratégiques Bull/Base/Bear avec optimisation de performance.
    """
    status = st.status(WorkflowTexts.STATUS_MAIN_LABEL, expanded=True)

    try:
        # ÉTAPE 1 : ACQUISITION DES DONNÉES
        status.write(WorkflowTexts.STATUS_DATA_ACQUISITION)
        provider = _create_data_provider()
        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker,
            request.projection_years
        )

        # TRIANGULATION : ACQUISITION DES MULTIPLES
        status.write(WorkflowTexts.STATUS_PEER_DISCOVERY)
        manual_peers = request.options.get("manual_peers")
        multiples_data = provider.get_peer_multiples(
            ticker=request.ticker,
            manual_peers=manual_peers
        )
        request.options["multiples_data"] = multiples_data

        # ÉTAPE 2 : CONCILIATION DES PARAMÈTRES (SMART MERGE)
        status.write(WorkflowTexts.STATUS_SMART_MERGE)
        final_params = _merge_parameters(request, auto_params)

        # ÉTAPE 3 : EXÉCUTION DU CAS DE RÉFÉRENCE (BASE CASE)
        status.write(WorkflowTexts.STATUS_ENGINE_RUN.format(mode=request.mode.value))
        if final_params.monte_carlo.enable_monte_carlo:
            status.write(WorkflowTexts.STATUS_MC_RUN)

        # run_valuation exécute : IV + Triangulation + Audit
        result = run_valuation(request, financials, final_params)

        # ÉTAPE 4 : ANALYSE DE SCÉNARIOS DÉTERMINISTES (SPRINT 5)
        if final_params.scenarios.enabled:
            status.write(WorkflowTexts.STATUS_SCENARIOS_RUN)
            # Orchestration des variantes sans recalculer l'audit ou les multiples
            synthesis = _orchestrate_scenarios(request, financials, final_params, result)
            result.scenario_synthesis = synthesis

        # ÉTAPE 5 : FINALISATION (L'audit est déjà inclus dans 'result')
        status.update(label=WorkflowTexts.STATUS_COMPLETE, state="complete", expanded=False)

        # RESTITUTION
        ui_kpis.render_executive_summary(result)
        ui_kpis.display_valuation_details(result, provider)

    except ValuationException as e:
        status.update(label=WorkflowTexts.STATUS_INTERRUPTED, state="error", expanded=True)
        _display_diagnostic_message(e.diagnostic)
        st.session_state.active_request = None

    except Exception as e:
        status.update(label=WorkflowTexts.STATUS_CRITICAL_ERROR, state="error", expanded=True)
        logger.error("Critical workflow error: %s", str(e), exc_info=True)
        _display_diagnostic_message(_create_crash_diagnostic(e))


# ==============================================================================
# 2. LOGIQUE DES SCÉNARIOS (STRATÉGIE DE CALCUL PARALLÈLE - OPTIMIZED)
# ==============================================================================

def _orchestrate_scenarios(
    request: ValuationRequest,
    financials: Any,
    params: DCFParameters,
    base_result: ValuationResult
) -> ScenarioSynthesis:
    """
    Exécute les variantes Bull et Bear de manière isolée et compile la synthèse.
    OPTIMISATIONS : Désactive Monte Carlo ET Triangulation sectorielle pour les variantes.
    """
    sc = params.scenarios
    results = []

    # Définition des variantes
    variants = [
        (sc.bull, "Bull"),
        (sc.base, "Base"),
        (sc.bear, "Bear")
    ]

    for variant, label in variants:
        # 1. Optimisation : Réutilisation directe du résultat de référence si inchangé
        is_base_no_override = (label == "Base" and variant.growth_rate is None and variant.target_fcf_margin is None)

        if is_base_no_override:
            val = base_result.intrinsic_value_per_share
            g_used = params.growth.fcf_growth_rate
            m_used = params.growth.target_fcf_margin
        else:
            # 2. Préparation des paramètres de la variante
            v_params = params.model_copy(deep=True)
            if variant.growth_rate is not None:
                v_params.growth.fcf_growth_rate = variant.growth_rate
            if variant.target_fcf_margin is not None:
                v_params.growth.target_fcf_margin = variant.target_fcf_margin

            # Gain de performance : Pas de Monte Carlo pour les trajectoires déterministes
            v_params.monte_carlo.enable_monte_carlo = False

            # 3. Optimisation Critique : Désactivation de la triangulation pour les variantes
            # Inutile de recalculer les multiples du secteur (static) pour Bull/Bear
            v_request = request.model_copy(deep=True)
            v_request.options["multiples_data"] = None

            # 4. Exécution ciblée du moteur
            v_res = run_valuation(v_request, financials, v_params)
            val = v_res.intrinsic_value_per_share
            g_used = v_params.growth.fcf_growth_rate
            m_used = v_params.growth.target_fcf_margin

        results.append(ScenarioResult(
            label=label,
            intrinsic_value=val,
            probability=variant.probability,
            growth_used=g_used or 0.0,
            margin_used=m_used or 0.0
        ))

    # Synthèse financière
    expected_val = sum(r.intrinsic_value * r.probability for r in results)
    ivs = [r.intrinsic_value for r in results]

    return ScenarioSynthesis(
        variants=results,
        expected_value=expected_val,
        max_upside=max(ivs),
        max_downside=min(ivs)
    )

# ==============================================================================
# 3. HELPERS DE FUSION (SMART MERGE V12)
# ==============================================================================

def _create_data_provider() -> YahooFinanceProvider:
    """Crée le fournisseur de données avec injection macro."""
    macro_provider = YahooMacroProvider()
    return YahooFinanceProvider(macro_provider)


def _merge_parameters(request: ValuationRequest, auto_params: DCFParameters) -> DCFParameters:
    """Bascule entre fusion automatique ou manuelle selon l'input source."""
    if request.input_source == InputSource.MANUAL:
        return _merge_manual_params(request, auto_params)
    return _merge_auto_params(request, auto_params)


def _merge_manual_params(request: ValuationRequest, auto_params: DCFParameters) -> DCFParameters:
    """Fusionne les paramètres du Terminal Expert avec respect de la segmentation."""
    final_params = auto_params.model_copy(deep=True)

    # Extraction des surcharges expert
    expert_rates = request.manual_params.rates.model_dump(exclude_unset=True)
    expert_growth = request.manual_params.growth.model_dump(exclude_unset=True)

    # Application sélective (Seulement si non-None)
    for k, v in expert_rates.items():
        if v is not None: setattr(final_params.rates, k, v)
    for k, v in expert_growth.items():
        if v is not None: setattr(final_params.growth, k, v)

    # Écrasement des segments de pilotage directs
    final_params.monte_carlo = request.manual_params.monte_carlo.model_copy()
    final_params.scenarios = request.manual_params.scenarios.model_copy()

    return final_params


def _merge_auto_params(request: ValuationRequest, auto_params: DCFParameters) -> DCFParameters:
    """Injecte les options simples de la barre latérale dans les paramètres auto."""
    final_params = auto_params.model_copy(deep=True)
    ui_options = request.options or {}

    final_params.monte_carlo.enable_monte_carlo = ui_options.get("enable_mc", False)
    final_params.monte_carlo.num_simulations = ui_options.get("mc_sims", 5000)

    # Scénarios toujours désactivés en mode Auto (Restriction par design)
    final_params.scenarios.enabled = False

    return final_params


# ==============================================================================
# 4. GESTION DU DIAGNOSTIC & ERREURS
# ==============================================================================

def _create_crash_diagnostic(error: Exception) -> DiagnosticEvent:
    """Encapsule une exception système dans un événement diagnostic."""
    return DiagnosticEvent(
        code="SYSTEM_CRASH",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message=DiagnosticTexts.SYSTEM_CRASH_MSG,
        technical_detail=f"{str(error)}\n{traceback.format_exc()}",
        remediation_hint=DiagnosticTexts.SYSTEM_CRASH_HINT
    )


def _display_diagnostic_message(diag: DiagnosticEvent) -> None:
    """Rendu Streamlit des erreurs et avertissements selon la sévérité."""
    if diag.severity in [SeverityLevel.CRITICAL, SeverityLevel.ERROR]:
        st.error(f"{WorkflowTexts.PREFIX_CRITICAL} {diag.message}")
    elif diag.severity == SeverityLevel.WARNING:
        st.warning(f"{WorkflowTexts.PREFIX_WARNING} {diag.message}")
    else:
        st.info(f"{WorkflowTexts.PREFIX_INFO} {diag.message}")

    with st.expander(WorkflowTexts.DIAG_EXPANDER_TITLE, expanded=True):
        st.markdown(f"**{WorkflowTexts.DIAG_ACTION_LABEL}** {diag.remediation_hint}")
        if diag.technical_detail:
            st.divider()
            st.code(diag.technical_detail, language="text")