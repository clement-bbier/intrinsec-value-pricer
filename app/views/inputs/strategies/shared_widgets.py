"""
app/views/inputs/strategies/shared_widgets.py

SHARED WIDGETS — Stateless UI components for expert terminals.
==============================================================
Role: Pure rendering of UI components using standardized session keys.
Architecture: V16 (Metadata-Driven). Data is pulled via UIBinder.
Strict I18n: No hardcoded strings permitted.

Pattern: Single Responsibility
Style: Numpy docstrings
"""

from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

from src.config.constants import UIKeys, UIWidgetDefaults
from src.i18n.fr.ui.terminals import CommonTerminals
from src.models import (
    TerminalValueMethod,
    ValuationMethodology,
)

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. BASE INPUT WIDGETS
# ==============================================================================
# NOTE: Projection Years slider has been promoted to the global Sidebar.
# It is no longer duplicated in strategy terminals (DRY compliance).


def widget_growth_rate(label: str, key_prefix: str) -> None:
    """
    Renders a numeric input for growth rates.
    """
    st.number_input(
        label,
        min_value=UIWidgetDefaults.MIN_GROWTH_RATE,
        max_value=UIWidgetDefaults.MAX_GROWTH_RATE,
        value=None,
        step=0.1,
        format="%.2f",
        help=CommonTerminals.HELP_GROWTH_RATE,
        key=f"{key_prefix}_{UIKeys.GROWTH_RATE}",
    )


# ==============================================================================
# 2. COST OF CAPITAL (Section 3)
# ==============================================================================


def widget_cost_of_capital(mode: ValuationMethodology) -> None:
    """
    Renders the financial rates and risk parameters section.
    """
    prefix = mode.name

    st.latex(CommonTerminals.FORMULA_CAPITAL_KE if mode.is_direct_equity else CommonTerminals.FORMULA_CAPITAL_WACC)

    # Debt weight only for enterprise value models (FCFF), not for direct equity models (FCFE, DDM)
    if not mode.is_direct_equity:
        st.number_input(
            CommonTerminals.INP_PRICE_WEIGHTS,
            value=None,
            format="%.2f",
            help=CommonTerminals.HELP_PRICE_WEIGHTS,
            key=f"{prefix}_{UIKeys.PRICE}",
        )

    col_a, col_b = st.columns(2)
    # Risk-free rate & Beta
    col_a.number_input(
        CommonTerminals.INP_RF,
        value=None,
        format="%.2f",
        help=CommonTerminals.HELP_RF,
        key=f"{prefix}_{UIKeys.RF}",
    )
    col_b.number_input(
        CommonTerminals.INP_BETA,
        value=None,
        format="%.2f",
        help=CommonTerminals.HELP_BETA,
        key=f"{prefix}_{UIKeys.BETA}",
    )

    # Risk premium
    col_a.number_input(
        CommonTerminals.INP_MRP,
        value=None,
        format="%.2f",
        help=CommonTerminals.HELP_MRP,
        key=f"{prefix}_{UIKeys.MRP}",
    )

    if not mode.is_direct_equity:
        # Cost of debt and Tax rate (FCFF/WACC models only)
        col_b.number_input(
            CommonTerminals.INP_KD,
            value=None,
            format="%.2f",
            help=CommonTerminals.HELP_KD,
            key=f"{prefix}_{UIKeys.KD}",
        )
        col_a.number_input(
            CommonTerminals.INP_TAX,
            value=None,
            format="%.2f",
            help=CommonTerminals.HELP_TAX,
            key=f"{prefix}_{UIKeys.TAX}",
        )

    st.divider()


# ==============================================================================
# 3. TERMINAL VALUE (Section 4)
# ==============================================================================


def get_terminal_value_narrative(mode: ValuationMethodology) -> str:
    """Maps methodology to its specific LaTeX TV formula."""
    mapping = {
        ValuationMethodology.FCFF_STANDARD: CommonTerminals.FORMULA_TV_FCFF_STD,
        ValuationMethodology.FCFF_NORMALIZED: CommonTerminals.FORMULA_TV_FCFF_NORM,
        ValuationMethodology.FCFF_GROWTH: CommonTerminals.FORMULA_TV_FCFF_GROWTH,
        ValuationMethodology.FCFE: CommonTerminals.FORMULA_TV_FCFE,
        ValuationMethodology.DDM: CommonTerminals.FORMULA_TV_DDM,
    }
    return mapping.get(mode, CommonTerminals.FORMULA_TV_GORDON)


