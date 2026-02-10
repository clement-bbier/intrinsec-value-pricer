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
from typing import Dict, Optional

import streamlit as st
import pandas as pd

from src.models import (
    ValuationMethodology,
    TerminalValueMethod,
)
from src.i18n import SharedTexts
from src.config.constants import UIWidgetDefaults

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. BASE INPUT WIDGETS
# ==============================================================================

def widget_projection_years(
    default: int = UIWidgetDefaults.DEFAULT_PROJECTION_YEARS,
    key_prefix: str = "strategy"
) -> None:
    """
    Renders a slider for the projection horizon.
    """
    st.slider(
        label=SharedTexts.INP_PROJ_YEARS,
        min_value=UIWidgetDefaults.MIN_PROJECTION_YEARS,
        max_value=UIWidgetDefaults.MAX_PROJECTION_YEARS,
        value=default,
        step=1,
        help=SharedTexts.HELP_PROJ_YEARS,
        key=f"{key_prefix}_years"
    )

def widget_growth_rate(
    label: str,
    key_prefix: str
) -> None:
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
        help=SharedTexts.HELP_GROWTH_RATE,
        key=f"{key_prefix}_growth_rate"
    )

# ==============================================================================
# 2. COST OF CAPITAL (Section 3)
# ==============================================================================

def widget_cost_of_capital(mode: ValuationMethodology) -> None:
    """
    Renders the financial rates and risk parameters section.
    """
    prefix = mode.name

    st.latex(SharedTexts.FORMULA_CAPITAL_KE if mode.is_direct_equity else SharedTexts.FORMULA_CAPITAL_WACC)

    st.number_input(
        SharedTexts.INP_PRICE_WEIGHTS,
        value=None,
        format="%.2f",
        help=SharedTexts.HELP_PRICE_WEIGHTS,
        key=f"{prefix}_price"
    )

    col_a, col_b = st.columns(2)
    # Taux sans risque & Beta
    col_a.number_input(SharedTexts.INP_RF, value=None, format="%.2f", help=SharedTexts.HELP_RF, key=f"{prefix}_rf")
    col_b.number_input(SharedTexts.INP_BETA, value=None, format="%.2f", help=SharedTexts.HELP_BETA, key=f"{prefix}_beta")

    # Prime de risque
    col_a.number_input(SharedTexts.INP_MRP, value=None, format="%.2f", help=SharedTexts.HELP_MRP, key=f"{prefix}_mrp")

    if not mode.is_direct_equity:
        # Coût de la dette et Taxe (uniquement pour FCFF/WACC)
        col_b.number_input(SharedTexts.INP_KD, value=None, format="%.2f", help=SharedTexts.HELP_KD, key=f"{prefix}_kd")
        col_a.number_input(SharedTexts.INP_TAX, value=None, format="%.2f", help=SharedTexts.HELP_TAX, key=f"{prefix}_tax")

# ==============================================================================
# 3. TERMINAL VALUE (Section 4)
# ==============================================================================

def get_terminal_value_narrative(mode: ValuationMethodology) -> str:
    """Maps methodology to its specific LaTeX TV formula."""
    mapping = {
        ValuationMethodology.FCFF_STANDARD: SharedTexts.FORMULA_TV_FCFF_STD,
        ValuationMethodology.FCFF_NORMALIZED: SharedTexts.FORMULA_TV_FCFF_NORM,
        ValuationMethodology.FCFF_GROWTH: SharedTexts.FORMULA_TV_FCFF_GROWTH,
        ValuationMethodology.FCFE: SharedTexts.FORMULA_TV_FCFE,
        ValuationMethodology.DDM: SharedTexts.FORMULA_TV_DDM,
    }
    return mapping.get(mode, SharedTexts.FORMULA_TV_GORDON)

@st.fragment
def widget_terminal_value_dcf(mode: ValuationMethodology, key_prefix: str) -> None:
    """Renders Terminal Value selection (Gordon vs Multiples)."""
    st.markdown(SharedTexts.SEC_4_TERMINAL)
    st.info(SharedTexts.SEC_4_DESC)

    method = st.radio(
        SharedTexts.RADIO_TV_METHOD,
        options=[TerminalValueMethod.GORDON_GROWTH, TerminalValueMethod.EXIT_MULTIPLE],
        format_func=lambda x: SharedTexts.TV_GORDON if x == TerminalValueMethod.GORDON_GROWTH else SharedTexts.TV_EXIT,
        horizontal=True,
        key=f"{key_prefix}_method"
    )

    if method == TerminalValueMethod.GORDON_GROWTH:
        st.latex(get_terminal_value_narrative(mode))
        st.number_input(
            SharedTexts.INP_PERP_G,
            value=None,
            format="%.2f",
            help=SharedTexts.HELP_PERP_G,
            key=f"{key_prefix}_gn"
        )
    else:
        st.latex(SharedTexts.FORMULA_TV_EXIT)
        st.number_input(
            SharedTexts.INP_EXIT_MULT,
            value=None,
            format="%.1f",
            help=SharedTexts.HELP_EXIT_MULT,
            key=f"{key_prefix}_exit_mult"
        )

