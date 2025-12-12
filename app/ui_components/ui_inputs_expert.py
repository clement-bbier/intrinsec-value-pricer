from __future__ import annotations

from typing import Optional, Tuple

import streamlit as st

from core.models import DCFParameters, InputSource, ValuationMode, ValuationRequest
from core.computation.transformations import relever_beta
from core.methodology.texts import TOOLTIPS

ExpertReturn = Tuple[str, int, DCFParameters, float, ValuationMode, bool]


def _display_simple_expert_inputs(ticker: str, years: int) -> DCFParameters:
    st.markdown("#### Hypothèses de Croissance")
    c1, c2 = st.columns(2)
    with c1:
        g = st.number_input(
            "Croissance FCF (g) %",
            value=5.0, step=0.5, format="%.1f",
            help=TOOLTIPS["growth_g"]
        ) / 100.0
    with c2:
        g_perp = st.number_input(
            "Croissance Terminale (g∞) %",
            value=2.0, step=0.1, min_value=0.0, max_value=5.0, format="%.1f",
            help=TOOLTIPS["growth_perp"]
        ) / 100.0

    st.markdown("#### Coût du Capital (WACC)")
    c1, c2 = st.columns(2)
    with c1:
        rf = st.number_input(
            "Taux sans risque (Rf) %",
            value=4.0, step=0.1, format="%.1f",
            help=TOOLTIPS["rf"]
        ) / 100.0
    with c2:
        mrp = st.number_input(
            "Prime de risque (MRP) %",
            value=5.5, step=0.1, format="%.1f",
            help=TOOLTIPS["mrp"]
        ) / 100.0

    c3, c4 = st.columns(2)
    with c3:
        kd = st.number_input(
            "Coût Dette Brut (Kd) %",
            value=5.0, step=0.25, format="%.2f",
            help=TOOLTIPS["cost_debt"]
        ) / 100.0
    with c4:
        tax = st.number_input(
            "Taux Impôt (IS) %",
            value=25.0, step=1.0, format="%.1f",
            help=TOOLTIPS["tax_rate"]
        ) / 100.0

    return DCFParameters(
        risk_free_rate=rf,
        market_risk_premium=mrp,
        cost_of_debt=kd,
        tax_rate=tax,
        fcf_growth_rate=g,
        perpetual_growth_rate=g_perp,
        projection_years=years,
    )