def widget_terminal_value_dcf(mode: ValuationMethodology, key_prefix: str) -> None:
    """
    Renders Terminal Value selection (Gordon vs Multiples).

    Note: @st.fragment decorator was removed to ensure reactivity when switching
    between valuation methodologies in the sidebar. The mode parameter needs to
    trigger a full re-render to display the correct terminal value formula.
    """
    st.markdown(CommonTerminals.STEP_4_TITLE)
    st.info(CommonTerminals.STEP_4_DESC)

    method = st.radio(
        CommonTerminals.RADIO_TV_METHOD,
        options=[TerminalValueMethod.GORDON_GROWTH, TerminalValueMethod.EXIT_MULTIPLE],
        format_func=lambda x: (
            CommonTerminals.TV_GORDON if x == TerminalValueMethod.GORDON_GROWTH else CommonTerminals.TV_EXIT
        ),
        horizontal=True,
        key=f"{key_prefix}_{UIKeys.TV_METHOD}",
    )

    if method == TerminalValueMethod.GORDON_GROWTH:
        st.latex(get_terminal_value_narrative(mode))
        st.number_input(
            CommonTerminals.INP_PERP_G,
            value=None,
            format="%.2f",
            help=CommonTerminals.HELP_PERP_G,
            key=f"{key_prefix}_{UIKeys.GN}",
        )
    else:
        st.latex(CommonTerminals.FORMULA_TV_EXIT)
        st.number_input(
            CommonTerminals.INP_EXIT_MULT,
            value=None,
            format="%.1f",
            help=CommonTerminals.HELP_EXIT_MULT,
            key=f"{key_prefix}_{UIKeys.EXIT_MULT}",
        )
    st.divider()

def widget_terminal_value_rim(formula_latex: str, key_prefix: str) -> None:
    """Renders RIM specific terminal value (Persistence)."""
    st.markdown(CommonTerminals.STEP_4_TITLE)
    st.info(CommonTerminals.STEP_4_DESC)
    st.latex(formula_latex)
    st.number_input(
        CommonTerminals.INP_OMEGA,
        min_value=0.0,
        max_value=1.0,
        value=None,
        help=CommonTerminals.HELP_OMEGA,
        key=f"{key_prefix}_{UIKeys.OMEGA}",
    )
    st.divider()

# ==============================================================================
# 4. EQUITY BRIDGE (Section 5)
# ==============================================================================


def widget_equity_bridge(formula_latex: str, mode: ValuationMethodology) -> None:
    """Renders balance sheet adjustments section."""
    prefix = f"bridge_{mode.name}"
    st.markdown(CommonTerminals.STEP_5_TITLE)
    st.info(CommonTerminals.STEP_5_DESC)
    st.latex(formula_latex)

    if mode.is_direct_equity:
        st.number_input(
            CommonTerminals.INP_SHARES,
            value=None,
            format="%.2f",
            help=CommonTerminals.HELP_SHARES,
            key=f"{prefix}_{UIKeys.SHARES}",
        )
    else:
        c1, c2 = st.columns(2)
        c1.number_input(
            CommonTerminals.INP_DEBT,
            value=None,
            format="%.2f",
            help=CommonTerminals.HELP_DEBT,
            key=f"{prefix}_{UIKeys.DEBT}",
        )
        c2.number_input(
            CommonTerminals.INP_CASH,
            value=None,
            format="%.2f",
            help=CommonTerminals.HELP_CASH,
            key=f"{prefix}_{UIKeys.CASH}",
        )

        c3, c4, c5 = st.columns(3)
        c3.number_input(CommonTerminals.INP_MINORITIES, value=None, format="%.2f", key=f"{prefix}_{UIKeys.MINORITIES}")
        c4.number_input(CommonTerminals.INP_PENSIONS, value=None, format="%.2f", key=f"{prefix}_{UIKeys.PENSIONS}")
        c5.number_input(
            CommonTerminals.INP_SHARES,
            value=None,
            format="%.2f",
            help=CommonTerminals.HELP_SHARES,
            key=f"{prefix}_{UIKeys.SHARES}",
        )

    st.number_input(
        CommonTerminals.INP_SBC_DILUTION,
        value=None,
        format="%.2f",
        help=CommonTerminals.HELP_SBC_DILUTION,
        key=f"{prefix}_{UIKeys.SBC_RATE}",
    )


