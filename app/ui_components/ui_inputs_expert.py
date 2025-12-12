from __future__ import annotations

from typing import Optional, Tuple

import streamlit as st

from core.models import DCFParameters, InputSource, ValuationMode, ValuationRequest
from core.computation.transformations import relever_beta

ExpertReturn = Tuple[str, int, DCFParameters, float, ValuationMode, bool]


def _display_simple_expert_inputs(ticker: str, years: int) -> DCFParameters:
    with st.expander("Hypothèses de Croissance", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            g = st.number_input("Taux Croissance (g) %", value=5.0, step=0.5) / 100
        with c2:
            g_perp = st.number_input("Taux Terminal (g∞) %", value=2.0, step=0.1, max_value=5.0) / 100

    with st.expander("Coût du Capital (WACC)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            rf = st.number_input("Taux sans risque %", value=4.0, step=0.1) / 100
        with c2:
            mrp = st.number_input("Prime de risque %", value=5.5, step=0.1) / 100

        c3, c4 = st.columns(2)
        with c3:
            kd = st.number_input("Coût Dette Brut %", value=5.0, step=0.25) / 100
        with c4:
            tax = st.number_input("Taux Impôt %", value=25.0, step=1.0) / 100

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
    with st.expander("Croissance & Flux", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            g = st.number_input("Taux Croissance Initial %", value=5.0, step=0.5) / 100
            high_growth_years = st.slider("Durée Phase Haute (années)", 0, 10, 5)
        with c2:
            g_perp = st.number_input("Taux Terminal (g∞) %", value=2.0, step=0.1) / 100

    with st.expander("Coût des Fonds Propres (Equity)", expanded=True):
        capm_mode = st.radio(
            "Méthode de calcul",
            ["CAPM (Modèle)", "Saisie Directe"],
            horizontal=True,
            label_visibility="collapsed",
        )

        beta_final = 1.0
        manual_ke = None
        rf = 0.04
        mrp = 0.055

        if capm_mode == "CAPM (Modèle)":
            beta_type = st.radio(
                "Source Beta",
                ["Beta Levier (Observé)", "Beta Désendetté (Hamada)"],
                horizontal=True,
            )
            c1, c2 = st.columns(2)
            with c1:
                rf = st.number_input("Taux sans Risque %", value=4.0, step=0.1) / 100
            with c2:
                mrp = st.number_input("Prime de Risque %", value=5.5, step=0.1) / 100

            if beta_type == "Beta Levier (Observé)":
                beta_final = st.number_input("Beta", value=1.0, step=0.05)
            else:
                beta_u = st.number_input("Beta Désendetté", value=0.8, step=0.05)
                target_d_e = st.number_input("Dette/Equity Cible %", value=30.0, step=5.0) / 100
                beta_final = relever_beta(beta_u, 0.25, target_d_e, 1.0)
                st.caption(f"Beta Réendetté Calculé : {beta_final:.2f}")
        else:
            manual_ke = st.number_input("Coût Equity Cible %", value=8.5, step=0.1) / 100
            beta_final = st.number_input("Beta (Pour info)", value=1.0)

    with st.expander("Structure Financière & Dette", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            kd = st.number_input("Coût Dette Brut %", value=5.0, step=0.25, key="kd_fund") / 100
            tax = st.number_input("Impôt %", value=25.0, step=1.0, key="tax_fund") / 100
        with c2:
            w_e = st.number_input("Poids Equity %", value=80.0, step=5.0) / 100
            w_d = st.number_input("Poids Dette %", value=20.0, step=5.0) / 100

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

    with st.expander("Paramètres de Simulation (Volatilité)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            vol_beta = st.number_input("Volatilité Beta %", value=10.0, step=1.0) / 100
        with c2:
            vol_g = st.number_input("Volatilité Croissance %", value=1.5, step=0.1) / 100

    base_params.beta_volatility = float(vol_beta)
    base_params.growth_volatility = float(vol_g)
    base_params.terminal_growth_volatility = float(vol_g) / 2.0

    return base_params, beta


def display_expert_request(default_ticker: str, default_years: int) -> Optional[ValuationRequest]:
    """
    Strict CH02 output: returns ValuationRequest when submitted, else None.
    """
    st.subheader("Paramètres Manuels")

    method_options = {
        "DCF Simplifié": ValuationMode.SIMPLE_FCFF,
        "DCF Analytique": ValuationMode.FUNDAMENTAL_FCFF,
        "DCF Probabiliste": ValuationMode.MONTE_CARLO,
    }
    label = st.selectbox("Méthode", list(method_options.keys()))
    mode = method_options[label]

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        ticker = st.text_input("Ticker", value=default_ticker).upper().strip()
    with c2:
        years = st.slider("Horizon (années)", 3, 15, int(default_years))

    if mode == ValuationMode.SIMPLE_FCFF:
        params = _display_simple_expert_inputs(ticker, years)
        beta_final = st.number_input("Beta", value=1.0, step=0.05)
    elif mode == ValuationMode.FUNDAMENTAL_FCFF:
        params, beta_final = _display_fundamental_expert_inputs(ticker, years)
    else:
        params, beta_final = _display_monte_carlo_expert_inputs(ticker, years)

    with st.expander("Avancé : Surcharge FCF Initial", expanded=False):
        if st.checkbox("Surcharger FCF Base"):
            params.manual_fcf_base = st.number_input("FCF Manuel", value=1_000_000.0, format="%.0f")

    st.markdown("---")

    submitted = st.button("Lancer l'analyse", type="primary", use_container_width=True)
    if not submitted:
        return None

    if not ticker:
        st.error("[INPUT ERROR] ticker is empty")
        return None

    params.normalize_weights()

    return ValuationRequest(
        ticker=ticker,
        projection_years=int(years),
        mode=mode,
        input_source=InputSource.MANUAL,
        manual_params=params,
        manual_beta=float(beta_final),
    )


def display_expert_inputs(default_ticker: str, default_years: int) -> Optional[ExpertReturn]:
    """
    Legacy wrapper (kept to avoid breaking external imports).
    Prefer display_expert_request().
    """
    req = display_expert_request(default_ticker, default_years)
    if req is None:
        return None

    assert req.manual_params is not None
    assert req.manual_beta is not None
    return req.ticker, req.projection_years, req.manual_params, req.manual_beta, req.mode, True
