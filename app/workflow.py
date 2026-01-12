"""
app/workflow.py

ORCHESTRATEUR LOGIQUE — VERSION V8.2
Rôle : Pilotage de l'analyse avec fusion résiliente et gestion d'erreurs enrichie.
Architecture : Smart Merge "Empty=Auto" vs "0=Value".
"""

from __future__ import annotations

import logging
import traceback

import streamlit as st

from core.diagnostics import DiagnosticDomain, DiagnosticEvent, SeverityLevel
from core. exceptions import ValuationException
from core.models import DCFParameters, InputSource, ValuationRequest
from core. valuation.engines import run_valuation
from infra.auditing.audit_engine import AuditEngine
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

import app.ui_components.ui_kpis as ui_kpis

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. POINT D'ENTRÉE PRINCIPAL
# ==============================================================================

def run_workflow_and_display(request:  ValuationRequest) -> None:
    """
    Point d'entrée unique pilotant le cycle de vie complet de l'analyse financière.

    Args:
        request: Requête de valorisation contenant ticker, mode et paramètres
    """
    status = st.status("Initialisation de l'analyse...", expanded=True)

    try:
        # =====================================================================
        # ÉTAPE 1 : ACQUISITION DES DONNÉES
        # =====================================================================
        status.write("Acquisition des données de marché et macro-économiques...")

        provider = _create_data_provider()
        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker,
            request.projection_years
        )

        # =====================================================================
        # ÉTAPE 2 : CONCILIATION DES PARAMÈTRES (SMART MERGE)
        # =====================================================================
        status.write("Conciliation des hypothèses (Smart Merge)...")

        final_params = _merge_parameters(request, auto_params)

        logger.info(
            "[Workflow] Dispatching calculation | Ticker: %s | Source: %s | MC: %s",
            request.ticker,
            request.input_source.value,
            final_params.enable_monte_carlo
        )

        # =====================================================================
        # ÉTAPE 3 :  EXÉCUTION DU MOTEUR DE VALORISATION
        # =====================================================================
        status.write(f"Exécution du moteur de calcul : {request. mode.value}...")

        if final_params.enable_monte_carlo:
            status.write("Simulation stochastique, tests de sensibilité et stress-testing en cours...")

        result = run_valuation(request, financials, final_params)

        # =====================================================================
        # ÉTAPE 4 : AUDIT DE CONFORMITÉ (GLASS BOX)
        # =====================================================================
        status.write("Génération du rapport d'audit et score de confiance...")
        result.audit_report = AuditEngine. compute_audit(result)

        status.update(label="Analyse finalisée avec succès", state="complete", expanded=False)

        # =====================================================================
        # ÉTAPE 5 : RESTITUTION DES RÉSULTATS
        # =====================================================================
        ui_kpis.render_executive_summary(result)
        ui_kpis.display_valuation_details(result, provider)

    except ValuationException as e:
        status.update(label="Analyse interrompue", state="error", expanded=True)
        _display_diagnostic_message(e.diagnostic)
        st.session_state.active_request = None

    except Exception as e:
        status.update(label="Erreur système critique", state="error", expanded=True)
        logger.error("Critical workflow error: %s", str(e), exc_info=True)
        _display_diagnostic_message(_create_crash_diagnostic(e))


# ==============================================================================
# 2. HELPERS
# ==============================================================================

def _create_data_provider() -> YahooFinanceProvider:
    """Crée et configure le fournisseur de données."""
    macro_provider = YahooMacroProvider()
    return YahooFinanceProvider(macro_provider)


def _merge_parameters(request: ValuationRequest, auto_params: DCFParameters) -> DCFParameters:
    """
    Fusionne les paramètres auto et manuels selon la source d'input.

    Logique Smart Merge :
    - Mode MANUAL : Paramètres expert écrasent les valeurs auto (sauf None)
    - Mode AUTO : Paramètres auto + options UI (Monte Carlo)

    Args:
        request: Requête contenant la source et les paramètres manuels
        auto_params:  Paramètres calculés automatiquement

    Returns:
        Paramètres finaux consolidés
    """
    if request.input_source == InputSource.MANUAL:
        return _merge_manual_params(request, auto_params)

    return _merge_auto_params(request, auto_params)


def _merge_manual_params(request: ValuationRequest, auto_params:  DCFParameters) -> DCFParameters:
    """Fusionne les paramètres en mode expert."""
    merged_data = auto_params.model_dump()
    expert_data = request.manual_params.model_dump(exclude_unset=True)

    # Écrasement sélectif : seules les valeurs non-None sont appliquées
    merged_data. update({k: v for k, v in expert_data.items() if v is not None})

    final_params = DCFParameters(**merged_data)

    # Respect des flags Monte Carlo du terminal expert
    final_params. enable_monte_carlo = request. manual_params.enable_monte_carlo
    final_params.num_simulations = request.manual_params.num_simulations

    return final_params


def _merge_auto_params(request: ValuationRequest, auto_params:  DCFParameters) -> DCFParameters:
    """Fusionne les paramètres en mode automatique."""
    final_params = auto_params.model_copy()

    ui_options = request.options or {}
    final_params.enable_monte_carlo = ui_options. get("enable_monte_carlo", False)
    final_params.num_simulations = ui_options.get("num_simulations", 2000)

    return final_params


def _create_crash_diagnostic(error: Exception) -> DiagnosticEvent:
    """Crée un événement diagnostic pour les erreurs système."""
    return DiagnosticEvent(
        code="SYSTEM_CRASH",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message="Une défaillance technique inattendue a été détectée lors de l'exécution.",
        technical_detail=f"{str(error)}\n{traceback.format_exc()}",
        remediation_hint="Veuillez vérifier votre connexion internet ou tenter une requête simplifiée (Mode Auto)."
    )


def _display_diagnostic_message(diag: DiagnosticEvent) -> None:
    """Affiche un message diagnostic formaté selon la sévérité."""
    if diag.severity in [SeverityLevel.CRITICAL, SeverityLevel.ERROR]:
        st. error(f"**ARRÊT CRITIQUE :** {diag.message}")
    elif diag.severity == SeverityLevel. WARNING:
        st.warning(f"**AVERTISSEMENT :** {diag.message}")
    else:
        st.info(f"**INFORMATION :** {diag.message}")

    with st.expander("Détails techniques et remédiation", expanded=True):
        st.markdown(f"**Action recommandée :** {diag.remediation_hint}")
        if diag.technical_detail:
            st.divider()
            st.code(diag.technical_detail, language="text")