# ==============================================================================
# 5. OPTIONAL EXTENSIONS (Sections 6-11)
# ==============================================================================


def widget_sensitivity() -> None:
    """
    Renders the sensitivity analysis settings (WACC vs g).
    Corresponds to Section 11 in CommonTerminals.

    Keys are global (from UIKeys registry), not strategy-prefixed.
    Ghost Pattern: All fields default to None so Pydantic system
    constants apply when no user override is provided.
    """
    st.markdown(CommonTerminals.SEC_11_SENSITIVITY)

    if st.toggle(CommonTerminals.LBL_SENSITIVITY_ENABLE, value=False, key=UIKeys.SENS_ENABLE):
        st.info(CommonTerminals.MSG_SENSITIVITY_DESC)

        c1, c2 = st.columns(2)
        c1.number_input(
            CommonTerminals.LBL_SENS_STEP,
            value=None,
            format="%.3f",
            help=CommonTerminals.HELP_SENS_STEP,
            key=UIKeys.SENS_STEP,
        )
        c2.number_input(
            CommonTerminals.LBL_SENS_RANGE,
            value=None,
            min_value=3,
            max_value=9,
            help=CommonTerminals.HELP_SENS_RANGE,
            key=UIKeys.SENS_RANGE,
        )


def widget_monte_carlo(
    mode: ValuationMethodology, terminal_method: TerminalValueMethod | None, custom_vols: dict[str, str] | None = None
) -> None:
    """Renders Monte Carlo simulation parameters."""
    st.markdown(CommonTerminals.SEC_6_MC)

    if not st.toggle(
        CommonTerminals.MC_CALIBRATION,
        value=False,
        help=CommonTerminals.HELP_MC_ENABLE,
        key=UIKeys.MC_ENABLE,
    ):
        return

    st.number_input(
        CommonTerminals.MC_ITERATIONS,
        value=None,
        min_value=1000,
        max_value=25000,
        step=1000,
        help=CommonTerminals.HELP_MC_SIMS,
        key=UIKeys.MC_SIMS,
    )

    col1, col2 = st.columns(2)
    # Dynamic Labels from BaseTerminal
    label_flow = (
        custom_vols.get("base_flow_volatility", CommonTerminals.MC_VOL_BASE_FLOW)
        if custom_vols
        else CommonTerminals.MC_VOL_BASE_FLOW
    )

    col1.number_input(
        label_flow,
        value=None,
        format="%.2f",
        help=CommonTerminals.HELP_MC_VOL_FLOW,
        key=UIKeys.MC_VOL_FLOW,
    )
    col1.number_input(
        CommonTerminals.MC_VOL_G,
        value=None,
        format="%.2f",
        help=CommonTerminals.HELP_MC_VOL_G,
        key=UIKeys.MC_VOL_GROWTH,
    )

    if mode != ValuationMethodology.GRAHAM:
        col2.number_input(
            CommonTerminals.MC_VOL_BETA,
            value=None,
            format="%.2f",
            help=CommonTerminals.HELP_MC_VOL_BETA,
            key=UIKeys.MC_VOL_BETA,
        )

    if terminal_method == TerminalValueMethod.EXIT_MULTIPLE:
        col2.number_input(CommonTerminals.LBL_VOL_EXIT_M, value=None, format="%.2f", key=UIKeys.MC_VOL_EXIT_M)
    elif terminal_method == TerminalValueMethod.GORDON_GROWTH:
        # STRICT ACCESS: LBL_VOL_GN must exist in SharedTexts
        col2.number_input(
            CommonTerminals.LBL_VOL_GN,
            value=None,
            format="%.2f",
            help=CommonTerminals.HELP_MC_VOL_GN,
            key=UIKeys.MC_VOL_GN,
        )


