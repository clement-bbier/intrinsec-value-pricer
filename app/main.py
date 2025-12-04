import os
import sys
import logging
from pathlib import Path
from typing import Sequence
from datetime import datetime, timedelta

# --- Ensure project root is on sys.path ---
ROOT = Path(__file__).resolve().parents[1]  # repo root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import altair as alt

from core.models import CompanyFinancials, DCFParameters, ValuationMode
from core.dcf.valuation_service import run_valuation
from core.exceptions import CalculationError, DataProviderError
from infra.data_providers.yahoo_provider import YahooFinanceProvider

# imports pour la VI historique
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from core.dcf.historical_params import YahooMacroHistoricalParamsStrategy
from core.dcf.historical_valuation_service import (
    build_intrinsic_value_time_series,
)

# -------------------------------------------------
# Logging configuration
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("app.main")

# Silence yfinance logs
logging.getLogger("yfinance").setLevel(logging.ERROR)

# -------------------------------------------------
# Valuation modes – labels shown to the end-user
# -------------------------------------------------
MODE_LABELS = {
    ValuationMode.SIMPLE_FCFF: (
        "Méthode 1 – DCF Simple "
        "(Valeur d'entreprise basée sur le FCFF et le CAPEX)"
    ),
    ValuationMode.FUNDAMENTAL_FCFF: (
        "Méthode 2 – DCF Détaillé "
        "(FCFF construit à partir du compte de résultat, bilan et tableau des flux)"
    ),
    ValuationMode.MARKET_MULTIPLES: (
        "Méthode 3 – Comparables de Marché "
        "(valorisation par multiples: P/E, EV/EBITDA, etc.)"
    ),
    ValuationMode.ADVANCED_SIMULATION: (
        "Méthode 4 – Scénarios et Simulations "
        "(tests de stress, Monte Carlo, modèles LBO)"
    ),
}
LABEL_TO_MODE = {v: k for k, v in MODE_LABELS.items()}

# -------------------------------------------------
# Global config
# -------------------------------------------------
DEFAULT_PROJECTION_YEARS = 5
PROVIDER = YahooFinanceProvider()
MACRO_PROVIDER = YahooMacroProvider()


# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def format_pct(x: float) -> str:
    """Formatte un taux en pourcentage avec 2 décimales."""
    return f"{x * 100:.2f} %"


def format_currency(x: float, currency: str) -> str:
    """Formatte un montant en devise avec 2 décimales et séparateurs de milliers."""
    return f"{x:,.2f} {currency}".replace(",", " ")


# -------------------------------------------------
# Core workflow
# -------------------------------------------------
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


