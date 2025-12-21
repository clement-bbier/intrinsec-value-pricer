"""
app/workflow.py

ORCHESTRATEUR UI / BACKEND (OPTIMISÉ)
Version : V2.1 — Workflow Haute Performance & Expérience Utilisateur

CHOIX ARCHITECTURAL (PERFORMANCE) :
-----------------------------------
Nous avons opté pour une optimisation du WORKFLOW et du CACHING (Option B),
plutôt qu'une réécriture vectorielle (NumPy pur) des formules (Option A).

Pourquoi ?
1. Maintien du style "Glass Box" : Chaque simulation reste auditable.
2. Lisibilité : On évite les matrices illisibles pour un humain.
3. UX : Avec 5 000 simulations, le temps de calcul (~2s) est géré
   par des indicateurs de progression visuels (st.status).

Ce fichier fait le pont entre :
- L'interface Streamlit (UI)
- L'infrastructure de données (avec Caching)
- Le moteur de calcul (avec Silent Mode)
"""

import logging
import streamlit as st

# --- CORE IMPORTS ---
from core.valuation.engines import run_valuation
from core.exceptions import DataProviderError, CalculationError, ExternalServiceError
from core.models import (
    ValuationRequest,
    ValuationResult,
    DCFValuationResult,
    DDMValuationResult,
    GrahamValuationResult,
    ValuationMode
)

# --- INFRA IMPORTS ---
# On importe le Macro Provider pour l'injection de dépendance
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.auditing.audit_engine import AuditEngine

# --- UI IMPORTS (Modularité) ---
from app.ui_components.ui_kpis import (
    display_dcf_summary,
    display_ddm_summary,
    display_graham_summary,
    display_audit_report,
    render_financial_badge
)
from app.ui_components.ui_charts import display_price_chart, display_simulation_chart

logger = logging.getLogger(__name__)


def run_workflow_and_display(request: ValuationRequest) -> None:
    """
    Orchestrateur Principal :
    1. Acquisition Données (Provider avec Cache)
    2. Calcul (Engine avec Silent Mode pour Monte Carlo)
    3. Audit (AuditEngine)
    4. Affichage (UI Réactive)
    """

    # Le composant 'status' permet de garder l'utilisateur informé sans bloquer
    status = st.status("Démarrage de l'analyse...", expanded=True)

    try:
        # --- ÉTAPE 1 : DONNÉES (CACHE ACTIF) ---
        status.write("📡 Connexion aux services financiers (Yahoo)...")

        # Injection de dépendance propre
        macro_provider = YahooMacroProvider()
        provider = YahooFinanceProvider(macro_provider)

        # Récupération (Rapide grâce au @st.cache_data dans le provider)
        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker,
            request.projection_years
        )

        # Fusion des paramètres (Mode Expert vs Auto)
        final_params = request.manual_params if request.manual_params else auto_params

        # --- ÉTAPE 2 : MOTEUR DE CALCUL (SILENT MODE INCLUS) ---
        msg_calcul = f"⚙️ Exécution du modèle : {request.mode.value}..."
        if final_params.enable_monte_carlo:
            msg_calcul += f" ({final_params.num_simulations} simulations)"

        status.write(msg_calcul)

        # Appel du moteur.
        # Si Monte Carlo est actif, 'monte_carlo.py' utilisera le 'Silent Mode' automatiquement.
        result = run_valuation(request, financials, final_params)

        # --- ÉTAPE 3 : AUDIT (GOUVERNANCE) ---
        status.write("🔍 Audit de fiabilité et cohérence...")

        # Le bug de signature a été corrigé dans audit_engine.py
        audit_report = AuditEngine.compute_audit(result)

        # On attache le rapport au résultat
        object.__setattr__(result, 'audit_report', audit_report)

        # Fin du processus visuel
        status.update(
            label="Analyse terminée avec succès",
            state="complete",
            expanded=False
        )

        # --- ÉTAPE 4 : RESTITUTION GRAPHIQUE ---
        _display_valuation_results(result, provider)

    except (DataProviderError, ExternalServiceError) as e:
        status.update(label="Erreur de données", state="error", expanded=False)
        st.error(f"Impossible de récupérer les données : {e.ui_user_message}")
        logger.error(f"Data Error: {e}")

    except CalculationError as e:
        status.update(label="Erreur de calcul", state="error", expanded=False)
        st.error(f"Le modèle n'a pas convergé : {e.ui_user_message}")
        logger.error(f"Calc Error: {e}")

    except Exception as e:
        status.update(label="Erreur système", state="error", expanded=False)
        st.error(f"Une erreur inattendue est survenue : {str(e)}")
        logger.error("Critical workflow error", exc_info=True)


def _display_valuation_results(res: ValuationResult, provider: YahooFinanceProvider) -> None:
    """
    Routeur d'affichage (Vue).
    Gère l'affichage optimisé des résultats, incluant les distributions Monte Carlo.
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
        st.metric(
            "Valeur Intrinsèque",
            f"{res.intrinsic_value_per_share:,.2f} {res.financials.currency}",
            delta=f"{res.upside_pct:.1%}" if res.upside_pct is not None else None
        )

    with c3:
        if res.audit_report:
            # Affiche le score de confiance (0-100)
            score = res.audit_report.global_score
            render_financial_badge("AUDIT SCORE", f"{score:.0f}/100", score)

    st.markdown("---")

    # 2. Corps de page (Détail Stratégie)

    if isinstance(res, DCFValuationResult):
        # Affichage standard DCF
        display_dcf_summary(res)

        # GESTION MONTE CARLO (Optimisée)
        # Si des résultats de simulation sont présents (liste de 5000 floats),
        # on affiche le graphique de distribution.
        if res.simulation_results:
            st.subheader(f"Distribution Monte Carlo ({len(res.simulation_results)} scénarios)")

            # Note : Altair gère très bien 5000 points, c'est fluide.
            display_simulation_chart(
                res.simulation_results,
                res.market_price,
                res.financials.currency
            )

            # Affichage des quantiles clés sous le graph
            q = res.quantiles
            if q:
                c_p10, c_p50, c_p90 = st.columns(3)
                c_p10.metric("P10 (Pessimiste)", f"{q.get('P10', 0):,.2f}")
                c_p50.metric("P50 (Central)", f"{q.get('P50', 0):,.2f}")
                c_p90.metric("P90 (Optimiste)", f"{q.get('P90', 0):,.2f}")

    elif isinstance(res, DDMValuationResult):
        display_ddm_summary(res)

    elif isinstance(res, GrahamValuationResult):
        display_graham_summary(res)

    else:
        st.warning(f"Type de résultat non reconnu : {type(res)}")

    # 3. Rapport d'Audit Complet (Tableau des logs)
    if res.audit_report:
        display_audit_report(res.audit_report)

    # 4. Historique de Prix (Appel Provider avec Cache)
    with st.expander("Historique de Prix & Analyse Technique", expanded=False):
        try:
            # Cet appel est maintenant instantané grâce au cache du provider
            hist_data = provider.get_price_history(res.financials.ticker)
            display_price_chart(res.financials.ticker, hist_data)
        except Exception as e:
            st.info(f"Graphique historique indisponible ({e}).")