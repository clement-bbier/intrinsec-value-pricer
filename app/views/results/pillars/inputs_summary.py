"""
app/views/results/pillars/inputs_summary.py

PILLAR 1: DETAILED INPUTS & CONFIGURATION
=========================================
Role: Renders the audit view of all assumptions used in the valuation.
Focus: Input traceability (Structures, Rates, Growth, Financials).
Style: Institutional "Fact Sheet" layout using structured tables.
"""


import pandas as pd
import streamlit as st

from src.i18n import InputLabels, KPITexts
from src.models import ValuationMethodology, ValuationResult


def render_detailed_inputs(result: ValuationResult) -> None:
    """
    Renders Pillar 1: Configuration Fact Sheet.

    Displays inputs organized in 3 horizontal blocks:
    1. Market & Capital Structure (The "What")
    2. Discount Rates & Risk (The "Cost")
    3. Operational Strategy (The "Driver" - Dynamic based on model)

    Parameters
    ----------
    result : ValuationResult
        The object containing calculation results and request parameters.
    """
    params = result.request.parameters

    # --- HEADER: CONTEXT ---
    currency = params.structure.currency if params.structure.currency else "USD"
    st.caption(f"{InputLabels.SECTION_STRUCTURE} • {result.request.mode.value} • {currency}")

    st.divider()

    # ==========================================================================
    # BLOCKS 1 & 2: STRUCTURE & RATES (SIDE BY SIDE TABLES)
    # ==========================================================================
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(f"#### 🏛️ {InputLabels.SECTION_STRUCTURE}")
        _render_capital_structure_table(params)

    with c2:
        st.markdown(f"#### ⚖️ {InputLabels.SECTION_WACC}")
        # Pass both inputs (params) and calculated results (common.rates) for fallback
        _render_rates_table(params, result.results.common.rates)

    st.divider()

    # ==========================================================================
    # BLOCK 3: OPERATIONAL ASSUMPTIONS (TABLE)
    # ==========================================================================
    st.markdown(f"#### 🚀 {InputLabels.SECTION_GROWTH}")

    # Renders a table specific to the selected valuation strategy
    _render_strategy_inputs_table(result)

    # ==========================================================================
    # BLOCK 4: RAW DATA SOURCE (EXPANDER)
    # ==========================================================================
    with st.expander(f"📚 {InputLabels.SECTION_FINANCIALS} ({InputLabels.RAW_DATA_SOURCE_TITLE})", expanded=False):
        st.json({
            InputLabels.DATA_SOURCE: InputLabels.DATA_SOURCE_VALUE,
            InputLabels.LAST_UPDATE: str(params.structure.last_update),
            InputLabels.TICKER: params.structure.ticker,
            InputLabels.SECTOR: params.structure.sector.value if params.structure.sector else InputLabels.UNKNOWN,
            InputLabels.PRICE_REFERENCE: params.structure.current_price
        })


# ==============================================================================
# SUB-RENDERERS (Private Helpers)
# ==============================================================================

def _safe_fmt(value: float | None, fmt: str, default: str = "-") -> str:
    """Safely formats a value handling None types."""
    if value is None:
        return default
    return format(value, fmt)

def _render_capital_structure_table(params) -> None:
    """
    Displays a clean dataframe for capital structure.
    """
    # Safe data access (V2 Model Path)
    struct = params.structure
    cap = params.common.capital

    # On-the-fly calculations for display
    # Fields may still be None if not resolved; default to zero for safe arithmetic
    shares = cap.shares_outstanding if cap.shares_outstanding is not None else 0
    price = struct.current_price if struct.current_price is not None else 0.0
    mkt_cap = price * shares

    debt = cap.total_debt if cap.total_debt is not None else 0.0
    cash = cap.cash_and_equivalents if cap.cash_and_equivalents is not None else 0.0
    net_debt = debt - cash

    # Use formatted strings for the table
    data = [
        {"Item": InputLabels.CURRENT_PRICE, "Value": f"{price:,.2f} {struct.currency}"},
        {"Item": InputLabels.SHARES_OUT,    "Value": f"{shares:,.0f}"},
        {"Item": KPITexts.MARKET_CAP_LABEL, "Value": f"{mkt_cap:,.0f} M"},
        {"Item": InputLabels.NET_DEBT,      "Value": f"{net_debt:,.0f} M"},
        {"Item": "Enterprise Value (Implied)", "Value": f"{(mkt_cap + net_debt):,.0f} M"},
    ]

    df = pd.DataFrame(data)
    # Display as a static table (cleaner than metric widgets for lists)
    st.table(df.set_index("Item"))


