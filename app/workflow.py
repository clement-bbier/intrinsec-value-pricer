"""
app/workflow.py
ORCHESTRATEUR LOGIQUE — VERSION HARMONISÉE V3.5
Rôle : Piloter la donnée et le calcul, puis déléguer l'intégralité de la restitution à ui_kpis.
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

# Jalon 2 : Import unique du module de restitution
import app.ui_components.ui_kpis as ui_kpis

logger = logging.getLogger(__name__)

def run_workflow_and_display(request: ValuationRequest) -> None:
    """
    Point d'entrée unique après le clic sur 'Lancer l'analyse'.
    Gère le cycle de vie complet de l'estimation.
    """
    # 1. État de chargement institutionnel
    status = st.status("Démarrage de l'analyse...", expanded=True)

    try:
        # --- ÉTAPE 1 : RÉCUPÉRATION DES DONNÉES (Yahoo Finance) ---
        status.write("📡 Connexion aux services financiers...")
        macro_provider = YahooMacroProvider()
        provider = YahooFinanceProvider(macro_provider)

        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker, request.projection_years
        )

        # --- ÉTAPE 2 : FUSION DES PARAMÈTRES (SMART MERGE) ---
        # On respecte la souveraineté de l'analyste ou les automatismes Yahoo
        if request.input_source == InputSource.MANUAL:
            final_params = request.manual_params
        else:
            final_params = auto_params
            if request.manual_params:
                # Injection de la config Monte Carlo dans le profil Auto
                final_params = auto_params.model_copy(update={
                    "enable_monte_carlo": request.manual_params.enable_monte_carlo,
                    "num_simulations": request.manual_params.num_simulations,
                    "projection_years": request.manual_params.projection_years
                })

        # --- ÉTAPE 3 : MOTEUR DE CALCUL (VALUATION CORE) ---
        status.write(f"⚙️ Exécution du modèle : {request.mode.value}...")
        result = run_valuation(request, financials, final_params)

        # --- ÉTAPE 4 : AUDIT DE FIABILITÉ (GOUVERNANCE) ---
        status.write("🔍 Audit de cohérence des hypothèses...")
        result.audit_report = AuditEngine.compute_audit(result)

        # Finalisation du loader
        status.update(label="Analyse terminée avec succès", state="complete", expanded=False)

        # --- ÉTAPE 5 : RESTITUTION INTÉGRALE (DÉLÉGATION UI_KPIS) ---
        # Action 2.1 : On affiche le bandeau de signal (Prix, Valeur, Marge, Rating)
        ui_kpis.render_executive_summary(result)

        # Jalon 3 : On affiche le détail structuré en 3 onglets (Preuve, Risque, Audit)
        # Note : On transmet 'provider' pour que l'onglet Risque puisse tracer l'historique
        ui_kpis.display_valuation_details(result, provider)

    except ValuationException as e:
        status.update(label="Analyse interrompue", state="error", expanded=True)
        _display_diagnostic_message(e.diagnostic)
    except Exception as e:
        status.update(label="Erreur Système Critique", state="error", expanded=True)
        logger.error("Critical workflow error", exc_info=True)
        _display_diagnostic_message(DiagnosticEvent(
            code="SYSTEM_CRASH", severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.SYSTEM, message="Une erreur technique inattendue est survenue.",
            technical_detail=f"{str(e)}\n{traceback.format_exc()}",
            remediation_hint="Veuillez contacter le support ou réessayer avec un autre ticker."
        ))

def _display_diagnostic_message(diag: DiagnosticEvent):
    """Rendu standardisé des erreurs métier."""
    if diag.severity in [SeverityLevel.CRITICAL, SeverityLevel.ERROR]:
        st.error(f"⛔ **BLOQUANT : {diag.message}**")
    elif diag.severity == SeverityLevel.WARNING:
        st.warning(f"⚠️ **ATTENTION : {diag.message}**")
    else:
        st.info(f"ℹ️ **INFO : {diag.message}**")

    with st.expander("🔍 Comprendre et Résoudre ce problème", expanded=True):
        st.success(f"💡 **Conseil :** {diag.remediation_hint}")
        if diag.technical_detail:
            st.divider()
            st.code(diag.technical_detail, language="text")