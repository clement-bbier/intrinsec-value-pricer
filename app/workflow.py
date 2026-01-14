"""
app/workflow.py

ORCHESTRATEUR LOGIQUE — VERSION V9.0 (Segmenté & i18n Secured)
Rôle : Pilotage de l'analyse avec fusion résiliente et gestion d'erreurs enrichie.
Architecture : Smart Merge respectant les segments Rates, Growth et MC.
"""

from __future__ import annotations

import logging
import traceback

import streamlit as st

from core.diagnostics import DiagnosticDomain, DiagnosticEvent, SeverityLevel
from core.exceptions import ValuationException
from core.models import DCFParameters, InputSource, ValuationRequest
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
    """
    status = st.status(WorkflowTexts.STATUS_MAIN_LABEL, expanded=True)

    try:
        # =====================================================================
        # ÉTAPE 1 : ACQUISITION DES DONNÉES
        # =====================================================================
        status.write(WorkflowTexts.STATUS_DATA_ACQUISITION)

        provider = _create_data_provider()
        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker,
            request.projection_years
        )

        # =====================================================================
        # ÉTAPE 2 : CONCILIATION DES PARAMÈTRES (SMART MERGE V9)
        # =====================================================================
        status.write(WorkflowTexts.STATUS_SMART_MERGE)

        final_params = _merge_parameters(request, auto_params)

        # CORRECTION V9 : Accès via .monte_carlo.enable_monte_carlo
        logger.info(
            "[Workflow] Dispatching calculation | Ticker: %s | Source: %s | MC: %s",
            request.ticker,
            request.input_source.value,
            final_params.monte_carlo.enable_monte_carlo
        )

        # =====================================================================
        # ÉTAPE 3 :  EXÉCUTION DU MOTEUR DE VALORISATION
        # =====================================================================
        status.write(WorkflowTexts.STATUS_ENGINE_RUN.format(mode=request.mode.value))

        # CORRECTION V9 : Accès via .monte_carlo.enable_monte_carlo
        if final_params.monte_carlo.enable_monte_carlo:
            status.write(WorkflowTexts.STATUS_MC_RUN)

        result = run_valuation(request, financials, final_params)

        # =====================================================================
        # ÉTAPE 4 : AUDIT DE CONFORMITÉ (GLASS BOX)
        # =====================================================================
        status.write(WorkflowTexts.STATUS_AUDIT_GEN)
        result.audit_report = AuditEngine.compute_audit(result)

        status.update(label=WorkflowTexts.STATUS_COMPLETE, state="complete", expanded=False)

        # =====================================================================
        # ÉTAPE 5 : RESTITUTION DES RÉSULTATS
        # =====================================================================
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
# 2. HELPERS DE FUSION (V9 SEGMENTÉ)
# ==============================================================================

def _create_data_provider() -> YahooFinanceProvider:
    """Crée et configure le fournisseur de données."""
    macro_provider = YahooMacroProvider()
    return YahooFinanceProvider(macro_provider)


def _merge_parameters(request: ValuationRequest, auto_params: DCFParameters) -> DCFParameters:
    """Fusionne les paramètres selon la source d'input."""
    if request.input_source == InputSource.MANUAL:
        return _merge_manual_params(request, auto_params)

    return _merge_auto_params(request, auto_params)


def _merge_manual_params(request: ValuationRequest, auto_params: DCFParameters) -> DCFParameters:
    """Fusionne les paramètres expert avec respect de la segmentation."""
    expert_rates = request.manual_params.rates.model_dump(exclude_unset=True)
    expert_growth = request.manual_params.growth.model_dump(exclude_unset=True)

    final_params = auto_params.model_copy(deep=True)

    for k, v in expert_rates.items():
        if v is not None: setattr(final_params.rates, k, v)

    for k, v in expert_growth.items():
        if v is not None: setattr(final_params.growth, k, v)

    # Le Monte Carlo expert prévaut
    final_params.monte_carlo = request.manual_params.monte_carlo.model_copy()

    return final_params


def _merge_auto_params(request: ValuationRequest, auto_params: DCFParameters) -> DCFParameters:
    """Fusionne les options simples pour le mode automatique (Alignement V9)."""
    final_params = auto_params.model_copy(deep=True)
    ui_options = request.options or {}

    # Utilisation des clés 'enable_mc' et 'mc_sims' définies dans main.py
    final_params.monte_carlo.enable_monte_carlo = ui_options.get("enable_mc", False)
    final_params.monte_carlo.num_simulations = ui_options.get("mc_sims", 5000)

    return final_params


def _create_crash_diagnostic(error: Exception) -> DiagnosticEvent:
    """Crée un événement diagnostic pour les erreurs système."""
    return DiagnosticEvent(
        code="SYSTEM_CRASH",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message=DiagnosticTexts.SYSTEM_CRASH_MSG,
        technical_detail=f"{str(error)}\n{traceback.format_exc()}",
        remediation_hint=DiagnosticTexts.SYSTEM_CRASH_HINT
    )


def _display_diagnostic_message(diag: DiagnosticEvent) -> None:
    """Affiche un message diagnostic formaté."""
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