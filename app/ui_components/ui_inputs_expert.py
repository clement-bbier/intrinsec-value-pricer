"""
app/ui_components/ui_inputs_expert.py
ARCHITECTURE ATOMIQUE — TERMINAL PROFESSIONNEL RÉACTIF (V7.1)
Rôle : Saisie expert avec Intelligence de Devise et fallback Auto.
Version : Épurée (Zéro Émoji).
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
# 0. RÉFÉRENTIEL DES NOMS ET SÉCURITÉ
# ==============================================================================

VALUATION_DISPLAY_NAMES = {
    ValuationMode.FCFF_TWO_STAGE: "FCFF Standard",
    ValuationMode.FCFF_NORMALIZED: "FCFF Fundamental",
    ValuationMode.FCFF_REVENUE_DRIVEN: "FCFF Growth",
    ValuationMode.RESIDUAL_INCOME_MODEL: "RIM",
    ValuationMode.GRAHAM_1974_REVISED: "Graham"
}

def safe_factory_params(all_data: Dict[str, Any]) -> DCFParameters:
    """
    Prépare les données pour DCFParameters en garantissant la présence
    des champs obligatoires et en gérant les fallbacks vers les données automatiques.
    """
    final_data = {
        "risk_free_rate": 0.0,
        "market_risk_premium": 0.0,
        "corporate_aaa_yield": 0.0,
        "tax_rate": 0.0,
        "cost_of_debt": 0.0,
        "fcf_growth_rate": 0.0,
        "perpetual_growth_rate": 0.0,
        "exit_multiple_value": 0.0,
        "projection_years": 5,
        "target_fcf_margin": 0.0,
        "terminal_method": TerminalValueMethod.GORDON_GROWTH,
        "enable_monte_carlo": False
    }

    # Mise à jour avec les saisies UI
    for key, value in all_data.items():
        if value is not None:
            final_data[key] = value

    # Traitement des souverainetés (0 -> None pour déclencher l'Auto Yahoo)
    sovereign_fields = [
        "manual_total_debt", "manual_cash", "manual_shares_outstanding",
        "manual_fcf_base", "manual_book_value", "manual_beta"
    ]
    for field in sovereign_fields:
        if final_data.get(field) == 0:
            final_data[field] = None

    return DCFParameters(**final_data)

# ==============================================================================
# 1. LES ATOMES INTELLIGENTS (ARCHITECTURE ÉPURÉE)
# ==============================================================================

def atom_currency_warning(ticker: str):
    """Avertissement sur la devise de rapport pour guider l'expert."""
    st.info(
        f"Note sur la devise : Les montants doivent être saisis dans la devise de rapport de {ticker}. "
        "Laissez à 0 pour que le système utilise automatiquement les données de marché (Yahoo Finance)."
    )

def atom_discount_rate_smart(mode: ValuationMode) -> Dict[str, Any]:
    """Gère la saisie du coût du capital avec ses formules respectives."""
    st.markdown("#### 3. Coût du Capital")

    if mode == ValuationMode.RESIDUAL_INCOME_MODEL:
        st.latex(r"k_e = R_f + \beta \times MRP")
    else:
        st.latex(r"WACC = w_e [R_f + \beta(MRP)] + w_d [k_d(1-\tau)]")

    manual_price = st.number_input("Prix de l'action (0 = Auto Yahoo)", 0.0, 10000.0, 0.0, 0.01, format="%.2f")

    col_a, col_b = st.columns(2)
    rf = col_a.number_input("Taux sans risque Rf (0 = Auto)", 0.0, 0.20, 0.04, 0.001, format="%.3f")
    beta = col_b.number_input("Coefficient Beta β (0 = Auto)", 0.0, 5.0, 1.1, 0.05, format="%.2f")
    mrp = col_a.number_input("Prime de risque marché MRP (0 = Auto)", 0.0, 0.20, 0.055, 0.001, format="%.3f")

    res = {"risk_free_rate": rf, "manual_beta": beta, "market_risk_premium": mrp, "manual_stock_price": manual_price if manual_price > 0 else None}

    if mode != ValuationMode.RESIDUAL_INCOME_MODEL:
        kd = col_b.number_input("Coût de la dette brut kd (0 = Auto)", 0.0, 0.20, 0.05, 0.001, format="%.3f")
        tau = col_a.number_input("Taux d'imposition effectif τ (0 = Auto)", 0.0, 0.60, 0.25, 0.01, format="%.2f")
        res.update({"cost_of_debt": kd, "tax_rate": tau})

    st.divider()
    return res

