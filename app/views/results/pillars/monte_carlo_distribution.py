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
        """Visible only if the simulation was enabled and results exist."""
        mc_config = result.request.parameters.extensions.monte_carlo
        mc_results = result.results.extensions.monte_carlo
        return mc_config.enabled and mc_results is not None

    @staticmethod
    def render(result: ValuationResult, **_kwargs: Any) -> None:
        """Institutional rendering of the Monte Carlo Risk Hub."""
        mc_data = result.results.extensions.monte_carlo
        if not mc_data:
            st.info(QuantTexts.MC_FAILED)
            return

        currency = result.request.parameters.structure.currency
        mc_params = result.request.parameters.extensions.monte_carlo
        market_price = result.request.parameters.structure.current_price

        # --- SECTION HEADER ---
        st.markdown(f"#### {QuantTexts.MC_TITLE}")

        # Dynamic configuration summary from i18n
        shocks = mc_params.shocks
        # beta_volatility is only available on BetaModelMCShocksParameters (not Graham)
        if shocks is not None:
            raw_beta_vol = getattr(shocks, 'beta_volatility', None)
            sig_b = raw_beta_vol if raw_beta_vol is not None else 0.10
            sig_g = shocks.growth_volatility if shocks.growth_volatility is not None else 0.015
        else:
            sig_b = 0.10
            sig_g = 0.015

        config_sub = QuantTexts.MC_CONFIG_SUB.format(
            sims=mc_params.iterations,
            sig_b=sig_b,
            sig_g=sig_g,
            rho=0.0
        )
        st.caption(config_sub)
        st.write("")

        # Build stats from MCResults
        median_val = mc_data.quantiles.get("P50", mc_data.mean)
        var_95 = mc_data.quantiles.get("P5", 0.0)
        p10 = mc_data.quantiles.get("P10", 0.0)
        p90 = mc_data.quantiles.get("P90", 0.0)

        # 1. RISK HUB (Dispersion & Tail Risk)
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                QuantTexts.MC_MEDIAN,
                format_smart_number(median_val, currency=currency)
            )

            c2.metric(
                QuantTexts.MC_VAR,
                format_smart_number(var_95, currency=currency),
                help=QuantTexts.MC_VAR
            )

            c3.metric(
                QuantTexts.MC_VOLATILITY,
                format_smart_number(mc_data.std_dev, currency=currency)
            )

            cv = mc_data.std_dev / median_val if median_val != 0 else 0
            c4.metric(QuantTexts.MC_TAIL_RISK, f"{cv:.1%}")

        # 2. PROBABILITY DENSITY CHART (Altair)
        st.write("")
        display_simulation_chart(
            simulation_results=mc_data.simulation_values,
            currency=currency
        )

        # 3. PROBABILITY ANALYSIS
        st.write("")
        with st.container(border=True):
            st.markdown(f"**{QuantTexts.MC_PROB_ANALYSIS.upper()}**")

            sim_array = mc_data.simulation_values

            if sim_array:
                ref_price = market_price if market_price else 0.0

                # Probability of Value > Price
                prob_above = sum(1 for v in sim_array if v > ref_price) / len(sim_array)

                p_col1, p_col2 = st.columns(2)

                # Verdict Logic
                is_undervalued = prob_above > 0.5
                delta_txt = QuantTexts.MC_PROB_UNDERVALUATION if is_undervalued else QuantTexts.MC_DOWNSIDE

                p_col1.metric(
                    label=QuantTexts.MC_PROB_UNDERVALUATION,
                    value=f"{prob_above:.1%}",
                    delta=delta_txt,
                    delta_color="normal" if is_undervalued else "inverse"
                )

                # 80% Confidence Interval
                range_str = (
                    f"{format_smart_number(p10)}"
                    f" — {format_smart_number(p90)}"
                )
                p_col2.metric(
                    label=QuantTexts.MC_FILTER_SUB.format(valid=len(sim_array), total=len(sim_array)),
                    value=range_str,
                    help=QuantTexts.CONFIDENCE_INTERVAL
                )
