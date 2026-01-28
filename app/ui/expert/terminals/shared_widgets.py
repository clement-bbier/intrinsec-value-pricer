"""
app/ui/expert_terminals/shared_widgets.py

SHARED WIDGETS — Reusable UI components across expert terminals.

Pattern: Single Responsibility (SOLID)
Style: Numpy docstrings

Naming Conventions:
    - widget_* : Interactive widgets (return user data)
    - build_* : Constructors (transform data into domain objects)
    - display_* : Pure display (no return, side-effects only)

Note: These widgets reproduce the legacy functionalities (ui_inputs_expert.py)
       while improving structure and readability.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

import streamlit as st
import pandas as pd

from src.models import (
    DCFParameters,
    ValuationMode,
    TerminalValueMethod,
    ScenarioParameters,
    ScenarioVariant,
    BusinessUnit,
    SOTPMethod,
)
from src.i18n import SharedTexts
from src.config.settings import SIMULATION_CONFIG, VALUATION_CONFIG
from src.config.constants import UIWidgetDefaults

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. BASE INPUT WIDGETS (Sections 1-2)
# ==============================================================================

def widget_projection_years(
    default: int = UIWidgetDefaults.DEFAULT_PROJECTION_YEARS,
    min_years: int = UIWidgetDefaults.MIN_PROJECTION_YEARS,
    max_years: int = UIWidgetDefaults.MAX_PROJECTION_YEARS,
    key_prefix: Optional[str] = None
) -> int:
    """
    Displays a slider to select the projection horizon.

    Uses boundaries defined in central configuration to ensure DCF model consistency.

    Parameters
    ----------
    default : int, optional
        Initial slider value (from UIWidgetDefaults).
    min_years : int, optional
        Lower bound for projection (from UIWidgetDefaults).
    max_years : int, optional
        Upper bound for projection (from UIWidgetDefaults).
    key_prefix : str, optional
        Unique prefix for the Streamlit key (e.g., "FCFF_STANDARD").

    Returns
    -------
    int
        The selected number of projection years (t).
    """
    # Key sanitization for st.session_state
    prefix = key_prefix or "projection"

    return st.slider(
        label=SharedTexts.INP_PROJ_YEARS,
        min_value=min_years,
        max_value=max_years,
        value=default,
        step=1,
        help=SharedTexts.HELP_PROJ_YEARS,
        key=f"{prefix}_years"
    )


def widget_growth_rate(
    label: str = None,
    min_val: float = UIWidgetDefaults.MIN_GROWTH_RATE,
    max_val: float = UIWidgetDefaults.MAX_GROWTH_RATE,
    default: Optional[float] = None,
    key_prefix: Optional[str] = None
) -> Optional[float]:
    """
    Widget to input a growth rate.

    Parameters
    ----------
    label : str, optional
        Field label.
    min_val : float, optional
        Minimum value.
    max_val : float, optional
        Maximum value.
    default : float, optional
        Default value (None = Yahoo Auto).
    key_prefix : str, optional
        Prefix for Streamlit keys (default: "growth").

    Returns
    -------
    Optional[float]
        Selected growth rate or None if empty.
    """
    # Generate key if not provided
    if key_prefix is None:
        key_prefix = "growth"

    return st.number_input(
        label or SharedTexts.INP_GROWTH_G,
        min_value=min_val,
        max_value=max_val,
        value=default,
        step=0.1,
        format="%.2f",
        key=f"{key_prefix}_growth_rate",
        help=SharedTexts.HELP_GROWTH_RATE
    )


# ==============================================================================
# 2. COST OF CAPITAL WIDGET (Section 3)
# ==============================================================================

def widget_cost_of_capital(mode: ValuationMode, key_prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Inputs for discount parameters (WACC or Ke).

    Delegates the header rendering to the base class to avoid visual duplication.
    Dynamically displays the LaTeX formula adapted to the valuation mode.
    """
    prefix = key_prefix or mode.name

    # Dynamic theoretical formula based on methodology
    st.latex(SharedTexts.FORMULA_CAPITAL_KE if mode.is_direct_equity else SharedTexts.FORMULA_CAPITAL_WACC)

    # Reference price for weight calculation
    manual_price = st.number_input(
        SharedTexts.INP_PRICE_WEIGHTS, 0.0, UIWidgetDefaults.MAX_MANUAL_PRICE, None, 0.01, "%.2f",
        help=SharedTexts.HELP_PRICE_WEIGHTS, key=f"{prefix}_price"
    )

    col_a, col_b = st.columns(2)
    rf = col_a.number_input(SharedTexts.INP_RF, 0.0, UIWidgetDefaults.MAX_DISCOUNT_RATE, None, 0.1, "%.2f",
                            SharedTexts.HELP_RF, f"{prefix}_rf")
    beta = col_b.number_input(SharedTexts.INP_BETA, 0.0, UIWidgetDefaults.MAX_BETA, None, 0.01, "%.2f",
                              SharedTexts.HELP_BETA, f"{prefix}_beta")
    mrp = col_a.number_input(SharedTexts.INP_MRP, 0.0, UIWidgetDefaults.MAX_DISCOUNT_RATE, None, 0.1, "%.2f",
                             SharedTexts.HELP_MRP, f"{prefix}_mrp")

    data = {"risk_free_rate": rf, "manual_beta": beta, "market_risk_premium": mrp, "manual_stock_price": manual_price}

    if not mode.is_direct_equity:
        kd = col_b.number_input(SharedTexts.INP_KD, 0.0, UIWidgetDefaults.MAX_COST_OF_DEBT, None, 0.1, "%.2f",
                                SharedTexts.HELP_KD, f"{prefix}_kd")
        tau = col_a.number_input(SharedTexts.INP_TAX, 0.0, UIWidgetDefaults.MAX_TAX_RATE, None, 0.1, "%.2f",
                                 SharedTexts.HELP_TAX, f"{prefix}_tax")
        data.update({"cost_of_debt": kd, "tax_rate": tau})

    st.divider()
    return data