def atom_terminal_smart(formula_latex: str) -> Dict[str, Any]:
    """Gère la valeur de continuation."""
    st.markdown("#### 4. Valeur de continuation")
    st.latex(formula_latex)

    method = st.radio(
        "Modèle de sortie",
        options=[TerminalValueMethod.GORDON_GROWTH, TerminalValueMethod.EXIT_MULTIPLE],
        format_func=lambda x: "Croissance Perpétuelle (Gordon)" if x == TerminalValueMethod.GORDON_GROWTH else "Multiple de Sortie",
        horizontal=True
    )

    c1, _ = st.columns(2)
    if method == TerminalValueMethod.GORDON_GROWTH:
        gn = c1.number_input("Taux de croissance à l'infini gn", 0.0, 0.05, 0.02, 0.001, format="%.3f")
        res = {"terminal_method": method, "perpetual_growth_rate": gn, "exit_multiple_value": 0.0}
    else:
        exit_m = c1.number_input("Multiple de sortie (facteur x)", 1.0, 50.0, 12.0, 0.5)
        res = {"terminal_method": method, "exit_multiple_value": exit_m, "perpetual_growth_rate": 0.0}
    st.divider()
    return res

def atom_bridge_smart(formula_latex: str) -> Dict[str, Any]:
    """Gère l'ajustement de la structure financière (Equity Bridge)."""
    st.markdown("#### 5. Ajustements de structure")
    st.latex(formula_latex)

    c1, c2, c3 = st.columns(3)
    debt = c1.number_input("Dette Totale (0 = Auto)", value=0.0, step=1e6, format="%.0f")
    cash = c2.number_input("Trésorerie (0 = Auto)", value=0.0, step=1e6, format="%.0f")
    shares = c3.number_input("Actions en circulation (0 = Auto)", value=0.0, step=1e5, format="%.0f")
    st.divider()
    return {"manual_total_debt": debt, "manual_cash": cash, "manual_shares_outstanding": shares}

def atom_monte_carlo_smart() -> Dict[str, Any]:
    """Simulation Probabiliste (Incertitude)."""
    st.markdown("#### 6. Analyse de risque (Monte Carlo)")
    enable = st.toggle("Activer la simulation", value=False)
    if enable:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            sims = c1.select_slider("Itérations", options=[1000, 5000, 10000, 20000], value=5000)
            st.caption("Calibration des Volatilités :")
            v1, v2, v3 = st.columns(3)
            vb = v1.number_input("Vol. β", 0.0, 1.0, 0.10, 0.01, format="%.3f")
            vg = v2.number_input("Vol. g", 0.0, 0.20, 0.02, 0.005, format="%.3f")
            vgn = v3.number_input("Vol. gn", 0.0, 0.05, 0.005, 0.001, format="%.3f")
            return {
                "enable_monte_carlo": True, "num_simulations": sims,
                "beta_volatility": vb, "growth_volatility": vg, "terminal_growth_volatility": vgn
            }
    return {"enable_monte_carlo": False}

# ==============================================================================
# 2. LES TERMINAUX EXPERTS
# ==============================================================================