def _display_fundamental_expert_inputs(ticker: str, years: int) -> Tuple[DCFParameters, float]:
    # 1. CROISSANCE
    with st.expander("Paramètres de Croissance (Cycle)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            g = st.number_input(
                "Croissance Initiale %",
                value=5.0, step=0.5, format="%.1f",
                help=TOOLTIPS["growth_g"]
            ) / 100.0
            high_growth_years = st.slider("Durée Plateau Croissance (années)", 0, 10, 5)
        with c2:
            g_perp = st.number_input(
                "Croissance Terminale (g∞) %",
                value=2.0, step=0.1, min_value=0.0, max_value=4.0, format="%.1f",
                help=TOOLTIPS["growth_perp"]
            ) / 100.0

    # 2. STRUCTURE & DETTE
    with st.expander("Structure Financière & Dette", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            kd = st.number_input(
                "Coût Dette Brut (Kd) %",
                value=5.0, step=0.25, key="kd_fund",
                help=TOOLTIPS["cost_debt"]
            ) / 100.0
            tax = st.number_input(
                "Taux Impôt (IS) %",
                value=25.0, step=1.0, key="tax_fund",
                help=TOOLTIPS["tax_rate"]
            ) / 100.0
        with c2:
            st.markdown("**Poids Cibles (Target)**", help=TOOLTIPS["target_weights"])
            w_e = st.number_input("Poids Equity %", value=80.0, step=5.0, max_value=100.0) / 100.0
            w_d = st.number_input("Poids Dette %", value=20.0, step=5.0, max_value=100.0) / 100.0

    # 3. EQUITY
    with st.expander("Coût des Fonds Propres (Equity)", expanded=True):
        mode_ke = st.radio("Méthode Calcul Ke", ["CAPM (Modèle)", "Saisie Directe"], horizontal=True,
                           label_visibility="collapsed")

        beta_final = 1.0
        manual_ke = None
        rf = 0.04
        mrp = 0.055

        if mode_ke == "CAPM (Modèle)":
            beta_type = st.radio("Source Beta", ["Beta Levier (Observé)", "Beta Désendetté (Hamada)"], horizontal=True)
            c1, c2 = st.columns(2)
            with c1:
                rf = st.number_input("Taux sans Risque (Rf) %", value=4.0, step=0.1, help=TOOLTIPS["rf"]) / 100.0
            with c2:
                mrp = st.number_input("Prime de Risque (MRP) %", value=5.5, step=0.1, help=TOOLTIPS["mrp"]) / 100.0

            if beta_type == "Beta Levier (Observé)":
                beta_final = st.number_input("Beta", value=1.0, step=0.05, help=TOOLTIPS["beta"])
            else:
                beta_u = st.number_input("Beta Désendetté (Unlevered)", value=0.8, step=0.05,
                                         help="Beta du risque opérationnel pur.")
                target_d_e = st.number_input("Dette/Equity Cible %", value=30.0, step=5.0) / 100.0
                beta_final = relever_beta(beta_u, tax, target_d_e, 1.0)
                st.caption(f"Beta Réendetté Calculé : {beta_final:.2f}")
        else:
            manual_ke = st.number_input("Coût Equity Cible (Ke) %", value=8.5, step=0.1) / 100.0
            beta_final = st.number_input("Beta (Pour information)", value=1.0)

    params = DCFParameters(
        risk_free_rate=rf,
        market_risk_premium=mrp,
        cost_of_debt=kd,
        tax_rate=tax,
        fcf_growth_rate=g,
        perpetual_growth_rate=g_perp,
        projection_years=years,
        high_growth_years=int(high_growth_years),
        target_equity_weight=float(w_e),
        target_debt_weight=float(w_d),
        manual_cost_of_equity=manual_ke,
    )
    params.normalize_weights()
    return params, float(beta_final)


def _display_monte_carlo_expert_inputs(ticker: str, years: int) -> Tuple[DCFParameters, float]:
    base_params, beta = _display_fundamental_expert_inputs(ticker, years)

    with st.expander("Simulation Monte Carlo (Volatilité)", expanded=True):
        st.caption("Écart-type relatif des paramètres (Sigma).")
        c1, c2 = st.columns(2)
        with c1:
            vol_beta = st.number_input(
                "Volatilité Beta %",
                value=15.0, step=1.0,
                help=TOOLTIPS["volatility"]
            ) / 100.0
        with c2:
            vol_g = st.number_input(
                "Volatilité Croissance %",
                value=20.0, step=1.0,
                help=TOOLTIPS["volatility"]
            ) / 100.0

    base_params.beta_volatility = float(vol_beta)
    base_params.growth_volatility = float(vol_g)
    base_params.terminal_growth_volatility = float(vol_g) / 2.0

    return base_params, beta


def display_expert_request(default_ticker: str, default_years: int) -> Optional[ValuationRequest]:
    st.subheader("Paramètres Manuels (Expert)")

    method_options = {
        "DCF Simplifié": ValuationMode.SIMPLE_FCFF,
        "DCF Analytique": ValuationMode.FUNDAMENTAL_FCFF,
        "DCF Probabiliste": ValuationMode.MONTE_CARLO,
    }
    label = st.selectbox("Méthode de Valorisation", list(method_options.keys()))
    mode = method_options[label]

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        ticker = st.text_input("Ticker", value=default_ticker).upper().strip()
    with c2:
        years = st.slider("Horizon de Projection (années)", 3, 15, int(default_years))

    if mode == ValuationMode.SIMPLE_FCFF:
        params = _display_simple_expert_inputs(ticker, years)
        beta_final = st.number_input("Beta", value=1.0, step=0.05, help=TOOLTIPS["beta"])
    elif mode == ValuationMode.FUNDAMENTAL_FCFF:
        params, beta_final = _display_fundamental_expert_inputs(ticker, years)
    else:
        params, beta_final = _display_monte_carlo_expert_inputs(ticker, years)

    with st.expander("Avancé : Surcharge Flux Initial", expanded=False):
        if st.checkbox("Surcharger FCF de Base"):
            params.manual_fcf_base = st.number_input("FCF Manuel (Devise Locale)", value=100_000_000.0,
                                                     step=1_000_000.0, format="%.0f")

    st.markdown("---")
    submitted = st.button("Lancer l'analyse", type="primary", use_container_width=True)

    if not submitted or not ticker:
        return None

    return ValuationRequest(
        ticker=ticker,
        projection_years=int(years),
        mode=mode,
        input_source=InputSource.MANUAL,
        manual_params=params,
        manual_beta=float(beta_final),
    )


def display_expert_inputs(default_ticker: str, default_years: int) -> Optional[ExpertReturn]:
    req = display_expert_request(default_ticker, default_years)
    if req is None: return None
    return req.ticker, req.projection_years, req.manual_params, req.manual_beta, req.mode, True