def widget_terminal_value_rim(formula_latex: str, key_prefix: str) -> None:
    """Renders RIM specific terminal value (Persistence)."""
    st.markdown(SharedTexts.SEC_4_TERMINAL)
    st.latex(formula_latex)
    st.number_input(
        SharedTexts.INP_OMEGA,
        min_value=0.0,
        max_value=1.0,
        value=None,
        help=SharedTexts.HELP_OMEGA,
        key=f"{key_prefix}_omega"
    )

# ==============================================================================
# 4. EQUITY BRIDGE (Section 5)
# ==============================================================================

def widget_equity_bridge(formula_latex: str, mode: ValuationMethodology) -> None:
    """Renders balance sheet adjustments section."""
    prefix = f"bridge_{mode.name}"
    st.markdown(SharedTexts.SEC_5_BRIDGE)
    st.info(SharedTexts.SEC_5_DESC)
    st.latex(formula_latex)

    if mode.is_direct_equity:
        st.number_input(SharedTexts.INP_SHARES, value=None, format="%.0f", help=SharedTexts.HELP_SHARES, key=f"{prefix}_shares")
    else:
        c1, c2 = st.columns(2)
        c1.number_input(SharedTexts.INP_DEBT, value=None, format="%.0f", help=SharedTexts.HELP_DEBT, key=f"{prefix}_debt")
        c2.number_input(SharedTexts.INP_CASH, value=None, format="%.0f", help=SharedTexts.HELP_CASH, key=f"{prefix}_cash")

        c3, c4, c5 = st.columns(3)
        c3.number_input(SharedTexts.INP_MINORITIES, value=None, format="%.0f", key=f"{prefix}_min")
        c4.number_input(SharedTexts.INP_PENSIONS, value=None, format="%.0f", key=f"{prefix}_pen")
        c5.number_input(SharedTexts.INP_SHARES, value=None, format="%.0f", help=SharedTexts.HELP_SHARES, key=f"{prefix}_shares")

    st.number_input(
        SharedTexts.INP_SBC_DILUTION,
        value=None,
        format="%.2f",
        help=SharedTexts.HELP_SBC_DILUTION,
        key=f"{prefix}_sbc_rate"
    )

# ==============================================================================
# 5. OPTIONAL EXTENSIONS (Sections 6-11)
# ==============================================================================

def widget_sensitivity(
    key_prefix: str = "sens",
    default_step: float = 0.005
) -> None:
    """
    Renders the sensitivity analysis settings (WACC vs g).
    Corresponds to Section 11 in SharedTexts.
    """
    # STRICT ACCESS: No strings allowed here. All texts must be in expert.py/SharedTexts
    st.markdown(SharedTexts.SEC_11_SENSITIVITY)

    if st.toggle(SharedTexts.LBL_SENSITIVITY_ENABLE, value=False, key=f"{key_prefix}_enable"):
        st.info(SharedTexts.MSG_SENSITIVITY_DESC)

        c1, c2 = st.columns(2)
        c1.number_input(
            SharedTexts.LBL_SENS_STEP,
            value=default_step,
            format="%.3f",
            help=SharedTexts.HELP_SENS_STEP,
            key=f"{key_prefix}_step"
        )
        c2.number_input(
            SharedTexts.LBL_SENS_RANGE,
            value=2,
            min_value=1,
            max_value=5,
            help=SharedTexts.HELP_SENS_RANGE,
            key=f"{key_prefix}_range"
        )

