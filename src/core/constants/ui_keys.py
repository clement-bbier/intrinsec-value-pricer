"""
src/core/constants/ui_keys.py

SINGLE SOURCE OF TRUTH — UI SESSION KEY REGISTRY
=================================================
Role: Canonical registry of every Streamlit ``session_state`` key suffix
used to bridge the UI layer with the Pydantic backend models.

Architecture
------------
* **Prefixed keys** are combined at runtime with a strategy or bridge
  prefix (e.g. ``f"{mode}_{UIKeys.RF}"`` -> ``"FCFF_STANDARD_rf"``).
* **Global keys** are used as-is for cross-strategy extensions
  (e.g. ``UIKeys.MC_ENABLE`` -> ``"mc_enable"``).

Adding a new key here and referencing it in both the ``UIKey(...)``
annotation and the widget ``key=`` parameter guarantees compile-time
safety and makes any future mismatch detectable by the contract test
``tests/unit/test_ui_backend_contract_integrity.py``.
"""


class UIKeys:
    """
    Centralized, immutable registry of UI session key suffixes.

    Every ``session_state`` key used to bridge the Streamlit UI with
    Pydantic backend models MUST be defined here.  This prevents silent
    mismatches between ``shared_widgets.py`` and the model layer.

    Attributes are plain ``str`` class variables grouped by functional
    domain for readability.
    """

    # ── Financial Rates (prefix: strategy mode) ──────────────────────
    RF: str = "rf"
    MRP: str = "mrp"
    BETA: str = "beta"
    KD: str = "kd"
    TAX: str = "tax"
    YIELD_AAA: str = "yield_aaa"
    WACC_OVERRIDE: str = "wacc_override"
    KE_OVERRIDE: str = "ke_override"
    PRICE: str = "price"
    TARGET_DEBT_TO_CAPITAL: str = "target_debt_to_capital"

    # ── Capital Structure (prefix: bridge_{mode}) ────────────────────
    DEBT: str = "debt"
    CASH: str = "cash"
    MINORITIES: str = "min"
    PENSIONS: str = "pen"
    SHARES: str = "shares"
    SBC_RATE: str = "sbc_rate"

    # ── Strategy Params (prefix: strategy mode) ──────────────────────
    GROWTH_RATE: str = "growth_rate"
    GN: str = "gn"
    EXIT_MULT: str = "exit_mult"
    YEARS: str = "years"
    GROWTH_VECTOR: str = "growth_vector"
    FCF_BASE: str = "fcf_base"
    FCF_NORM: str = "fcf_norm"
    REVENUE_TTM: str = "revenue_ttm"
    FCF_MARGIN: str = "fcf_margin"
    FCFE_ANCHOR: str = "fcfe_anchor"
    NET_BORROWING_DELTA: str = "net_borrowing_delta"
    DIV_BASE: str = "div_base"
    BV_ANCHOR: str = "bv_anchor"
    OMEGA: str = "omega"
    EPS_NORMALIZED: str = "eps_normalized"
    EPS_ANCHOR: str = "eps_anchor"
    GROWTH_ESTIMATE: str = "growth_estimate"

    # ── Monte Carlo (global, no prefix) ──────────────────────────────
    MC_ENABLE: str = "mc_enable"
    MC_SIMS: str = "mc_sims"
    MC_VOL_FLOW: str = "mc_vol_flow"
    MC_VOL_GROWTH: str = "mc_vol_growth"
    MC_VOL_BETA: str = "mc_vol_beta"
    MC_VOL_EXIT_M: str = "mc_vol_exit_m"
    MC_VOL_GN: str = "mc_vol_gn"

    # ── Sensitivity (global, no prefix) ──────────────────────────────
    SENS_ENABLE: str = "sens_enable"
    SENS_STEP: str = "sens_step"
    SENS_RANGE: str = "sens_range"
    SENSI_WACC: str = "sensi_wacc"
    SENSI_GROWTH: str = "sensi_growth"

    # ── Scenarios (global, no prefix) ────────────────────────────────
    SCENARIO_ENABLE: str = "scenario_enable"
    SCENARIO_P: str = "p"
    SCENARIO_G: str = "g"
    SCENARIO_M: str = "m"

    # ── Backtest (global, no prefix) ─────────────────────────────────
    BT_ENABLE: str = "bt_enable"
    BT_LOOKBACK: str = "bt_lookback"

    # ── Peers (global, no prefix) ────────────────────────────────────
    PEER_ENABLE: str = "peer_enable"
    PEER_INPUT: str = "peer_input"
    PEER_LIST: str = "peer_list"

    # ── SOTP (global, no prefix) ─────────────────────────────────────
    SOTP_ENABLE: str = "sotp_enable"
    SOTP_DISCOUNT: str = "sotp_discount"
    SOTP_SEGS: str = "sotp_segs"
    SOTP_EDITOR: str = "sotp_editor"

    # ── MC Shocks (global, no prefix) ────────────────────────────────
    VOL_GROWTH: str = "vol_growth"
    VOL_BETA: str = "vol_beta"
    VOL_FLOW: str = "vol_flow"

    # ── Terminal Value (prefix: strategy mode) ───────────────────────
    TV_METHOD: str = "method"
