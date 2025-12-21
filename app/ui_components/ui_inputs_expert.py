"""
ui_inputs_expert.py

INTERFACE — MODE EXPERT
Version : V2.6 — Stable & Debuggée

Correctifs :
- Ajout de l'argument obligatoire 'projection_years' dans ValuationRequest
- Conforme à 100% avec core/models.py
"""

from __future__ import annotations
from typing import Optional

import streamlit as st

from core.models import (
    DCFParameters,
    InputSource,
    ValuationMode,
    ValuationRequest,
    TerminalValueMethod
)

# Gestion robuste des tooltips
try:
    from core.methodology.texts import TOOLTIPS
except ImportError:
    TOOLTIPS = {}

# --- CONSTANTES PAR DÉFAUT ---
DEFAULT_RF = 0.042
DEFAULT_MRP = 0.055
DEFAULT_TAX = 0.25
DEFAULT_COST_DEBT = 0.05


def display_expert_request(
    default_ticker: str = "AAPL",
    default_years: int = 5
) -> Optional[ValuationRequest]:
    """
    MODE EXPERT — Contrôle total des hypothèses.
    """

    st.markdown("### 🛠️ Configuration — Mode EXPERT")

    # ------------------------------------------------------------------
    # AVERTISSEMENT
    # ------------------------------------------------------------------
    with st.expander("⚠️ Responsabilité utilisateur", expanded=False):
        st.info("Vous définissez manuellement toutes les hypothèses. L'audit ne vérifiera que la cohérence mathématique.")

    # ------------------------------------------------------------------
    # 1. IDENTIFICATION & STRATÉGIE
    # ------------------------------------------------------------------
    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        ticker = st.text_input(
            "Ticker",
            value=default_ticker,
            help=TOOLTIPS.get("ticker", "Symbole boursier")
        ).upper().strip()

    with c2:
        years = st.number_input(
            "Horizon (ans)",
            value=int(default_years),
            min_value=1,
            max_value=20
        )

    with c3:
        # MAPPING STRICT basé sur ton fichier core/models.py
        strategies = {
            "DCF Standard (Damodaran)": ValuationMode.FCFF_TWO_STAGE,
            "DCF Fondamental (Normalisé)": ValuationMode.FCFF_NORMALIZED,
            "DCF Tech (Revenu & Marge)": ValuationMode.FCFF_REVENUE_DRIVEN,
            "RIM (Banques / Assurances)": ValuationMode.RESIDUAL_INCOME_MODEL,
            "Graham (Value Investor)": ValuationMode.GRAHAM_1974_REVISED,
        }

        selected_label = st.selectbox("Méthode de valorisation", list(strategies.keys()))
        mode = strategies[selected_label]

    st.markdown("---")

    # ------------------------------------------------------------------
    # 2. TAUX & COÛT DU CAPITAL
    # ------------------------------------------------------------------
    is_graham = mode == ValuationMode.GRAHAM_1974_REVISED

    # Titre dynamique pour le 4ème champ (Kd ou AAA Yield)
    label_kd = "Taux obligataire AAA" if is_graham else "Coût dette (pré-impôt)"

    with st.expander("1. Taux & Coût du Capital", expanded=True):
        m1, m2, m3, m4 = st.columns(4)

        with m1:
            rf = st.number_input("Taux sans risque (Rf)", value=DEFAULT_RF, format="%.4f", step=0.001)
        with m2:
            mrp = st.number_input("Prime de risque (MRP)", value=DEFAULT_MRP, format="%.4f", step=0.001)
        with m3:
            beta = st.number_input("Beta", value=1.00, format="%.2f", step=0.05)
        with m4:
            # Ce champ servira de Kd pour le DCF, ou de AAA Yield pour Graham
            kd_or_aaa = st.number_input(label_kd, value=DEFAULT_COST_DEBT, format="%.4f", step=0.001)

        # Structure du capital (uniquement utile pour DCF)
        we, wd, tax = 1.0, 0.0, DEFAULT_TAX

        if not is_graham:
            st.caption("Structure de capital cible (Target Weights)")
            w1, w2, w3 = st.columns([1, 1, 2])
            with w1:
                we_input = st.number_input("Poids Equity %", value=80.0, step=5.0)
            with w2:
                wd_input = st.number_input("Poids Dette %", value=20.0, step=5.0)
            with w3:
                tax = st.number_input("Taux d’imposition", value=DEFAULT_TAX, step=0.01)

            # Normalisation
            total_w = we_input + wd_input
            if total_w > 0:
                we = we_input / total_w
                wd = wd_input / total_w
            else:
                we, wd = 0.8, 0.2

    # ------------------------------------------------------------------
    # 3. CROISSANCE
    # ------------------------------------------------------------------
    g_growth = 0.05
    g_perp = 0.02
    high_growth_years = 0

    with st.expander("2. Hypothèses de croissance", expanded=True):
        g1, g2, g3 = st.columns(3)

        label_g = "Croissance Revenu" if mode == ValuationMode.FCFF_REVENUE_DRIVEN else "Croissance FCF"

        with g1:
            g_growth = st.number_input(f"{label_g} (CAGR)", value=0.05, format="%.3f", step=0.005)
        with g2:
            g_perp = st.number_input("Croissance terminale", value=0.02, format="%.3f", step=0.001)
        with g3:
            high_growth_years = st.slider("Années croissance forte", 0, int(years), 0)

    # ------------------------------------------------------------------
    # 4. PARAMÈTRES SPÉCIFIQUES
    # ------------------------------------------------------------------
    target_margin = None
    manual_override = None

    # --- Spécifique Tech (Revenue Driven) ---
    if mode == ValuationMode.FCFF_REVENUE_DRIVEN:
        with st.expander("3. Spécifique Tech — Marge", expanded=True):
            target_margin = st.slider("Marge FCF cible long terme", 0.05, 0.50, 0.25, step=0.01)

    # --- Override Manuel ---
    with st.expander("4. Override manuel du point de départ", expanded=False):
        label_override = "FCF"
        if mode == ValuationMode.FCFF_REVENUE_DRIVEN: label_override = "Revenu"
        elif mode == ValuationMode.GRAHAM_1974_REVISED: label_override = "EPS"
        elif mode == ValuationMode.RESIDUAL_INCOME_MODEL: label_override = "Book Value / EPS"

        if st.checkbox(f"Forcer la valeur initiale ({label_override})"):
            manual_override = st.number_input(f"{label_override} initial (monnaie locale)", value=0.0, step=100.0)

    # --- Monte Carlo ---
    st.divider()
    use_mc = st.checkbox("Activer l'analyse Monte Carlo")

    sims = 1000
    beta_vol = 0.10
    growth_vol = 0.015
    term_vol = 0.005

    if use_mc:
        c_mc1, c_mc2, c_mc3 = st.columns(3)
        with c_mc1:
            sims = st.selectbox("Simulations", [1000, 2000, 5000], index=1)
        with c_mc2:
            beta_vol = st.number_input("Volatilité Beta", value=0.10, step=0.01)
        with c_mc3:
            growth_vol = st.number_input("Volatilité Croissance", value=0.015, step=0.001)

    # ------------------------------------------------------------------
    # 5. SOUMISSION
    # ------------------------------------------------------------------
    st.markdown("---")
    submitted = st.button("Lancer l’analyse (EXPERT) 🚀", type="primary", use_container_width=True)

    if submitted and ticker:

        # Mapping contextuel pour Graham : le champ Kd devient le AAA Yield
        aaa_yield_val = kd_or_aaa if is_graham else 0.0
        cost_debt_val = kd_or_aaa if not is_graham else 0.0

        # Construction de l'objet paramètres
        params = DCFParameters(
            risk_free_rate=rf,
            market_risk_premium=mrp,
            corporate_aaa_yield=aaa_yield_val,
            cost_of_debt=cost_debt_val,
            tax_rate=tax,
            fcf_growth_rate=g_growth,
            perpetual_growth_rate=g_perp,
            projection_years=int(years),
            high_growth_years=high_growth_years,

            target_equity_weight=we,
            target_debt_weight=wd,

            target_fcf_margin=target_margin,
            manual_fcf_base=manual_override,

            enable_monte_carlo=use_mc,
            num_simulations=sims,
            beta_volatility=beta_vol,
            growth_volatility=growth_vol,
            terminal_growth_volatility=term_vol,

            terminal_method=TerminalValueMethod.GORDON_SHAPIRO
        )

        # RETOUR CORRIGÉ : Ajout de 'projection_years' qui manquait
        return ValuationRequest(
            ticker=ticker,
            projection_years=int(years),  # <--- AJOUT CRITIQUE ICI
            mode=mode,
            input_source=InputSource.MANUAL,
            manual_params=params,
            manual_beta=beta,
            options={"compute_monte_carlo": use_mc}
        )

    return None