def widget_monte_carlo(
    mode: ValuationMethodology,
    terminal_method: Optional[TerminalValueMethod],
    custom_vols: Optional[Dict[str, str]] = None
) -> None:
    """Renders Monte Carlo simulation parameters."""
    prefix = "mc"
    st.markdown(SharedTexts.SEC_6_MC)

    if not st.toggle(SharedTexts.MC_CALIBRATION, value=False, help=SharedTexts.HELP_MC_ENABLE, key=f"{prefix}_enable"):
        return

    st.select_slider(
        SharedTexts.MC_ITERATIONS,
        options=[1000, 5000, 10000, 25000],
        value=5000,
        help=SharedTexts.HELP_MC_SIMS,
        key=f"{prefix}_sims"
    )

    col1, col2 = st.columns(2)
    # Dynamic Labels from BaseTerminal
    label_flow = custom_vols.get("base_flow_volatility", SharedTexts.MC_VOL_BASE_FLOW) if custom_vols else SharedTexts.MC_VOL_BASE_FLOW

    col1.number_input(label_flow, value=None, format="%.2f", help=SharedTexts.HELP_MC_VOL_FLOW, key=f"{prefix}_vol_flow")
    col1.number_input(SharedTexts.MC_VOL_G, value=None, format="%.2f", help=SharedTexts.HELP_MC_VOL_G, key=f"{prefix}_vol_growth")

    if mode != ValuationMethodology.GRAHAM:
        col2.number_input(SharedTexts.MC_VOL_BETA, value=None, format="%.2f", help=SharedTexts.HELP_MC_VOL_BETA, key=f"{prefix}_vol_beta")

    if terminal_method == TerminalValueMethod.EXIT_MULTIPLE:
        col2.number_input(SharedTexts.LBL_VOL_EXIT_M, value=None, format="%.2f", key=f"{prefix}_vol_exit_m")
    elif terminal_method == TerminalValueMethod.GORDON_GROWTH:
        # STRICT ACCESS: LBL_VOL_GN must exist in SharedTexts
        col2.number_input(SharedTexts.LBL_VOL_GN, value=None, format="%.2f", help=SharedTexts.HELP_MC_VOL_GN, key=f"{prefix}_vol_gn")

def widget_backtest() -> None:
    """Renders historical backtest activation."""
    st.markdown(SharedTexts.SEC_10_BACKTEST)
    if st.toggle(SharedTexts.LBL_BACKTEST_ENABLE, value=False, help=SharedTexts.HELP_BACKTEST_ENABLE, key="bt_enable"):
        st.number_input(SharedTexts.LBL_LOOKBACK, min_value=1, max_value=10, value=3, key="bt_lookback")

def widget_peer_triangulation() -> None:
    """Renders peer selection for relative valuation."""
    st.markdown(SharedTexts.SEC_7_PEERS)
    if st.toggle(SharedTexts.LBL_PEER_ENABLE, value=False, help=SharedTexts.HELP_PEER_TRIANGULATION, key="peer_peer_enable"):
        raw_input = st.text_input(SharedTexts.INP_MANUAL_PEERS, placeholder=SharedTexts.PLACEHOLDER_PEERS, help=SharedTexts.HELP_MANUAL_PEERS, key="peer_input")
        # Processed into a list for the Binder
        if raw_input:
            st.session_state["peer_list"] = [t.strip().upper() for t in raw_input.split(",") if t.strip()]

def widget_scenarios(mode: ValuationMethodology) -> None:
    """Renders probabilistic scenario variants."""
    st.markdown(SharedTexts.SEC_8_SCENARIOS)
    if not st.toggle(SharedTexts.INP_SCENARIO_ENABLE, value=False, help=SharedTexts.HELP_SCENARIO_ENABLE, key="scenario_scenario_enable"):
        return

    for case in ["bull", "base", "bear"]:
        st.markdown(f"**{case.upper()}**")
        c1, c2, c3 = st.columns(3)
        c1.number_input(SharedTexts.INP_SCENARIO_PROBA, value=33.3, key=f"scenario_p_{case}")
        c2.number_input(SharedTexts.INP_SCENARIO_GROWTH, value=None, key=f"scenario_g_{case}")
        if mode == ValuationMethodology.FCFF_GROWTH:
            c3.number_input(SharedTexts.INP_SCENARIO_MARGIN, value=None, key=f"scenario_m_{case}")

def widget_sotp() -> None:
    """Renders Sum-of-the-Parts segment editor."""
    st.markdown(SharedTexts.SEC_9_SOTP)
    if st.toggle(SharedTexts.LBL_SOTP_ENABLE, value=False, help=SharedTexts.HELP_SOTP, key="sotp_enable"):
        st.data_editor(
            pd.DataFrame([{"name": SharedTexts.DEFAULT_SEGMENT_NAME, "value": 0.0, "method": "DCF"}]),
            num_rows="dynamic",
            key="sotp_editor",
            column_config={
                "name": st.column_config.TextColumn(SharedTexts.LBL_SEGMENT_NAME),
                "value": st.column_config.NumberColumn(SharedTexts.LBL_SEGMENT_VALUE, format="$%.2f"),
                "method": st.column_config.SelectboxColumn(
                    SharedTexts.LBL_SEGMENT_METHOD,
                    options=["DCF", "Multiple", "Net Asset"], # Technical keys can remain strings
                    required=True
                )
            }
        )
        st.slider(SharedTexts.LBL_DISCOUNT, 0, 50, 0, key="sotp_discount")