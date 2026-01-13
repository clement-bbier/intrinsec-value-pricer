"""
app/ui_components/ui_inputs_expert.py
ARCHITECTURE ATOMIQUE — TERMINAL PROFESSIONNEL RÉACTIF (V7.6)
Rôle : Standardisation UI pilotée par ui_texts.py.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
import streamlit as st

from core.models import (
    DCFParameters,
    InputSource,
    ValuationMode,
    ValuationRequest,
    TerminalValueMethod
)
from app.ui_components.ui_texts import ExpertTerminalTexts

# ==============================================================================
# 0. RÉFÉRENTIEL ET SÉCURITÉ
# ==============================================================================

def safe_factory_params(all_data: Dict[str, Any]) -> DCFParameters:
    """SÉCURITÉ PYDANTIC : Traite les données UI (Empty=Auto, 0=Value)."""
    final_data = {
        "projection_years": 5,
        "terminal_method": TerminalValueMethod.GORDON_GROWTH,
        "enable_monte_carlo": False
    }
    final_data.update({k: v for k, v in all_data.items() if v is not None})
    allowed_keys = DCFParameters.model_fields.keys()
    filtered_data = {k: v for k, v in final_data.items() if k in allowed_keys}
    return DCFParameters(**filtered_data)

# ==============================================================================
# 1. LES ATOMES UI (PILOTÉS PAR UI_TEXTS)
# ==============================================================================

def atom_discount_rate_smart(mode: ValuationMode) -> Dict[str, Any]:
    """Étape 3 : Coût du Capital - Labels centralisés."""
    st.markdown(ExpertTerminalTexts.SEC_3_CAPITAL)

    if mode == ValuationMode.RESIDUAL_INCOME_MODEL:
        st.latex(r"k_e = R_f + \beta \times MRP")
    else:
        st.latex(r"WACC = w_e [R_f + \beta(MRP)] + w_d [k_d(1-\tau)]")

    manual_price = st.number_input(ExpertTerminalTexts.INP_PRICE_WEIGHTS, min_value=0.0, max_value=10000.0, value=None, format="%.2f")

    col_a, col_b = st.columns(2)
    rf = col_a.number_input(ExpertTerminalTexts.INP_RF, min_value=0.0, max_value=0.20, value=None, format="%.3f")
    beta = col_b.number_input(ExpertTerminalTexts.INP_BETA, min_value=0.0, max_value=5.0, value=None, format="%.2f")
    mrp = col_a.number_input(ExpertTerminalTexts.INP_MRP, min_value=0.0, max_value=0.20, value=None, format="%.3f")

    res = {"risk_free_rate": rf, "manual_beta": beta, "market_risk_premium": mrp, "manual_stock_price": manual_price}

    if mode != ValuationMode.RESIDUAL_INCOME_MODEL:
        kd = col_b.number_input(ExpertTerminalTexts.INP_KD, min_value=0.0, max_value=0.20, value=None, format="%.3f")
        tau = col_a.number_input(ExpertTerminalTexts.INP_TAX, min_value=0.0, max_value=0.60, value=None, format="%.2f")
        res.update({"cost_of_debt": kd, "tax_rate": tau})

    st.divider()
    return res

def atom_terminal_dcf(formula_latex: str) -> Dict[str, Any]:
    """Atome spécifique aux modèles de flux (DCF)."""
    st.markdown(ExpertTerminalTexts.SEC_4_TERMINAL)
    st.latex(formula_latex)

    method = st.radio(
        ExpertTerminalTexts.RADIO_TV_METHOD,
        options=[TerminalValueMethod.GORDON_GROWTH, TerminalValueMethod.EXIT_MULTIPLE],
        format_func=lambda x: ExpertTerminalTexts.TV_GORDON if x == TerminalValueMethod.GORDON_GROWTH else ExpertTerminalTexts.TV_EXIT,
        horizontal=True
    )

    c1, _ = st.columns(2)
    if method == TerminalValueMethod.GORDON_GROWTH:
        gn = c1.number_input(ExpertTerminalTexts.INP_GN, min_value=0.0, max_value=0.05, value=None, format="%.3f")
        st.divider()
        return {"terminal_method": method, "perpetual_growth_rate": gn}
    else:
        exit_m = c1.number_input(ExpertTerminalTexts.INP_EXIT_M, min_value=0.0, max_value=100.0, value=None, format="%.1f")
        st.divider()
        return {"terminal_method": method, "exit_multiple_value": exit_m}

def atom_terminal_rim(formula_latex: str) -> Dict[str, Any]:
    """Atome spécifique au modèle RIM (Facteur de Persistance)."""
    st.markdown(ExpertTerminalTexts.SEC_4_TERMINAL)
    st.latex(formula_latex)

    c1, _ = st.columns(2)
    omega = c1.number_input(ExpertTerminalTexts.INP_OMEGA, min_value=0.0, max_value=1.0, value=None, format="%.2f")
    st.divider()

    return {"terminal_method": TerminalValueMethod.EXIT_MULTIPLE, "exit_multiple_value": omega}

def atom_bridge_smart(formula_latex: str, is_rim: bool = False) -> Dict[str, Any]:
    """Étape 5 : Equity Bridge - Labels centralisés."""
    st.markdown(ExpertTerminalTexts.SEC_5_BRIDGE)
    st.latex(formula_latex)

    if is_rim:
        shares = st.number_input(ExpertTerminalTexts.INP_SHARES, value=None, format="%.0f")
        st.divider()
        return {"manual_shares_outstanding": shares}

    c1, c2, c3 = st.columns(3)
    debt = c1.number_input(ExpertTerminalTexts.INP_DEBT, value=None, format="%.0f")
    cash = c2.number_input(ExpertTerminalTexts.INP_CASH, value=None, format="%.0f")
    shares = c3.number_input(ExpertTerminalTexts.INP_SHARES, value=None, format="%.0f")

    minorities = c1.number_input(ExpertTerminalTexts.INP_MINORITIES, value=None, format="%.0f")
    pensions = c2.number_input(ExpertTerminalTexts.INP_PENSIONS, value=None, format="%.0f")

    st.divider()
    return {
        "manual_total_debt": debt, "manual_cash": cash, "manual_shares_outstanding": shares,
        "manual_minority_interests": minorities, "manual_pension_provisions": pensions
    }

def atom_monte_carlo_smart(mode: ValuationMode) -> Dict[str, Any]:
    """Étape 6 : Monte Carlo - Labels centralisés."""
    st.markdown(ExpertTerminalTexts.SEC_6_MC)
    enable = st.toggle(ExpertTerminalTexts.MC_CALIBRATION, value=False)
    if enable:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            sims = c1.select_slider(ExpertTerminalTexts.MC_ITERATIONS, options=[1000, 5000, 10000, 20000], value=5000)

            st.caption(ExpertTerminalTexts.MC_CALIBRATION)
            v1, v2, v3 = st.columns(3)

            vb = v1.number_input(ExpertTerminalTexts.MC_VOL_BETA, min_value=0.0, max_value=1.0, value=None, format="%.3f")
            vg = v2.number_input(ExpertTerminalTexts.MC_VOL_G, min_value=0.0, max_value=0.20, value=None, format="%.3f")

            label_v_terminal = ExpertTerminalTexts.MC_VOL_OMEGA if mode == ValuationMode.RESIDUAL_INCOME_MODEL else ExpertTerminalTexts.MC_VOL_GN
            v_term = v3.number_input(label_v_terminal, min_value=0.0, max_value=0.05, value=None, format="%.3f")
            return {
                "enable_monte_carlo": True, "num_simulations": sims,
                "beta_volatility": vb, "growth_volatility": vg, "terminal_growth_volatility": v_term
            }
    return {"enable_monte_carlo": False}

# ==============================================================================
# 2. LES TERMINAUX EXPERTS
# ==============================================================================

def render_expert_fcff_standard(ticker: str) -> Optional[ValuationRequest]:
    st.subheader(ExpertTerminalTexts.TITLE_FCFF_STD)
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    st.markdown(ExpertTerminalTexts.SEC_1_FCF_STD)
    fcf_base = st.number_input(ExpertTerminalTexts.INP_FCF_TTM, value=None, format="%.0f")
    st.divider()

    st.markdown(ExpertTerminalTexts.SEC_2_PROJ)
    st.latex(r"FCF_t = FCF_{t-1} \times (1 + g)")
    c1, c2 = st.columns(2)
    n_years = c1.slider(ExpertTerminalTexts.SLIDER_PROJ_YEARS, 3, 15, 5)
    g_rate = c2.number_input(ExpertTerminalTexts.INP_GROWTH_G, min_value=-0.50, max_value=1.0, value=None, format="%.3f")
    st.divider()

    all_data = {"manual_fcf_base": fcf_base, "projection_years": n_years, "fcf_growth_rate": g_rate}
    all_data.update(atom_discount_rate_smart(ValuationMode.FCFF_TWO_STAGE))
    all_data.update(atom_terminal_dcf(r"TV_n = \begin{cases} \dfrac{FCF_n(1+g_n)}{WACC - g_n} & \text{(Gordon)} \\ FCF_n \times \text{Multiple} & \text{(Exit)} \end{cases}"))
    all_data.update(atom_bridge_smart(r"P = \dfrac{V_0 - \text{Dette} + \text{Trésorerie} - \text{Minoritaires} - \text{Pensions}}{\text{Actions}}"))
    all_data.update(atom_monte_carlo_smart(ValuationMode.FCFF_TWO_STAGE))

    if st.button(ExpertTerminalTexts.BTN_VALUATE_STD.format(ticker=ticker), type="primary", use_container_width=True):        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_TWO_STAGE, input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data))
    return None

def render_expert_fcff_fundamental(ticker: str) -> Optional[ValuationRequest]:
    st.subheader(ExpertTerminalTexts.TITLE_FCFF_FUND)
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_{norm} \times (1+g)^t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    st.markdown(ExpertTerminalTexts.SEC_1_FCF_NORM)
    fcf_base = st.number_input(ExpertTerminalTexts.INP_FCF_SMOOTHED, value=None, format="%.0f")
    st.divider()

    st.markdown(ExpertTerminalTexts.SEC_2_PROJ_FUND)
    st.latex(r"FCF_t = FCF_{norm} \times (1+g)^t")
    c1, c2 = st.columns(2)
    n_years = c1.slider(ExpertTerminalTexts.SLIDER_CYCLE_YEARS, 3, 15, 5)
    g_rate = c2.number_input(ExpertTerminalTexts.INP_GROWTH_G, min_value=-0.20, max_value=0.30, value=None, format="%.3f")
    st.divider()

    all_data = {"manual_fcf_base": fcf_base, "projection_years": n_years, "fcf_growth_rate": g_rate}
    all_data.update(atom_discount_rate_smart(ValuationMode.FCFF_NORMALIZED))
    all_data.update(atom_terminal_dcf(r"TV_n = \begin{cases} \dfrac{FCF_n(1+g_n)}{WACC - g_n} & \text{(Gordon)} \\ FCF_n \times \text{Multiple} & \text{(Exit)} \end{cases}"))
    all_data.update(atom_bridge_smart(r"P = \dfrac{V_0 - \text{Dette} + \text{Trésorerie} - \text{Minoritaires} - \text{Pensions}}{\text{Actions}}"))
    all_data.update(atom_monte_carlo_smart(ValuationMode.FCFF_NORMALIZED))

    if st.button(ExpertTerminalTexts.BTN_VALUATE_FUND.format(ticker=ticker), type="primary", use_container_width=True):        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_NORMALIZED, input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data))
    return None

def render_expert_fcff_growth(ticker: str) -> Optional[ValuationRequest]:
    st.subheader(ExpertTerminalTexts.TITLE_FCFF_GROWTH)
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{Rev_0(1+g_{rev})^t \times Margin_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    st.markdown(ExpertTerminalTexts.SEC_1_REV_BASE)
    rev_base = st.number_input(ExpertTerminalTexts.INP_REV_TTM, value=None, format="%.0f")
    st.divider()

    st.markdown(ExpertTerminalTexts.SEC_2_PROJ_GROWTH)
    st.latex(r"Rev_t = Rev_0 \times (1 + g_{rev})^t \quad | \quad Margin_t \rightarrow Margin_{target}")
    c1, c2, c3 = st.columns(3)
    n_years = c1.slider(ExpertTerminalTexts.SLIDER_PROJ_T, 3, 15, 5)
    g_rev = c2.number_input(ExpertTerminalTexts.INP_REV_GROWTH, min_value=0.0, max_value=1.0, value=None, format="%.3f")
    m_target = c3.number_input(ExpertTerminalTexts.INP_MARGIN_TARGET, min_value=0.0, max_value=0.80, value=None, format="%.2f")
    st.divider()

    all_data = {"manual_fcf_base": rev_base, "projection_years": n_years, "fcf_growth_rate": g_rev, "target_fcf_margin": m_target}
    all_data.update(atom_discount_rate_smart(ValuationMode.FCFF_REVENUE_DRIVEN))
    all_data.update(atom_terminal_dcf(r"TV_n = \begin{cases} \dfrac{FCF_n(1+g_n)}{WACC - g_n} & \text{(Gordon)} \\ FCF_n \times \text{Multiple} & \text{(Exit)} \end{cases}"))
    all_data.update(atom_bridge_smart(r"P = \dfrac{V_0 - \text{Dette} + \text{Trésorerie} - \text{Minoritaires} - \text{Pensions}}{\text{Actions}}"))
    all_data.update(atom_monte_carlo_smart(ValuationMode.FCFF_REVENUE_DRIVEN))

    if st.button(ExpertTerminalTexts.BTN_VALUATE_GROWTH.format(ticker=ticker), type="primary", use_container_width=True):
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_REVENUE_DRIVEN, input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data))
    return None

def render_expert_rim(ticker: str) -> Optional[ValuationRequest]:
    st.subheader(ExpertTerminalTexts.TITLE_RIM)
    st.latex(r"P = BV_0 + \sum_{t=1}^{n} \frac{NI_t - (k_e \times BV_{t-1})}{(1+k_e)^t} + \frac{TV_{RI}}{(1+k_e)^n}")

    st.markdown(ExpertTerminalTexts.SEC_1_RIM_BASE)
    c1, c2 = st.columns(2)
    bv = c1.number_input(ExpertTerminalTexts.INP_BV_INITIAL, value=None, format="%.0f")
    ni = c2.number_input(ExpertTerminalTexts.INP_NI_TTM, value=None, format="%.0f")
    st.divider()

    st.markdown(ExpertTerminalTexts.SEC_2_PROJ_RIM)
    st.latex(r"NI_t = NI_{t-1} \times (1 + g)")
    c1, c2 = st.columns(2)
    n_years = c1.slider(ExpertTerminalTexts.SLIDER_PROJ_N, 3, 15, 5)
    g_ni = c2.number_input(ExpertTerminalTexts.INP_GROWTH_G, min_value=0.0, max_value=0.50, value=None, format="%.3f")
    st.divider()

    all_data = {"manual_book_value": bv, "manual_fcf_base": ni, "projection_years": n_years, "fcf_growth_rate": g_ni}
    all_data.update(atom_discount_rate_smart(ValuationMode.RESIDUAL_INCOME_MODEL))
    all_data.update(atom_terminal_rim(r"TV_{RI} = \frac{RI_n \times \omega}{1 + k_e - \omega}"))
    all_data.update(atom_bridge_smart(r"P = \dfrac{\text{Equity Value}}{\text{Actions}}", is_rim=True))
    all_data.update(atom_monte_carlo_smart(ValuationMode.RESIDUAL_INCOME_MODEL))

    if st.button(ExpertTerminalTexts.BTN_VALUATE_RIM.format(ticker=ticker), type="primary", use_container_width=True):
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.RESIDUAL_INCOME_MODEL, input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data))
    return None

def render_expert_graham(ticker: str) -> Optional[ValuationRequest]:
    st.subheader(ExpertTerminalTexts.TITLE_GRAHAM)
    st.latex(r"P = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}")

    st.markdown(ExpertTerminalTexts.SEC_1_GRAHAM_BASE)
    st.latex(r"P \propto EPS \times (8.5 + 2g)")
    c1, c2 = st.columns(2)
    eps = c1.number_input(ExpertTerminalTexts.INP_EPS_NORM, value=None, format="%.2f")
    g_lt = c2.number_input(ExpertTerminalTexts.INP_GROWTH_G_SIMPLE, min_value=0.0, max_value=0.20, value=None, format="%.3f")
    st.divider()

    st.markdown(ExpertTerminalTexts.SEC_2_GRAHAM)
    st.latex(r"P \propto \frac{4.4}{Y}")
    c1, c2 = st.columns(2)
    yield_aaa = c1.number_input(ExpertTerminalTexts.INP_YIELD_AAA, min_value=0.0, max_value=0.20, value=None, format="%.3f")
    tau = c2.number_input(ExpertTerminalTexts.INP_TAX_SIMPLE, min_value=0.0, max_value=0.60, value=None, format="%.2f")
    st.divider()

    if st.button(ExpertTerminalTexts.BTN_VALUATE_GRAHAM.format(ticker=ticker), type="primary", use_container_width=True):
        all_data = {"manual_fcf_base": eps, "fcf_growth_rate": g_lt, "corporate_aaa_yield": yield_aaa, "tax_rate": tau, "projection_years": 1, "enable_monte_carlo": False}
        return ValuationRequest(ticker=ticker, projection_years=1, mode=ValuationMode.GRAHAM_1974_REVISED, input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data))
    return None