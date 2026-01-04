"""
app/workflow.py
ORCHESTRATEUR LOGIQUE — VERSION HARMONISÉE V3.6
Rôle : Pilotage de l'acquisition de données, exécution du moteur de calcul et délégation du rendu.
"""

import logging
import streamlit as st
import traceback
from core.valuation.engines import run_valuation
from core.exceptions import ValuationException
from core.diagnostics import DiagnosticEvent, SeverityLevel, DiagnosticDomain
from core.models import ValuationRequest, InputSource
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
    # État de chargement professionnel
    status = st.status("Initialisation de l'analyse...", expanded=True)

    try:
        # --- ÉTAPE 1 : ACQUISITION DES DONNÉES ---
        status.write("Connexion aux services de données financières...")
        macro_provider = YahooMacroProvider()
        provider = YahooFinanceProvider(macro_provider)

        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker, request.projection_years
        )

        # --- ÉTAPE 2 : CONCILIATION DES PARAMÈTRES (SMART MERGE) ---
        # Respect de la hiérarchie des sources de données (Manuel vs Automatique)
        if request.input_source == InputSource.MANUAL:
            final_params = request.manual_params
        else:
            final_params = auto_params
            if request.manual_params:
                # Intégration sélective des paramètres de simulation
                final_params = auto_params.model_copy(update={
                    "enable_monte_carlo": request.manual_params.enable_monte_carlo,
                    "num_simulations": request.manual_params.num_simulations,
                    "projection_years": request.manual_params.projection_years
                })

        # --- ÉTAPE 3 : EXÉCUTION DU MOTEUR DE VALORISATION ---
        status.write(f"Exécution du modèle : {request.mode.value}...")
        result = run_valuation(request, financials, final_params)

        # --- ÉTAPE 4 : AUDIT DE CONFORMITÉ ET FIABILITÉ ---
        status.write("Analyse de cohérence des hypothèses et audit du modèle...")
        result.audit_report = AuditEngine.compute_audit(result)

        # Finalisation du processus
        status.update(label="Analyse finalisée avec succès", state="complete", expanded=False)

        # --- ÉTAPE 5 : RESTITUTION DES RÉSULTATS ---
        # Affichage du résumé exécutif (Signaux financiers et notation d'audit)
        ui_kpis.render_executive_summary(result)

        # Affichage du rapport détaillé (Preuve mathématique, Analyse de risque, Audit)
        ui_kpis.display_valuation_details(result, provider)

    except ValuationException as e:
        status.update(label="Analyse interrompue", state="error", expanded=True)
        _display_diagnostic_message(e.diagnostic)
    except Exception as e:
        status.update(label="Erreur système critique", state="error", expanded=True)
        logger.error("Critical workflow error", exc_info=True)
        _display_diagnostic_message(DiagnosticEvent(
            code="SYSTEM_CRASH",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.SYSTEM,
            message="Une défaillance technique inattendue a été détectée.",
            technical_detail=f"{str(e)}\n{traceback.format_exc()}",
            remediation_hint="Veuillez contacter l'assistance technique ou tenter une nouvelle requête avec un autre identifiant (ticker)."
        ))

def _display_diagnostic_message(diag: DiagnosticEvent):
    """Rendu normalisé des événements de diagnostic et erreurs métier."""
    if diag.severity in [SeverityLevel.CRITICAL, SeverityLevel.ERROR]:
        st.error(f"ARRET CRITIQUE : {diag.message}")
    elif diag.severity == SeverityLevel.WARNING:
        st.warning(f"AVERTISSEMENT : {diag.message}")
    else:
        st.info(f"INFORMATION : {diag.message}")

    with st.expander("Analyse détaillée et mesures correctives", expanded=True):
        st.success(f"Action recommandée : {diag.remediation_hint}")
        if diag.technical_detail:
            st.divider()
            st.code(diag.technical_detail, language="text")