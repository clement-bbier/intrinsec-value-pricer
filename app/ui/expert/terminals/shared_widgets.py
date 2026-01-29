"""
app/ui/expert/terminals/shared_widgets.py

SHARED WIDGETS — Reusable UI components across expert terminals.

Pattern: Single Responsibility (SOLID)
Style: Numpy docstrings

Naming Conventions:
    - widget_* : Interactive widgets (return user data)
    - build_* : Constructors (transform data into domain objects)
    - display_* : Pure display (no return, side-effects only)

Architecture Note:
    All percentage values are returned AS-IS from widgets.
    Normalization (% to decimal) is handled by Pydantic validators
    in the model layer (DCFParameters._normalize_rate).
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

    Parameters
    ----------
    default : int, optional
        Initial slider value.
    min_years : int, optional
        Lower bound for projection.
    max_years : int, optional
        Upper bound for projection.
    key_prefix : str, optional
        Unique prefix for the Streamlit key.

    Returns
    -------
    int
        The selected number of projection years.
    """
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
    label: Optional[str] = None,
    min_val: float = UIWidgetDefaults.MIN_GROWTH_RATE,
    max_val: float = UIWidgetDefaults.MAX_GROWTH_RATE,
    default: Optional[float] = None,
    key_prefix: Optional[str] = None
) -> Optional[float]:
    """
    Widget to input a growth rate as percentage.

    Parameters
    ----------
    label : str, optional
        Field label.
    min_val : float, optional
        Minimum value (percentage).
    max_val : float, optional
        Maximum value (percentage).
    default : float, optional
        Default value (None = auto from provider).
    key_prefix : str, optional
        Prefix for Streamlit keys.

    Returns
    -------
    Optional[float]
        Selected growth rate as percentage (e.g., 5.0 for 5%).
        Pydantic handles conversion to decimal.
    """
    prefix = key_prefix or "growth"

    return st.number_input(
        label or SharedTexts.INP_GROWTH_G,
        min_value=min_val,
        max_value=max_val,
        value=default,
        step=0.1,
        format="%.2f",
        key=f"{prefix}_growth_rate",
        help=SharedTexts.HELP_GROWTH_RATE
    )


# ==============================================================================
# 2. COST OF CAPITAL WIDGET (Section 3)
# ==============================================================================

