"""
app/views/results/pillars/inputs_summary.py
PILLAR 1: DETAILED INPUTS & CONFIGURATION
=========================================
Role: Renders the detailed view of all assumptions used in the valuation.
Focus: Input only (Structures, Rates, Growth, Financials).
Dependencies: Streamlit, Models, i18n.
"""

import streamlit as st
import pandas as pd
from src.models import ValuationResult
from src.i18n import InputLabels, ResultsTexts

def render_detailed_inputs(result: ValuationResult) -> None:
    """
    Renders Pillar 1: Detailed Configuration & Assumptions.

    This view displays every single parameter used in the model:
    - Market Structure (Shares, Debt, etc.)
    - Discount Rates (Rf, Beta, MRP, Cost of Debt)
    - Operational Assumptions (Tax, Growth)
    - Raw Financial Inputs (if available)

    Parameters
    ----------
    result : ValuationResult
        The object containing the full request configuration.
    """
    st.subheader(InputLabels.SECTION_STRUCTURE) # Using a consistent subheader concept if needed, or KPITexts.TAB_INPUTS

    params = result.request.parameters

    # --- Section A: Market Structure & Enterprise Value Components ---
    st.markdown(f"#### {InputLabels.SECTION_STRUCTURE}")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)

    with col_s1:
        st.metric(InputLabels.TICKER, result.request.ticker)
        st.metric(InputLabels.CURRENCY, params.structure.currency)

    with col_s2:
        st.metric(InputLabels.CURRENT_PRICE, f"{params.structure.current_price:,.2f}")
        st.metric(InputLabels.SHARES_OUT, f"{params.structure.shares_outstanding:,.0f}")

    with col_s3:
        st.metric(InputLabels.NET_DEBT, f"{params.structure.net_debt:,.0f} M")
        st.metric(InputLabels.MINORITY_INTEREST, f"{params.structure.minority_interests:,.0f} M")

    with col_s4:
        # Enterprise Value (Bridge) implied by Current Price
        implied_ev = (params.structure.current_price * params.structure.shares_outstanding) + params.structure.net_debt
        st.metric(InputLabels.IMPLIED_EV, f"{implied_ev:,.0f} M")

    st.divider()

    # --- Section B: Cost of Capital (WACC) Components ---
    st.markdown(f"#### {InputLabels.SECTION_WACC}")

    if params.rates:
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)

        with col_r1:
            st.metric(InputLabels.RISK_FREE_RATE, f"{params.rates.risk_free_rate:.2%}")
            st.caption(InputLabels.SOURCE_RF)

        with col_r2:
            st.metric(InputLabels.BETA, f"{params.rates.beta:.2f}")
            st.caption(InputLabels.SOURCE_BETA)

        with col_r3:
            st.metric(InputLabels.ERP, f"{params.rates.equity_risk_premium:.2%}")
            st.metric(InputLabels.COST_OF_EQUITY, f"{params.rates.cost_of_equity:.2%}")

        with col_r4:
            st.metric(InputLabels.COST_OF_DEBT_PRE_TAX, f"{params.rates.cost_of_debt_pre_tax:.2%}")
            st.metric(InputLabels.TAX_RATE, f"{params.rates.tax_rate:.2%}")

        # WACC Calculation Display
        with st.expander(InputLabels.WACC_DETAILS):
            st.write(f"**{InputLabels.WEIGHT_EQUITY}:** {params.rates.weight_equity:.1%}")
            st.write(f"**{InputLabels.WEIGHT_DEBT}:** {params.rates.weight_debt:.1%}")
            st.write(f"**{InputLabels.WACC_CALC}:** {params.rates.wacc_calculated:.2%}")
    else:
        st.warning(ResultsTexts.NO_RATES_DATA)

    st.divider()

    # --- Section C: Operational & Terminal Assumptions ---
    st.markdown(f"#### {InputLabels.SECTION_GROWTH}")
    col_g1, col_g2, col_g3 = st.columns(3)

    with col_g1:
        # Safe access to growth parameters
        tgr = params.growth.terminal_growth_rate if params.growth else 0.02
        st.metric(InputLabels.TERMINAL_GROWTH, f"{tgr:.2%}")

    with col_g2:
        proj_years = params.growth.projection_years if params.growth else 5
        st.metric(InputLabels.PROJECTION_PERIOD, f"{proj_years} Y")

    with col_g3:
        # Method used (e.g., DCF GGM or Exit Multiple)
        method = params.strategy.valuation_method if params.strategy else "DCF Standard"
        st.metric(InputLabels.VALUATION_METHOD, method)

    # --- Section D: Raw Financial Inputs (The "Books") ---
    st.markdown(f"#### {InputLabels.SECTION_FINANCIALS}")

    if result.request.financials:
        with st.expander(InputLabels.VIEW_RAW_DATA, expanded=False):
            # Converting list of objects to DataFrame for display
            try:
                # Assumes financials.history is a list of Pydantic models
                data = [f.model_dump() for f in result.request.financials.history]
                df_fin = pd.DataFrame(data)
                st.dataframe(df_fin, use_container_width=True)
            except Exception as e:
                st.caption(f"Technical error details: {e}")
                st.text(InputLabels.DATA_UNFORMATTED)
    else:
        st.info(ResultsTexts.NO_FINANCIALS_PROVIDED)