"""
app/views/results/pillars/sensitivity.py

PILLAR 4 — SUB-COMPONENT: SENSITIVITY ANALYSIS (HEATMAP)
========================================================
Role: Visualization of the valuation elasticity vs WACC/Growth.
Architecture: Injectable Spoke.
Style: Institutional Heatmap with conditional formatting.
"""

from typing import Any
import pandas as pd
import altair as alt
import streamlit as st

from src.models import ValuationResult
from src.i18n import SharedTexts, KPITexts
from src.core.formatting import format_smart_number
from app.views.results.base_result import ResultTabBase
from app.views.components.ui_kpis import atom_kpi_metric


class SensitivityAnalysisTab(ResultTabBase):
    """
    Rendering component for the 2D Sensitivity Matrix (WACC vs Growth).
    """

    TAB_ID = "sensitivity_analysis"
    LABEL = "Sensibilité"
    ORDER = 4
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible only if sensitivity data is computed."""
        return (result.results.extensions.sensitivity is not None)

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Renders the WACC/Growth heatmap and volatility metrics.
        """
        data = result.results.extensions.sensitivity
        if not data:
            return

        currency = result.financials.currency

        # --- 1. HEADER & SCORE ---
        st.markdown(SharedTexts.SEC_SENSITIVITY)

        # Volatility Score Display
        score = data.sensitivity_score
        score_delta = "Stable" if score < 15 else ("Volatile" if score < 30 else "Critique")
        score_color = "normal" if score < 15 else ("off" if score < 30 else "inverse")

        col_kpi, col_chart = st.columns([1, 3])

        with col_kpi:
            atom_kpi_metric(
                label=SharedTexts.LBL_SENS_SCORE,
                value=f"{score:.1f}",
                delta=score_delta,
                delta_color=score_color,
                help_text=SharedTexts.HELP_SENS_SCORE
            )
            st.info(f"""
            **Axe X :** {SharedTexts.LBL_SENS_X}
            **Axe Y :** {SharedTexts.LBL_SENS_Y}
            """)

        # --- 2. HEATMAP CONSTRUCTION (Altair) ---
        with col_chart:
            # Transformation des données pour Altair (Format Long)
            # data.matrix est une liste de listes [row][col]
            # data.rows = growth steps (Y)
            # data.cols = wacc steps (X)

            heatmap_data = []
            for i, g_val in enumerate(data.rows):
                for j, wacc_val in enumerate(data.cols):
                    val = data.matrix[i][j]
                    heatmap_data.append({
                        "g": f"{g_val:.1%}",
                        "wacc": f"{wacc_val:.1%}",
                        "value": round(val, 2),
                        "label": format_smart_number(val)
                    })

            df = pd.DataFrame(heatmap_data)

            # Base Chart
            base = alt.Chart(df).encode(
                x=alt.X('wacc:O', title=SharedTexts.LBL_SENS_X),
                y=alt.Y('g:O', title=SharedTexts.LBL_SENS_Y)
            )

            # Heatmap Rectangles
            heatmap = base.mark_rect().encode(
                color=alt.Color('value:Q', scale=alt.Scale(scheme='yellowgreenblue'), legend=None),
                tooltip=[
                    alt.Tooltip('wacc', title=SharedTexts.LBL_SENS_X),
                    alt.Tooltip('g', title=SharedTexts.LBL_SENS_Y),
                    alt.Tooltip('label', title='Valorisation')
                ]
            )

            # Text Labels over Rectangles
            text = base.mark_text(baseline='middle').encode(
                text='label:N',
                color=alt.condition(
                    alt.datum.value > df['value'].mean(),
                    alt.value('white'),
                    alt.value('black')
                )
            )

            final_chart = (heatmap + text).properties(
                height=350,
                width='container'
            )

            st.altair_chart(final_chart, use_container_width=True)