def render_expert_fcff_standard(ticker: str) -> Optional[ValuationRequest]:
    st.subheader(f"Terminal Expert : FCFF Standard")
    atom_currency_warning(ticker)
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    st.markdown("#### 1. Flux de trésorerie de base ($FCF_0$)")
    fcf_base = st.number_input("Dernier flux TTM (0 = Auto)", value=0.0, format="%.0f")
    st.divider()

    st.markdown("#### 2. Phase de croissance ($g$)")
    st.latex(r"FCF_t = FCF_{t-1} \times (1 + g)")
    c1, c2 = st.columns(2)
    n_years = c1.slider("Horizon de projection (n années)", 3, 15, 5)
    g_rate = c2.number_input("Croissance moyenne attendue g", -0.50, 1.0, 0.05, 0.005, format="%.3f")
    st.divider()

    wacc_data = atom_discount_rate_smart(ValuationMode.FCFF_TWO_STAGE)
    tv_data = atom_terminal_smart(r"TV_n = \begin{cases} \dfrac{FCF_n(1+g_n)}{WACC - g_n} & \text{(Gordon)} \\ FCF_n \times \text{Multiple} & \text{(Exit)} \end{cases}")
    bridge_data = atom_bridge_smart(r"P = \dfrac{V_0 - D + C}{S}")
    mc_data = atom_monte_carlo_smart()

    if st.button(f"Lancer la valorisation {ticker}", type="primary", use_container_width=True):
        all_data = {"manual_fcf_base": fcf_base, "projection_years": n_years, "fcf_growth_rate": g_rate, **wacc_data, **tv_data, **bridge_data, **mc_data}
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_TWO_STAGE, input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data))
    return None

def render_expert_fcff_fundamental(ticker: str) -> Optional[ValuationRequest]:
    st.subheader(f"Terminal Expert : FCFF Fundamental")
    atom_currency_warning(ticker)
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_{norm} \times (1+g)^t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    st.markdown("#### 1. Flux normalisé de base ($FCF_{norm}$)")
    fcf_base = st.number_input("Flux lissé de cycle (0 = Auto)", value=0.0, format="%.0f")
    st.divider()

    st.markdown("#### 2. Croissance moyenne de cycle ($g$)")
    st.latex(r"FCF_t = FCF_{norm} \times (1+g)^t")
    c1, c2 = st.columns(2)
    n_years = c1.slider("Horizon du cycle (n années)", 3, 15, 5)
    g_rate = c2.number_input("Croissance moyenne attendue g", -0.20, 0.30, 0.03, 0.005, format="%.3f")
    st.divider()

    wacc_data = atom_discount_rate_smart(ValuationMode.FCFF_NORMALIZED)
    tv_data = atom_terminal_smart(r"TV_n = \begin{cases} \dfrac{FCF_n(1+g_n)}{WACC - g_n} & \text{(Gordon)} \\ FCF_n \times \text{Multiple} & \text{(Exit)} \end{cases}")
    bridge_data = atom_bridge_smart(r"P = \dfrac{V_0 - D + C}{S}")
    mc_data = atom_monte_carlo_smart()

    if st.button(f"Lancer la valorisation Fondamentale ({ticker})", type="primary", use_container_width=True):
        all_data = {"manual_fcf_base": fcf_base, "projection_years": n_years, "fcf_growth_rate": g_rate, **wacc_data, **tv_data, **bridge_data, **mc_data}
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_NORMALIZED, input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data))
    return None

def render_expert_fcff_growth(ticker: str) -> Optional[ValuationRequest]:
    st.subheader(f"Terminal Expert : FCFF Growth")
    atom_currency_warning(ticker)
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{Rev_0(1+g_{rev})^t \times Margin_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    st.markdown("#### 1. Chiffre d'Affaires de base ($Rev_0$)")
    rev_base = st.number_input("Chiffre d'affaires TTM (0 = Auto)", value=0.0, format="%.0f")
    st.divider()

    st.markdown("#### 2. Horizon et Convergence des Marges")
    st.latex(r"Rev_t = Rev_0 \times (1 + g_{rev})^t \quad | \quad Margin_t \rightarrow Margin_{target}")
    c1, c2, c3 = st.columns(3)
    n_years = c1.slider("Années de projection (n)", 3, 15, 5)
    g_rev = c2.number_input("Croissance CA g_rev", 0.0, 1.0, 0.15, 0.005, format="%.3f")
    m_target = c3.number_input("Marge FCF cible", 0.0, 0.80, 0.20, 0.01, format="%.2f")
    st.divider()

    wacc_data = atom_discount_rate_smart(ValuationMode.FCFF_REVENUE_DRIVEN)
    tv_data = atom_terminal_smart(r"TV_n = \begin{cases} \dfrac{FCF_n(1+g_n)}{WACC - g_n} & \text{(Gordon)} \\ FCF_n \times \text{Multiple} & \text{(Exit)} \end{cases}")
    bridge_data = atom_bridge_smart(r"P = \dfrac{V_0 - D + C}{S}")
    mc_data = atom_monte_carlo_smart()

    if st.button(f"Lancer l'analyse Growth : {ticker}", type="primary", use_container_width=True):
        all_data = {"manual_fcf_base": rev_base, "projection_years": n_years, "fcf_growth_rate": g_rev, "target_fcf_margin": m_target, **wacc_data, **tv_data, **bridge_data, **mc_data}
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_REVENUE_DRIVEN, input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data))
    return None

