import logging
from typing import Sequence

import streamlit as st

from core.models import ValuationMode
from core.dcf.historical_params import YahooMacroHistoricalParamsStrategy
from core.dcf.historical_valuation_service import build_intrinsic_value_time_series
from core.dcf.valuation_service import run_valuation
from core.exceptions import CalculationError, DataProviderError
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

# Imports UI
from app.ui_kpis import display_results
from app.ui_charts import (
    display_price_chart,
    _get_sample_dates,
    display_simulation_chart,
)

logger = logging.getLogger(__name__)

PROVIDER = YahooFinanceProvider()
MACRO_PROVIDER = YahooMacroProvider()

# --- LISTE DES SECTEURS INTERDITS POUR LE DCF ---
FORBIDDEN_SECTORS = ["Financial Services", "Real Estate"]


def run_workflow_and_display(
        ticker: str,
        projection_years: int,
        mode: ValuationMode,
) -> None:
    """
    Workflow complet avec garde-fous sectoriels, affichage des résultats,
    du profil de risque et de l'historique de valorisation.
    """
    logger.info("=== NOUVELLE DEMANDE : %s | Mode: %s ===", ticker, mode.value)

    # Création du conteneur de statut
    status = st.status("Analyse en cours...", expanded=True)

    try:
        # 1) Chargement
        status.write(f"📥 Récupération des données pour {ticker}...")
        financials, params = PROVIDER.get_company_financials_and_parameters(
            ticker=ticker,
            projection_years=projection_years,
        )

        # --- GARDE-FOU SECTORIEL ---
        if financials.sector in FORBIDDEN_SECTORS:
            status.update(label="Analyse Interrompue 🛑", state="error", expanded=True)
            st.error(f"🛑 Méthode Inadaptée pour ce Secteur : {financials.sector}")
            st.markdown(
                f"""
                **Pourquoi ?**
                L'entreprise **{financials.ticker}** appartient au secteur **{financials.sector}** (Industrie : {financials.industry}).
                Les modèles DCF basés sur le Free Cash Flow ne fonctionnent pas correctement 
                pour les Banques (Financial Services) ou les Foncières (REITs) car leur structure de bilan est différente.

                **Recommandation Pro :**
                Ces secteurs nécessitent une valorisation par **Modèle de Dividende (DDM)** ou par **Multiples d'Actif Net (P/B)**.
                """
            )
            logger.warning("[GUARDRAIL] DCF arrêté pour le secteur %s.", financials.sector)
            return
        # -------------------------------------

        logger.info("[1] Données récupérées. Secteur: %s", financials.sector)

        # 2) Calcul
        status.write("🧮 Calcul de la valorisation actuelle...")
        dcf_result = run_valuation(financials, params, mode)
        logger.info("[2] Valorisation actuelle terminée.")

        # 3) Historique (Sauf Monte Carlo)
        price_history = None
        hist_iv_df = None
        hist_msgs: Sequence[str] = []

        try:
            status.write("📈 Récupération de l'historique de prix...")
            price_history = PROVIDER.get_price_history(ticker, period="5y")

            if mode == ValuationMode.MONTE_CARLO:
                status.write("📈 Mode Simulation : Historique désactivé.")
            else:
                status.write("📈 Construction de l'historique (Haute Résolution)...")
                price_history_reset = price_history.reset_index()
                sample_dates = _get_sample_dates(price_history_reset, freq="1W")

                if len(sample_dates) > 0:
                    macro_strategy = YahooMacroHistoricalParamsStrategy(
                        MACRO_PROVIDER, financials.currency
                    )
                    hist_iv_df, errors = build_intrinsic_value_time_series(
                        ticker, financials, params, mode, PROVIDER, macro_strategy, sample_dates
                    )
                    hist_msgs.extend(errors)
                    logger.info("[3] Historique construit (%d points).", len(hist_iv_df))
                else:
                    status.write("📈 Pas assez de points pour l'historique.")

        except Exception as e:
            logger.warning("[HistIV] Échec/Skip historique : %s", e)
            st.warning("Historique de valorisation indisponible.")

        # 4) Affichage
        status.update(label="Analyse terminée ✅", state="complete", expanded=False)

        # Info Contextuelle
        vol_label = "Moyenne"
        if params.beta_volatility > 0.12:
            vol_label = "Élevée (Forte Incertitude)"
        elif params.beta_volatility < 0.08:
            vol_label = "Faible (Stable)"

        st.caption(
            f"📍 Secteur : **{financials.sector}** | Industrie : *{financials.industry}* | "
            f"🎲 Profil de Risque : **{vol_label}**"
        )

        # Affiche les KPIs + Score + Onglets
        display_results(financials, params, dcf_result, mode)

        # Graphiques
        if mode == ValuationMode.MONTE_CARLO and dcf_result.simulation_results:
            display_simulation_chart(dcf_result.simulation_results, financials.current_price, financials.currency)

        display_price_chart(ticker, price_history, hist_iv_df, dcf_result.intrinsic_value_per_share)

        if hist_msgs:
            with st.expander("ℹ️ Notes sur l'historique"):
                for m in hist_msgs: st.info(m)

    except DataProviderError as e:
        status.update(label="Erreur de données", state="error")
        st.error("Impossible de récupérer les données financières.")
        st.caption(f"Détails : {e}")

    except CalculationError as e:
        status.update(label="Erreur de calcul", state="error")
        st.error("Erreur mathématique dans le modèle.")
        st.caption(f"Détails : {e}")

    except Exception as e:
        status.update(label="Erreur critique", state="error")
        st.error("Une erreur inattendue est survenue.")
        st.exception(e)