"""
app/ui_components/ui_inputs_expert.py
ARCHITECTURE SEGMENTÉE — TERMINAL PROFESSIONNEL RÉACTIF (V6.3)
Souveraineté totale : Formules LaTeX, Réactivité Monte Carlo et Clarté Décimale.
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

# ==============================================================================
# 0. RÉFÉRENTIEL DES NOMS UNIFIÉS
# ==============================================================================

VALUATION_DISPLAY_NAMES = {
    ValuationMode.FCFF_TWO_STAGE: "FCFF Standard",
    ValuationMode.FCFF_NORMALIZED: "FCFF Fundamental",
    ValuationMode.FCFF_REVENUE_DRIVEN: "FCFF Growth",
    ValuationMode.RESIDUAL_INCOME_MODEL: "RIM",
    ValuationMode.GRAHAM_1974_REVISED: "Graham"
}

# ==============================================================================
# 1. LES ATOMES PROFESSIONNELS (STANDARD DÉCIMAL CLAIR)
# ==============================================================================

def atom_macro_rates_pro():
    c1, c2 = st.columns(2)
    rf = c1.number_input("Taux sans risque $R_f$ (décimal, ex: 0.042 pour 4.2%)", 0.0, 0.20, 0.042, 0.001, format="%.3f")
    mrp = c2.number_input("Prime de risque marché $MRP$ (décimal, ex: 0.055 pour 5.5%)", 0.0, 0.20, 0.055, 0.001, format="%.3f")
    return {"risk_free_rate": rf, "market_risk_premium": mrp}

def atom_beta_control_pro():
    beta = st.number_input("Coefficient Beta $\\beta$ (ex: 1.10)", 0.0, 5.0, 1.0, 0.05,
                           help="Mesure de volatilité relative. Saisir 0.0 pour utiliser le calcul automatique.")
    return {"manual_beta": beta}

def atom_tax_and_debt_pro(mode: ValuationMode):
    c1, c2 = st.columns(2)
    tax = c1.number_input("Taux d'imposition effectif (décimal, ex: 0.25 pour 25%)", 0.0, 0.60, 0.25, 0.01, format="%.2f")
    if mode == ValuationMode.GRAHAM_1974_REVISED:
        yield_aaa = c2.number_input("Rendement Obligations AAA $Y$ (décimal, ex: 0.045 pour 4.5%)", 0.0, 0.20, 0.045, 0.001, format="%.3f")
        return {"tax_rate": tax, "corporate_aaa_yield": yield_aaa}
    else:
        kd = c2.number_input("Coût de la dette brut $K_d$ (décimal, ex: 0.05 pour 5%)", 0.0, 0.20, 0.05, 0.001, format="%.3f")
        return {"tax_rate": tax, "cost_of_debt": kd}

def atom_terminal_strategy_pro():
    method = st.radio(
        "Stratégie de sortie",
        options=[TerminalValueMethod.GORDON_GROWTH, TerminalValueMethod.EXIT_MULTIPLE],
        format_func=lambda x: "Croissance Perpétuelle (Gordon)" if x == TerminalValueMethod.GORDON_GROWTH else "Multiple de Sortie",
        horizontal=True
    )
    c1, _ = st.columns(2)
    if method == TerminalValueMethod.GORDON_GROWTH:
        gn = c1.number_input("Taux de croissance à l'infini $g_n$ (décimal, ex: 0.02 pour 2%)", 0.0, 0.05, 0.02, 0.001, format="%.3f")
        return {"terminal_method": method, "perpetual_growth_rate": gn, "exit_multiple_value": 12.0}
    else:
        exit_m = c1.number_input("Multiple de sortie (EV/FCF ou EV/EBITDA, ex: 12.5)", 1.0, 50.0, 12.0, 0.5)
        return {"terminal_method": method, "perpetual_growth_rate": 0.02, "exit_multiple_value": exit_m}

def atom_equity_bridge_pro():
    st.caption("Ajustements Bilanciels (Unités monétaires en $, 0 = Auto)")
    c1, c2, c3 = st.columns(3)
    debt = c1.number_input("Dette Totale ($)", value=0.0, step=1e6, format="%.0f")
    cash = c2.number_input("Trésorerie ($)", value=0.0, step=1e6, format="%.0f")
    shares = c3.number_input("Actions (#)", value=0.0, step=1e5, format="%.0f")
    return {"manual_total_debt": debt, "manual_cash": cash, "manual_shares_outstanding": shares}

def atom_monte_carlo_pro():
    """Phase 6 : Simulation Probabiliste réactive (Positionnée en fin de flux)."""
    st.markdown("#### 6. Simulation Probabiliste (Analyse d'Incertitude)")
    enable = st.toggle("Activer Monte Carlo", value=False)
    if enable:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            sims = c1.select_slider("Itérations", options=[1000, 5000, 10000, 20000], value=5000)
            st.caption("Calibration des Volatilités (Décimales, ex: 0.02 pour 2%) :")
            v1, v2, v3 = st.columns(3)
            vb = v1.number_input("Vol. Beta", 0.0, 1.0, 0.10, 0.01, format="%.3f")
            vg = v2.number_input("Vol. Croissance $g$", 0.0, 0.20, 0.02, 0.005, format="%.3f")
            vgn = v3.number_input("Vol. $g_n$", 0.0, 0.05, 0.005, 0.001, format="%.3f")
            return {"enable_monte_carlo": True, "num_simulations": sims, "beta_volatility": vb, "growth_volatility": vg, "terminal_growth_volatility": vgn}
    return {"enable_monte_carlo": False}

# ==============================================================================
# 2. FACTORY
# ==============================================================================

def factory_pydantic_params(raw_data: Dict[str, Any]) -> DCFParameters:
    processed = raw_data.copy()
    sovereign_fields = ["manual_total_debt", "manual_cash", "manual_shares_outstanding", "manual_fcf_base", "manual_book_value", "manual_beta"]
    for field in sovereign_fields:
        if processed.get(field) == 0:
            processed[field] = None
    return DCFParameters(**processed)

# ==============================================================================
# 3. TERMINAUX EXPERTS (VUES RÉACTIVES)
# ==============================================================================

def render_expert_fcff_standard(ticker: str) -> Optional[ValuationRequest]:
    name = VALUATION_DISPLAY_NAMES[ValuationMode.FCFF_TWO_STAGE]
    st.subheader(f"Terminal Expert : {name}")
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    st.markdown("#### 1. Détermination du flux de base ($FCF_0$)")
    fcf_base = st.number_input("Flux de trésorerie disponible (TTM) (en $)", value=0.0, format="%.0f")
    st.divider()

    st.markdown("#### 2. Phase de croissance explicite : $FCF_t = FCF_{t-1} \\times (1 + g)$")
    c1, c2 = st.columns(2)
    n_years = c1.slider("Années de projection", 3, 15, 5)
    g_rate = c2.number_input("Croissance annuelle $g$ (décimal, ex: 0.05 pour 5%)", -0.50, 1.0, 0.05, 0.005, format="%.3f")
    st.divider()

    st.markdown("#### 3. Coût Moyen Pondéré du Capital (WACC)")
    wacc_data = atom_macro_rates_pro(); beta_data = atom_beta_control_pro(); tax_debt_data = atom_tax_and_debt_pro(ValuationMode.FCFF_TWO_STAGE)
    st.divider()

    st.markdown("#### 4. Valeur de continuation (Sortie)")
    terminal_data = atom_terminal_strategy_pro(); st.divider()

    st.markdown("#### 5. Passage à la Valeur Actionnaire (Bridge)")
    bridge_data = atom_equity_bridge_pro(); st.divider()

    mc_data = atom_monte_carlo_pro()

    if st.button(f"Établir la valorisation intrinsèque ({ticker})", type="primary", use_container_width=True):
        all_data = {"manual_fcf_base": fcf_base, "projection_years": n_years, "fcf_growth_rate": g_rate, **wacc_data, **beta_data, **tax_debt_data, **terminal_data, **bridge_data, **mc_data}
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_TWO_STAGE, input_source=InputSource.MANUAL, manual_params=factory_pydantic_params(all_data))
    return None

def render_expert_fcff_fundamental(ticker: str) -> Optional[ValuationRequest]:
    name = VALUATION_DISPLAY_NAMES[ValuationMode.FCFF_NORMALIZED]
    st.subheader(f"Terminal Expert : {name}")
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_{normalisé} \times (1+g)^t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    st.markdown("#### 1. Flux normalisé ($FCF_0$)")
    fcf_base = st.number_input("Flux lissé de cycle (en $)", value=0.0, format="%.0f")
    st.divider()

    st.markdown("#### 2. Croissance de cycle : $FCF_t = FCF_0 \\times (1+g)^t$")
    c1, c2 = st.columns(2)
    n_years = c1.slider("Années cycle", 3, 15, 5)
    g_rate = c2.number_input("Croissance moyenne (décimal, ex: 0.03 pour 3%)", -0.20, 0.30, 0.03, 0.005, format="%.3f")
    st.divider()

    st.markdown("#### 3. WACC"); wacc_data = atom_macro_rates_pro(); beta_data = atom_beta_control_pro(); tax_debt_data = atom_tax_and_debt_pro(ValuationMode.FCFF_NORMALIZED)
    st.divider(); st.markdown("#### 4. Sortie"); terminal_data = atom_terminal_strategy_pro()
    st.divider(); st.markdown("#### 5. Bridge"); bridge_data = atom_equity_bridge_pro(); st.divider()

    mc_data = atom_monte_carlo_pro()

    if st.button(f"Lancer la valorisation Fondamentale ({ticker})", type="primary", use_container_width=True):
        all_data = {"manual_fcf_base": fcf_base, "projection_years": n_years, "fcf_growth_rate": g_rate, **wacc_data, **beta_data, **tax_debt_data, **terminal_data, **bridge_data, **mc_data}
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_NORMALIZED, input_source=InputSource.MANUAL, manual_params=factory_pydantic_params(all_data))
    return None

def render_expert_fcff_growth(ticker: str) -> Optional[ValuationRequest]:
    name = VALUATION_DISPLAY_NAMES[ValuationMode.FCFF_REVENUE_DRIVEN]
    st.subheader(f"Terminal Expert : {name}")
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{Rev_0(1+g_{rev})^t \times Margin_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    st.markdown("#### 1. Chiffre d'Affaires ($Rev_0$)")
    rev_base = st.number_input("Chiffre d'affaires TTM (en $)", value=0.0, format="%.0f")
    st.divider()

    st.markdown("#### 2. Convergence des Marges")
    c1, c2, c3 = st.columns(3)
    n_years = c1.slider("Années de projection", 3, 15, 5)
    g_rev = c2.number_input("Croissance CA (décimal, ex: 0.15 pour 15%)", 0.0, 1.0, 0.15, 0.005, format="%.3f")
    m_target = c3.number_input("Marge FCF cible (décimal, ex: 0.20 pour 20%)", 0.0, 0.80, 0.20, 0.01, format="%.2f")
    st.divider()

    st.markdown("#### 3. WACC"); wacc_data = atom_macro_rates_pro(); beta_data = atom_beta_control_pro(); tax_debt_data = atom_tax_and_debt_pro(ValuationMode.FCFF_REVENUE_DRIVEN)
    st.divider(); st.markdown("#### 4. Sortie"); terminal_data = atom_terminal_strategy_pro()
    st.divider(); st.markdown("#### 5. Bridge"); bridge_data = atom_equity_bridge_pro(); st.divider()

    mc_data = atom_monte_carlo_pro()

    if st.button(f"Lancer la valorisation Growth ({ticker})", type="primary", use_container_width=True):
        all_data = {"manual_fcf_base": rev_base, "projection_years": n_years, "fcf_growth_rate": g_rev, "target_fcf_margin": m_target, **wacc_data, **beta_data, **tax_debt_data, **terminal_data, **bridge_data, **mc_data}
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_REVENUE_DRIVEN, input_source=InputSource.MANUAL, manual_params=factory_pydantic_params(all_data))
    return None

def render_expert_rim(ticker: str) -> Optional[ValuationRequest]:
    name = VALUATION_DISPLAY_NAMES[ValuationMode.RESIDUAL_INCOME_MODEL]
    st.subheader(f"Terminal Expert : {name}")
    st.latex(r"V_0 = BV_0 + \sum_{t=1}^{n} \frac{NetIncome_t - (k_e \times BV_{t-1})}{(1+k_e)^t} + \frac{TV_{RI}}{(1+k_e)^n}")

    st.markdown("#### 1. Valeur Comptable & Profits")
    c1, c2 = st.columns(2)
    bv = c1.number_input("Book Value (Equity) (en $)", value=0.0, format="%.0f")
    ni = c2.number_input("Résultat Net TTM (en $)", value=0.0, format="%.0f")
    st.divider()

    st.markdown("#### 2. Horizon & Croissance")
    c1, c2 = st.columns(2)
    n_years = c1.slider("Années de projection", 3, 15, 5)
    g_ni = c2.number_input("Croissance attendue RN (décimal, ex: 0.05 pour 5%)", 0.0, 0.50, 0.05, 0.005, format="%.3f")
    st.divider()

    st.markdown("#### 3. Coût des Fonds Propres"); wacc_data = atom_macro_rates_pro(); beta_data = atom_beta_control_pro(); tax_debt_data = atom_tax_and_debt_pro(ValuationMode.RESIDUAL_INCOME_MODEL)
    st.divider(); st.markdown("#### 4. Sortie"); terminal_data = atom_terminal_strategy_pro()
    st.divider(); st.markdown("#### 5. Bridge"); bridge_data = atom_equity_bridge_pro(); st.divider()

    mc_data = atom_monte_carlo_pro()

    if st.button(f"Lancer la valorisation RIM ({ticker})", type="primary", use_container_width=True):
        all_data = {"manual_book_value": bv, "manual_fcf_base": ni, "projection_years": n_years, "fcf_growth_rate": g_ni, **wacc_data, **beta_data, **tax_debt_data, **terminal_data, **bridge_data, **mc_data}
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.RESIDUAL_INCOME_MODEL, input_source=InputSource.MANUAL, manual_params=factory_pydantic_params(all_data))
    return None

def render_expert_graham(ticker: str) -> Optional[ValuationRequest]:
    name = VALUATION_DISPLAY_NAMES[ValuationMode.GRAHAM_1974_REVISED]
    st.subheader(f"Terminal Expert : {name}")
    st.latex(r"V_0 = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}")

    st.markdown("#### 1. Capacité Bénéficiaire")
    c1, c2 = st.columns(2)
    eps = c1.number_input("EPS normalisé (en $)", value=0.0, format="%.2f")
    g_lt = c2.number_input("Croissance attendue $g$ (décimal, ex: 0.05 pour 5%)", 0.0, 0.20, 0.05, 0.005, format="%.3f")
    st.divider()

    st.markdown("#### 2. Conditions de Marché AAA")
    tax_debt_data = atom_tax_and_debt_pro(ValuationMode.GRAHAM_1974_REVISED)

    if st.button(f"Calculer la valeur Graham ({ticker})", type="primary", use_container_width=True):
        all_data = {"manual_fcf_base": eps, "fcf_growth_rate": g_lt, **tax_debt_data, "projection_years": 1, "perpetual_growth_rate": 0.0, "risk_free_rate": 0.0, "market_risk_premium": 0.0, "enable_monte_carlo": False}
        return ValuationRequest(ticker=ticker, projection_years=1, mode=ValuationMode.GRAHAM_1974_REVISED, input_source=InputSource.MANUAL, manual_params=factory_pydantic_params(all_data))
    return None