def render_expert_rim(ticker: str) -> Optional[ValuationRequest]:
    st.subheader(f"Terminal Expert : RIM")
    atom_currency_warning(ticker)
    st.latex(r"P = BV_0 + \sum_{t=1}^{n} \frac{NI_t - (k_e \times BV_{t-1})}{(1+k_e)^t} + \frac{TV_{RI}}{(1+k_e)^n}")

    st.markdown("#### 1. Valeur Comptable ($BV_0$) et Profits ($NI_t$)")
    c1, c2 = st.columns(2)
    bv = c1.number_input("Valeur comptable initiale BV0 (0 = Auto)", value=0.0, format="%.0f")
    ni = c2.number_input("Résultat Net TTM NI (0 = Auto)", value=0.0, format="%.0f")
    st.divider()

    st.markdown("#### 2. Horizon et Croissance des profits ($g$)")
    st.latex(r"NI_t = NI_{t-1} \times (1 + g)")
    c1, c2 = st.columns(2)
    n_years = c1.slider("Années de projection (n)", 3, 15, 5)
    g_ni = c2.number_input("Croissance moyenne attendue g", 0.0, 0.50, 0.05, 0.005, format="%.3f")
    st.divider()

    ke_data = atom_discount_rate_smart(ValuationMode.RESIDUAL_INCOME_MODEL)
    tv_data = atom_terminal_smart(r"TV_{RI} = \dfrac{(NI_n - k_e \times BV_{n-1}) \times (1+g_n)}{k_e - g_n}")
    bridge_data = atom_bridge_smart(r"P = \dfrac{\text{Equity Value}}{\text{Actions}}")
    mc_data = atom_monte_carlo_smart()

    if st.button(f"Lancer la valorisation RIM : {ticker}", type="primary", use_container_width=True):
        all_data = {"manual_book_value": bv, "manual_fcf_base": ni, "projection_years": n_years, "fcf_growth_rate": g_ni, **ke_data, **tv_data, **bridge_data, **mc_data}
        return ValuationRequest(ticker=ticker, projection_years=n_years, mode=ValuationMode.RESIDUAL_INCOME_MODEL, input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data))
    return None

def render_expert_graham(ticker: str) -> Optional[ValuationRequest]:
    st.subheader(f"Terminal Expert : Graham")
    atom_currency_warning(ticker)
    st.latex(r"P = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}")

    st.markdown("#### 1. Profits ($EPS$) et Croissance ($g$)")
    st.latex(r"P \propto EPS \times (8.5 + 2g)")
    c1, c2 = st.columns(2)
    eps = c1.number_input("BPA normalisé EPS (0 = Auto)", value=0.0, format="%.2f")
    g_lt = c2.number_input("Croissance moyenne g (ex: 0.05)", 0.0, 0.20, 0.05, 0.005, format="%.3f")
    st.divider()

    st.markdown("#### 2. Marché obligataire ($Y$) et Fiscalité ($\\tau$)")
    st.latex(r"P \propto \frac{4.4}{Y}")
    c1, c2 = st.columns(2)
    yield_aaa = c1.number_input("Rendement Obligations AAA Y", 0.0, 0.20, 0.045, 0.001, format="%.3f")
    tau = c2.number_input("Taux d'imposition τ", 0.0, 0.60, 0.25, 0.01, format="%.2f")
    st.divider()

    if st.button(f"Calculer la valeur Graham : {ticker}", type="primary", use_container_width=True):
        all_data = {"manual_fcf_base": eps, "fcf_growth_rate": g_lt, "corporate_aaa_yield": yield_aaa, "tax_rate": tau, "projection_years": 1, "enable_monte_carlo": False}
        return ValuationRequest(ticker=ticker, projection_years=1, mode=ValuationMode.GRAHAM_1974_REVISED, input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data))
    return None