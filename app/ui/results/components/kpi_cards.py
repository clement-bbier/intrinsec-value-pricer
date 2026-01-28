"""
app/ui/results/components/kpi_cards.py

KPI CARDS ORGANISM — Valuation results display manager.
Role: Orchestrates atomic components to render final financial metrics.
Architecture: Senior Institution Grade (Streamlined).
"""

import streamlit as st
from src.models import ValuationResult
from src.i18n import KPITexts, TooltipsTexts
from src.utilities.formatting import format_smart_number
from app.ui.components.ui_kpis import atom_kpi_metric

def render_valuation_summary_cards(result: ValuationResult):
    """
    Renders the top band of valuation KPIs (four-column layout).
    Displays core model outputs: Discount Rate, Growth, Size, and Upside.
    """
    cols = st.columns(4)

    with cols[0]:
        # Dynamic switch between WACC (Entity approach) and Ke (Equity approach)
        label = KPITexts.WACC_LABEL if result.is_entity_approach else KPITexts.KE_LABEL
        help_t = TooltipsTexts.WACC_HELP if result.is_entity_approach else TooltipsTexts.KE_HELP
        atom_kpi_metric(
            label=label,
            value=format_smart_number(result.discount_rate, is_pct=True),
            help_text=help_t
        )

    with cols[1]:
        # Perpetual Terminal Growth Rate (g)
        atom_kpi_metric(
            label=KPITexts.GROWTH_G_LABEL,
            value=format_smart_number(result.terminal_growth_rate, is_pct=True),
            help_text=TooltipsTexts.GROWTH_G
        )

    with cols[2]:
        # Current Market Capitalization (Reference point)
        atom_kpi_metric(
            label=KPITexts.MARKET_CAP_LABEL,
            value=format_smart_number(result.market_cap, currency=result.currency),
            help_text=TooltipsTexts.MARKET_CAP_HELP
        )

    with cols[3]:
        # Margin of Safety (Upside/Downside) with conditional color logic
        upside = result.upside
        atom_kpi_metric(
            label=KPITexts.MARGIN_SAFETY_LABEL,
            value=format_smart_number(upside, is_pct=True),
            delta=format_smart_number(upside, is_pct=True),
            delta_color="normal" if upside > 0 else "inverse",
            help_text=KPITexts.HELP_MOS
        )

def render_instrument_details(result: ValuationResult):
    """
    Renders granular intrinsic value details (Equity Value & Price Per Share).
    Used in the Executive Summary for the 'Price vs Value' section.
    """
    with st.container(border=True):
        col_equity, col_price = st.columns(2)

        with col_equity:
            # Aggregate Equity Value (Fonds Propres)
            atom_kpi_metric(
                label=KPITexts.EQUITY_VALUE_LABEL,
                value=format_smart_number(result.equity_value, currency=result.currency),
                help_text=KPITexts.HELP_EQUITY_VALUE
            )

        with col_price:
            # Intrinsic Price Per Share (Theoretical Target Price)
            atom_kpi_metric(
                label=KPITexts.INTRINSIC_PRICE_LABEL,
                value=format_smart_number(result.intrinsic_price, currency=result.currency),
                help_text=KPITexts.HELP_IV
            )