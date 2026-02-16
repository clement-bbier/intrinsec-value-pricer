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

from src.core.formatting import CurrencyFormatter
from src.i18n import InputLabels, KPITexts
from src.models import ValuationMethodology, ValuationResult


def get_display_currency(result: ValuationResult) -> str:
    """
    Extracts the display currency from the valuation result.

    Uses the financial snapshot currency (Yahoo source of truth) as the primary source,
    with a fallback to USD if the snapshot is not available.

    Parameters
    ----------
    result : ValuationResult
        The valuation result containing the financial snapshot.

    Returns
    -------
    str
        The currency code to use for display (e.g., "EUR", "USD").
    """
    if result.financials and result.financials.currency:
        return result.financials.currency
    return "USD"


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
    # Use currency from financial snapshot (Yahoo source of truth)
    currency = get_display_currency(result)
    st.caption(f"{InputLabels.SECTION_STRUCTURE} • {result.request.mode.value} • {currency}")

    st.divider()

    # ==========================================================================
    # BLOCKS 1 & 2: STRUCTURE & RATES (SIDE BY SIDE TABLES)
    # ==========================================================================
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(f"#### {InputLabels.SECTION_STRUCTURE}")
        _render_capital_structure_table(params, currency)

    with c2:
        st.markdown(f"#### {InputLabels.SECTION_WACC}")
        # Pass both inputs (params) and calculated results (common.rates) for fallback
        _render_rates_table(params, result.results.common.rates)

    st.divider()

    # ==========================================================================
    # BLOCK 3: OPERATIONAL ASSUMPTIONS (TABLE)
    # ==========================================================================
    st.markdown(f"#### {InputLabels.SECTION_GROWTH}")

    # Renders a table specific to the selected valuation strategy
    _render_strategy_inputs_table(result)

    # ==========================================================================
    # BLOCK 4: RAW DATA SOURCE (EXPANDER)
    # ==========================================================================
    with st.expander(f"{InputLabels.SECTION_FINANCIALS} ({InputLabels.RAW_DATA_SOURCE_TITLE})", expanded=False):
        st.json(
            {
                InputLabels.DATA_SOURCE: InputLabels.DATA_SOURCE_VALUE,
                InputLabels.LAST_UPDATE: str(params.structure.last_update),
                InputLabels.TICKER: params.structure.ticker,
                InputLabels.SECTOR: params.structure.sector.value if params.structure.sector else InputLabels.UNKNOWN,
                InputLabels.PRICE_REFERENCE: params.structure.current_price,
            }
        )


# ==============================================================================
# SUB-RENDERERS (Private Helpers)
# ==============================================================================


def _safe_fmt(value: float | None, fmt: str, default: str = "-") -> str:
    """
    Safely formats a value handling None types.

    Parameters
    ----------
    value : float | None
        The value to format.
    fmt : str
        Python format specification (e.g., ".2%", ".2f").
    default : str, default="-"
        The default string to return if value is None.

    Returns
    -------
    str
        Formatted value string.
    """
    if value is None:
        return default
    return format(value, fmt)


def _clean_label(label: str) -> str:
    """
    Removes leading '.' or '*' characters from label strings.

    Parameters
    ----------
    label : str
        The label to clean.

    Returns
    -------
    str
        The cleaned label with leading special characters removed.
    """
    # Iteratively strip leading dots and asterisks until none remain
    while label and label[0] in (".", "*"):
        label = label[1:]
    return label


