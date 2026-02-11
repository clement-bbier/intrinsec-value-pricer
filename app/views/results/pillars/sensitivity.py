"""
app/views/results/pillars/sensitivity.py
PILLAR 4 — SUB-COMPONENT: SENSITIVITY ANALYSIS (HEATMAP)
========================================================
Role: Visualization of the valuation elasticity vs WACC/Growth.
Architecture: Injectable Spoke.
Style: Institutional Heatmap with conditional formatting.
"""

from typing import Any, Literal

import altair as alt
import pandas as pd
import streamlit as st

from app.views.components.ui_kpis import atom_kpi_metric
from src.core.formatting import format_smart_number
from src.i18n import ChartTexts, QuantTexts
from src.models import ValuationResult


class SensitivityAnalysisTab:
    """
    Rendering component for the 2D Sensitivity Matrix (WACC vs Growth).
    Architecture: Stateless Component.
    """

    @staticmethod
    def is_visible(result: ValuationResult) -> bool:
        """Visible only if sensitivity data is computed and available."""
        return (
            result.params.extensions.sensitivity.enabled
            and result.results.extensions.sensitivity is not None
        )

    @staticmethod
    def render(result: ValuationResult, **_kwargs: Any) -> None:
        """
        Renders the WACC/Growth heatmap and volatility metrics.
        Note: **_kwargs is present for signature compatibility but unused.
        """
        data = result.results.extensions.sensitivity
        if not data:
            return

        # --- 1. HEADER & SCORE ---
        st.markdown(f"#### {QuantTexts.SENS_TITLE}")

        # Volatility Score Logic
        score = data.sensitivity_score

        # Explicit typing to satisfy the Linter regarding atom_kpi_metric signature
        score_color: Literal["green", "orange", "red"]
        score_delta: str

        # Interpretation: <15 Stable (Green), <30 Volatile (Orange), >30 Critical (Red)
        if score < 15:
            score_delta = getattr(QuantTexts, 'SENS_STABLE', "Stable")
            score_color = "green"
        elif score < 30:
            score_delta = getattr(QuantTexts, 'SENS_VOLATILE', "Volatile")
            score_color = "orange"
        else:
            score_delta = getattr(QuantTexts, 'SENS_CRITICAL', "Critique")
            score_color = "red"

        col_kpi, col_chart = st.columns([1, 3])

        with col_kpi:
            atom_kpi_metric(
                label=QuantTexts.LBL_SENS_SCORE,
                value=f"{score:.1f}",
                delta=score_delta,
                delta_color=score_color,
                help_text=QuantTexts.HELP_SENS_SCORE
            )

            # Safe access to axis names
            x_name = data.x_axis_name or ChartTexts.AXIS_WACC
            y_name = data.y_axis_name or ChartTexts.AXIS_GROWTH

            st.info(f"""
            **Axe X :** {x_name}
            **Axe Y :** {y_name}
            """)

        # --- 2. HEATMAP CONSTRUCTION (Altair) ---
        with col_chart:
            # Data Transformation: Matrix -> Long Format DataFrame for Altair
            heatmap_data: list[dict[str, Any]] = []

            # data.values is List[List[float]] -> [row][col]
            for i, y_val in enumerate(data.y_values):
                for j, x_val in enumerate(data.x_values):
                    try:
                        val = data.values[i][j]
                        heatmap_data.append({
                            "y_axis": f"{y_val:.2%}", # Growth
                            "x_axis": f"{x_val:.2%}", # WACC
                            "value": val,
                            "label": format_smart_number(val)
                        })
                    except IndexError:
                        continue

            df = pd.DataFrame(heatmap_data)

            if df.empty:
                st.warning(getattr(QuantTexts, 'MSG_SENS_NO_DATA', "Données insuffisantes."))
                return

            # Base Chart
            base = alt.Chart(df).encode(
                x=alt.X('x_axis:O', title=None),
                y=alt.Y('y_axis:O', title=None)
            )

            # Heatmap Rectangles
            heatmap = base.mark_rect().encode(
                color=alt.Color(
                    'value:Q',
                    scale=alt.Scale(scheme='yellowgreenblue'),
                    legend=None
                ),
                tooltip=[
                    alt.Tooltip('x_axis', title=x_name),
                    alt.Tooltip('y_axis', title=y_name),
                    alt.Tooltip('label', title=getattr(ChartTexts, 'TOOLTIP_VALUATION', 'Valorisation'))
                ]
            )

            # Pre-calculate mean for the condition to avoid Type Error in Altair expr
            mean_val = float(df['value'].mean())

            # Text Labels over Rectangles
            text = base.mark_text(baseline='middle', fontSize=10).encode(
                text='label:N',
                color=alt.condition(
                    alt.datum.value > mean_val,  # Clean scalar comparison
                    alt.value('white'),
                    alt.value('black')
                )
            )

            final_chart = (heatmap + text).properties(
                height=350,
                width='container',
                title=alt.TitleParams(
                    text=QuantTexts.SENS_TITLE,
                    subtitle=ChartTexts.CORREL_CAPTION,
                    anchor='start',
                    fontSize=14
                )
            )

            st.altair_chart(final_chart, use_container_width=True)
