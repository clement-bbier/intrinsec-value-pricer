from __future__ import annotations
from typing import Optional

import streamlit as st

from core.models import (
    DCFParameters,
    InputSource,
    ValuationMode,
    ValuationRequest
)
from core.methodology.texts import TOOLTIPS

# --- CONSTANTES PAR DÉFAUT (REPÈRES, NON NORMATIFS) ---
DEFAULT_RF = 0.04
DEFAULT_MRP = 0.05
DEFAULT_TAX = 0.25
DEFAULT_COST_DEBT = 0.05


def display_expert_request(
    default_ticker: str,
    default_years: int
) -> Optional[ValuationRequest]:
    """
    MODE EXPERT — Contrôle total des hypothèses.

    Principes :
    - Données présumées exactes
    - Responsabilité portée par l’utilisateur
    - Audit logique et financier strict
    - Aucune aberration tolérée
    """

    st.markdown("### 🛠️ Configuration — Mode EXPERT")

    # ------------------------------------------------------------------
    # CONTRAT UTILISATEUR — MODE EXPERT
    # ------------------------------------------------------------------
    with st.expander("⚠️ Responsabilité utilisateur — Mode EXPERT", expanded=True):
        st.markdown(
            """
            **Vous êtes en MODE EXPERT**

            - Toutes les hypothèses sont **fournies par vous**
            - La **qualité des données est affichée à titre informatif**
            - L’**audit logique et financier reste strict**
            - Toute aberration économique (**WACC ≤ g, EPS ≤ 0, etc.**) **bloquera le calcul**

            👉 Utilisez ce mode uniquement si vous maîtrisez les hypothèses financières.
            """
        )

    st.markdown("---")

    # ------------------------------------------------------------------
    # 1. IDENTIFICATION & STRATÉGIE
    # ------------------------------------------------------------------
    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        ticker = st.text_input(
            "Ticker",
            value=default_ticker,
            help=TOOLTIPS.get("ticker")
        ).upper().strip()

    with c2:
        years = st.number_input(
            "Horizon (années)",
            value=int(default_years),
            min_value=1,
            max_value=20
        )

    with c3:
        strategies = {
            "DCF Standard (FCF TTM)": ValuationMode.SIMPLE_FCFF,
            "DCF Fondamental (Normalisé)": ValuationMode.FUNDAMENTAL_FCFF,
            "DCF Growth (Revenu & Marge)": ValuationMode.GROWTH_TECH,
            "DDM Banques (Dividendes)": ValuationMode.DDM_BANKS,
            "Graham (Value)": ValuationMode.GRAHAM_VALUE,
            "Monte Carlo (Analyse de Risque)": ValuationMode.MONTE_CARLO,
        }
        selected = st.selectbox(
            "Méthode de valorisation",
            list(strategies.keys())
        )
        mode = strategies[selected]

    st.markdown("---")

    # ------------------------------------------------------------------
    # 2. TAUX & COÛT DU CAPITAL
    # ------------------------------------------------------------------
    show_wacc = mode not in [ValuationMode.DDM_BANKS, ValuationMode.GRAHAM_VALUE]

    with st.expander("1. Taux & Coût du Capital", expanded=True):
        m1, m2, m3, m4 = st.columns(4)

        with m1:
            rf = st.number_input(
                "Taux sans risque (Rf)",
                value=DEFAULT_RF,
                format="%.4f",
                step=0.001,
                help=TOOLTIPS.get("rf")
            )
        with m2:
            mrp = st.number_input(
                "Prime de risque (MRP)",
                value=DEFAULT_MRP,
                format="%.4f",
                step=0.001,
                help=TOOLTIPS.get("mrp")
            )
        with m3:
            beta = st.number_input(
                "Beta",
                value=1.0,
                format="%.2f",
                step=0.05,
                help=TOOLTIPS.get("beta")
            )
        with m4:
            kd = st.number_input(
                "Coût de la dette (pré-impôt)",
                value=DEFAULT_COST_DEBT,
                format="%.4f",
                step=0.001,
                disabled=not show_wacc
            )

        if show_wacc:
            st.caption("Structure de capital cible (normalisée automatiquement)")
            w1, w2, w3 = st.columns([1, 1, 2])
            with w1:
                we = st.number_input("Poids Equity %", value=80.0, step=5.0) / 100.0
            with w2:
                wd = st.number_input("Poids Dette %", value=20.0, step=5.0) / 100.0
            with w3:
                tax = st.number_input("Taux d’imposition", value=DEFAULT_TAX, step=0.01)
        else:
            we, wd, tax = 1.0, 0.0, DEFAULT_TAX

    # ------------------------------------------------------------------
    # 3. CROISSANCE
    # ------------------------------------------------------------------
    if mode != ValuationMode.GRAHAM_VALUE:
        with st.expander("2. Hypothèses de croissance", expanded=True):
            g1, g2, g3 = st.columns(3)

            label = "Croissance CA" if mode == ValuationMode.GROWTH_TECH else "Croissance FCF"

            with g1:
                g_growth = st.number_input(
                    f"{label} (CAGR)",
                    value=0.05,
                    format="%.3f",
                    step=0.005,
                    help=TOOLTIPS.get("growth_g")
                )
            with g2:
                g_perp = st.number_input(
                    "Croissance terminale",
                    value=0.02,
                    format="%.3f",
                    step=0.001,
                    help=TOOLTIPS.get("growth_perp")
                )
            with g3:
                high_growth_years = st.slider(
                    "Années de croissance forte",
                    0, years, 0
                )
    else:
        g_growth = g_perp = 0.0
        high_growth_years = 0

    # ------------------------------------------------------------------
    # 4. PARAMÈTRES SPÉCIFIQUES
    # ------------------------------------------------------------------
    advanced_params = {}

    if mode == ValuationMode.GROWTH_TECH:
        with st.expander("3. Spécifique Tech — Marge", expanded=True):
            advanced_params["target_fcf_margin"] = st.slider(
                "Marge FCF cible long terme",
                0.05, 0.50, 0.25, step=0.01
            )

    elif mode == ValuationMode.MONTE_CARLO:
        with st.expander("3. Monte Carlo — Incertitudes", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                advanced_params["beta_volatility"] = st.number_input(
                    "Volatilité Beta", value=0.10, step=0.01
                )
            with c2:
                advanced_params["growth_volatility"] = st.number_input(
                    "Volatilité Croissance", value=0.015, step=0.001
                )
            with c3:
                advanced_params["num_simulations"] = st.selectbox(
                    "Nombre de simulations", [1000, 2000, 5000, 10000], index=1
                )

    # ------------------------------------------------------------------
    # 5. OVERRIDE MANUEL
    # ------------------------------------------------------------------
    manual_override = None
    with st.expander("4. Override manuel du point de départ", expanded=False):
        label = (
            "Revenu" if mode == ValuationMode.GROWTH_TECH
            else "EPS" if mode == ValuationMode.GRAHAM_VALUE
            else "Dividende" if mode == ValuationMode.DDM_BANKS
            else "FCF"
        )
        if st.checkbox(f"Forcer la valeur initiale ({label})"):
            manual_override = st.number_input(
                f"{label} initial (monnaie locale)",
                value=0.0,
                step=1000.0
            )

    # ------------------------------------------------------------------
    # 6. VALIDATION
    # ------------------------------------------------------------------
    st.markdown("---")
    submitted = st.button(
        "Lancer l’analyse (EXPERT)",
        type="primary",
        use_container_width=True
    )

    if not submitted:
        return None

    if not ticker:
        st.error("Le ticker est requis.")
        return None

    # Normalisation des poids
    total = we + wd
    if total > 0:
        we /= total
        wd /= total

    params = DCFParameters(
        risk_free_rate=rf,
        market_risk_premium=mrp,
        cost_of_debt=kd,
        tax_rate=tax,
        fcf_growth_rate=g_growth,
        perpetual_growth_rate=g_perp,
        projection_years=int(years),
        high_growth_years=high_growth_years,
        target_equity_weight=we,
        target_debt_weight=wd,

        target_fcf_margin=advanced_params.get("target_fcf_margin"),
        beta_volatility=advanced_params.get("beta_volatility", 0.0),
        growth_volatility=advanced_params.get("growth_volatility", 0.0),
        num_simulations=advanced_params.get("num_simulations"),

        manual_fcf_base=manual_override
    )

    return ValuationRequest(
        ticker=ticker,
        projection_years=int(years),
        mode=mode,
        input_source=InputSource.MANUAL,
        manual_params=params,
        manual_beta=beta
    )
