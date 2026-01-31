"""
app/ui/results/optional/scenario_analysis.py

PILLAR 4 — SUB-COMPONENT: DETERMINISTIC SCENARIO ANALYSIS
=========================================================
Role: Bull/Base/Bear comparison and mathematical expectation calculation.
Architecture: Injectable Grade-A component.
"""

from typing import Any
import streamlit as st
import pandas as pd

from src.models import ValuationResult
from src.i18n import QuantTexts, KPITexts
from src.utilities.formatting import format_smart_number
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_kpis import atom_kpi_metric

class ScenarioAnalysisTab(ResultTabBase):
    """
    Rendering component for multi-scenario analysis.
    Typically integrated vertically within the RiskEngineering tab.
    """

    TAB_ID = "scenario_analysis"
    LABEL = KPITexts.TAB_SCENARIOS
    ORDER = 4
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible only if the scenario engine generated variants."""
        return result.params.scenarios.enabled

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Renders the scenario synthesis with comparative table and weighted expectation.
        """
        synthesis = result.scenario_synthesis
        currency = result.financials.currency
        market_price = result.market_price

        # --- SECTION HEADER (Standardized ####) ---
        st.markdown(f"#### {QuantTexts.SCENARIO_TITLE}")
        st.caption(KPITexts.LABEL_SCENARIO_RANGE)
        st.write("")

        # --- 1. COMPARATIVE TABLE (DETAILED VIEW) ---

        with st.container(border=True):
            data = []
            for variant in synthesis.variants:
                # Calculate scenario-specific upside/downside
                upside = (variant.intrinsic_value / market_price - 1) if market_price > 0 else 0

                data.append({
                    QuantTexts.COL_SCENARIO: variant.label.upper(),
                    QuantTexts.COL_PROBABILITY: variant.probability,
                    QuantTexts.COL_GROWTH: variant.growth_used,
                    QuantTexts.COL_MARGIN_FCF: variant.margin_used if variant.margin_used else 0.0,
                    QuantTexts.COL_VALUE_PER_SHARE: variant.intrinsic_value,
                    QuantTexts.COL_UPSIDE: upside
                })

            df = pd.DataFrame(data)

            # Institutional Column Configuration
            column_config = {
                QuantTexts.COL_PROBABILITY: st.column_config.NumberColumn(format="%.0f%%"),
                QuantTexts.COL_GROWTH: st.column_config.NumberColumn(format="%.2f%%"),
                QuantTexts.COL_MARGIN_FCF: st.column_config.NumberColumn(format="%.2f%%"),
                QuantTexts.COL_VALUE_PER_SHARE: st.column_config.NumberColumn(format=f"%.2f {currency}"),
                QuantTexts.COL_UPSIDE: st.column_config.ProgressColumn(
                    label=QuantTexts.COL_UPSIDE,
                    format="%.1%+",
                    min_value=-1.0,
                    max_value=1.0,
                    color="blue"
                )
            }

            st.dataframe(
                df,
                hide_index=True,
                column_config=column_config,
                width="stretch"
            )

        # --- 2. WEIGHTED SYNTHESIS (EXPECTED VALUE HUB) ---
        expected_val = synthesis.expected_value
        if expected_val > 0:
            st.write("")
            with st.container(border=True):
                col_val, col_upside = st.columns(2)

                with col_val:
                    # Mathematical expectation of the intrinsic value
                    atom_kpi_metric(
                        label=QuantTexts.METRIC_WEIGHTED_VALUE,
                        value=format_smart_number(expected_val, currency=currency),
                        help_text=KPITexts.HELP_IV
                    )

                with col_upside:
                    # Weighted Potential (Expected Upside)
                    weighted_upside = (expected_val / market_price - 1) if market_price > 0 else 0
                    atom_kpi_metric(
                        label=QuantTexts.METRIC_WEIGHTED_UPSIDE,
                        value=f"{weighted_upside:+.1%}",
                        delta=f"{weighted_upside:+.1%}",
                        delta_color="normal" if weighted_upside > 0 else "inverse",
                        help_text=KPITexts.HELP_MOS
                    )

    def get_display_label(self) -> str:
        """Returns the localized tab label from i18n."""
        return self.LABEL