# -------------------------------------------------
# Display functions
# -------------------------------------------------
def display_results(
        financials: CompanyFinancials,
        params: DCFParameters,
        result,
        mode: ValuationMode,
) -> None:
    """Affiche les KPIs, les hypothèses du modèle et la méthodologie."""
    st.subheader(f"Valorisation Intrinsèque – {financials.ticker}")

    # --- KPIs principaux ---
    col_price, col_iv, col_delta, col_wacc = st.columns(4)

    market_price = financials.current_price
    intrinsic_value = result.intrinsic_value_per_share
    currency = financials.currency

    delta_abs = intrinsic_value - market_price
    delta_pct = (delta_abs / market_price) * 100 if market_price > 0 else 0.0

    with col_price:
        st.metric(
            label=f"Prix Actuel ({currency})",
            value=format_currency(market_price, currency),
        )

    with col_iv:
        st.metric(
            label=f"Valeur Intrinsèque ({currency})",
            value=format_currency(intrinsic_value, currency),
            delta=f"{delta_abs:,.2f} {currency}".replace(",", " "),
        )

    with col_delta:
        delta_prefix = "Sous-évalué" if delta_abs > 0 else "Surévalué"
        st.metric(
            label="Potentiel",
            value=delta_prefix,
            delta=f"{delta_pct:.2f}%",
            delta_color="normal" if delta_abs > 0 else "inverse",
        )

    with col_wacc:
        st.metric(
            label="CMPC (WACC)",
            value=format_pct(result.wacc),
        )

    st.markdown("---")

    # --- Onglets Détails ---
    tab1, tab2 = st.tabs(["📋 Hypothèses Détaillées", "🧮 Méthodologie"])

    with tab1:
        # --- Hypothèses détaillées et aperçu du bilan ---
        c1, c2, c3 = st.columns(3)

        # Inputs de marché et risque
        with c1:
            st.caption("Inputs de marché et risque")
            df_market = pd.DataFrame(
                {
                    "Paramètre": [
                        "Taux sans risque (Rf)",
                        "Prime de risque du marché (MRP)",
                        "Coût de la dette (Rd)",
                        "Taux d'imposition",
                        "CMPC (WACC)",
                    ],
                    "Valeur": [
                        format_pct(params.risk_free_rate),
                        format_pct(params.market_risk_premium),
                        format_pct(params.cost_of_debt),
                        format_pct(params.tax_rate),
                        format_pct(result.wacc),
                    ],
                }
            )
            df_market.index = [""] * len(df_market)
            st.table(df_market)

        # Hypothèses de croissance DCF
        with c2:
            st.caption("Hypothèses de croissance DCF")
            df_growth = pd.DataFrame(
                {
                    "Paramètre": [
                        "Dernier FCFF (TTM)",
                        "Croissance FCFF (phase 1)",
                        "Croissance perpétuelle (g∞)",
                        "Années de projection",
                    ],
                    "Valeur": [
                        format_currency(financials.fcf_last, currency),
                        format_pct(params.fcf_growth_rate),
                        format_pct(params.perpetual_growth_rate),
                        f"{params.projection_years} ans",
                    ],
                }
            )
            df_growth.index = [""] * len(df_growth)
            st.table(df_growth)

        # Aperçu du bilan
        with c3:
            st.caption("Aperçu du bilan (en millions)")

            def to_m(v: float) -> str:
                return f"{v / 1e6:,.2f} M".replace(",", " ")

            df_bs = pd.DataFrame(
                {
                    "Paramètre": [
                        "Actions en circulation",
                        "Dette Totale",
                        "Liquidités et équivalents",
                    ],
                    "Valeur": [
                        to_m(financials.shares_outstanding),
                        to_m(financials.total_debt),
                        to_m(financials.cash_and_equivalents),
                    ],
                }
            )
            df_bs.index = [""] * len(df_bs)
            st.table(df_bs)

    with tab2:
        # --- Section de la formule de valorisation ---
        if mode == ValuationMode.SIMPLE_FCFF:
            display_simple_dcf_formula()
        else:
            st.warning("La méthodologie détaillée pour cette méthode n'est pas encore disponible.")


def display_simple_dcf_formula() -> None:
    """
    Affiche la formule symbolique utilisée dans la Méthode 1 – DCF Simple.
    """
    st.markdown("### Formule de Valorisation – Méthode 1 (DCF Simple)")

    st.markdown("#### Étape 1 – Projection du Free Cash Flow to the Firm (FCFF)")
    st.latex(r"FCFF_0 = \text{Dernier FCFF (TTM)}")
    st.latex(
        r"FCFF_t = FCFF_{t-1} \times (1 + g_{\text{FCFF}})"
        r"\quad\text{pour } t = 1,\dots,n"
    )
    st.markdown(
        "- `Dernier FCFF` provient du flux de trésorerie d'exploitation moins le CAPEX.\n"
        "- $g_{\\text{FCFF}}$ correspond à la **Croissance FCFF (phase 1)**.\n"
        "- $n$ correspond aux **Années de projection**."
    )

    st.markdown("#### Étape 2 – Actualisation et calcul de la Valeur Terminale (TV)")
    st.latex(
        r"VE = \sum_{t=1}^{n} \frac{FCFF_t}{(1 + CMPC)^t}"
        r" + \frac{VT}{(1 + CMPC)^n}"
    )
    st.latex(
        r"VT = \frac{FCFF_{n+1}}{CMPC - g_{\infty}}"
        r"\quad\text{avec}\quad FCFF_{n+1} = FCFF_n \times (1 + g_{\infty})"
    )
    st.markdown(
        "- `CMPC` (Coût Moyen Pondéré du Capital) est calculé à partir du **Taux sans risque (Rf)**, "
        "la **Prime de risque du marché (MRP)**, le **Coût de la dette (Rd)** et le **Taux d'imposition**.\n"
        "- $g_{\\infty}$ correspond à la **Croissance perpétuelle**."
    )

    st.markdown("#### Étape 3 – De la Valeur d'Entreprise (VE) à la Valeur des Capitaux Propres")
    st.latex(
        r"\text{Valeur Capitaux Propres} = VE - \text{Dette Totale} + \text{Liquidités et équivalents}"
    )

    st.markdown("#### Étape 4 – Valeur Intrinsèque par Action")
    st.latex(
        r"\text{VI par action} = "
        r"\frac{\text{Valeur Capitaux Propres}}{\text{Actions en circulation}}"
    )
    st.caption(
        "La Valeur Intrinsèque utilisée dans la section KPI est le résultat de ces étapes "
        "appliquées aux paramètres affichés dans les tables ci-dessus."
    )


