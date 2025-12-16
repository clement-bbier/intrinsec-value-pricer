import sys
from pathlib import Path
import logging
import streamlit as st

# --- 0. SETUP DES CHEMINS ---
file_path = Path(__file__).resolve()
root_path = file_path.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# --- 1. CONFIG STREAMLIT ---
st.set_page_config(
    page_title="Intrinsic Value Pricer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. IMPORTS ---
from core.models import (
    ValuationRequest,
    ValuationMode,
    InputSource
)
from core.valuation.engines import run_valuation
from infra.data_providers.yahoo_provider import YahooFinanceProvider  # Correction Nom
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.auditing.audit_engine import AuditEngine

# Composants UI (Noms corrigés selon vos fichiers)
from app.ui_components.ui_inputs_auto import display_auto_inputs
from app.ui_components.ui_inputs_expert import display_expert_request
from app.ui_components.ui_kpis import display_main_kpis, display_valuation_details
from app.ui_components.ui_charts import display_price_chart, display_simulation_chart, display_sensitivity_heatmap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    st.title("💎 Intrinsic Value Pricer")
    st.caption("Standard Institutionnel (CFA/Damodaran) • Architecture 'Glass Box'")

    # --- A. SÉLECTEUR DE MODE ---
    st.sidebar.header("Mode d'utilisation")
    mode_input = st.sidebar.radio(
        "Source des données",
        options=[InputSource.AUTO.value, InputSource.MANUAL.value],
        format_func=lambda x: "🚀 Auto (Yahoo)" if x == "AUTO" else "🛠️ Expert (Manuel)"
    )
    current_source = InputSource(mode_input)

    # --- B. AFFICHAGE DES INPUTS ---
    request: ValuationRequest = None

    if current_source == InputSource.AUTO:
        # Le mode Auto est géré dans la sidebar par votre composant
        request = display_auto_inputs("AAPL", 5)
    else:
        # Le mode Expert prend la page principale
        request = display_expert_request("AAPL", 5)

    # --- C. EXÉCUTION DU WORKFLOW ---
    # Si le composant UI a retourné une requête (bouton cliqué), on lance le calcul
    if request:
        try:
            with st.spinner(f"Analyse financière de {request.ticker} ({request.mode.value})..."):

                # 1. Instanciation Providers
                macro_provider = YahooMacroProvider()
                data_provider = YahooFinanceProvider(macro_provider=macro_provider)

                # 2. Récupération Données (si Auto) ou Juste Prix (si Manuel)
                if request.input_source == InputSource.AUTO:
                    # En mode Auto, le provider calcule tout
                    financials, params = data_provider.get_company_financials_and_parameters(
                        ticker=request.ticker,
                        projection_years=request.projection_years
                    )
                    # Injection des options spécifiques (ex: Monte Carlo sims)
                    if request.options.get("num_simulations"):
                        params.num_simulations = request.options["num_simulations"]

                else:
                    # En mode Manuel, on a déjà les params dans la requête
                    # On récupère juste les financials de base pour le prix actuel
                    financials = data_provider.get_company_financials(request.ticker)
                    params = request.manual_params

                    # On applique les overrides manuels s'ils existent dans la requête
                    if request.manual_beta:
                        financials.beta = request.manual_beta

                # 3. Exécution Moteur
                result = run_valuation(request, financials, params)

                # 4. Audit
                audit_report = AuditEngine.compute_audit(result)
                result.audit_report = audit_report

            # --- D. AFFICHAGE RÉSULTATS ---

            # KPI Principaux
            display_main_kpis(result)

            # Graphiques
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("Historique & Contexte")
                try:
                    hist = data_provider.get_price_history(request.ticker)
                    display_price_chart(request.ticker, hist)
                except:
                    st.warning("Graphique prix indisponible")

                if result.simulation_results:
                    display_simulation_chart(result.simulation_results, result.market_price, result.financials.currency)

            with c2:
                # Heatmap pour les DCF
                if request.mode in [ValuationMode.DISCOUNTED_CASH_FLOW_STANDARD,
                                    ValuationMode.NORMALIZED_FCFF_CYCLICAL]:
                    # Fonction proxy légère pour la heatmap (évite de relancer tout le moteur)
                    from core.computation.financial_math import calculate_terminal_value_gordon

                    # On capture les valeurs actuelles pour la lambda
                    last_fcf = result.projected_fcfs[-1] if hasattr(result,
                                                                    'projected_fcfs') and result.projected_fcfs else 0
                    base_pv = result.sum_discounted_fcf if hasattr(result, 'sum_discounted_fcf') else 0
                    net_debt = result.financials.total_debt - result.financials.cash_and_equivalents
                    shares = result.financials.shares_outstanding
                    years = params.projection_years

                    def quick_calc(w, g):
                        if w <= g: return None
                        tv = calculate_terminal_value_gordon(last_fcf, w, g)
                        tv_disc = tv / ((1 + w) ** years)
                        ev = base_pv + tv_disc  # Approximation: on garde la PV des flux explicites constante (w impacte peu sur 5 ans vs TV)
                        return (ev - net_debt) / shares

                    display_sensitivity_heatmap(result.wacc, result.params.perpetual_growth_rate, quick_calc,
                                                result.financials.currency)

            # Détails Glass Box
            st.markdown("---")
            display_valuation_details(result)

        except Exception as e:
            st.error(f"Erreur d'exécution : {str(e)}")
            # st.exception(e) # Décommenter pour debug

    else:
        # Message d'accueil si aucune analyse lancée
        if current_source == InputSource.AUTO:
            st.info("👈 Configurez l'analyse dans la barre latérale et cliquez sur 'Lancer'.")
        else:
            st.info("Remplissez les paramètres expert ci-dessus pour démarrer.")


if __name__ == "__main__":
    main()