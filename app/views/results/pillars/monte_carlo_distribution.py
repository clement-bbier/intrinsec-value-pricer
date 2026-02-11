"""
app/views/results/pillars/monte_carlo_distribution.py
PILLAR 4 — SUB-COMPONENT: MONTE CARLO DISTRIBUTION (Versatile)
==============================================================
Role: Visualization of stochastic dispersion and Value at Risk (VaR) metrics.
Architecture: Statistical Risk Hub (Grade-A compliance).
"""

from typing import Any

import streamlit as st

from app.views.components.ui_charts import display_simulation_chart
from src.core.formatting import format_smart_number
from src.i18n import QuantTexts
from src.models import ValuationResult


class MonteCarloDistributionTab:
    """
    Rendering component for Monte Carlo simulation results.
    Can be integrated as a standalone tab or a vertical section in Risk Engineering.
    Architecture: Stateless Component.
    """

    @staticmethod
    def is_visible(result: ValuationResult) -> bool:
        """Visible only if the simulation array is populated and enabled."""
        if not result.params.extensions or not result.params.extensions.monte_carlo:
            return False
        return result.params.extensions.monte_carlo.enabled

    @staticmethod
    def render(result: ValuationResult, **kwargs: Any) -> None:
        """Institutional rendering of the Monte Carlo Risk Hub."""

        stats: dict[str, Any] | None = kwargs.get("mc_stats")
        currency = result.financials.currency
        mc_params = result.params.extensions.monte_carlo

        # --- SECTION HEADER ---
        st.markdown(f"#### {QuantTexts.MC_TITLE}")

        # Dynamic configuration summary from i18n
        shocks = mc_params.shocks
        sig_b = shocks.beta_volatility if shocks else 0.10
        sig_g = shocks.growth_volatility if shocks else 0.015

        config_sub = QuantTexts.MC_CONFIG_SUB.format(
            sims=mc_params.iterations,
            sig_b=sig_b,
            sig_g=sig_g,
            rho=0.0  # Default or retrieved if available
        )
        st.caption(config_sub)
        st.write("")

        # 1. RISK HUB (Dispersion & Tail Risk)
        if stats:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    QuantTexts.MC_MEDIAN,
                    format_smart_number(stats.get("median", 0), currency=currency)
                )

                c2.metric(
                    QuantTexts.MC_VAR,
                    format_smart_number(stats.get("var_95", 0), currency=currency),
                    help=QuantTexts.MC_VAR
                )

                c3.metric(
                    QuantTexts.MC_VOLATILITY,
                    format_smart_number(stats.get("std", 0), currency=currency)
                )

                median = stats.get("median", 1)
                std_dev = stats.get("std", 0)
                cv = std_dev / median if median != 0 else 0

                c4.metric(QuantTexts.MC_TAIL_RISK, f"{cv:.1%}")

        # 2. PROBABILITY DENSITY CHART (Altair)
        st.write("")
        display_simulation_chart(
            ticker=result.request.ticker,
            simulation_results=result.simulation_results,
            market_price=result.market_price,
            currency=currency
        )

        # 3. PROBABILITY ANALYSIS
        st.write("")
        with st.container(border=True):
            st.markdown(f"**{QuantTexts.MC_PROB_ANALYSIS.upper()}**")

            sim_array = [v for v in result.simulation_results if v is not None]

            if sim_array:
                ref_price = result.market_price if result.market_price else 0.0

                # Probability of Value > Price
                prob_above = sum(1 for v in sim_array if v > ref_price) / len(sim_array)

                p_col1, p_col2 = st.columns(2)

                # Verdict Logic
                is_undervalued = prob_above > 0.5
                delta_txt = QuantTexts.MC_PROB_UNDERVALUATION if is_undervalued else QuantTexts.MC_DOWNSIDE

                # "Normal" = Green if positive delta, Red if negative.
                # "Inverse" = Red if positive delta, Green if negative.
                # Here we want Green if Undervalued (High Probability) -> Normal logic fits if we treat prob as score

                p_col1.metric(
                    label=QuantTexts.MC_PROB_UNDERVALUATION,
                    value=f"{prob_above:.1%}",
                    delta=delta_txt,
                    delta_color="normal" if is_undervalued else "inverse"
                )

                # 80% Confidence Interval
                if stats:
                    range_str = f"{format_smart_number(stats.get('p10', 0))} — {format_smart_number(stats.get('p90', 0))}"
                    p_col2.metric(
                        label=QuantTexts.MC_FILTER_SUB.format(valid=len(sim_array), total=len(sim_array)),
                        value=range_str,
                        help=QuantTexts.CONFIDENCE_INTERVAL
                    )