def _render_rates_table(params, resolved_rates) -> None:
    """
    Displays a clean dataframe for rates (WACC/Ke).
    Uses inputs from 'params' and falls back to 'resolved_rates' (calculated) if inputs are None.
    """
    # Inputs (Parameters) - FinancialRatesParameters
    p_rates = params.common.rates

    # Helper to format input vs calculated
    def fmt_rate(input_val, calc_val):
        if input_val is not None:
            return f"{input_val:.2%}" # User Override
        if calc_val is not None:
            return f"{calc_val:.2%} (Auto)" # Calculated
        return "-"

    # Specific logic for Cost of Debt (Input is pre-tax, Resolved is post-tax usually)
    kd_display = _safe_fmt(p_rates.cost_of_debt, ".2%", default="Auto")

    data = [
        {"Parameter": InputLabels.RISK_FREE_RATE,
         "Value": fmt_rate(p_rates.risk_free_rate, getattr(resolved_rates, 'risk_free_rate', None))},
        {"Parameter": InputLabels.BETA,           "Value": _safe_fmt(p_rates.beta, ".2f", default="Auto")},
        {"Parameter": InputLabels.ERP,
         "Value": _safe_fmt(p_rates.market_risk_premium, ".2%", default="Auto")},
        {"Parameter": InputLabels.COST_OF_EQUITY,
         "Value": fmt_rate(p_rates.cost_of_equity, resolved_rates.cost_of_equity)},
        {"Parameter": InputLabels.COST_OF_DEBT_PRE_TAX,   "Value": kd_display},
        {"Parameter": InputLabels.WACC_CALC,      "Value": f"**{resolved_rates.wacc:.2%}**"} # WACC is always calculated
    ]

    df = pd.DataFrame(data)
    st.table(df.set_index("Parameter"))


def _render_strategy_inputs_table(result: ValuationResult) -> None:
    """
    Displays assumptions specific to the selected model as a table.
    Adapts dynamically to content of `result.request.parameters.strategy`.
    """
    strat_params = result.request.parameters.strategy
    mode = result.request.mode

    data: list[dict[str, str]]

    if mode == ValuationMethodology.RIM:
        data = [
            {"Assumption": "Anchor (Book Value)", "Value": f"{getattr(strat_params, 'book_value_anchor', 0):,.0f} M"},
            {"Assumption": "Persistence Factor (ω)",
             "Value": _safe_fmt(getattr(strat_params, 'persistence_factor', None), ".2f")},
            {"Assumption": "Growth (g)", "Value": _safe_fmt(getattr(strat_params, 'growth_rate', None), ".2%")}
        ]

    elif mode == ValuationMethodology.GRAHAM:
        # Check resolved rates for AAA yield if not in inputs
        aaa_yield = getattr(result.request.parameters.common.rates, 'corporate_aaa_yield', None)
        if aaa_yield is None:
             aaa_yield = getattr(result.results.common.rates, 'corporate_aaa_yield', None)

        data = [
            {"Assumption": "Normalized EPS", "Value": _safe_fmt(getattr(strat_params, 'eps_normalized', None), ".2f")},
            {"Assumption": "Conservative Growth",
             "Value": _safe_fmt(getattr(strat_params, 'growth_estimate', None), ".2%")},
            {"Assumption": "AAA Corp Rate", "Value": _safe_fmt(aaa_yield, ".2%")}
        ]

    else: # DCF Family (Standard, Growth, Normalized, FCFE, DDM)
        # Handle common fields for DCF-like models
        anchor_val = getattr(strat_params, 'fcf_anchor', None) or \
                     getattr(strat_params, 'fcf_norm', None) or \
                     getattr(strat_params, 'revenue_ttm', None) or \
                     getattr(strat_params, 'dividend_base', None) or \
                     getattr(strat_params, 'fcfe_anchor', None) or 0

        # Phase 1 Growth
        g_p1 = getattr(strat_params, 'growth_rate_p1', None)
        if g_p1 is None:
            g_p1 = getattr(strat_params, 'revenue_growth_rate', getattr(strat_params, 'growth_rate', None))

        data = [
            {"Assumption": "Base Flow (FCF/Div/EPS)", "Value": f"{anchor_val:,.2f} M"},
            {"Assumption": "Phase 1 Growth", "Value": _safe_fmt(g_p1, ".2%")},
            {"Assumption": "Projection Years", "Value": f"{getattr(strat_params, 'projection_years', 5)} years"},
            {"Assumption": "Terminal Growth (g)",
             "Value": _safe_fmt(getattr(strat_params, 'perpetual_growth_rate', 0.02), ".2%")},
            {"Assumption": "Terminal Method", "Value": str(getattr(strat_params, 'terminal_method', 'Gordon Growth'))}
        ]

    if data:
        df = pd.DataFrame(data)
        st.table(df.set_index("Assumption"))
    else:
        st.info(InputLabels.NO_OPERATIONAL_ASSUMPTIONS)
