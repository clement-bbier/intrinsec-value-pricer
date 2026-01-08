"""
app/workflow.py
ORCHESTRATEUR LOGIQUE — VERSION V3.8 (Hedge Fund Standard)
Rôle : Pilotage de l'analyse avec fusion résiliente et gestion d'erreurs enrichie.
Note : Implémente la logique "Empty=Auto" vs "0=Value".
"""

import logging
import streamlit as st
import traceback
from core.valuation.engines import run_valuation
from core.exceptions import ValuationException
from core.diagnostics import DiagnosticEvent, SeverityLevel, DiagnosticDomain
from core.models import ValuationRequest, InputSource, DCFParameters
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.auditing.audit_engine import AuditEngine

# Import du module de restitution
import app.ui_components.ui_kpis as ui_kpis

logger = logging.getLogger(__name__)

def run_workflow_and_display(request: ValuationRequest) -> None:
    """
    Point d'entrée unique pilotant le cycle de vie complet de l'analyse financière.
    """
    # État de chargement professionnel conforme Streamlit 2026
    status = st.status("Initialisation de l'analyse...", expanded=True)

    try:
        # --- ÉTAPE 1 : ACQUISITION DES DONNÉES ---
        status.write("Acquisition des données de marché et macro-économiques...")
        macro_provider = YahooMacroProvider()
        provider = YahooFinanceProvider(macro_provider)

        # Récupération initiale (Auto Yahoo)
        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker, request.projection_years
        )

        # --- ÉTAPE 2 : CONCILIATION DES PARAMÈTRES (SMART MERGE) ---
        status.write("Conciliation des hypothèses (Smart Merge)...")

        if request.input_source == InputSource.MANUAL:
            # SOUVERAINETÉ EXPERT : On fusionne les chiffres, mais on garde les options MC du terminal
            merged_data = auto_params.model_dump()
            expert_data = request.manual_params.model_dump(exclude_unset=True)
            merged_data.update({k: v for k, v in expert_data.items() if v is not None})

            final_params = DCFParameters(**merged_data)

            # On force le respect des flags Monte Carlo saisis dans le terminal expert
            final_params.enable_monte_carlo = request.manual_params.enable_monte_carlo
            final_params.num_simulations = request.manual_params.num_simulations
        else:
            # MODE AUTO : On utilise les options de la sidebar
            final_params = auto_params.model_copy()
            ui_options = request.options or {}
            final_params.enable_monte_carlo = ui_options.get("enable_monte_carlo", False)
            final_params.num_simulations = ui_options.get("num_simulations", 2000)

        # Log de certification pour l'audit console
        logger.info(
            f"[Workflow] Dispatching calculation | Ticker: {request.ticker} | "
            f"Source: {request.input_source.value} | MC: {final_params.enable_monte_carlo}"
        )

        # --- ÉTAPE 3 : EXÉCUTION DU MOTEUR DE VALORISATION ---
        status.write(f"Exécution du moteur de calcul : {request.mode.value}...")

        if final_params.enable_monte_carlo:
            status.write("Simulation stochastique, tests de sensibilité et stress-testing en cours...")

        result = run_valuation(request, financials, final_params)

        # --- ÉTAPE 4 : AUDIT DE CONFORMITÉ (GLASS BOX) ---
        status.write("Génération du rapport d'audit et score de confiance...")
        result.audit_report = AuditEngine.compute_audit(result)

        # Finalisation de la barre de statut
        status.update(label="Analyse finalisée avec succès", state="complete", expanded=False)

        # --- ÉTAPE 5 : RESTITUTION DES RÉSULTATS ---
        ui_kpis.render_executive_summary(result)
        ui_kpis.display_valuation_details(result, provider)

    except ValuationException as e:
        status.update(label="Analyse interrompue", state="error", expanded=True)
        _display_diagnostic_message(e.diagnostic)

    except Exception as e:
        status.update(label="Erreur système critique", state="error", expanded=True)
        logger.error(f"Critical workflow error: {str(e)}", exc_info=True)
        _display_diagnostic_message(DiagnosticEvent(
            code="SYSTEM_CRASH",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.SYSTEM,
            message="Une défaillance technique inattendue a été détectée lors de l'exécution.",
            technical_detail=f"{str(e)}\n{traceback.format_exc()}",
            remediation_hint="Veuillez vérifier votre connexion internet ou tenter une requête simplifiée (Mode Auto)."
        ))

def _display_diagnostic_message(diag: DiagnosticEvent):
    """Rendu visuel des diagnostics d'erreurs."""
    if diag.severity in [SeverityLevel.CRITICAL, SeverityLevel.ERROR]:
        st.error(f"**ARRÊT CRITIQUE :** {diag.message}")
    elif diag.severity == SeverityLevel.WARNING:
        st.warning(f"**AVERTISSEMENT :** {diag.message}")
    else:
        st.info(f"**INFORMATION :** {diag.message}")

    with st.expander("Détails techniques et remédiation", expanded=True):
        st.markdown(f"**Action recommandée :** {diag.remediation_hint}")
        if diag.technical_detail:
            st.divider()
            st.code(diag.technical_detail, language="text")