def widget_cost_of_capital(
    mode: ValuationMode,
    key_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Inputs for discount parameters (WACC or Ke).

    All rate values are returned as percentages (e.g., 4.2 for 4.2%).
    Pydantic handles normalization to decimals.

    Parameters
    ----------
    mode : ValuationMode
        Current valuation mode (determines WACC vs Ke display).
    key_prefix : str, optional
        Prefix for session state keys.

    Returns
    -------
    Dict[str, Any]
        Raw percentage values for rates, absolute values for beta/price.
    """
    prefix = key_prefix or mode.name

    # Dynamic formula based on methodology
    if mode.is_direct_equity:
        st.latex(SharedTexts.FORMULA_CAPITAL_KE)
    else:
        st.latex(SharedTexts.FORMULA_CAPITAL_WACC)

    # Reference price for weight calculation (absolute value)
    manual_price = st.number_input(
        SharedTexts.INP_PRICE_WEIGHTS,
        min_value=0.0,
        max_value=UIWidgetDefaults.MAX_MANUAL_PRICE,
        value=None,
        step=0.01,
        format="%.2f",
        help=SharedTexts.HELP_PRICE_WEIGHTS,
        key=f"{prefix}_price"
    )

    col_a, col_b = st.columns(2)

    # Risk-free rate (percentage input)
    rf = col_a.number_input(
        SharedTexts.INP_RF,
        min_value=0.0,
        max_value=UIWidgetDefaults.MAX_DISCOUNT_RATE,
        value=None,
        step=0.1,
        format="%.2f",
        help=SharedTexts.HELP_RF,
        key=f"{prefix}_rf"
    )

    # Beta (absolute value, not a percentage)
    beta = col_b.number_input(
        SharedTexts.INP_BETA,
        min_value=0.0,
        max_value=UIWidgetDefaults.MAX_BETA,
        value=None,
        step=0.01,
        format="%.2f",
        help=SharedTexts.HELP_BETA,
        key=f"{prefix}_beta"
    )

    # Market Risk Premium (percentage input)
    mrp = col_a.number_input(
        SharedTexts.INP_MRP,
        min_value=0.0,
        max_value=UIWidgetDefaults.MAX_DISCOUNT_RATE,
        value=None,
        step=0.1,
        format="%.2f",
        help=SharedTexts.HELP_MRP,
        key=f"{prefix}_mrp"
    )

    data = {
        "risk_free_rate": rf,
        "manual_beta": beta,
        "market_risk_premium": mrp,
        "manual_stock_price": manual_price
    }

    # Additional fields for entity-level (WACC) models
    if not mode.is_direct_equity:
        kd = col_b.number_input(
            SharedTexts.INP_KD,
            min_value=0.0,
            max_value=UIWidgetDefaults.MAX_COST_OF_DEBT,
            value=None,
            step=0.1,
            format="%.2f",
            help=SharedTexts.HELP_KD,
            key=f"{prefix}_kd"
        )

        tau = col_a.number_input(
            SharedTexts.INP_TAX,
            min_value=0.0,
            max_value=UIWidgetDefaults.MAX_TAX_RATE,
            value=None,
            step=0.1,
            format="%.2f",
            help=SharedTexts.HELP_TAX,
            key=f"{prefix}_tax"
        )

        data["cost_of_debt"] = kd
        data["tax_rate"] = tau

    st.divider()
    return data


# ==============================================================================
# 3. TERMINAL VALUE WIDGET (Section 4)
# ==============================================================================

@st.fragment
def widget_terminal_value_dcf(key_prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Widget for Terminal Value selection and calibration.

    Parameters
    ----------
    key_prefix : str, optional
        Prefix for session state keys.

    Returns
    -------
    Dict[str, Any]
        Terminal value configuration with raw percentage values.
    """
    prefix = key_prefix or "terminal"

    st.markdown(SharedTexts.SEC_4_TERMINAL)
    st.info(SharedTexts.SEC_4_DESC)

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

    # Dynamic formula display
    if method == TerminalValueMethod.GORDON_GROWTH:
        st.latex(SharedTexts.FORMULA_TV_GORDON)
    else:
        st.latex(SharedTexts.FORMULA_TV_EXIT)

    col_inp, _ = st.columns(2)

    if method == TerminalValueMethod.GORDON_GROWTH:
        # Perpetual growth rate (percentage input)
        gn = col_inp.number_input(
            SharedTexts.INP_PERP_G,
            min_value=0.0,
            max_value=UIWidgetDefaults.MAX_TERMINAL_GROWTH,
            value=None,
            step=0.1,
            format="%.2f",
            help=SharedTexts.HELP_PERP_G,
            key=f"{prefix}_gn"
        )
        st.divider()
        return {"terminal_method": method, "perpetual_growth_rate": gn}
    else:
        # Exit multiple (absolute value)
        exit_m = col_inp.number_input(
            SharedTexts.INP_EXIT_MULT,
            min_value=0.0,
            max_value=100.0,
            value=None,
            format="%.1f",
            help=SharedTexts.HELP_EXIT_MULT,
            key=f"{prefix}_exit_mult"
        )
        st.divider()
        return {"terminal_method": method, "exit_multiple_value": exit_m}


def widget_terminal_value_rim(
    formula_latex: str,
    key_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Widget for RIM model terminal value (omega persistence factor).

    Parameters
    ----------
    formula_latex : str
        LaTeX formula for RIM terminal value.
    key_prefix : str, optional
        Prefix for Streamlit keys.

    Returns
    -------
    Dict[str, Any]
        Terminal configuration with omega factor (0-1 range, not percentage).
    """
    prefix = key_prefix or "terminal"

    st.markdown(SharedTexts.SEC_4_TERMINAL)
    st.latex(formula_latex)

    col1, _ = st.columns(2)

    # Omega is a coefficient (0-1), not a percentage
    omega = col1.number_input(
        SharedTexts.INP_OMEGA,
        min_value=0.0,
        max_value=1.0,
        value=None,
        format="%.2f",
        help=SharedTexts.HELP_OMEGA,
        key=f"{prefix}_omega"
    )

    logger.debug("RIM terminal value: omega=%s", omega)
    st.divider()

    return {
        "terminal_method": TerminalValueMethod.EXIT_MULTIPLE,
        "exit_multiple_value": omega
    }


# ==============================================================================
# 4. EQUITY BRIDGE WIDGET (Section 5)
# ==============================================================================

@st.fragment
def widget_equity_bridge(
    formula_latex: str,
    mode: ValuationMode,
    key_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified Equity Bridge widget.

    Parameters
    ----------
    formula_latex : str
        LaTeX formula for the equity bridge.
    mode : ValuationMode
        Current valuation mode.
    key_prefix : str, optional
        Prefix for session state keys.

    Returns
    -------
    Dict[str, Any]
        Bridge parameters with raw values.
        SBC rate is percentage, currency amounts are absolute.
    """
    prefix = key_prefix or f"bridge_{mode.value}"

    st.markdown(SharedTexts.SEC_5_BRIDGE)
    st.info(SharedTexts.SEC_5_DESC)
    st.latex(formula_latex)

    if mode.is_direct_equity:
        shares = st.number_input(
            SharedTexts.INP_SHARES,
            value=None,
            format="%.0f",
            help=SharedTexts.HELP_SHARES,
            key=f"{prefix}_shares_direct"
        )

        # SBC rate as percentage
        sbc_rate = st.number_input(
            SharedTexts.INP_SBC_DILUTION,
            min_value=0.0,
            max_value=100.0,
            value=None,
            step=0.1,
            format="%.2f",
            key=f"{prefix}_sbc_rate"
        )

        return {
            "manual_shares_outstanding": shares,
            "annual_dilution_rate": sbc_rate
        }

    # Enterprise Value Layout (FCFF models)
    c_d, c_c = st.columns(2)

    debt = c_d.number_input(
        SharedTexts.INP_DEBT,
        value=None,
        format="%.0f",
        key=f"{prefix}_debt"
    )

    cash = c_c.number_input(
        SharedTexts.INP_CASH,
        value=None,
        format="%.0f",
        key=f"{prefix}_cash"
    )

    c_m, c_p, c_s = st.columns(3)

    minorities = c_m.number_input(
        SharedTexts.INP_MINORITIES,
        value=None,
        format="%.0f",
        key=f"{prefix}_min"
    )

    pensions = c_p.number_input(
        SharedTexts.INP_PENSIONS,
        value=None,
        format="%.0f",
        key=f"{prefix}_pen"
    )

    shares = c_s.number_input(
        SharedTexts.INP_SHARES,
        value=None,
        format="%.0f",
        key=f"{prefix}_shares"
    )

    # SBC rate as percentage
    sbc_rate = st.number_input(
        SharedTexts.INP_SBC_DILUTION,
        min_value=-100.0,
        max_value=100.0,
        value=None,
        step=0.1,
        format="%.2f",
        key=f"{prefix}_sbc_rate"
    )

    return {
        "manual_total_debt": debt,
        "manual_cash": cash,
        "manual_shares_outstanding": shares,
        "manual_minority_interests": minorities,
        "manual_pension_provisions": pensions,
        "annual_dilution_rate": sbc_rate
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
    Stochastic calibration widget (Monte Carlo).

    Parameters
    ----------
    mode : ValuationMode
        Current valuation mode for label customization.
    terminal_method : TerminalValueMethod, optional
        Terminal value method for exit multiple volatility.
    custom_vols : Dict[str, str], optional
        Custom label overrides for volatility inputs.
    key_prefix : str, optional
        Prefix for session state keys.

    Returns
    -------
    Dict[str, Any]
        Monte Carlo configuration with volatility values as decimals (0-1).
    """
    prefix = key_prefix or "mc"

    st.markdown(SharedTexts.SEC_6_MC)
    st.info(SharedTexts.SEC_6_DESC_MC)

    enable = st.toggle(
        SharedTexts.MC_CALIBRATION,
        value=False,
        key=f"{prefix}_enable"
    )

    if not enable:
        return {"enable_monte_carlo": False}

    sims = st.select_slider(
        SharedTexts.MC_ITERATIONS,
        options=[1000, 2500, 5000, 10000, 15000, 20000, 25000],
        value=5000,
        key=f"{prefix}_sims"
    )

    st.caption(SharedTexts.MC_VOL_INCERTITUDE)

    v_col1, v_col2 = st.columns(2)

    # Determine base flow volatility label
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

    # Volatilities are input as percentage (5 for 5%)
    v_base = v_col1.number_input(
        label_base,
        min_value=0.0,
        max_value=100.0,
        value=None,
        format="%.2f",
        key=f"{prefix}_vol_flow",
        help=SharedTexts.HELP_VOL_BASE
    )

    # Growth volatility label
    if custom_vols and "growth_volatility" in custom_vols:
        label_growth = custom_vols["growth_volatility"]
    else:
        label_growth = (
            SharedTexts.LBL_VOL_OMEGA if mode == ValuationMode.RIM
            else SharedTexts.MC_VOL_G
        )

    v_growth = v_col1.number_input(
        label_growth,
        min_value=0.0,
        max_value=100.0,
        value=None,
        format="%.2f",
        key=f"{prefix}_vol_growth"
    )

    v_beta = None
    if mode != ValuationMode.GRAHAM:
        v_beta = v_col2.number_input(
            SharedTexts.MC_VOL_BETA,
            min_value=0.0,
            max_value=100.0,
            value=None,
            format="%.2f",
            key=f"{prefix}_vol_beta"
        )

    v_exit_m = None
    if terminal_method == TerminalValueMethod.EXIT_MULTIPLE:
        v_exit_m = v_col2.number_input(
            SharedTexts.LBL_VOL_EXIT_M,
            min_value=0.0,
            max_value=100.0,
            value=None,
            format="%.2f",
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


def widget_backtest(key_prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Widget for historical backtest activation.

    Parameters
    ----------
    key_prefix : str, optional
        Prefix for session state keys.

    Returns
    -------
    Dict[str, Any]
        Backtest configuration.
    """
    prefix = key_prefix or "bt"

    st.markdown(SharedTexts.SEC_10_BACKTEST)
    st.info(SharedTexts.SEC_10_DESC_BACKTEST)

    enable = st.toggle(
        SharedTexts.LBL_BACKTEST_ENABLE,
        value=False,
        key=f"{prefix}_enable",
        help=SharedTexts.HELP_BACKTEST_ENABLE
    )

    return {"enable_backtest": enable}


# ==============================================================================
# 6. PEER TRIANGULATION WIDGET (Section 7 - Optional)
# ==============================================================================

def widget_peer_triangulation(key_prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Widget for peer group cohort definition.

    Parameters
    ----------
    key_prefix : str, optional
        Prefix for session state keys.

    Returns
    -------
    Dict[str, Any]
        Peer triangulation configuration.
    """
    prefix = key_prefix or "peer"

    st.markdown(SharedTexts.SEC_7_PEERS)
    st.info(SharedTexts.SEC_7_DESC_PEERS)

    enable = st.toggle(
        SharedTexts.LBL_PEER_ENABLE,
        value=False,
        help=SharedTexts.HELP_PEER_TRIANGULATION,
        key=f"{prefix}_peer_enable"
    )

    if not enable:
        return {"enable_peer_multiples": False, "manual_peers": None}

    raw_input = st.text_input(
        SharedTexts.INP_MANUAL_PEERS,
        placeholder=SharedTexts.PLACEHOLDER_PEERS,
        help=SharedTexts.HELP_MANUAL_PEERS,
        key=f"{prefix}_input"
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

def widget_scenarios(
    mode: ValuationMode,
    key_prefix: Optional[str] = None
) -> ScenarioParameters:
    """
    Multi-variant operational scenarios (Bull/Base/Bear).

    Parameters
    ----------
    mode : ValuationMode
        Current valuation mode.
    key_prefix : str, optional
        Prefix for session state keys.

    Returns
    -------
    ScenarioParameters
        Scenario configuration with raw percentage values.
    """
    prefix = key_prefix or "scenario"

    st.markdown(SharedTexts.SEC_8_SCENARIOS)
    st.info(SharedTexts.SEC_8_DESC_SCENARIOS)

    if not st.toggle(SharedTexts.INP_SCENARIO_ENABLE, False, key=f"{prefix}_enable"):
        return ScenarioParameters(enabled=False)

    show_margin = (mode == ValuationMode.FCFF_GROWTH)

    def _render_variant(label: str, case_id: str, default_p: float):
        """Renders a single scenario variant row."""
        st.markdown(f"**{label}**")
        c1, c2, c3 = st.columns(3)

        # Probability as percentage (0-100), converted to 0-1
        p = c1.number_input(
            SharedTexts.INP_SCENARIO_PROBA,
            min_value=0.0,
            max_value=100.0,
            value=default_p,
            step=5.0,
            key=f"{prefix}_p_{case_id}"
        ) / 100.0

        # Growth rate as percentage (raw value)
        g = c2.number_input(
            SharedTexts.INP_SCENARIO_GROWTH,
            min_value=-100.0,
            max_value=500.0,
            value=None,
            format="%.2f",
            key=f"{prefix}_g_{case_id}"
        )

        # Margin as percentage (raw value) - only for FCFF_GROWTH
        m = None
        if show_margin:
            m = c3.number_input(
                SharedTexts.INP_SCENARIO_MARGIN,
                min_value=0.0,
                max_value=100.0,
                value=None,
                format="%.2f",
                key=f"{prefix}_m_{case_id}"
            )

        return p, g, m

    p_bull, g_bull, m_bull = _render_variant(SharedTexts.LABEL_SCENARIO_BULL, "bull", 25.0)
    p_base, g_base, m_base = _render_variant(SharedTexts.LABEL_SCENARIO_BASE, "base", 50.0)
    p_bear, g_bear, m_bear = _render_variant(SharedTexts.LABEL_SCENARIO_BEAR, "bear", 25.0)

    # Probability validation
    if round(p_bull + p_base + p_bear, 2) != 1.0:
        total_pct = int((p_bull + p_base + p_bear) * 100)
        st.error(SharedTexts.ERR_SCENARIO_PROBA_SUM.format(sum=total_pct))
        return ScenarioParameters(enabled=False)

    return ScenarioParameters(
        enabled=True,
        bull=ScenarioVariant(
            label=SharedTexts.LBL_BULL,
            probability=p_bull,
            growth_rate=g_bull,
            target_fcf_margin=m_bull
        ),
        base=ScenarioVariant(
            label=SharedTexts.LBL_BASE,
            probability=p_base,
            growth_rate=g_base,
            target_fcf_margin=m_base
        ),
        bear=ScenarioVariant(
            label=SharedTexts.LBL_BEAR,
            probability=p_bear,
            growth_rate=g_bear,
            target_fcf_margin=m_bear
        )
    )


# ==============================================================================
# 8. SOTP WIDGET (Sum-of-the-Parts - Optional)
# ==============================================================================

def widget_sotp(
    params: DCFParameters,
    is_conglomerate: bool = False,
    key_prefix: Optional[str] = None
) -> None:
    """
    SOTP Segmentation widget.

    Parameters
    ----------
    params : DCFParameters
        Parameter object to be populated.
    is_conglomerate : bool, optional
        Whether the firm is identified as a conglomerate.
    key_prefix : str, optional
        Prefix for session state keys.
    """
    prefix = key_prefix or "sotp"

    st.markdown(SharedTexts.SEC_9_SOTP)
    st.info(SharedTexts.SEC_9_DESC)

    if not is_conglomerate:
        st.warning(SharedTexts.WARN_SOTP_RELEVANCE)

    enabled = st.toggle(
        SharedTexts.LBL_SOTP_ENABLE,
        value=params.sotp.enabled,
        key=f"{prefix}_enable",
        help=SharedTexts.HELP_SOTP_ENABLE
    )
    params.sotp.enabled = enabled

    if not enabled:
        return

    # Segment table
    df_init = pd.DataFrame([{
        SharedTexts.LBL_SEGMENT_NAME: SharedTexts.DEFAULT_SEGMENT_NAME,
        SharedTexts.LBL_SEGMENT_VALUE: 0.0,
        SharedTexts.LBL_SEGMENT_METHOD: SOTPMethod.DCF.value
    }]).astype({SharedTexts.LBL_SEGMENT_VALUE: 'float64'})

    edited_df = st.data_editor(
        df_init,
        num_rows="dynamic",
        width="stretch",
        key=f"{prefix}_editor"
    )

    params.sotp.segments = [
        BusinessUnit(
            name=row[SharedTexts.LBL_SEGMENT_NAME],
            enterprise_value=row[SharedTexts.LBL_SEGMENT_VALUE],
            method=SOTPMethod(row[SharedTexts.LBL_SEGMENT_METHOD])
        )
        for _, row in edited_df.iterrows()
        if row[SharedTexts.LBL_SEGMENT_NAME]
    ]

    st.markdown(SharedTexts.SEC_SOTP_ADJUSTMENTS)

    val_init = int(params.sotp.conglomerate_discount * 100)

    # Discount as percentage, stored as decimal
    discount_pct= st.slider(
        SharedTexts.LBL_DISCOUNT,
        min_value=0,
        max_value=50,
        value=val_init,
        step=1.0,
        key=f"{prefix}_discount",
        help=SharedTexts.HELP_SOTP
    )

    params.sotp.conglomerate_discount = discount_pct / 100.0


# ==============================================================================
# 9. PARAMETERS CONSTRUCTOR
# ==============================================================================

def build_dcf_parameters(collected_data: Dict[str, Any]) -> DCFParameters:
    """
    Constructs DCFParameters from collected widget data.

    Parameters
    ----------
    collected_data : Dict[str, Any]
        Raw data from widgets. Percentage values are passed as-is;
        Pydantic validators handle normalization.

    Returns
    -------
    DCFParameters
        Validated parameter object with normalized values.
    """
    defaults = {
        "projection_years": VALUATION_CONFIG.default_projection_years,
        "terminal_method": TerminalValueMethod.GORDON_GROWTH,
        "enable_monte_carlo": False,
        "num_simulations": SIMULATION_CONFIG.default_simulations,
        "base_flow_volatility": UIWidgetDefaults.DEFAULT_BASE_FLOW_VOLATILITY,
        "beta_volatility": SIMULATION_CONFIG.default_volatility_beta,
        "growth_volatility": SIMULATION_CONFIG.default_volatility_growth,
    }

    # Merge with collected data, excluding None values
    merged = {
        **defaults,
        **{k: v for k, v in collected_data.items() if v is not None}
    }

    return DCFParameters.from_legacy(merged)