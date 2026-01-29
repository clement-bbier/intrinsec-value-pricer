"""
app/ui/results/optional/monte_carlo_distribution.py

PILLAR 4 — SUB-COMPONENT: MONTE CARLO DISTRIBUTION (Versatile)
==============================================================
Role: Visualization of stochastic dispersion and Value at Risk (VaR) metrics.
Architecture: Statistical Risk Hub (Grade-A compliance).
"""

from typing import Any, Dict, Optional
import streamlit as st

from src.models import ValuationResult
from src.i18n import QuantTexts, KPITexts, AuditTexts
from src.utilities.formatting import format_smart_number
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_charts import display_simulation_chart

class MonteCarloDistributionTab(ResultTabBase):
    """
    Rendering component for Monte Carlo simulation results.
    Can be integrated as a standalone tab or a vertical section in Risk Engineering.
    """

    TAB_ID = "monte_carlo"
    LABEL = KPITexts.TAB_MC
    ORDER = 4
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible only if the simulation array is populated."""
        return bool(result.simulation_results and len(result.simulation_results) > 0)

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Institutional rendering of the Monte Carlo Risk Hub."""

        stats: Optional[Dict[str, Any]] = kwargs.get("mc_stats")
        currency = result.financials.currency

        # --- SECTION HEADER (Standardized ####) ---
        st.markdown(f"#### {QuantTexts.MC_TITLE}")

        # Dynamic configuration summary from i18n
        config_sub = QuantTexts.MC_CONFIG_SUB.format(
            sims=len(result.simulation_results),
            sig_b=result.params.monte_carlo.beta_volatility,
            sig_g=result.params.monte_carlo.growth_volatility,
            rho=result.params.monte_carlo.correlation_beta_growth
        )
        st.caption(config_sub)
        st.write("")

        # 1. RISK HUB (Dispersion & Tail Risk)

        if stats:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns(4)

                # Center of the distribution
                c1.metric(QuantTexts.MC_MEDIAN, format_smart_number(stats["median"], currency=currency))

                # Potential loss at 95% confidence (VaR)
                c2.metric(QuantTexts.MC_VAR, format_smart_number(stats["var_95"], currency=currency), help=KPITexts.HELP_VAR)

                # Standard Deviation (Volatility)
                c3.metric(QuantTexts.MC_VOLATILITY, format_smart_number(stats["std"], currency=currency))

                # Coefficient of Variation (Relative Risk)
                cv = stats["std"] / stats["median"] if stats["median"] != 0 else 0
                c4.metric(QuantTexts.MC_TAIL_RISK, f"{cv:.1%}")

        # 2. PROBABILITY DENSITY CHART (Altair / Plotly)
        st.write("")
        display_simulation_chart(
            ticker=result.financials.ticker,
            simulation_results=result.simulation_results,
            market_price=result.market_price,
            currency=currency
        )

        # 3. PROBABILITY ANALYSIS (Market Price Over/Under Performance)
        st.write("")
        with st.container(border=True):
            st.markdown(f"**{QuantTexts.MC_PROB_ANALYSIS.upper()}**")

            sim_array = [v for v in result.simulation_results if v is not None]
            if sim_array:
                # Probability of being 'In the Money' (Value > Price)
                prob_above = sum(1 for v in sim_array if v > result.market_price) / len(sim_array)
                p_col1, p_col2 = st.columns(2)

                # Undervaluation Verdict
                p_col1.metric(
                    label=AuditTexts.H_VERDICT,
                    value=f"{prob_above:.1%}",
                    delta=QuantTexts.MC_PROB_UNDERVALUATION if prob_above > 0.5 else QuantTexts.MC_DOWNSIDE,
                    delta_color="normal" if prob_above > 0.5 else "inverse"
                )

                # 80% Confidence Interval (P10 - P90)
                if stats:
                    range_str = f"{format_smart_number(stats['p10'])} — {format_smart_number(stats['p90'])}"
                    p_col2.metric(
                        label=QuantTexts.MC_FILTER_SUB.format(valid=len(sim_array), total=len(sim_array)),
                        value=range_str
                    )

    def get_display_label(self) -> str:
        """Returns the localized tab label."""
        return self.LABEL