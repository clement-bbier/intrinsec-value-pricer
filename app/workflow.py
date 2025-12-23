"""
app/workflow.py

ORCHESTRATEUR UI / BACKEND (OPTIMISÉ - V3.3 PYDANTIC FIX)
Version : V3.3 — Fix dataclasses.replace pour compatibilité Pydantic

Ce fichier fait le pont entre :
- L'interface Streamlit (UI)
- L'infrastructure de données (YahooProvider)
- Le moteur de calcul (Valuation Engines)
- Le nouveau système de gestion d'erreurs (Diagnostics)
"""

import logging
import streamlit as st
import traceback
# [MODIFICATION] : On retire 'replace' car on utilise maintenant la méthode native de Pydantic

# --- CORE IMPORTS ---
# Note : engines.py est le routeur qui appelle vos stratégies (Standard, Graham, RIM, etc.)
from core.valuation.engines import run_valuation

# NOUVEAU : On importe le système de diagnostic unifié
from core.exceptions import ValuationException
from core.diagnostics import DiagnosticEvent, SeverityLevel, DiagnosticDomain
from core.models import (
    ValuationRequest,
    ValuationResult,
    DCFValuationResult,
    DDMValuationResult,
    GrahamValuationResult,
    RIMValuationResult,
    InputSource
)

# --- INFRA IMPORTS ---
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.auditing.audit_engine import AuditEngine

# --- UI IMPORTS ---
from app.ui_components.ui_kpis import (
    display_dcf_summary,
    display_ddm_summary,
    display_graham_summary,
    display_rim_summary,
    display_audit_report,
    render_financial_badge
)
from app.ui_components.ui_charts import display_price_chart, display_simulation_chart

logger = logging.getLogger(__name__)


def run_workflow_and_display(request: ValuationRequest) -> None:
    """
    Orchestrateur Principal V3.
    Gère le flux d'exécution et intercepte les ValuationException pour afficher
    des diagnostics précis à l'utilisateur.
    """

    # 1. Initialisation du Status (Loader visuel "Modern Streamlit")
    status = st.status("Démarrage de l'analyse...", expanded=True)

    try:
        # --- ÉTAPE 1 : DONNÉES (CACHE ACTIF) ---
        status.write("📡 Connexion aux services financiers (Yahoo)...")

        # Injection de dépendance (Pattern propre)
        macro_provider = YahooMacroProvider()
        provider = YahooFinanceProvider(macro_provider)

        # Récupération (Peut lever TickerNotFoundError, DataMissingError...)
        # Cette méthode doit être celle définie dans votre DataProvider mis à jour
        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker,
            request.projection_years
        )

        # --- ÉTAPE 2 : FUSION INTELLIGENTE DES PARAMÈTRES (SMART MERGE) ---
        # C'est ici que se joue la compatibilité Auto + Monte Carlo [V3.3 Fix]

        if request.input_source == InputSource.MANUAL:
            # Mode EXPERT total : On prend tout ce que l'user a saisi
            final_params = request.manual_params
        else:
            # Mode AUTO : On prend Yahoo par défaut
            final_params = auto_params

            # MAIS si l'user a activé Monte Carlo (via manual_params), on injecte juste la config
            # sans écraser les taux financiers (WACC, etc.) de Yahoo
            if request.manual_params:
                # [CORRECTIF CRITIQUE] : Utilisation de model_copy pour Pydantic V2
                # Au lieu de dataclasses.replace() qui ferait crasher l'application
                final_params = auto_params.model_copy(update={
                    "enable_monte_carlo": request.manual_params.enable_monte_carlo,
                    "num_simulations": request.manual_params.num_simulations,
                    "projection_years": request.manual_params.projection_years
                })

        # --- ÉTAPE 3 : MOTEUR DE CALCUL ---
        msg_calcul = f"⚙️ Exécution du modèle : {request.mode.value}..."
        if final_params.enable_monte_carlo:
            msg_calcul += f" ({final_params.num_simulations} simulations)"

        status.write(msg_calcul)

        # Appel du moteur (Peut lever ModelIncoherenceError)
        result = run_valuation(request, financials, final_params)

        # --- ÉTAPE 4 : AUDIT (GOUVERNANCE) ---
        status.write("🔍 Audit de fiabilité et cohérence...")

        # Le moteur d'audit inspecte le résultat pour générer le score /100
        audit_report = AuditEngine.compute_audit(result)

        # On attache le rapport au résultat
        result.audit_report = audit_report

        # Fin du processus visuel (Succès)
        status.update(
            label="Analyse terminée avec succès",
            state="complete",
            expanded=False
        )

        # --- ÉTAPE 5 : RESTITUTION GRAPHIQUE ---
        _display_valuation_results(result, provider)

    # --- GESTION DES ERREURS UNIFIÉE (V3) ---
    except ValuationException as e:
        # C'est une erreur "prévue" et qualifiée (Métier, Donnée, Infra)
        diag = e.diagnostic

        # On met à jour le statut du spinner pour montrer l'échec visuellement
        status.update(label="Analyse interrompue", state="error", expanded=True)

        # On délègue l'affichage à notre routeur de messages intelligent
        _display_diagnostic_message(diag)

    except Exception as e:
        # C'est une erreur imprévue (Bug code, librairie externe qui crash)
        status.update(label="Erreur Système Critique", state="error", expanded=True)
        logger.error("Critical workflow error", exc_info=True)

        # On crée un diagnostic d'urgence pour ne pas laisser l'user dans le flou
        unexpected_diag = DiagnosticEvent(
            code="SYSTEM_CRASH",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.SYSTEM,
            message="Une erreur technique inattendue est survenue.",
            technical_detail=f"{str(e)}\n{traceback.format_exc()}",
            remediation_hint="Veuillez contacter le support ou réessayer plus tard."
        )
        _display_diagnostic_message(unexpected_diag)


