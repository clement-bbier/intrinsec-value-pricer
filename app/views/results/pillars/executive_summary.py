"""
app/views/results/pillars/executive_summary.py
PILLAR 0: EXECUTIVE SUMMARY (DASHBOARD)
=======================================
Role: Renders the top-level decision dashboard.
Focus: Output only (Price, Safety Margin, WACC, Upside, Football Field).
Dependencies: Streamlit, Models, UI Components.
"""

from typing import Literal
import streamlit as st
from src.models import ValuationResult
from src.i18n import KPITexts, ResultsTexts
from app.views.components.ui_kpis import atom_kpi_metric
from app.views.components.ui_charts import display_football_field


def render_dashboard(result: ValuationResult) -> None:
    """
    Renders the Pillar 0: Executive Dashboard.

    Displays the top-level KPIs (Intrinsic Value, MOS, WACC, Upside) and
    the main visualization (Football Field).

    Parameters
    ----------
    result : ValuationResult
        The object containing calculation results and request parameters.
    """
    st.header(ResultsTexts.VALUATION_SUMMARY)

    # --- 1. Top Level KPIs (The "Decision Row") ---
    c1, c2, c3, c4 = st.columns(4)

    # Intrinsic Price
    with c1:
        atom_kpi_metric(
            label=KPITexts.INTRINSIC_PRICE_LABEL,
            value=f"{result.results.common.intrinsic_value_per_share:,.2f} {result.request.parameters.structure.currency}",
            delta=None,
            help_text=KPITexts.HELP_IV
        )

    # Margin of Safety
    with c2:
        mos = result.results.common.margin_of_safety

        # Correction de type : On force le type Literal pour satisfaire le checker
        color: Literal["green", "orange", "red"] = (
            "green" if mos > 0.3 else "orange" if mos > 0 else "red"
        )

        atom_kpi_metric(
            label=KPITexts.MARGIN_SAFETY_LABEL,
            value=f"{mos:.1%}",
            delta_color=color,
            help_text=KPITexts.HELP_MOS
        )

    # WACC
    with c3:
        wacc = result.results.dcf.wacc if result.results.dcf else 0.0
        atom_kpi_metric(
            label=KPITexts.WACC_LABEL,
            value=f"{wacc:.2%}",
            help_text=KPITexts.HELP_WACC
        )

    # Upside Potential
    with c4:
        current_price = result.request.parameters.structure.current_price
        intrinsic = result.results.common.intrinsic_value_per_share

        # Guard against division by zero
        if current_price and current_price > 0:
            upside = (intrinsic / current_price) - 1
        else:
            upside = 0.0

        atom_kpi_metric(
            label=KPITexts.UPSIDE_LABEL,
            value=f"{upside:+.1%}",
            delta=f"{upside:+.1%}",
            delta_color="normal"
        )

    st.divider()

    # --- 2. Football Field Visualization ---
    st.subheader(KPITexts.FOOTBALL_FIELD_TITLE)
    st.caption(KPITexts.RELATIVE_VAL_DESC)
    display_football_field(result)