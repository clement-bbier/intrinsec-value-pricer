from __future__ import annotations
from typing import Optional, Tuple

import streamlit as st

from core.models import (
    DCFParameters,
    InputSource,
    ValuationMode,
    ValuationRequest
)
from core.methodology.texts import TOOLTIPS

# --- CONSTANTES PAR DÉFAUT ---
DEFAULT_RF = 0.04
DEFAULT_MRP = 0.05
DEFAULT_TAX = 0.25
DEFAULT_COST_DEBT = 0.05


def display_expert_request(
        default_ticker: str,
        default_years: int
) -> Optional[ValuationRequest]:
    """
    Formulaire Expert Complet.
    Permet de surcharger chaque hypothèse du modèle (Taux, Croissance, Structure).
    Retourne une ValuationRequest prête à l'emploi.
    """

    st.markdown("### 🛠️ Configuration Expert")
    st.caption("Contrôle total sur les hypothèses de modélisation.")

    # 1. IDENTIFICATION & STRATÉGIE
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        ticker = st.text_input("Ticker", value=default_ticker, help=TOOLTIPS["ticker"]).upper().strip()
    with c2:
        years = st.number_input("Horizon (Ans)", value=int(default_years), min_value=1, max_value=20)
    with c3:
        # Mapping User-Friendly -> Enum Technique
        strategies = {
            "DCF Standard (FCF TTM)": ValuationMode.SIMPLE_FCFF,
            "DCF Fondamental (Lissé)": ValuationMode.FUNDAMENTAL_FCFF,
            "DCF Growth (Revenu + Marge)": ValuationMode.GROWTH_TECH,
            "DDM Banques (Dividendes)": ValuationMode.DDM_BANKS,
            "Graham (Deep Value)": ValuationMode.GRAHAM_VALUE,
            "Monte Carlo (Simulation)": ValuationMode.MONTE_CARLO
        }
        selected_strat = st.selectbox("Stratégie de Valorisation", list(strategies.keys()))
        mode = strategies[selected_strat]

    st.markdown("---")

    # 2. PARAMÈTRES DE MARCHÉ (WACC / Ke)
    # On adapte l'affichage selon si on a besoin d'un WACC complet ou juste du Ke
    show_wacc = mode not in [ValuationMode.DDM_BANKS, ValuationMode.GRAHAM_VALUE]

    with st.expander("1. Taux & Coût du Capital", expanded=True):
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)

        with col_m1:
            rf = st.number_input("Taux Sans Risque (Rf)", value=DEFAULT_RF, format="%.4f", step=0.001,
                                 help=TOOLTIPS["rf"])
        with col_m2:
            mrp = st.number_input("Prime de Risque (MRP)", value=DEFAULT_MRP, format="%.4f", step=0.001,
                                  help=TOOLTIPS["mrp"])
        with col_m3:
            beta = st.number_input("Beta", value=1.0, format="%.2f", step=0.05, help=TOOLTIPS["beta"])
        with col_m4:
            # Pour DDM, on n'a pas besoin du coût de la dette pour le discount rate, mais on le garde pour info
            kd = st.number_input("Coût Dette (Pre-Tax)", value=DEFAULT_COST_DEBT, format="%.4f", step=0.001,
                                 disabled=(not show_wacc))

        if show_wacc:
            st.caption("Structure du Capital Cible (Doit sommer à 100%)")
            cw1, cw2, cw3 = st.columns([1, 1, 2])
            with cw1:
                we = st.number_input("Poids Equity %", value=80.0, step=5.0, max_value=100.0) / 100.0
            with cw2:
                wd = st.number_input("Poids Dette %", value=20.0, step=5.0, max_value=100.0) / 100.0
            with cw3:
                tax = st.number_input("Taux IS (Tax)", value=DEFAULT_TAX, format="%.2f", step=0.01)
        else:
            # Valeurs par défaut pour les modes sans WACC (pour éviter None)
            we, wd, tax = 1.0, 0.0, DEFAULT_TAX

    # 3. PARAMÈTRES DE CROISSANCE
    # Graham n'utilise pas de projection explicite
    if mode != ValuationMode.GRAHAM_VALUE:
        with st.expander("2. Hypothèses de Croissance", expanded=True):
            cg1, cg2, cg3 = st.columns(3)

            label_g = "Croissance CA" if mode == ValuationMode.GROWTH_TECH else "Croissance FCF"

            with cg1:
                g_growth = st.number_input(f"{label_g} (CAGR)", value=0.05, format="%.3f", step=0.005,
                                           help=TOOLTIPS["growth_g"])
            with cg2:
                g_perp = st.number_input("Croissance Terminale", value=0.02, format="%.3f", step=0.001,
                                         help=TOOLTIPS["growth_perp"])
            with cg3:
                high_growth_years = st.slider("Années Croissance Forte", 0, years, 0,
                                              help="Durée du plateau de croissance avant ralentissement.")

    # 4. PARAMÈTRES SPÉCIFIQUES (Polymorphisme UI)
    advanced_params: dict = {}

    if mode == ValuationMode.GROWTH_TECH:
        with st.expander("3. Spécifique Tech : Convergence de Marge", expanded=True):
            target_margin = st.slider("Marge FCF Cible (à terme)", 0.05, 0.50, 0.25, step=0.01)
            advanced_params["target_fcf_margin"] = target_margin

    elif mode == ValuationMode.MONTE_CARLO:
        with st.expander("3. Spécifique Monte Carlo : Volatilité", expanded=True):
            cm1, cm2, cm3 = st.columns(3)
            with cm1:
                beta_vol = st.number_input("Volatilité Beta", value=0.10, step=0.01)
            with cm2:
                g_vol = st.number_input("Volatilité Croissance", value=0.015, step=0.001)
            with cm3:
                sims = st.selectbox("Nb Simulations", [1000, 2000, 5000, 10000], index=1)

            advanced_params["beta_volatility"] = beta_vol
            advanced_params["growth_volatility"] = g_vol
            advanced_params["num_simulations"] = sims

    # 5. OVERRIDES MANUELS (Optionnel)
    manual_override_val = None
    with st.expander("4. Override Point de Départ (Optionnel)", expanded=False):
        label_base = "Revenu" if mode == ValuationMode.GROWTH_TECH else "EPS" if mode == ValuationMode.GRAHAM_VALUE else "Dividende" if mode == ValuationMode.DDM_BANKS else "FCF"
        if st.checkbox(f"Forcer la valeur initiale ({label_base})",
                       help="Remplace la donnée automatique par votre valeur."):
            manual_override_val = st.number_input(f"Valeur {label_base} (Monnaie Locale)", value=0.0, step=1000.0)

    # 6. VALIDATION
    st.markdown("---")
    submitted = st.button("Lancer l'analyse Expert", type="primary", use_container_width=True)

    if not submitted:
        return None

    if not ticker:
        st.error("Le ticker est requis.")
        return None

    # Construction de l'objet Paramètres
    # On normalise les poids s'ils sont incohérents
    total_w = we + wd
    if abs(total_w - 1.0) > 0.01 and total_w > 0:
        we /= total_w
        wd /= total_w

    # On peuple l'objet DCFParameters (Standardisé)
    # Les champs inutiles pour certaines stratégies seront ignorés par le moteur
    params = DCFParameters(
        risk_free_rate=rf,
        market_risk_premium=mrp,
        cost_of_debt=kd,
        tax_rate=tax,
        fcf_growth_rate=g_growth if mode != ValuationMode.GRAHAM_VALUE else 0.0,
        perpetual_growth_rate=g_perp if mode != ValuationMode.GRAHAM_VALUE else 0.0,
        projection_years=int(years),
        high_growth_years=high_growth_years if mode != ValuationMode.GRAHAM_VALUE else 0,
        target_equity_weight=we,
        target_debt_weight=wd,

        # Spécifiques injectés
        target_fcf_margin=advanced_params.get("target_fcf_margin"),
        beta_volatility=advanced_params.get("beta_volatility", 0.0),
        growth_volatility=advanced_params.get("growth_volatility", 0.0),
        num_simulations=advanced_params.get("num_simulations"),

        # Overrides
        manual_fcf_base=manual_override_val
    )

    # Construction de la Requête
    return ValuationRequest(
        ticker=ticker,
        projection_years=int(years),
        mode=mode,
        input_source=InputSource.MANUAL,
        manual_params=params,
        manual_beta=beta  # Le beta expert est forcé via le paramètre ou via financial override plus tard
        # Note: Dans notre architecture, le beta est souvent attaché aux financials.
        # Ici, on le passe dans request.manual_beta pour que le Provider puisse le surcharger.
    )