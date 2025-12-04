from typing import Any

import streamlit as st
import pandas as pd

from core.models import CompanyFinancials, DCFParameters, ValuationMode
from app.ui_methodology import display_simple_dcf_formula


def format_pct(x: float) -> str:
    """Formatte un taux en pourcentage avec 2 décimales."""
    return f"{x * 100:.2f} %"


def format_currency(x: float, currency: str) -> str:
    """Formatte un montant en devise avec 2 décimales et séparateurs de milliers."""
    return f"{x:,.2f} {currency}".replace(",", " ")


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