def widget_backtest() -> None:
    """Renders historical backtest activation.

    Ghost Pattern: lookback defaults to None so the Pydantic system
    constant (BacktestDefaults.DEFAULT_LOOKBACK_YEARS) applies.
    """
    st.markdown(CommonTerminals.SEC_10_BACKTEST)
    if st.toggle(
        CommonTerminals.LBL_BACKTEST_ENABLE,
        value=False,
        help=CommonTerminals.HELP_BACKTEST_ENABLE,
        key=UIKeys.BT_ENABLE,
    ):
        st.number_input(CommonTerminals.LBL_LOOKBACK, min_value=1, max_value=10, value=None, key=UIKeys.BT_LOOKBACK)


def widget_peer_triangulation() -> None:
    """Renders peer selection for relative valuation."""
    st.markdown(CommonTerminals.SEC_7_PEERS)
    if st.toggle(
        CommonTerminals.LBL_PEER_ENABLE,
        value=False,
        help=CommonTerminals.HELP_PEER_TRIANGULATION,
        key=UIKeys.PEER_ENABLE,
    ):
        raw_input = st.text_input(
            CommonTerminals.INP_MANUAL_PEERS,
            placeholder=CommonTerminals.PLACEHOLDER_PEERS,
            help=CommonTerminals.HELP_MANUAL_PEERS,
            key=UIKeys.PEER_INPUT,
        )
        # Processed into a list for the Binder
        if raw_input:
            st.session_state[UIKeys.PEER_LIST] = [t.strip().upper() for t in raw_input.split(",") if t.strip()]


def widget_scenarios(mode: ValuationMethodology) -> None:
    """Renders probabilistic scenario variants."""
    st.markdown(CommonTerminals.SEC_8_SCENARIOS)
    if not st.toggle(
        CommonTerminals.INP_SCENARIO_ENABLE,
        value=False,
        help=CommonTerminals.HELP_SCENARIO_ENABLE,
        key=UIKeys.SCENARIO_ENABLE,
    ):
        return

    for case in ["bull", "base", "bear"]:
        st.markdown(f"**{case.upper()}**")
        c1, c2, c3 = st.columns(3)
        c1.number_input(CommonTerminals.INP_SCENARIO_PROBA, value=None, key=f"scenario_{UIKeys.SCENARIO_P}_{case}")
        c2.number_input(CommonTerminals.INP_SCENARIO_GROWTH, value=None, key=f"scenario_{UIKeys.SCENARIO_G}_{case}")
        if mode == ValuationMethodology.FCFF_GROWTH:
            c3.number_input(CommonTerminals.INP_SCENARIO_MARGIN, value=None, key=f"scenario_{UIKeys.SCENARIO_M}_{case}")


def widget_sotp() -> None:
    """Renders Sum-of-the-Parts segment editor."""
    st.markdown(CommonTerminals.SEC_9_SOTP)
    if st.toggle(CommonTerminals.LBL_SOTP_ENABLE, value=False, help=CommonTerminals.HELP_SOTP, key=UIKeys.SOTP_ENABLE):
        st.data_editor(
            pd.DataFrame([{"name": CommonTerminals.DEFAULT_SEGMENT_NAME, "value": 0.0, "method": "DCF"}]),
            num_rows="dynamic",
            key=UIKeys.SOTP_EDITOR,
            column_config={
                "name": st.column_config.TextColumn(CommonTerminals.LBL_SEGMENT_NAME),
                "value": st.column_config.NumberColumn(CommonTerminals.LBL_SEGMENT_VALUE, format="%.2f"),
                "method": st.column_config.SelectboxColumn(
                    CommonTerminals.LBL_SEGMENT_METHOD,
                    options=["DCF", "Multiple", "Net Asset"],  # Technical keys can remain strings
                    required=True,
                ),
            },
        )
        st.number_input(
            CommonTerminals.LBL_DISCOUNT,
            value=None,
            min_value=0,
            max_value=50,
            help=CommonTerminals.HELP_SOTP,
            key=UIKeys.SOTP_DISCOUNT,
        )