# ==============================================================================
# 3. TERMINAL VALUE WIDGET (Section 4)
# ==============================================================================

@st.fragment
def widget_terminal_value_dcf(key_prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Widget Step 4: Selection and calibration of Terminal Value (TV).

    Displays the LaTeX formula centrally under the description,
    dynamically updated based on the selected method.

    Parameters
    ----------
    key_prefix : str, optional
        Prefix for st.session_state keys, defaults to "terminal".

    Returns
    -------
    Dict[str, Any]
        TV parameters: method, growth rate, or multiple.
    """
    prefix = key_prefix or "terminal"

    # 1. Section Header
    st.markdown(SharedTexts.SEC_4_TERMINAL)
    st.info(SharedTexts.SEC_4_DESC)

    # 2. Method selection (Radio)
    method = st.radio(
        SharedTexts.RADIO_TV_METHOD,
        options=[TerminalValueMethod.GORDON_GROWTH, TerminalValueMethod.EXIT_MULTIPLE],
        format_func=lambda x: (
            SharedTexts.TV_GORDON if x == TerminalValueMethod.GORDON_GROWTH
            else SharedTexts.TV_EXIT
        ),
        horizontal=True,
        key=f"{prefix}_method"
    )

    # 3. Centered dynamic formula
    if method == TerminalValueMethod.GORDON_GROWTH:
        st.latex(SharedTexts.FORMULA_TV_GORDON)
    else:
        st.latex(SharedTexts.FORMULA_TV_EXIT)

    # 4. Data input
    col_inp, _ = st.columns(2)

    if method == TerminalValueMethod.GORDON_GROWTH:
        gn = col_inp.number_input(
            SharedTexts.INP_PERP_G,
            min_value=0.0, max_value=UIWidgetDefaults.MAX_TERMINAL_GROWTH,
            value=None, step=0.1, format="%.2f",
            help=SharedTexts.HELP_PERP_G,
            key=f"{prefix}_gn"
        )
        st.divider()
        return {"terminal_method": method, "perpetual_growth_rate": gn}
    else:
        exit_m = col_inp.number_input(
            SharedTexts.INP_EXIT_MULT,
            min_value=0.0, max_value=100.0,
            value=None, format="%.1f",
            help=SharedTexts.HELP_EXIT_MULT,
            key=f"{prefix}_exit_mult"
        )
        st.divider()
        return {"terminal_method": method, "exit_multiple_value": exit_m}


def widget_terminal_value_rim(formula_latex: str, key_prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Widget for RIM model terminal value (persistence factor).

    RIM uses an omega (ω) factor representing the persistence of
    abnormal profits beyond the explicit horizon.

    Parameters
    ----------
    formula_latex : str
        LaTeX formula for RIM terminal value.
    key_prefix : str, optional
        Prefix for Streamlit keys (default: "terminal").

    Returns
    -------
    Dict[str, Any]
        - terminal_method: EXIT_MULTIPLE (RIM convention)
        - exit_multiple_value: omega factor
    """
    if key_prefix is None:
        key_prefix = "terminal"

    st.markdown(SharedTexts.SEC_4_TERMINAL)
    st.latex(formula_latex)

    col1, _ = st.columns(2)
    omega = col1.number_input(
        SharedTexts.INP_OMEGA,
        min_value=0.0,
        max_value=1.0,
        value=None,
        format="%.2f",
        help=SharedTexts.HELP_OMEGA,
        key=f"{key_prefix}_omega"
    )
    logger.debug("RIM terminal value: omega=%s", omega)
    st.divider()

    return {
        "terminal_method": TerminalValueMethod.EXIT_MULTIPLE,
        "exit_multiple_value": omega
    }


# ==============================================================================
# 4. EQUITY BRIDGE WIDGET (Section 5) Pitchbook Design
# ==============================================================================

@st.fragment
def widget_equity_bridge(
        formula_latex: str,
        mode: ValuationMode,
        key_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified Equity Bridge with normalized percentage inputs for SBC.
    """
    prefix = key_prefix or f"bridge_{mode.value}"

    st.markdown(SharedTexts.SEC_5_BRIDGE)
    st.info(SharedTexts.SEC_5_DESC)
    st.latex(formula_latex)

    if mode.is_direct_equity:
        shares = st.number_input(SharedTexts.INP_SHARES, value=None, format="%.0f", help=SharedTexts.HELP_SHARES,
                                 key=f"{prefix}_shares_direct")
        sbc_rate = st.number_input(SharedTexts.INP_SBC_DILUTION, 0.0, 100.0, None, 0.1, format="%.2f",
                                   key=f"{prefix}_sbc_rate")
        return {"manual_shares_outstanding": shares, "stock_based_compensation_rate": sbc_rate}

    # Enterprise Value Layout (FCFF)
    c_d, c_c = st.columns(2)
    debt = c_d.number_input(SharedTexts.INP_DEBT, value=None, format="%.0f", key=f"{prefix}_debt")
    cash = c_c.number_input(SharedTexts.INP_CASH, value=None, format="%.0f", key=f"{prefix}_cash")

    c_m, c_p, c_s = st.columns(3)
    minorities = c_m.number_input(SharedTexts.INP_MINORITIES, value=None, format="%.0f", key=f"{prefix}_min")
    pensions = c_p.number_input(SharedTexts.INP_PENSIONS, value=None, format="%.0f", key=f"{prefix}_pen")
    shares = c_s.number_input(SharedTexts.INP_SHARES, value=None, format="%.0f", key=f"{prefix}_shares")

    sbc_rate = st.number_input(SharedTexts.INP_SBC_DILUTION, 0.0, 100.0, None, 0.1, format="%.2f",
                               key=f"{prefix}_sbc_rate")

    return {
        "manual_total_debt": debt, "manual_cash": cash,
        "manual_shares_outstanding": shares, "manual_minority_interests": minorities,
        "manual_pension_provisions": pensions, "stock_based_compensation_rate": sbc_rate
    }

# ==============================================================================
# 5. MONTE CARLO WIDGET (Section 6 - Optional)
# ==============================================================================

def widget_monte_carlo(
    mode: ValuationMode,
    terminal_method: Optional[TerminalValueMethod] = None,
    custom_vols: Optional[Dict[str, str]] = None,
    key_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stochastic calibration widget (Monte Carlo) with dynamic i18n injection.

    Uses 'custom_vols' to override default labels if provided,
    otherwise selects the label based on 'mode' (EPS, NI, FCF).
    """
    prefix = key_prefix or "mc"

    # 1. HEADER AND DESCRIPTION (i18n)
    st.markdown(SharedTexts.SEC_6_MC)
    st.info(SharedTexts.SEC_6_DESC_MC)

    # 2. ACTIVATION TOGGLE
    enable = st.toggle(SharedTexts.MC_CALIBRATION, value=False, key=f"{prefix}_enable")
    if not enable:
        return {"enable_monte_carlo": False}

    # 3. SIMULATION DEPTH
    sims = st.select_slider(
        SharedTexts.MC_ITERATIONS,
        options=[1000, 5000, 10000, 20000],
        value=5000,
        key=f"{prefix}_sims"
    )
    st.caption(SharedTexts.MC_VOL_INCERTITUDE)

    # 4. INPUT GRID (Institutional double column)
    v_col1, v_col2 = st.columns(2)

    # --- LABEL LOGIC WITH OVERRIDE ---
    if custom_vols and "base_flow_volatility" in custom_vols:
        label_base = custom_vols["base_flow_volatility"]
    elif mode == ValuationMode.GRAHAM:
        label_base = SharedTexts.MC_VOL_EPS
    elif mode == ValuationMode.RIM:
        label_base = SharedTexts.MC_VOL_NI
    elif mode == ValuationMode.DDM:
        label_base = SharedTexts.MC_VOL_DIV
    else:
        label_base = SharedTexts.MC_VOL_BASE_FLOW

    # 5. COLUMN 1: OPERATIONAL VOLATILITIES
    v_base = v_col1.number_input(
        label_base,
        min_value=0.0, max_value=0.5,
        value=None, format="%.3f",
        key=f"{prefix}_vol_flow",
        help=SharedTexts.HELP_VOL_BASE
    )

    # Growth label (g or ω) - Also overridable
    if custom_vols and "growth_volatility" in custom_vols:
        label_growth = custom_vols["growth_volatility"]
    else:
        label_growth = SharedTexts.LBL_VOL_OMEGA if mode == ValuationMode.RIM else SharedTexts.MC_VOL_G

    v_growth = v_col1.number_input(
        label_growth,
        min_value=0.0, max_value=0.2,
        value=None, format="%.3f",
        key=f"{prefix}_vol_growth"
    )

    # 6. COLUMN 2: MARKET & EXIT RISKS
    v_beta = None
    if mode != ValuationMode.GRAHAM:
        v_beta = v_col2.number_input(
            SharedTexts.MC_VOL_BETA,
            min_value=0.0, max_value=1.0,
            value=None, format="%.3f",
            key=f"{prefix}_vol_beta"
        )

    v_exit_m = None
    if terminal_method == TerminalValueMethod.EXIT_MULTIPLE:
        v_exit_m = v_col2.number_input(
            SharedTexts.LBL_VOL_EXIT_M,
            min_value=0.0, max_value=0.4,
            value=None, format="%.3f",
            key=f"{prefix}_vol_exit_m"
        )

    return {
        "enable_monte_carlo": True,
        "num_simulations": sims,
        "base_flow_volatility": v_base,
        "beta_volatility": v_beta,
        "growth_volatility": v_growth,
        "exit_multiple_volatility": v_exit_m
    }

# ==============================================================================
# 6. PEER TRIANGULATION WIDGET (Section 7 - Optional)
# ==============================================================================

def widget_peer_triangulation(key_prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Flat widget for the peer group cohort.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing activation state and ticker list.
    """
    if key_prefix is None:
        key_prefix = "peer"

    st.markdown(SharedTexts.SEC_7_PEERS)
    st.info(SharedTexts.SEC_7_DESC_PEERS)

    enable = st.toggle(
        SharedTexts.LBL_PEER_ENABLE,
        value=False,
        help=SharedTexts.HELP_PEER_TRIANGULATION,
        key=f"{key_prefix}_peer_enable"
    )

    if not enable:
        return {"enable_peer_multiples": False, "manual_peers": None}

    raw_input = st.text_input(
        SharedTexts.INP_MANUAL_PEERS,
        placeholder=SharedTexts.PLACEHOLDER_PEERS,
        help=SharedTexts.HELP_MANUAL_PEERS,
        key=f"{key_prefix}_input"
    )

    peers_list = None
    if raw_input and raw_input.strip():
        peers_list = [t.strip().upper() for t in raw_input.split(",") if t.strip()]
        if peers_list:
            st.caption(SharedTexts.PEERS_SELECTED.format(peers=', '.join(peers_list)))

    return {
        "enable_peer_multiples": True,
        "manual_peers": peers_list,
    }


# ==============================================================================
# 7. SCENARIOS WIDGET (Section 8 - Optional)
# ==============================================================================

def widget_scenarios(mode: ValuationMode, key_prefix: Optional[str] = None) -> ScenarioParameters:
    """
    Multi-variant operational scenarios (Bull/Base/Bear).
    """
    prefix = key_prefix or "scenario"
    st.markdown(SharedTexts.SEC_8_SCENARIOS)
    st.info(SharedTexts.SEC_8_DESC_SCENARIOS)

    if not st.toggle(SharedTexts.INP_SCENARIO_ENABLE, False, key=f"{prefix}_enable"):
        return ScenarioParameters(enabled=False)

    show_margin = (mode == ValuationMode.FCFF_GROWTH)

    def _render_variant(label: str, case_id: str, default_p: float):
        st.markdown(f"**{label}**")
        c1, c2, c3 = st.columns(3)
        p = c1.number_input(SharedTexts.INP_SCENARIO_PROBA, 0.0, 100.0, default_p, 5.0, key=f"{prefix}_p_{case_id}") / 100.0
        g = c2.number_input(SharedTexts.INP_SCENARIO_GROWTH, -100.0, 500.0, value=None, format="%.2f", key=f"{prefix}_g_{case_id}")
        m = c3.number_input(SharedTexts.INP_SCENARIO_MARGIN, 0.0, 100.0, value=None, format="%.2f", key=f"{prefix}_m_{case_id}") if show_margin else None
        return p, g, m

    p_bull, g_bull, m_bull = _render_variant(SharedTexts.LABEL_SCENARIO_BULL, "bull", 25.0)
    p_base, g_base, m_base = _render_variant(SharedTexts.LABEL_SCENARIO_BASE, "base", 50.0)
    p_bear, g_bear, m_bear = _render_variant(SharedTexts.LABEL_SCENARIO_BEAR, "bear", 25.0)

    if round(p_bull + p_base + p_bear, 2) != 1.0:
        st.error(SharedTexts.ERR_SCENARIO_PROBA_SUM.format(sum=int((p_bull+p_base+p_bear)*100)))
        return ScenarioParameters(enabled=False)

    return ScenarioParameters(
        enabled=True,
        bull=ScenarioVariant(label=SharedTexts.LBL_BULL, probability=p_bull, growth_rate=g_bull, target_fcf_margin=m_bull),
        base=ScenarioVariant(label=SharedTexts.LBL_BASE, probability=p_base, growth_rate=g_base, target_fcf_margin=m_base),
        bear=ScenarioVariant(label=SharedTexts.LBL_BEAR, probability=p_bear, growth_rate=g_bear, target_fcf_margin=m_bear)
    )

# ==============================================================================
# 8. SOTP WIDGET (Sum-of-the-Parts - Optional)
# ==============================================================================

def widget_sotp(params: DCFParameters, is_conglomerate: bool = False, key_prefix: Optional[str] = None) -> None:
    """
    Step 9 Widget: SOTP Segmentation with relevance arbitrage (ST-4.2).

    Allows splitting total value across different Business Units.
    Includes a relevance test to limit SOTP usage to diversified structures
    or specific breakdown needs.

    Parameters
    ----------
    params : DCFParameters
        Parameter object to be populated for the calculation engine.
    is_conglomerate : bool, optional
        Indicates if the firm is identified as a conglomerate (default: False).
    key_prefix : str, optional
        Prefix to ensure key uniqueness in session_state.
    """
    prefix = key_prefix or "sotp"

    # --- HEADER AND DESCRIPTION ---
    st.markdown(SharedTexts.SEC_9_SOTP)
    st.info(SharedTexts.SEC_9_DESC)

    # --- RELEVANCE ARBITRAGE ---
    # Display a preventive warning if the firm is not a conglomerate
    if not is_conglomerate:
        st.warning(SharedTexts.WARN_SOTP_RELEVANCE)

    # --- MODULE ACTIVATION ---
    enabled = st.toggle(
        SharedTexts.LBL_SOTP_ENABLE,
        value=params.sotp.enabled,
        key=f"{prefix}_enable",
        help=SharedTexts.HELP_SOTP_ENABLE
    )
    params.sotp.enabled = enabled

    if not enabled:
        return

    # --- SEGMENT TABLE CONFIGURATION ---
    # Initialize with float64 typing to prevent pandas FutureWarnings
    df_init = pd.DataFrame([{
        SharedTexts.LBL_SEGMENT_NAME: SharedTexts.DEFAULT_SEGMENT_NAME,
        SharedTexts.LBL_SEGMENT_VALUE: 0.0,
        SharedTexts.LBL_SEGMENT_METHOD: SOTPMethod.DCF.value
    }]).astype({SharedTexts.LBL_SEGMENT_VALUE: 'float64'})

    # Dynamic data editor (Pitchbook style)
    edited_df = st.data_editor(
        df_init,
        num_rows="dynamic",
        width='stretch',
        key=f"{prefix}_editor"
    )

    # --- EXTRACTION AND PYDANTIC VALIDATION ---
    # Named arguments used for BusinessUnit compatibility
    params.sotp.segments = [
        BusinessUnit(
            name=row[SharedTexts.LBL_SEGMENT_NAME],
            enterprise_value=row[SharedTexts.LBL_SEGMENT_VALUE],
            method=SOTPMethod(row[SharedTexts.LBL_SEGMENT_METHOD])
        )
        for _, row in edited_df.iterrows() if row[SharedTexts.LBL_SEGMENT_NAME]
    ]

    # --- HOLDING ADJUSTMENTS ---
    st.markdown(SharedTexts.SEC_SOTP_ADJUSTMENTS)

    # Calculate initial percentage value for the slider
    current_discount = int(params.sotp.conglomerate_discount * 100)

    params.sotp.conglomerate_discount = st.slider(
        SharedTexts.LBL_DISCOUNT,
        min_value=0,
        max_value=50,
        value=current_discount,
        step=5,
        key=f"{prefix}_discount"
    ) / 100.0

# ==============================================================================
# 9. PARAMETERS CONSTRUCTOR
# ==============================================================================

def build_dcf_parameters(collected_data: Dict[str, Any]) -> DCFParameters:
    """Final constructor with validated constants."""
    defaults = {
        "projection_years": VALUATION_CONFIG.default_projection_years,
        "terminal_method": TerminalValueMethod.GORDON_GROWTH,
        "enable_monte_carlo": False,
        "num_simulations": SIMULATION_CONFIG.default_simulations,
        "base_flow_volatility": UIWidgetDefaults.DEFAULT_BASE_FLOW_VOLATILITY,
        "beta_volatility": SIMULATION_CONFIG.default_volatility_beta,
        "growth_volatility": SIMULATION_CONFIG.default_volatility_growth,
    }
    merged = {**defaults, **{k: v for k, v in collected_data.items() if v is not None}}
    return DCFParameters.from_legacy(merged)