def _render_capital_structure_table(params, currency: str) -> None:
    """
    Displays a clean dataframe for capital structure with proper currency formatting.

    Parameters
    ----------
    params : Parameters
        The parameter bundle containing structure and capital data.
    currency : str
        The currency code to use for formatting (from financials snapshot).
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

    # Use CurrencyFormatter for proper symbol placement
    # Note: 'currency' parameter is passed from Yahoo snapshot (source of truth)
    # and takes precedence over struct.currency which may have been overridden during resolution
    formatter = CurrencyFormatter()

    # Use formatted strings for the table
    data = [
        {"Item": _clean_label(InputLabels.CURRENT_PRICE), "Value": formatter.format(price, currency, decimals=2, smart_scale=False)},
        {"Item": _clean_label(InputLabels.SHARES_OUT), "Value": f"{shares:,.0f}"},
        {"Item": _clean_label(KPITexts.MARKET_CAP_LABEL), "Value": formatter.format(mkt_cap, currency, decimals=0, smart_scale=True)},
        {"Item": _clean_label(InputLabels.NET_DEBT), "Value": formatter.format(net_debt, currency, decimals=0, smart_scale=True)},
        {
            "Item": _clean_label(InputLabels.IMPLIED_EV),
            "Value": formatter.format(mkt_cap + net_debt, currency, decimals=0, smart_scale=True),
        },
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
            return f"{input_val:.2%}"  # User Override
        if calc_val is not None:
            return f"{calc_val:.2%} (Auto)"  # Calculated
        return "-"

    # Specific logic for Cost of Debt (Input is pre-tax, Resolved is post-tax usually)
    kd_display = _safe_fmt(p_rates.cost_of_debt, ".2%", default="Auto")

    data = [
        {
            "Parameter": _clean_label(InputLabels.RISK_FREE_RATE),
            "Value": fmt_rate(
                p_rates.risk_free_rate,
                resolved_rates.risk_free_rate if hasattr(resolved_rates, "risk_free_rate") else None,
            ),
        },
        {"Parameter": _clean_label(InputLabels.BETA), "Value": _safe_fmt(p_rates.beta, ".2f", default="Auto")},
        {"Parameter": _clean_label(InputLabels.ERP), "Value": _safe_fmt(p_rates.market_risk_premium, ".2%", default="Auto")},
        {
            "Parameter": _clean_label(InputLabels.COST_OF_EQUITY),
            "Value": fmt_rate(p_rates.cost_of_equity, resolved_rates.cost_of_equity),
        },
        {"Parameter": _clean_label(InputLabels.COST_OF_DEBT_PRE_TAX), "Value": kd_display},
        {"Parameter": _clean_label(InputLabels.WACC_CALC), "Value": f"**{resolved_rates.wacc:.2%}**"},
    ]

    df = pd.DataFrame(data)
    st.table(df.set_index("Parameter"))


def _render_strategy_inputs_table(result: ValuationResult) -> None:
    """
    Displays assumptions specific to the selected model as a table.

    Parameters
    ----------
    result : ValuationResult
        The complete valuation result containing strategy parameters.
    """
    strat_params = result.request.parameters.strategy
    mode = result.request.mode

    data: list[dict[str, str]]

    if mode == ValuationMethodology.RIM:
        bv_display = f"{strat_params.book_value_anchor:,.0f} M" if strat_params.book_value_anchor is not None else "-"
        growth_val = strat_params.growth_rate if hasattr(strat_params, "growth_rate") else None
        data = [
            {
                InputLabels.TABLE_COL_ASSUMPTION: _clean_label(InputLabels.ANCHOR_BOOK_VALUE),
                InputLabels.TABLE_COL_VALUE: bv_display,
            },
            {
                InputLabels.TABLE_COL_ASSUMPTION: _clean_label(InputLabels.PERSISTENCE_FACTOR),
                InputLabels.TABLE_COL_VALUE: _safe_fmt(strat_params.persistence_factor, ".2f"),
            },
            {
                InputLabels.TABLE_COL_ASSUMPTION: _clean_label(InputLabels.TERMINAL_GROWTH_LABEL),
                InputLabels.TABLE_COL_VALUE: _safe_fmt(growth_val, ".2%"),
            },
        ]

    elif mode == ValuationMethodology.GRAHAM:
        aaa_yield = result.request.parameters.common.rates.corporate_aaa_yield if hasattr(result.request.parameters.common.rates, "corporate_aaa_yield") else None
        if aaa_yield is None and hasattr(result.results.common.rates, "corporate_aaa_yield"):
            aaa_yield = result.results.common.rates.corporate_aaa_yield

        data = [
            {
                InputLabels.TABLE_COL_ASSUMPTION: _clean_label(InputLabels.NORMALIZED_EPS),
                InputLabels.TABLE_COL_VALUE: _safe_fmt(strat_params.eps_normalized, ".2f"),
            },
            {
                InputLabels.TABLE_COL_ASSUMPTION: _clean_label(InputLabels.CONSERVATIVE_GROWTH),
                InputLabels.TABLE_COL_VALUE: _safe_fmt(strat_params.growth_estimate, ".2%"),
            },
            {
                InputLabels.TABLE_COL_ASSUMPTION: _clean_label(InputLabels.AAA_CORP_RATE),
                InputLabels.TABLE_COL_VALUE: _safe_fmt(aaa_yield, ".2%"),
            },
        ]

    else:
        # DCF Family (Standard, Growth, Normalized, FCFE, DDM)
        # Determine anchor value: each strategy stores its base flow under a
        # different attribute name. The priority order matches the most common
        # strategies first (FCFF Standard > Normalized > Growth > DDM > FCFE).
        anchor_val: float = 0.0
        for attr in ("fcf_anchor", "fcf_norm", "revenue_ttm", "dividend_base", "fcfe_anchor"):
            val = getattr(strat_params, attr, None)
            if val is not None:
                anchor_val = val
                break

        # Phase 1 Growth — each strategy stores growth under a different name.
        # Priority: explicit P1 growth > revenue growth > generic growth rate.
        g_p1: float | None = None
        for attr in ("growth_rate_p1", "revenue_growth_rate", "growth_rate"):
            val = getattr(strat_params, attr, None)
            if val is not None:
                g_p1 = val
                break

        # Get terminal growth if it exists
        terminal_growth = None
        if hasattr(strat_params, "terminal_value") and strat_params.terminal_value:
            terminal_growth = strat_params.terminal_value.perpetual_growth_rate
        elif hasattr(strat_params, "perpetual_growth_rate"):
            terminal_growth = strat_params.perpetual_growth_rate

        # Get terminal method if it exists
        terminal_method_val = None
        if hasattr(strat_params, "terminal_value") and strat_params.terminal_value:
            terminal_method_val = strat_params.terminal_value.method

        data = [
            {
                InputLabels.TABLE_COL_ASSUMPTION: _clean_label(InputLabels.BASE_FLOW_LABEL),
                InputLabels.TABLE_COL_VALUE: f"{anchor_val:,.2f} M",
            },
            {
                InputLabels.TABLE_COL_ASSUMPTION: _clean_label(InputLabels.PHASE_1_GROWTH_LABEL),
                InputLabels.TABLE_COL_VALUE: _safe_fmt(g_p1, ".2%"),
            },
            {
                InputLabels.TABLE_COL_ASSUMPTION: _clean_label(InputLabels.PROJECTION_YEARS_LABEL),
                InputLabels.TABLE_COL_VALUE: f"{strat_params.projection_years} ans",
            },
        ]

        # Only add Terminal Growth if it exists and is not None
        if terminal_growth is not None:
            data.append(
                {
                    InputLabels.TABLE_COL_ASSUMPTION: _clean_label(InputLabels.TERMINAL_GROWTH_LABEL),
                    InputLabels.TABLE_COL_VALUE: _safe_fmt(terminal_growth, ".2%"),
                }
            )

        # Only add Terminal Method if it exists and is not None
        if terminal_method_val is not None:
            method_str = str(terminal_method_val.value if hasattr(terminal_method_val, "value") else terminal_method_val)
            data.append(
                {
                    InputLabels.TABLE_COL_ASSUMPTION: _clean_label(InputLabels.TERMINAL_METHOD_LABEL),
                    InputLabels.TABLE_COL_VALUE: method_str,
                }
            )

    if data:
        df = pd.DataFrame(data)
        st.table(df.set_index(InputLabels.TABLE_COL_ASSUMPTION))
    else:
        st.info(InputLabels.NO_OPERATIONAL_ASSUMPTIONS)