def _display_diagnostic_message(diag: DiagnosticEvent):
    """
    Affiche un DiagnosticEvent dans l'UI avec la bonne couleur et les détails.
    C'est ici que la 'magie' de l'UX opère pour rassurer l'utilisateur.
    """
    # Titre principal du message avec code couleur
    if diag.severity == SeverityLevel.CRITICAL:
        st.error(f"⛔ **BLOQUANT : {diag.message}**")
    elif diag.severity == SeverityLevel.ERROR:
        st.error(f"❌ **ERREUR : {diag.message}**")
    elif diag.severity == SeverityLevel.WARNING:
        st.warning(f"⚠️ **ATTENTION : {diag.message}**")
    else:
        st.info(f"ℹ️ **INFO : {diag.message}**")

    # Zone de détails (Expandable) pour ne pas polluer l'écran si pas nécessaire
    with st.expander("🔍 Comprendre et Résoudre ce problème", expanded=True):
        col_meta, col_hint = st.columns([1, 2])

        with col_meta:
            st.markdown(f"**Domaine :** `{diag.domain.value}`")
            st.markdown(f"**Code Erreur :** `{diag.code}`")

        with col_hint:
            if diag.remediation_hint:
                st.success(f"💡 **Conseil :** {diag.remediation_hint}")
            else:
                st.info("Aucune action spécifique recommandée. Vérifiez les données d'entrée.")

        if diag.technical_detail:
            st.divider()
            st.markdown("**Détail Technique (pour développeurs) :**")
            st.code(diag.technical_detail, language="text")


def _display_valuation_results(res: ValuationResult, provider: YahooFinanceProvider) -> None:
    """
    Routeur d'affichage (Vue).
    Gère l'affichage optimisé des résultats selon le type de modèle.
    """
    st.markdown("---")

    # 1. En-tête (KPIs Haut Niveau)
    c1, c2, c3 = st.columns([2, 2, 3])

    with c1:
        st.metric(
            "Prix de Marché",
            f"{res.market_price:,.2f} {res.financials.currency}"
        )

    with c2:
        # Affichage conditionnel de l'upside
        delta_val = f"{res.upside_pct:.1%}" if res.upside_pct is not None else None

        st.metric(
            "Valeur Intrinsèque",
            f"{res.intrinsic_value_per_share:,.2f} {res.financials.currency}",
            delta=delta_val
        )

    with c3:
        if res.audit_report:
            score = res.audit_report.global_score
            # Utilisation du composant existant pour le badge
            render_financial_badge("AUDIT SCORE", f"{score:.0f}/100", score)

    st.markdown("---")

    # 2. Corps de page (Détail Stratégie Spécifique)
    if isinstance(res, DCFValuationResult):
        display_dcf_summary(res)

    elif isinstance(res, RIMValuationResult):
        # Support pour le nouveau modèle RIM (Banques)
        try:
            display_rim_summary(res)
        except NameError:
             st.warning("Le composant d'affichage RIM (display_rim_summary) n'est pas encore implémenté dans ui_kpis.")
             st.json(res.__dict__) # Fallback propre

    elif isinstance(res, DDMValuationResult):
        display_ddm_summary(res)

    elif isinstance(res, GrahamValuationResult):
        display_graham_summary(res)

    else:
        st.warning(f"Type de résultat non reconnu : {type(res)}. Affichage des données brutes.")
        st.write(res)

    # ==========================================================================
    # 3. SECTION MONTE CARLO UNIVERSELLE (COMPATIBLE RIM + DCF)
    # ==========================================================================
    # Cette section s'affiche maintenant pour TOUS les modèles qui ont des simulations.

    if res.simulation_results:
        st.markdown("---")
        st.subheader(f"🔮 Distribution de Probabilité ({len(res.simulation_results)} scénarios)")

        # Affichage du Chart
        display_simulation_chart(res.simulation_results, res.market_price, res.financials.currency)

        # Affichage des Quantiles
        q = res.quantiles
        if q:
            c1, c2, c3 = st.columns(3)
            c1.metric("Scénario Pessimiste (P10)", f"{q.get('P10', 0):,.2f} {res.financials.currency}")
            c2.metric("Scénario Central (P50)", f"{q.get('P50', 0):,.2f} {res.financials.currency}")
            c3.metric("Scénario Optimiste (P90)", f"{q.get('P90', 0):,.2f} {res.financials.currency}")

    # 4. Rapport d'Audit Détaillé
    if res.audit_report:
        display_audit_report(res.audit_report)

    # 5. Historique de Prix (Toujours utile pour le contexte)
    with st.expander("📈 Historique de Prix & Analyse Technique", expanded=False):
        try:
            hist_data = provider.get_price_history(res.financials.ticker)
            display_price_chart(res.financials.ticker, hist_data)
        except Exception as e:
            st.info("Graphique historique indisponible.")
            logger.warning(f"Chart error: {e}")