# -------------------------------------------------
# Utilitaire pour définir les dates d'échantillonnage
# -------------------------------------------------
def _get_sample_dates(df_price: pd.DataFrame, freq: str = "6ME") -> Sequence[datetime]:
    """
    Fonction utilitaire pour définir les dates auxquelles nous recalculons la valeur
    intrinsèque historique (par défaut : tous les 6 mois, basés sur les données de prix).
    """
    tmp = (
        df_price.set_index("Date")
        .resample(freq)
        .first()
        .dropna()
    )
    # Convertit l'index de Timestamp en datetime pour la fonction build_intrinsic_value_time_series
    return [dt.to_pydatetime() for dt in tmp.index]


# -------------------------------------------------
# Graphique Prix vs Valeur Intrinsèque
# -------------------------------------------------
def display_price_chart(
    ticker: str,
    price_history: pd.DataFrame | None,
    hist_iv_df: pd.DataFrame | None,
    current_iv: float | None = None,
) -> None:
    """
    Affiche le graphique prix de marché vs valeur intrinsèque historique.

    Parameters
    ----------
    ticker : str
        Ticker de l'action.
    price_history : pd.DataFrame | None
        Historique des prix, index = dates, colonnes incluant 'Close' ou 'Adj Close'.
    hist_iv_df : pd.DataFrame | None
        Historique des valorisations DCF avec au minimum :
        - une colonne date (ex: 'valuation_date' ou 'date')
        - une colonne IV par action (ex: 'intrinsic_value_per_share' ou 'iv_per_share').
    current_iv : float | None
        Valeur intrinsèque actuelle (pour éventuellement tracer une ligne horizontale).
    """

    if price_history is None or price_history.empty:
        st.warning("Impossible de charger l'historique des prix pour afficher le graphique.")
        return

    # 1) Normaliser l'historique de prix → colonne 'Date' + 'Market Price'
    df_price = price_history.copy()

    # Si les dates sont en index, on les remet en colonne
    if df_price.index.name is not None or not isinstance(df_price.index, pd.RangeIndex):
        df_price = df_price.reset_index()

    # Harmoniser le nom de la colonne de date
    if "Date" not in df_price.columns:
        datetime_cols = [c for c in df_price.columns if "date" in c.lower()]
        if datetime_cols:
            df_price = df_price.rename(columns={datetime_cols[0]: "Date"})
        else:
            df_price = df_price.rename(columns={df_price.columns[0]: "Date"})

    # Choisir la colonne prix (Close ou Adj Close)
    price_col = None
    for candidate in ["Close", "Adj Close", "close", "adjclose"]:
        if candidate in df_price.columns:
            price_col = candidate
            break

    if price_col is None:
        st.warning(
            "Impossible de trouver une colonne de prix ('Close' ou 'Adj Close') "
            "dans l'historique des prix. Graphique non affiché."
        )
        return

    df_price = df_price[["Date", price_col]].rename(columns={price_col: "Market Price"})

    # 2) Normaliser l'historique d'IV → colonne 'Date' + 'Intrinsic Value'
    if hist_iv_df is None or hist_iv_df.empty:
        # Si pas d'historique IV, on affiche au moins le prix
        df_plot = df_price.copy()
        df_plot["Intrinsic Value"] = None
    else:
        df_iv = hist_iv_df.copy()

        # Trouver la colonne date
        date_col_candidates = [
            c
            for c in df_iv.columns
            if c.lower() in ("date", "valuation_date", "as_of_date", "valuation_dt")
        ]
        if not date_col_candidates:
            datetime_cols = [
                c for c in df_iv.columns if pd.api.types.is_datetime64_any_dtype(df_iv[c])
            ]
            if datetime_cols:
                date_col = datetime_cols[0]
            else:
                date_col = df_iv.columns[0]
        else:
            date_col = date_col_candidates[0]

        # Trouver la colonne IV
        iv_col_candidates = [
            c
            for c in df_iv.columns
            if any(
                k in c.lower()
                for k in ("iv_per_share", "intrinsic_value", "intrinsic_value_per_share")
            )
        ]
        if not iv_col_candidates:
            num_cols = [
                c
                for c in df_iv.columns
                if pd.api.types.is_numeric_dtype(df_iv[c]) and c != date_col
            ]
            if num_cols:
                iv_col = num_cols[0]
            else:
                iv_col = None
        else:
            iv_col = iv_col_candidates[0]

        if iv_col is None:
            st.warning(
                "Impossible de trouver une colonne de valeur intrinsèque dans l'historique IV. "
                "Graphique marché vs IV désactivé."
            )
            df_plot = df_price.copy()
            df_plot["Intrinsic Value"] = None
        else:
            df_iv = df_iv[[date_col, iv_col]].rename(
                columns={date_col: "Date", iv_col: "Intrinsic Value"}
            )

            # Merge prix + IV sur la date
            df_merged = pd.merge(df_price, df_iv, on="Date", how="left")
            df_plot = df_merged

    # 4) Ajouter éventuellement un point/ligne pour la valeur intrinsèque actuelle
    if current_iv is not None:
        df_plot["Current IV"] = current_iv
    else:
        if "Current IV" in df_plot.columns:
            df_plot.drop(columns=["Current IV"], inplace=True)

    # 5) Reshape en format long pour Altair
    value_cols = [c for c in ["Market Price", "Intrinsic Value", "Current IV"] if c in df_plot.columns]

    if "Date" not in df_plot.columns or len(value_cols) == 0:
        st.warning(
            "Données insuffisantes pour tracer le graphique marché vs valeur intrinsèque."
        )
        return

    df_long = df_plot.melt(
        id_vars="Date",
        value_vars=value_cols,
        var_name="Series",
        value_name="Price",
    )

    # Filtrer les NaN
    df_long = df_long.dropna(subset=["Price"])

    if df_long.empty:
        st.warning("Aucune donnée exploitable pour le graphique.")
        return

    # 6) Graphique Altair
    chart = (
        alt.Chart(df_long)
        .mark_line()
        .encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Price:Q", title="Price per share"),
            color=alt.Color("Series:N", title="Série"),
            tooltip=["Date:T", "Series:N", "Price:Q"],
        )
        .properties(
            title=f"Historique du prix de marché vs valeur intrinsèque estimée - {ticker}",
            height=400,
        )
        .interactive()
    )

    st.altair_chart(chart, width="stretch")

