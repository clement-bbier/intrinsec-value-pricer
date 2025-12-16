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
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.auditing.audit_engine import AuditEngine

# --- UI IMPORTS (Modularité) ---
# Ces fonctions sont définies dans app/ui_components/ui_kpis.py
from app.ui_components.ui_kpis import (
    display_dcf_summary,
    display_ddm_summary,
    display_graham_summary,
    display_audit_report,
    render_financial_badge
)
# Cette fonction est définie dans app/ui_components/ui_charts.py
from app.ui_components.ui_charts import display_price_chart, display_simulation_chart

logger = logging.getLogger(__name__)


def run_workflow_and_display(request: ValuationRequest) -> None:
    """
    Orchestrateur Principal :
    1. Acquisition Données (Provider)
    2. Calcul (Engine)
    3. Audit (AuditEngine)
    4. Affichage (UI)
    """
    # Feedback visuel pour l'utilisateur
    status = st.status("Analyse en cours...", expanded=True)

    try:
        # --- ÉTAPE 1 : DONNÉES ---
        status.write("📡 Connexion aux services financiers (Yahoo)...")
        provider = YahooFinanceProvider()

        # Récupération automatique des états financiers et des paramètres macro
        financials, auto_params = provider.get_company_financials_and_parameters(
            request.ticker,
            request.projection_years
        )

        # Application de la surcharge manuelle si nécessaire (Mode Expert)
        final_params = request.manual_params if request.manual_params else auto_params

        # --- ÉTAPE 2 : MOTEUR DE CALCUL ---
        status.write(f"⚙️ Exécution du modèle : {request.mode.value}...")

        # Appel du moteur (retourne un objet ValuationResult unique)
        result = run_valuation(request, financials, final_params)

        # --- ÉTAPE 3 : AUDIT ---
        status.write("🔍 Audit de fiabilité et cohérence...")
        audit_report = AuditEngine.compute_audit(result)

        # On attache le rapport d'audit au résultat pour l'affichage
        object.__setattr__(result, 'audit_report', audit_report)

        status.update(label="Analyse terminée avec succès", state="complete", expanded=False)

        # --- ÉTAPE 4 : AFFICHAGE ---
        # On passe le résultat ET le provider (pour l'historique de prix)
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
    Affiche les KPIs, les graphiques et l'audit selon la stratégie.
    """
    st.markdown("---")

    # 1. En-tête (Prix vs Valeur)
    c1, c2, c3 = st.columns([2, 2, 3])

    with c1:
        st.metric("Prix de Marché", f"{res.market_price:,.2f} {res.financials.currency}")

    with c2:
        st.metric(
            "Valeur Intrinsèque",
            f"{res.intrinsic_value_per_share:,.2f} {res.financials.currency}",
            delta=f"{res.upside_pct:.1%}" if res.upside_pct is not None else None
        )

    with c3:
        if res.audit_report:
            # Badge de qualité
            score = res.audit_report.global_score
            render_financial_badge("AUDIT SCORE", f"{score:.0f}/100", score)

    st.markdown("---")

    # 2. Corps de page (Spécifique par Stratégie)
    # On utilise le polymorphisme : isinstance vérifie le type de résultat

    if isinstance(res, DCFValuationResult):
        # Pour Simple, Fundamental, Growth
        display_dcf_summary(res)

        # Si c'est un Monte Carlo, on ajoute le graphique de distribution
        if res.simulation_results:
            st.subheader("Distribution Monte Carlo")
            # Appel à ui_charts
            display_simulation_chart(res.simulation_results, res.market_price, res.financials.currency)

    elif isinstance(res, DDMValuationResult):
        # Pour les Banques
        display_ddm_summary(res)

    elif isinstance(res, GrahamValuationResult):
        # Pour la méthode Graham
        display_graham_summary(res)

    else:
        st.warning(f"Type de résultat non reconnu : {type(res)}")

    # 3. Rapport d'Audit Complet
    if res.audit_report:
        display_audit_report(res.audit_report)

    # 4. Historique de Prix (Nécessite le provider passé en argument)
    with st.expander("Historique de Prix & Analyse", expanded=False):
        try:
            hist_data = provider.get_price_history(res.financials.ticker)
            # Appel à ui_charts
            display_price_chart(res.financials.ticker, hist_data, None)
        except Exception as e:
            st.info(f"Graphique historique indisponible ({e}).")