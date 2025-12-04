import logging
from typing import Sequence
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import altair as alt

from core.models import CompanyFinancials, DCFParameters, ValuationMode
from core.dcf.valuation_service import run_valuation
from core.exceptions import CalculationError, DataProviderError
from infra.data_providers.yahoo_provider import YahooFinanceProvider

# Imports des modules d'UI récemment créés
from app.ui_kpis import display_results
from app.ui_charts import display_price_chart
from app.ui_charts import _get_sample_dates # Utilitaire pour les dates historiques

# Imports pour la VI historique
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from core.dcf.historical_params import YahooMacroHistoricalParamsStrategy
from core.dcf.historical_valuation_service import (
    build_intrinsic_value_time_series,
)

logger = logging.getLogger(__name__)

# Instances déplacées de main.py
PROVIDER = YahooFinanceProvider()
MACRO_PROVIDER = YahooMacroProvider()


def run_workflow_and_display(
        ticker: str,
        projection_years: int,
        mode: ValuationMode,
) -> None:
    """
    Workflow complet :
    - Récupère les données financières
    - Construit les hypothèses DCF
    - Lance le moteur de valorisation (selon le mode)
    - Calcule l'historique de valeur intrinsèque
    - Affiche les résultats et le graphique
    """
    logger.info("=== NOUVELLE DEMANDE DE VALORISATION ===")
    logger.info(
        "Ticker=%s | Années projection=%d | Mode=%s",
        ticker,
        projection_years,
        mode.value,
    )

    status = st.status("Analyse en cours...", expanded=True)

    try:
        # ---------------------------------------------------------
        # 1) Chargement des données + paramètres DCF
        # ---------------------------------------------------------
        status.write(f"📥 Récupération des données financières et hypothèses pour {ticker}...")

        financials, params = PROVIDER.get_company_financials_and_parameters(
            ticker=ticker,
            projection_years=projection_years,
        )

        logger.info("[1] Données récupérées.")

        # --- Warnings de qualité de données (côté provider) ---
        if getattr(financials, "warnings", None):
            for msg in financials.warnings:
                st.warning(f"⚠️ {msg}")

        # ---------------------------------------------------------
        # 2) Exécution du moteur de valorisation (selon le mode)
        # ---------------------------------------------------------
        status.write("🧮 Calcul de la valorisation actuelle...")
        dcf_result = run_valuation(financials, params, mode)
        logger.info("[2] Valorisation terminée.")

        # ---------------------------------------------------------
        # 3) Construction de l'historique de valeur intrinsèque
        # ---------------------------------------------------------
        status.write("📈 Construction de l'historique de valeur intrinsèque...")

        price_history = None
        hist_iv_df = None

        try:
            # a) Historique de prix via le provider
            price_history = PROVIDER.get_price_history(ticker, period="5y")

            # b) Dates d'échantillonnage (tous les 6 mois par défaut)
            sample_dates = _get_sample_dates(
                price_history.reset_index(),  # pour avoir une colonne 'Date'
                freq="6ME",
            )

            if len(sample_dates) == 0:
                logger.warning("[HistIV] Aucune date d'échantillonnage trouvée.")
            else:
                macro_strategy = YahooMacroHistoricalParamsStrategy(
                    macro_provider=MACRO_PROVIDER,
                    currency=financials.currency,
                )

                # Appel à la fonction de construction de la série temporelle de VI
                hist_iv_df, hist_msgs = build_intrinsic_value_time_series(
                    ticker=ticker,
                    financials=financials,
                    base_params=params,
                    mode=mode,
                    provider=PROVIDER,
                    params_strategy=macro_strategy,
                    sample_dates=sample_dates,
                )

                # (optionnel) Afficher les messages d'avertissement / info liés à l'historique
                if hist_msgs:
                    for m in hist_msgs:
                        logger.warning("[HistIV] %s", m)

                logger.info(
                    "[3] Historique de valeur intrinsèque construit (%d points).",
                    0 if hist_iv_df is None else len(hist_iv_df),
                )


        except Exception as e:
            logger.warning(
                "[HistIV] Échec de la construction de l'historique de VI pour %s: %s",
                ticker,
                e,
            )
            st.warning(
                "Impossible de construire l'historique de valeur intrinsèque. "
                "Le graphique affichera uniquement le prix de marché."
            )

        # ---------------------------------------------------------
        # 4) Affichage dans l'interface
        # ---------------------------------------------------------
        status.update(label="Analyse terminée !", state="complete", expanded=False)

        # Affichage des KPIs et des tables d'hypothèses
        display_results(financials, params, dcf_result, mode)

        # Affichage du graphique de prix vs valeur intrinsèque
        display_price_chart(
            ticker=ticker,
            price_history=price_history,
            hist_iv_df=hist_iv_df,
            current_iv=dcf_result.intrinsic_value_per_share,
        )

    except DataProviderError as e:
        status.update(label="Erreur de données", state="error")
        logger.error("[ERREUR] DataProviderError for %s: %s", ticker, e)
        st.error(f"Erreur de données : impossible de récupérer les informations financières nécessaires pour {ticker}.")
        st.caption(f"Détails : {e}")

    except CalculationError as e:
        status.update(label="Erreur de calcul", state="error")
        logger.error("[ERREUR] CalculationError for %s: %s", ticker, e)
        st.error("Erreur de calcul : le modèle de valorisation n'a pas pu être résolu.")
        st.caption(f"Détails : {e}")

    except NotImplementedError as e:
        status.update(label="Méthode non implémentée", state="error")
        logger.warning(
            "[ERREUR] Mode de valorisation %s non encore implémenté pour %s: %s",
            mode.value,
            ticker,
            e,
        )
        st.error("Cette méthode de valorisation n'est pas encore implémentée dans l'application.")
        st.caption("Pour l'instant, seule la Méthode 1 – DCF Simple est entièrement fonctionnelle.")

    except Exception as e:
        status.update(label="Erreur inattendue", state="error")
        logger.exception("[ERREUR] Exception inattendue lors de la valorisation pour %s", ticker)
        st.exception(f"Erreur inattendue : {e}")