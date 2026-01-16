"""
app/ui_components/ui_inputs_expert.py
ARCHITECTURE ATOMIQUE — TERMINAL PROFESSIONNEL RÉACTIF (V13.0)
Sprint 6 : Sum-of-the-Parts & Backtesting
Rôle : Standardisation UI pilotée par ui_texts.py et models.py.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
import streamlit as st
import pandas as pd

from core.models import (
    DCFParameters,
    InputSource,
    ValuationMode,
    ValuationRequest,
    TerminalValueMethod,
    ScenarioParameters,
    ScenarioVariant,
    BusinessUnit,
    SOTPMethod
)
from app.ui_components.ui_texts import ExpertTerminalTexts, SOTPTexts


# ==============================================================================
# 1. LOGIQUE DE TRANSITION ET SÉCURITÉ
# ==============================================================================

def safe_factory_params(all_data: Dict[str, Any]) -> DCFParameters:
    """
    SÉCURITÉ PYDANTIC : Convertit le dictionnaire plat de l'UI vers
    la structure segmentée DCFParameters.
    """
    base_defaults = {
        "projection_years": 5,
        "terminal_method": TerminalValueMethod.GORDON_GROWTH,
        "enable_monte_carlo": False,
        "num_simulations": 5000,
        "base_flow_volatility": 0.05,
        "beta_volatility": 0.10,
        "growth_volatility": 0.02
    }
    # Fusion des données UI avec les valeurs par défaut
    full_data = {**base_defaults, **{k: v for k, v in all_data.items() if v is not None}}
    return DCFParameters.from_legacy(full_data)


# ==============================================================================
# 2. LES ATOMES UI PARTAGÉS (ÉTAPES 3 À 8)
# ==============================================================================

def atom_discount_rate_smart(mode: ValuationMode) -> Dict[str, Any]:
    """Étape 3 : Coût du Capital - Bifurcation Ke (Equity) vs WACC (Firm)."""
    st.markdown(ExpertTerminalTexts.SEC_3_CAPITAL)

    if mode.is_direct_equity:
        st.latex(r"k_e = R_f + \beta \times MRP")
    else:
        st.latex(r"WACC = w_e [R_f + \beta(MRP)] + w_d [k_d(1-\tau)]")

    manual_price = st.number_input(ExpertTerminalTexts.INP_PRICE_WEIGHTS, min_value=0.0, max_value=10000.0, value=None, format="%.2f")

    col_a, col_b = st.columns(2)
    rf = col_a.number_input(ExpertTerminalTexts.INP_RF, min_value=0.0, max_value=0.20, value=None, format="%.3f")
    beta = col_b.number_input(ExpertTerminalTexts.INP_BETA, min_value=0.0, max_value=5.0, value=None, format="%.2f")
    mrp = col_a.number_input(ExpertTerminalTexts.INP_MRP, min_value=0.0, max_value=0.20, value=None, format="%.3f")

    res = {"risk_free_rate": rf, "manual_beta": beta, "market_risk_premium": mrp, "manual_stock_price": manual_price}

    if not mode.is_direct_equity:
        kd = col_b.number_input(ExpertTerminalTexts.INP_KD, min_value=0.0, max_value=0.20, value=None, format="%.3f")
        tau = col_a.number_input(ExpertTerminalTexts.INP_TAX, min_value=0.0, max_value=0.60, value=None, format="%.2f")
        res.update({"cost_of_debt": kd, "tax_rate": tau})

    st.divider()
    return res


def atom_terminal_dcf(formula_latex: str) -> Dict[str, Any]:
    """Atome spécifique aux modèles de flux (DCF / FCFE / DDM)."""
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


def atom_bridge_smart(formula_latex: str, mode: ValuationMode) -> Dict[str, Any]:
    """Étape 5 : Equity Bridge - Isolation selon le niveau de valorisation."""
    st.markdown(ExpertTerminalTexts.SEC_5_BRIDGE)
    st.latex(formula_latex)

    if mode.is_direct_equity:
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


def atom_monte_carlo_smart(mode: ValuationMode, terminal_method: Optional[TerminalValueMethod] = None) -> Dict[str, Any]:
    """Étape 6 : Monte Carlo - Réactif à la méthode de sortie et incluant Vol Y0."""
    st.markdown(ExpertTerminalTexts.SEC_6_MC)
    enable = st.toggle(ExpertTerminalTexts.MC_CALIBRATION, value=False)

    if enable:
        with st.container(border=True):
            c_iter, _ = st.columns([2, 2])
            sims = c_iter.select_slider(ExpertTerminalTexts.MC_ITERATIONS, options=[1000, 5000, 10000, 20000], value=5000)
            st.divider()

            v_col1, v_col2 = st.columns(2)
            v0 = v_col1.number_input(ExpertTerminalTexts.MC_VOL_BASE_FLOW, 0.0, 0.50, 0.05, "%.3f", help=ExpertTerminalTexts.MC_VOL_BASE_FLOW_HELP)
            vb = v_col2.number_input(ExpertTerminalTexts.MC_VOL_BETA, 0.0, 1.0, 0.10, "%.3f")
            vg = v_col1.number_input(ExpertTerminalTexts.MC_VOL_G, 0.0, 0.20, 0.02, "%.3f")

            v_term = 0.0
            if mode == ValuationMode.RESIDUAL_INCOME_MODEL:
                v_term = v_col2.number_input(ExpertTerminalTexts.MC_VOL_OMEGA, 0.0, 0.20, 0.05, "%.3f")
            elif terminal_method == TerminalValueMethod.GORDON_GROWTH:
                v_term = v_col2.number_input(ExpertTerminalTexts.MC_VOL_GN, 0.0, 0.05, 0.01, "%.3f")
            else:
                v_col2.empty()

            return {
                "enable_monte_carlo": True, "num_simulations": sims,
                "base_flow_volatility": v0, "beta_volatility": vb,
                "growth_volatility": vg, "terminal_growth_volatility": v_term
            }
    return {"enable_monte_carlo": False}


def atom_peer_selection() -> List[str]:
    """Étape 7 : Sélection manuelle des pairs pour la triangulation (Sprint 4)."""
    st.markdown(ExpertTerminalTexts.SEC_7_PEERS)
    raw_input = st.text_input(ExpertTerminalTexts.INP_MANUAL_PEERS, placeholder="ex: AAPL, MSFT, GOOG", help=ExpertTerminalTexts.INP_MANUAL_PEERS_HELP)
    st.divider()
    if not raw_input: return []
    return [t.strip().upper() for t in raw_input.split(",") if t.strip()]


def atom_scenario_configuration(mode: ValuationMode) -> ScenarioParameters:
    """Étape 8 : Configuration des scénarios déterministes (Sprint 5)."""
    st.markdown(ExpertTerminalTexts.SEC_8_SCENARIOS)
    enabled = st.toggle(ExpertTerminalTexts.INP_SCENARIO_ENABLE, value=False)

    if not enabled: return ScenarioParameters(enabled=False)

    with st.container(border=True):
        st.caption("Définissez des variantes. Laissez vide pour utiliser la valeur de base du terminal.")

        # Bull
        with st.expander(ExpertTerminalTexts.LABEL_SCENARIO_BULL, expanded=True):
            c1, c2, c3 = st.columns(3)
            p_bull = c1.number_input(f"{ExpertTerminalTexts.INP_SCENARIO_PROBA} (Bull)", 0.0, 100.0, 25.0, 5.0, key="sc_p_bull") / 100
            g_bull = c2.number_input(f"{ExpertTerminalTexts.INP_SCENARIO_GROWTH} (Bull)", value=None, format="%.3f", key="sc_g_bull")
            m_bull = c3.number_input(f"{ExpertTerminalTexts.INP_SCENARIO_MARGIN} (Bull)", value=None, format="%.2f", key="sc_m_bull") if mode == ValuationMode.FCFF_REVENUE_DRIVEN else None

        # Base
        with st.expander(ExpertTerminalTexts.LABEL_SCENARIO_BASE, expanded=True):
            c1, c2, c3 = st.columns(3)
            p_base = c1.number_input(f"{ExpertTerminalTexts.INP_SCENARIO_PROBA} (Base)", 0.0, 100.0, 50.0, 5.0, key="sc_p_base") / 100
            g_base = c2.number_input(f"{ExpertTerminalTexts.INP_SCENARIO_GROWTH} (Base)", value=None, format="%.3f", key="sc_g_base")
            m_base = c3.number_input(f"{ExpertTerminalTexts.INP_SCENARIO_MARGIN} (Base)", value=None, format="%.2f", key="sc_m_base") if mode == ValuationMode.FCFF_REVENUE_DRIVEN else None

        # Bear
        with st.expander(ExpertTerminalTexts.LABEL_SCENARIO_BEAR, expanded=True):
            c1, c2, c3 = st.columns(3)
            p_bear = c1.number_input(f"{ExpertTerminalTexts.INP_SCENARIO_PROBA} (Bear)", 0.0, 100.0, 25.0, 5.0, key="sc_p_bear") / 100
            g_bear = c2.number_input(f"{ExpertTerminalTexts.INP_SCENARIO_GROWTH} (Bear)", value=None, format="%.3f", key="sc_g_bear")
            m_bear = c3.number_input(f"{ExpertTerminalTexts.INP_SCENARIO_MARGIN} (Bear)", value=None, format="%.2f", key="sc_m_bear") if mode == ValuationMode.FCFF_REVENUE_DRIVEN else None

        if abs((p_bull + p_base + p_bear) - 1.0) > 0.001:
            st.warning(ExpertTerminalTexts.HELP_SCENARIO_PROBA)

    return ScenarioParameters(
        enabled=True,
        bull=ScenarioVariant(label="Bull", growth_rate=g_bull, target_fcf_margin=m_bull, probability=p_bull),
        base=ScenarioVariant(label="Base", growth_rate=g_base, target_fcf_margin=m_base, probability=p_base),
        bear=ScenarioVariant(label="Bear", growth_rate=g_bear, target_fcf_margin=m_bear, probability=p_bear)
    )


# ==============================================================================
# 3. SECTIONS SPÉCIALISÉES (SOTP - SPRINT 6)
# ==============================================================================

def render_sotp_section(params: DCFParameters) -> None:
    """Rendu de la section Sum-of-the-Parts (SOTP) (ST 2.1)."""
    st.divider()
    st.markdown(f"### {SOTPTexts.TITLE}")

    params.sotp.enabled = st.toggle(SOTPTexts.SEC_SEGMENTS, value=params.sotp.enabled, help=SOTPTexts.HELP_SOTP)

    if params.sotp.enabled:
        current_data = [
            {
                SOTPTexts.LBL_SEGMENT_NAME: bu.name,
                SOTPTexts.LBL_SEGMENT_VALUE: bu.enterprise_value,
                SOTPTexts.LBL_SEGMENT_METHOD: bu.method.value
            }
            for bu in params.sotp.segments
        ]

        if not current_data:
            current_data = [{SOTPTexts.LBL_SEGMENT_NAME: "Segment A", SOTPTexts.LBL_SEGMENT_VALUE: 0.0, SOTPTexts.LBL_SEGMENT_METHOD: SOTPMethod.DCF.value}]

        edited_df = st.data_editor(
            pd.DataFrame(current_data), num_rows="dynamic", use_container_width=True, key="sotp_editor",
            column_config={
                SOTPTexts.LBL_SEGMENT_VALUE: st.column_config.NumberColumn(format="%.2f"),
                SOTPTexts.LBL_SEGMENT_METHOD: st.column_config.SelectboxColumn(options=[m.value for m in SOTPMethod])
            }
        )

        params.sotp.segments = [
            BusinessUnit(name=row[SOTPTexts.LBL_SEGMENT_NAME], enterprise_value=row[SOTPTexts.LBL_SEGMENT_VALUE], method=SOTPMethod(row[SOTPTexts.LBL_SEGMENT_METHOD]))
            for _, row in edited_df.iterrows() if row[SOTPTexts.LBL_SEGMENT_NAME]
        ]

        st.markdown(SOTPTexts.SEC_ADJUSTMENTS)
        params.sotp.conglomerate_discount = st.slider(SOTPTexts.LBL_DISCOUNT, 0, 50, int(params.sotp.conglomerate_discount * 100), 5) / 100.0


# ==============================================================================
# 4. LES TERMINAUX EXPERTS (ENTRÉES PRINCIPALES)
# ==============================================================================

def render_expert_fcff_standard(ticker: str) -> Optional[ValuationRequest]:
    """Terminal Expert : FCFF Standard."""
    st.subheader(ExpertTerminalTexts.TITLE_FCFF_STD)
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    st.markdown(ExpertTerminalTexts.SEC_1_FCF_STD)
    fcf_base = st.number_input(ExpertTerminalTexts.INP_FCF_TTM, value=None, format="%.0f")
    st.divider()

    st.markdown(ExpertTerminalTexts.SEC_2_PROJ)
    c1, c2 = st.columns(2)
    n_years = c1.slider(ExpertTerminalTexts.SLIDER_PROJ_YEARS, 3, 15, 5)
    g_rate = c2.number_input(ExpertTerminalTexts.INP_GROWTH_G, -0.50, 1.0, value=None, format="%.3f")
    st.divider()

    all_data = {"manual_fcf_base": fcf_base, "projection_years": n_years, "fcf_growth_rate": g_rate}
    all_data.update(atom_discount_rate_smart(ValuationMode.FCFF_TWO_STAGE))
    tv_data = atom_terminal_dcf(r"TV_n = f(FCF_n, g_n, WACC)")
    all_data.update(tv_data)
    all_data.update(atom_bridge_smart(r"P = \dfrac{V_0 - \text{Debt} + \text{Cash}}{\text{Actions}}", ValuationMode.FCFF_TWO_STAGE))
    all_data.update(atom_monte_carlo_smart(ValuationMode.FCFF_TWO_STAGE, tv_data.get("terminal_method")))

    manual_peers = atom_peer_selection()
    scenarios = atom_scenario_configuration(ValuationMode.FCFF_TWO_STAGE)

    if st.button(ExpertTerminalTexts.BTN_VALUATE_STD.format(ticker=ticker), type="primary", use_container_width=True):
        params = safe_factory_params(all_data)
        params.scenarios = scenarios
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_TWO_STAGE, input_source=InputSource.MANUAL, manual_params=params, options={"manual_peers": manual_peers})
    return None


def render_expert_fcff_fundamental(ticker: str) -> Optional[ValuationRequest]:
    """Terminal Expert : FCFF Fondamental."""
    st.subheader(ExpertTerminalTexts.TITLE_FCFF_FUND)
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_{norm} \times (1+g)^t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    st.markdown(ExpertTerminalTexts.SEC_1_FCF_NORM)
    fcf_base = st.number_input(ExpertTerminalTexts.INP_FCF_SMOOTHED, value=None, format="%.0f")
    st.divider()

    st.markdown(ExpertTerminalTexts.SEC_2_PROJ_FUND)
    c1, c2 = st.columns(2)
    n_years = c1.slider(ExpertTerminalTexts.SLIDER_CYCLE_YEARS, 3, 15, 5)
    g_rate = c2.number_input(ExpertTerminalTexts.INP_GROWTH_G, -0.20, 0.30, value=None, format="%.3f")
    st.divider()

    all_data = {"manual_fcf_base": fcf_base, "projection_years": n_years, "fcf_growth_rate": g_rate}
    all_data.update(atom_discount_rate_smart(ValuationMode.FCFF_NORMALIZED))
    tv_data = atom_terminal_dcf(r"TV_n = f(FCF_n, g_n, WACC)")
    all_data.update(tv_data)
    all_data.update(atom_bridge_smart(r"P = \dfrac{V_0 - \text{Debt} + \text{Cash}}{\text{Actions}}", ValuationMode.FCFF_NORMALIZED))
    all_data.update(atom_monte_carlo_smart(ValuationMode.FCFF_NORMALIZED, tv_data.get("terminal_method")))

    manual_peers = atom_peer_selection()
    scenarios = atom_scenario_configuration(ValuationMode.FCFF_NORMALIZED)

    if st.button(ExpertTerminalTexts.BTN_VALUATE_FUND.format(ticker=ticker), type="primary", use_container_width=True):
        params = safe_factory_params(all_data)
        params.scenarios = scenarios
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_NORMALIZED, input_source=InputSource.MANUAL, manual_params=params, options={"manual_peers": manual_peers})
    return None


def render_expert_fcff_growth(ticker: str) -> Optional[ValuationRequest]:
    """Terminal Expert : FCFF Growth."""
    st.subheader(ExpertTerminalTexts.TITLE_FCFF_GROWTH)
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{Rev_0(1+g_{rev})^t \times Margin_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    st.markdown(ExpertTerminalTexts.SEC_1_REV_BASE)
    rev_base = st.number_input(ExpertTerminalTexts.INP_REV_TTM, value=None, format="%.0f")
    st.divider()

    st.markdown(ExpertTerminalTexts.SEC_2_PROJ_GROWTH)
    c1, c2, c3 = st.columns(3)
    n_years = c1.slider(ExpertTerminalTexts.SLIDER_PROJ_T, 3, 15, 5)
    g_rev = c2.number_input(ExpertTerminalTexts.INP_REV_GROWTH, 0.0, 1.0, value=None, format="%.3f")
    m_target = c3.number_input(ExpertTerminalTexts.INP_MARGIN_TARGET, 0.0, 0.80, value=None, format="%.2f")
    st.divider()

    all_data = {"manual_fcf_base": rev_base, "projection_years": n_years, "fcf_growth_rate": g_rev, "target_fcf_margin": m_target}
    all_data.update(atom_discount_rate_smart(ValuationMode.FCFF_REVENUE_DRIVEN))
    tv_data = atom_terminal_dcf(r"TV_n = f(FCF_n, g_n, WACC)")
    all_data.update(tv_data)
    all_data.update(atom_bridge_smart(r"P = \dfrac{V_0 - \text{Debt} + \text{Cash}}{\text{Actions}}", ValuationMode.FCFF_REVENUE_DRIVEN))
    all_data.update(atom_monte_carlo_smart(ValuationMode.FCFF_REVENUE_DRIVEN, tv_data.get("terminal_method")))

    manual_peers = atom_peer_selection()
    scenarios = atom_scenario_configuration(ValuationMode.FCFF_REVENUE_DRIVEN)

    if st.button(ExpertTerminalTexts.BTN_VALUATE_GROWTH.format(ticker=ticker), type="primary", use_container_width=True):
        params = safe_factory_params(all_data)
        params.scenarios = scenarios
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_REVENUE_DRIVEN, input_source=InputSource.MANUAL, manual_params=params, options={"manual_peers": manual_peers})
    return None


def render_expert_fcfe(ticker: str) -> Optional[ValuationRequest]:
    """Terminal Expert : FCFE (Direct Equity)."""
    st.subheader(ExpertTerminalTexts.TITLE_FCFE)
    st.latex(r"P = \sum_{t=1}^{n} \frac{FCFE_t}{(1+k_e)^t} + \frac{TV_n}{(1+k_e)^n}")

    st.markdown(ExpertTerminalTexts.SEC_1_FCFE_BASE)
    c1, c2 = st.columns(2)
    fcfe_base = c1.number_input(ExpertTerminalTexts.INP_FCFE_BASE, value=None, format="%.0f")
    net_borrowing = c2.number_input(ExpertTerminalTexts.INP_NET_BORROWING, value=None, format="%.0f", help=ExpertTerminalTexts.INP_NET_BORROWING_HELP)
    st.divider()

    st.markdown(ExpertTerminalTexts.SEC_2_PROJ)
    c1, c2 = st.columns(2)
    n_years = c1.slider(ExpertTerminalTexts.SLIDER_PROJ_YEARS, 3, 15, 5)
    g_rate = c2.number_input(ExpertTerminalTexts.INP_GROWTH_G, -0.50, 1.0, value=None, format="%.3f")
    st.divider()

    all_data = {"manual_fcf_base": fcfe_base, "manual_net_borrowing": net_borrowing, "projection_years": n_years, "fcf_growth_rate": g_rate}
    all_data.update(atom_discount_rate_smart(ValuationMode.FCFE_TWO_STAGE))
    tv_data = atom_terminal_dcf(r"TV_n = \begin{cases} \dfrac{FCFE_n(1+g_n)}{k_e - g_n} & \text{(Gordon)} \\ FCFE_n \times \text{Multiple} & \text{(Exit)} \end{cases}")
    all_data.update(tv_data)
    all_data.update(atom_bridge_smart(r"P = \frac{\text{Equity Value}}{\text{Actions}}", ValuationMode.FCFE_TWO_STAGE))
    all_data.update(atom_monte_carlo_smart(ValuationMode.FCFE_TWO_STAGE, tv_data.get("terminal_method")))

    manual_peers = atom_peer_selection()
    scenarios = atom_scenario_configuration(ValuationMode.FCFE_TWO_STAGE)

    if st.button(ExpertTerminalTexts.BTN_VALUATE_FCFE.format(ticker=ticker), type="primary", use_container_width=True):
        params = safe_factory_params(all_data)
        params.scenarios = scenarios
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFE_TWO_STAGE, input_source=InputSource.MANUAL, manual_params=params, options={"manual_peers": manual_peers})
    return None


def render_expert_ddm(ticker: str) -> Optional[ValuationRequest]:
    """Terminal Expert : Dividend Discount Model."""
    st.subheader(ExpertTerminalTexts.TITLE_DDM)
    st.latex(r"P = \sum_{t=1}^{n} \frac{D_0(1+g)^t}{(1+k_e)^t} + \frac{TV_n}{(1+k_e)^n}")

    st.markdown(ExpertTerminalTexts.SEC_1_DDM_BASE)
    d0_base = st.number_input(ExpertTerminalTexts.INP_DIVIDEND_BASE, value=None, format="%.2f", help=ExpertTerminalTexts.INP_DIVIDEND_BASE_HELP)
    st.divider()

    st.markdown(ExpertTerminalTexts.SEC_2_PROJ)
    c1, c2 = st.columns(2)
    n_years = c1.slider(ExpertTerminalTexts.SLIDER_PROJ_YEARS, 3, 15, 5)
    g_rate = c2.number_input(ExpertTerminalTexts.INP_GROWTH_G, 0.0, 0.20, value=None, format="%.3f")
    st.divider()

    all_data = {"manual_dividend_base": d0_base, "projection_years": n_years, "fcf_growth_rate": g_rate}
    all_data.update(atom_discount_rate_smart(ValuationMode.DDM_GORDON_GROWTH))
    tv_data = atom_terminal_dcf(r"TV_n = \frac{D_n(1+g_n)}{k_e - g_n}")
    all_data.update(tv_data)
    all_data.update(atom_bridge_smart(r"P = \frac{\text{Equity Value}}{\text{Actions}}", ValuationMode.DDM_GORDON_GROWTH))
    all_data.update(atom_monte_carlo_smart(ValuationMode.DDM_GORDON_GROWTH, tv_data.get("terminal_method")))

    manual_peers = atom_peer_selection()
    scenarios = atom_scenario_configuration(ValuationMode.DDM_GORDON_GROWTH)

    if st.button(ExpertTerminalTexts.BTN_VALUATE_DDM.format(ticker=ticker), type="primary", use_container_width=True):
        params = safe_factory_params(all_data)
        params.scenarios = scenarios
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.DDM_GORDON_GROWTH, input_source=InputSource.MANUAL, manual_params=params, options={"manual_peers": manual_peers})
    return None


def render_expert_rim(ticker: str) -> Optional[ValuationRequest]:
    """Terminal Expert : RIM."""
    st.subheader(ExpertTerminalTexts.TITLE_RIM)
    st.latex(r"P = BV_0 + \sum_{t=1}^{n} \frac{NI_t - (k_e \times BV_{t-1})}{(1+k_e)^t} + \frac{TV_{RI}}{(1+k_e)^n}")

    st.markdown(ExpertTerminalTexts.SEC_1_RIM_BASE)
    c1, c2 = st.columns(2)
    bv = c1.number_input(ExpertTerminalTexts.INP_BV_INITIAL, value=None, format="%.0f")
    ni = c2.number_input(ExpertTerminalTexts.INP_NI_TTM, value=None, format="%.0f")
    st.divider()

    st.markdown(ExpertTerminalTexts.SEC_2_PROJ_RIM)
    c1, c2 = st.columns(2)
    n_years = c1.slider(ExpertTerminalTexts.SLIDER_PROJ_N, 3, 15, 5)
    g_ni = c2.number_input(ExpertTerminalTexts.INP_GROWTH_G, 0.0, 0.50, value=None, format="%.3f")
    st.divider()

    all_data = {"manual_book_value": bv, "manual_fcf_base": ni, "projection_years": n_years, "fcf_growth_rate": g_ni}
    all_data.update(atom_discount_rate_smart(ValuationMode.RESIDUAL_INCOME_MODEL))
    all_data.update(atom_terminal_rim(r"TV_{RI} = \frac{RI_n \times \omega}{1 + k_e - \omega}"))
    all_data.update(atom_bridge_smart(r"P = \dfrac{\text{Equity Value}}{\text{Actions}}", ValuationMode.RESIDUAL_INCOME_MODEL))
    all_data.update(atom_monte_carlo_smart(ValuationMode.RESIDUAL_INCOME_MODEL))

    manual_peers = atom_peer_selection()
    scenarios = atom_scenario_configuration(ValuationMode.RESIDUAL_INCOME_MODEL)

    if st.button(ExpertTerminalTexts.BTN_VALUATE_RIM.format(ticker=ticker), type="primary", use_container_width=True):
        params = safe_factory_params(all_data)
        params.scenarios = scenarios
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.RESIDUAL_INCOME_MODEL, input_source=InputSource.MANUAL, manual_params=params, options={"manual_peers": manual_peers})
    return None


def render_expert_graham(ticker: str) -> Optional[ValuationRequest]:
    """Terminal Expert : Graham."""
    st.subheader(ExpertTerminalTexts.TITLE_GRAHAM)
    st.latex(r"P = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}")

    st.markdown(ExpertTerminalTexts.SEC_1_GRAHAM_BASE)
    c1, c2 = st.columns(2)
    eps = c1.number_input(ExpertTerminalTexts.INP_EPS_NORM, value=None, format="%.2f")
    g_lt = c2.number_input(ExpertTerminalTexts.INP_GROWTH_G_SIMPLE, 0.0, 0.20, value=None, format="%.3f")
    st.divider()

    st.markdown(ExpertTerminalTexts.SEC_2_GRAHAM)
    c1, c2 = st.columns(2)
    yield_aaa = c1.number_input(ExpertTerminalTexts.INP_YIELD_AAA, 0.0, 0.20, value=None, format="%.3f")
    tau = c2.number_input(ExpertTerminalTexts.INP_TAX_SIMPLE, 0.0, 0.60, value=None, format="%.2f")
    st.divider()

    manual_peers = atom_peer_selection()
    scenarios = atom_scenario_configuration(ValuationMode.GRAHAM_1974_REVISED)

    if st.button(ExpertTerminalTexts.BTN_VALUATE_GRAHAM.format(ticker=ticker), type="primary", use_container_width=True):
        all_data = {"manual_fcf_base": eps, "fcf_growth_rate": g_lt, "corporate_aaa_yield": yield_aaa, "tax_rate": tau, "projection_years": 1, "enable_monte_carlo": False}
        params = safe_factory_params(all_data)
        params.scenarios = scenarios
        return ValuationRequest(ticker=ticker, projection_years=1, mode=ValuationMode.GRAHAM_1974_REVISED, input_source=InputSource.MANUAL, manual_params=params, options={"manual_peers": manual_peers})
    return None