# -------------------------------------------------
# Streamlit main
# -------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="Calculateur de Valeur Intrinsèque (DCF)",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🔎 Calculateur de Valeur Intrinsèque (DCF)")

    # Inputs de la barre latérale
    st.sidebar.header("Paramètres")

    ticker = (
        st.sidebar.text_input(
            "Symbole Boursier (Ticker)",
            value="AAPL",
            help="Exemple: AAPL, MSFT, TSLA",
        )
        .upper()
        .strip()
    )

    projection_years = st.sidebar.number_input(
        "Années de projection (n)",
        min_value=3,
        max_value=10,
        value=DEFAULT_PROJECTION_YEARS,
        step=1,
        help="Horizon de projection du DCF (en années).",
    )

    # Selectbox du mode de valorisation
    mode_label = st.sidebar.selectbox(
        "Méthode de valorisation",
        options=list(MODE_LABELS.values()),
        index=0,
        help="Choisissez la méthode utilisée pour calculer la valeur intrinsèque.",
    )
    mode = LABEL_TO_MODE[mode_label]
    logger.info("Mode de valorisation sélectionné dans l'interface : %s", mode.value)

    st.sidebar.markdown("---")
    run_button = st.sidebar.button("Lancer le Calcul", type="primary")

    if run_button:
        if not ticker:
            st.error("Veuillez entrer un symbole boursier (Ticker).")
        else:
            run_workflow_and_display(ticker, int(projection_years), mode)
    else:
        st.info(
            "Entrez un ticker et un horizon de projection à gauche, "
            "puis cliquez sur Lancer le Calcul."
        )


if __name__ == "__main__":
    main()
