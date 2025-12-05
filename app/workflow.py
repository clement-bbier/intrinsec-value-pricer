import logging
from datetime import datetime
from typing import Sequence

import pandas as pd
import streamlit as st

from core.models import ValuationMode
from core.dcf.historical_params import YahooMacroHistoricalParamsStrategy
from core.dcf.historical_valuation_service import (
    build_intrinsic_value_time_series,
)
from core.dcf.valuation_service import run_valuation
from core.exceptions import CalculationError, DataProviderError
from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

# Imports UI
from app.ui_kpis import display_results
from app.ui_charts import display_price_chart, _get_sample_dates

logger = logging.getLogger(__name__)

# Instances globales
PROVIDER = YahooFinanceProvider()
MACRO_PROVIDER = YahooMacroProvider()


def run_workflow_and_display(
    ticker: str,
    projection_years: int,
    mode: ValuationMode,
) -> None:
    """
    Workflow complet :
    - Récupère les données financières et paramètres DCF
    - Lance le moteur de valorisation (selon le mode)
    - Construit l'historique de valeur intrinsèque
    - Affiche les résultats (KPIs + tableau d'hypothèses + méthodo)
    - Affiche le graphique Prix vs Valeur Intrinsèque
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
        # ------------------------------------------------------------------
        # 1) Chargement des données + paramètres DCF
        # ------------------------------------------------------------------
        status.write(
            f"📥 Récupération des données financières et hypothèses pour {ticker}..."
        )

        financials, params = PROVIDER.get_company_financials_and_parameters(
            ticker=ticker,
            projection_years=projection_years,
        )
        logger.info("[1] Données et paramètres DCF récupérés.")

        # Warnings de qualité de données (côté provider → visibles dans l'UI)
        if getattr(financials, "warnings", None):
            for msg in financials.warnings:
                st.warning(f"⚠️ {msg}")

        # ------------------------------------------------------------------
        # 2) Exécution du moteur de valorisation (Méthode 1 ou 2, etc.)
        # ------------------------------------------------------------------
        status.write("🧮 Calcul de la valorisation actuelle...")
        dcf_result = run_valuation(financials, params, mode)
        logger.info("[2] Valorisation actuelle terminée.")

        # ------------------------------------------------------------------
        # 3) Construction de l'historique de valeur intrinsèque
        # ------------------------------------------------------------------
        status.write("📈 Construction de l'historique de valeur intrinsèque...")

        price_history = None
        hist_iv_df = None
        hist_msgs: Sequence[str] = []

        try:
            # a) Historique de prix via le provider (5 ans)
            price_history = PROVIDER.get_price_history(ticker, period="5y")
            if price_history is None or price_history.empty:
                logger.warning(
                    "[HistIV] Historique de prix vide ou indisponible pour %s", ticker
                )
                raise DataProviderError("Historique de prix indisponible.")

            # b) Dates d'échantillonnage (tous les 6 mois par défaut)
            price_history_reset = price_history.reset_index()
            sample_dates = _get_sample_dates(price_history_reset, freq="6ME")

            if len(sample_dates) == 0:
                logger.warning(
                    "[HistIV] Aucune date d'échantillonnage trouvée pour l'historique."
                )
            else:
                macro_strategy = YahooMacroHistoricalParamsStrategy(
                    macro_provider=MACRO_PROVIDER,
                    currency=financials.currency,
                )

                # c) Calcul de la série temporelle de VI (en fonction du mode)
                hist_iv_df, hist_msgs = build_intrinsic_value_time_series(
                    ticker=ticker,
                    financials=financials,
                    base_params=params,
                    mode=mode,
                    provider=PROVIDER,
                    params_strategy=macro_strategy,
                    sample_dates=sample_dates,
                )

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

        # ------------------------------------------------------------------
        # 4) Affichage dans l'interface
        # ------------------------------------------------------------------
        status.update(label="Analyse terminée ✅", state="complete", expanded=False)

        # 4a. KPIs + Hypothèses + Méthodologie
        display_results(financials, params, dcf_result, mode)

        # 4b. Graphique Prix vs Valeur Intrinsèque
        display_price_chart(
            ticker=ticker,
            price_history=price_history,
            hist_iv_df=hist_iv_df,
            current_iv=dcf_result.intrinsic_value_per_share,
        )

        # 4c. Messages historiques éventuels (ΔNWC, FCF TTM, etc.)
        if hist_msgs:
            with st.expander("ℹ️ Détails sur l'historique de valeur intrinsèque"):
                for m in hist_msgs:
                    st.info(m)

    except DataProviderError as e:
        status.update(label="Erreur de données", state="error")
        logger.error("[ERREUR] DataProviderError for %s: %s", ticker, e)
        st.error(
            "Erreur de données : impossible de récupérer les informations financières nécessaires."
        )
        st.caption(f"Détails : {e}")

    except CalculationError as e:
        status.update(label="Erreur de calcul", state="error")
        logger.error("[ERREUR] CalculationError for %s: %s", ticker, e)
        st.error(
            "Erreur de calcul : le modèle de valorisation n'a pas pu être résolu "
            "(FCFF, WACC ou TV incohérents)."
        )
        st.caption(f"Détails : {e}")

    except NotImplementedError as e:
        status.update(label="Méthode non implémentée", state="error")
        logger.warning(
            "[ERREUR] Mode de valorisation %s non encore implémenté pour %s: %s",
            mode.value,
            ticker,
            e,
        )
        st.error(
            "Cette méthode de valorisation n'est pas encore implémentée dans l'application "
            "(par exemple Méthode 3 ou 4)."
        )
        st.caption("Les Méthodes 1 et 2 (DCF Simple et DCF Fondamental) sont disponibles.")

    except Exception as e:
        status.update(label="Erreur inattendue", state="error")
        logger.exception(
            "[ERREUR] Exception inattendue lors de la valorisation pour %s", ticker
        )
        st.exception(f"Erreur inattendue : {e}")
