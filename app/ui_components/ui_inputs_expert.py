"""
app/ui_components/ui_inputs_expert.py

INTERFACE — MODE EXPERT (CONTEXT-AWARE V3.3)
Version : V3.3 — Correctif Constantes & Polymorphisme

Rôle :
- Interface de saisie manuelle complète.
- S'adapte au contexte (Banque vs Tech vs Industrie).
- Intègre les définitions de toutes les constantes par défaut.
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

# ==============================================================================
# CONSTANTES PAR DÉFAUT (CRITIQUE : NE PAS SUPPRIMER)
# ==============================================================================
DEFAULT_RF = 0.042        # 4.2% (Taux sans risque)
DEFAULT_MRP = 0.055       # 5.5% (Prime de risque)
DEFAULT_TAX = 0.25        # 25% (Impôt société)
DEFAULT_COST_DEBT = 0.05  # 5% (Coût dette brut)
DEFAULT_GROWTH = 0.03     # 3% (Croissance phase 1) - C'ÉTAIT CELUI-LA QUI MANQUAIT
DEFAULT_PERP = 0.02       # 2% (Croissance perpétuelle / Inflation)


def display_expert_request(
    default_ticker: str = "AAPL",
    selected_mode: ValuationMode = ValuationMode.FCFF_TWO_STAGE
) -> Optional[ValuationRequest]:
    """
    Formulaire Expert Polymorphe.
    S'adapte intelligemment selon le modèle de valorisation choisi.
    """

    st.markdown(f"### 🛠️ Paramétrage Expert : {selected_label(selected_mode)}")

    # Indicateurs de contexte
    is_rim = selected_mode == ValuationMode.RESIDUAL_INCOME_MODEL
    is_growth = selected_mode == ValuationMode.FCFF_REVENUE_DRIVEN
    is_graham = selected_mode == ValuationMode.GRAHAM_1974_REVISED
    # is_standard = not (is_rim or is_growth or is_graham)

    with st.form("expert_form"):

        # ==============================================================================
        # 1. RISQUE & TAUX (Adaptatif)
        # ==============================================================================
        st.markdown("#### 1. Environnement de Taux & Risque")

        c1, c2, c3 = st.columns(3)

        rf = c1.number_input(
            "Taux sans risque (Rf)",
            0.0, 0.20, DEFAULT_RF, 0.001, format="%.3f",
            help="Obligations d'État 10 ans"
        )
        mrp = c2.number_input(
            "Prime de risque (MRP)",
            0.0, 0.20, DEFAULT_MRP, 0.001, format="%.3f",
            help="Prime de risque marché actions"
        )

        # Le 3ème champ change selon le modèle
        manual_beta = 1.0 # Valeur par défaut
        rate_val = 0.0

        if is_graham:
            rate_val = c3.number_input("Taux AAA (Corporate)", 0.0, 0.15, 0.045, 0.001, help="Référence obligataire privée")
        elif is_rim:
            # Pour les banques, le coût de la dette est opérationnel, on se focus sur le Beta
            manual_beta = c3.number_input("Beta (Risque Bancaire)", 0.0, 3.0, 1.0, 0.05, help="Volatilité systématique")
            rate_val = 0.0 # Pas utilisé comme input direct Kd
        else:
            rate_val = c3.number_input("Coût de la dette (Kd brut)", 0.0, 0.20, DEFAULT_COST_DEBT, 0.001, help="Taux d'emprunt de l'entreprise")
            manual_beta = 1.0 # Sera géré plus bas ou via surcharge

        # ==============================================================================
        # 2. STRUCTURE DU CAPITAL (Caché pour RIM/Graham)
        # ==============================================================================
        we, wd, tax = 1.0, 0.0, DEFAULT_TAX

        if not (is_rim or is_graham):
            with st.expander("⚖️ Structure du Capital (WACC)", expanded=True):
                w1, w2, w3, w4 = st.columns(4)
                manual_beta = w1.number_input("Beta", 0.0, 5.0, 1.0, 0.05)
                tax = w2.number_input("Taux IS (Tax)", 0.0, 0.50, DEFAULT_TAX, 0.01)

                # Saisie intelligente des poids
                we_input = w3.number_input("Poids Equity (%)", 0.0, 100.0, 80.0, 5.0)
                wd_input = w4.number_input("Poids Dette (%)", 0.0, 100.0, 100.0 - we_input, 5.0)

                # Normalisation immédiate pour le calcul
                total_w = we_input + wd_input
                if total_w > 0:
                    we = we_input / total_w
                    wd = wd_input / total_w

        # ==============================================================================
        # 3. CROISSANCE & PERFORMANCES (Le cœur du polymorphisme)
        # ==============================================================================
        st.markdown("#### 2. Hypothèses de Croissance")

        # LABEL DYNAMIQUE
        if is_growth:
            growth_label = "Croissance du Chiffre d'Affaires (CAGR)"
            growth_help = "Taux de croissance annuel des ventes sur la période explicite."
        elif is_rim:
            growth_label = "Croissance du Bénéfice (EPS)"
            growth_help = "Croissance du Net Income / EPS pour projeter les profits futurs."
        else:
            growth_label = "Croissance du FCF"
            growth_help = "Taux de croissance du Cash Flow Libre."

        cg1, cg2, cg3 = st.columns(3)
        years = cg1.slider("Horizon de projection (ans)", 3, 15, 5)

        # --- C'EST ICI QUE CA PLANTAIT AVANT (DEFAULT_GROWTH manquant) ---
        g_growth = cg2.number_input(growth_label, -0.50, 1.0, DEFAULT_GROWTH, 0.005, format="%.3f", help=growth_help)
        g_perp = cg3.number_input("Croissance Terminale (g)", 0.0, 0.05, DEFAULT_PERP, 0.001, help="Ne doit pas dépasser le Rf.")

        # ==============================================================================
        # 4. PARAMÈTRES SPÉCIFIQUES AU MODÈLE
        # ==============================================================================
        target_margin = None
        high_growth_years = 0 # Par défaut

        if is_growth:
            st.info("💎 **Mode Revenue-Driven** : La valeur dépend de la convergence des marges.")
            cm1, cm2 = st.columns(2)
            target_margin = cm1.number_input("Marge FCF Cible (Long Terme)", 0.01, 0.60, 0.20, 0.01, help="Marge normative à l'équilibre")
            manual_base_label = "Chiffre d'Affaires TTM (Override)"

        elif is_rim:
            st.info("🏦 **Mode Banques (RIM)** : La valeur dépend de la Book Value et du ROE.")
            manual_base_label = "EPS de base (Override)"

        else:
            manual_base_label = "FCF de base (Override)"

        # ==============================================================================
        # 5. SURCHARGES & MONTE CARLO
        # ==============================================================================
        with st.expander("⚙️ Surcharges & Analyse de Risque (Monte Carlo)", expanded=False):
            c_ov1, c_ov2 = st.columns(2)
            manual_base = c_ov1.number_input(f"Forcer {manual_base_label}", value=0.0, step=100.0, help="Laisser 0 pour utiliser Yahoo Finance")
            wacc_ov = c_ov2.number_input("Forcer WACC / Ke Global", 0.0, 0.30, 0.0, 0.001, help="Surcharge le calcul automatique du taux d'actualisation")

            st.divider()
            st.markdown("**🎲 Configuration Monte Carlo**")
            use_mc = st.toggle("Activer la simulation", value=False)

            mc1, mc2, mc3 = st.columns(3)
            sims = mc1.selectbox("Simulations", [1000, 2000, 5000, 10000], index=1)
            beta_vol = mc2.number_input("Incertitude Beta (Vol)", 0.05, 0.50, 0.10, 0.01, help="Écart-type sur le risque")
            growth_vol = mc3.number_input("Incertitude Croissance (Vol)", 0.005, 0.10, 0.015, 0.001, help="Écart-type sur la croissance")

            # Ajout variable manquante pour éviter tout NameError futur
            term_vol = 0.005

        st.markdown("---")

        # ==============================================================================
        # 6. SOUMISSION (Le bouton est bien là !)
        # ==============================================================================
        submitted = st.form_submit_button("Lancer l'Analyse Expert", type="primary", use_container_width=True)

        if submitted:
            # Mapping logique
            aaa_val = rate_val if is_graham else 0.0
            kd_val = rate_val if not (is_graham or is_rim) else 0.0

            final_manual_base = manual_base if manual_base != 0.0 else None
            final_wacc_ov = wacc_ov if wacc_ov != 0.0 else None

            try:
                params = DCFParameters(
                    risk_free_rate=rf,
                    market_risk_premium=mrp,
                    corporate_aaa_yield=aaa_val,
                    cost_of_debt=kd_val,
                    tax_rate=tax,
                    fcf_growth_rate=g_growth,
                    perpetual_growth_rate=g_perp,
                    projection_years=int(years),
                    high_growth_years=high_growth_years,

                    target_equity_weight=we,
                    target_debt_weight=wd,

                    target_fcf_margin=target_margin,
                    manual_fcf_base=final_manual_base,
                    wacc_override=final_wacc_ov,

                    enable_monte_carlo=use_mc,
                    num_simulations=sims,
                    beta_volatility=beta_vol,
                    growth_volatility=growth_vol,
                    terminal_growth_volatility=term_vol
                )

                return ValuationRequest(
                    ticker=default_ticker,
                    projection_years=int(years),
                    mode=selected_mode,
                    input_source=InputSource.MANUAL,
                    manual_params=params,
                    manual_beta=manual_beta
                )

            except Exception as e:
                st.error(f"Erreur de paramètres : {e}")
                return None

    return None

def selected_label(mode: ValuationMode) -> str:
    """Helper pour afficher un nom joli dans le titre."""
    return mode.value