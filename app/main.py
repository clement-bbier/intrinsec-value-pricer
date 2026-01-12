"""
app/main.py
POINT D'ENTRÉE — INTERFACE UTILISATEUR
Refonte V8.3 :  Suppression du bouton "Retour aux paramètres".
"""

import sys
import logging
from pathlib import Path
import streamlit as st

FILE_PATH = Path(__file__).resolve()
ROOT_PATH = FILE_PATH.parent. parent
if str(ROOT_PATH) not in sys.path:
    sys. path.insert(0, str(ROOT_PATH))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.assets. style_system import inject_institutional_design, render_terminal_header

from core.models import ValuationRequest, ValuationMode, InputSource, DCFParameters
from app.workflow import run_workflow_and_display
from app.ui_components.ui_inputs_expert import (
    render_expert_fcff_standard,
    render_expert_fcff_fundamental,
    render_expert_fcff_growth,
    render_expert_rim,
    render_expert_graham
)

VALUATION_DISPLAY_NAMES = {
    ValuationMode.FCFF_TWO_STAGE: "FCFF Standard",
    ValuationMode. FCFF_NORMALIZED: "FCFF Fundamental",
    ValuationMode. FCFF_REVENUE_DRIVEN: "FCFF Growth",
    ValuationMode.RESIDUAL_INCOME_MODEL: "RIM",
    ValuationMode.GRAHAM_1974_REVISED: "Graham"
}


def setup_page():
    """Configure la page en utilisant le module de style centralisé."""
    st.set_page_config(
        page_title="Intrinsic Value Pricer",
        page_icon="📊",
        layout="wide"
    )
    inject_institutional_design()
    render_terminal_header()


def display_onboarding_guide():
    """Guide d'onboarding - Version mot pour mot de votre original."""
    st.info("Estimez la valeur intrinsèque d'une entreprise et comparez-la à son prix de marché.")
    st.divider()

    st.subheader("A.  Sélection de la Méthodologie")
    st.markdown(
        "Chaque méthodologie vise à modéliser la réalité économique d'une entreprise à un instant donné, "
        "conditionnellement à un ensemble d'hypothèses financières, "
        "selon les principes de "
        "[l'évaluation intrinsèque](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm) :"
    )

    m1, m2, m3 = st.columns(3)

    with m1:
        st.markdown("**Modèles DCF (FCFF)**")
        st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")
        st.markdown("""
                    <small style="color: #64748b;">
                    • <b>Standard</b> : Approche de Damodaran pour entreprises matures aux flux de trésorerie prévisibles. <br>
                    • <b>Fundamental</b> : Adapté aux cycliques ; utilise des flux normalisés pour gommer la volatilité d'un cycle économique complet.<br>
                    • <b>Growth</b> :  Modèle "Revenue-Driven" pour la Tech ; simule la convergence des marges vers un profil normatif à l'équilibre. 
                    </small>
                    """, unsafe_allow_html=True)

    with m2:
        st.markdown("**Residual Income (RIM)**")
        st.latex(r"V_0 = BV_0 + \sum_{t=1}^{n} \frac{RI_t}{(1+k_e)^t} + \frac{TV_{RI}}{(1+k_e)^n}")
        st.markdown("""
                    <small style="color: #64748b;">
                    Standard académique (Penman/Ohlson) pour les <b>Banques et Assurances</b> dont la valeur repose sur l'actif net. <br>
                    Additionne la valeur comptable actuelle et la valeur actuelle de la richesse créée au-delà du coût d'opportunité des fonds propres. 
                    </small>
                    """, unsafe_allow_html=True)

    with m3:
        st.markdown("**Modèle de Graham**")
        st.latex(r"V_0 = EPS \times (8. 5 + 2g) \times \frac{4. 4}{Y}")
        st.markdown("""
                    <small style="color: #64748b;">
                    Estimation "Value" (1974 Revised) liant la capacité bénéficiaire actuelle aux conditions de crédit de haute qualité (AAA).<br>
                    Définit un prix de référence basé sur le multiple de croissance historique et l'ajustement au rendement obligataire actuel.
                    </small>
                    """, unsafe_allow_html=True)

    st.divider()

    st.subheader("B.  Pilotage & Gestion du Risque")
    c1, c2 = st. columns(2)
    with c1:
        st.markdown("**Pilotage des Données (Auto vs Expert)**")
        st.caption("Le mode **Auto** extrait les données de Yahoo Finance...  Le mode **Expert** offre une autonomie totale...")
    with c2:
        st. markdown("**Analyse Probabiliste (Monte Carlo)**")
        st.caption("La valeur intrinsèque est présentée comme une distribution...  simule des variations sur la croissance et le risque...")

    st.divider()

    st.subheader("C. Gouvernance & Transparence")
    g1, g2 = st. columns([2, 3])
    with g1:
        st.markdown("**Audit Reliability Score**")
        st.caption("Indicateur mesurant la cohérence des inputs...")
    with g2:
        st.markdown("**Valuation Traceability**")
        st.caption("Chaque étape est détaillé dans l'onglet 'Calcul'...")

    st.divider()
    st.markdown("Système de Diagnostic :")
    d1, d2, d3 = st.columns(3)
    d1.error("**Bloquant** : Erreur de donnée ou paramètre manquant.")
    d2.warning("**Avertissement** : Hypothèse divergente (ex: g > WACC).")
    d3.info("**Information** : Note ou recommandation.")


def main():
    setup_page()

    if "active_request" not in st.session_state:
        st.session_state.active_request = None

    with st.sidebar:
        st. header("1. Choix de l'entreprise")
        ticker = st.text_input("Ticker (Yahoo Finance)", value="AAPL").strip().upper()
        st.divider()

        st.header("2. Choix de la méthodologie")
        selected_display_name = st.selectbox("Méthode de Valorisation", options=list(VALUATION_DISPLAY_NAMES.values()))
        selected_mode = next(mode for mode, name in VALUATION_DISPLAY_NAMES.items() if name == selected_display_name)
        st.divider()

        st.header("3. Source des données")
        input_mode = st.radio("Stratégie de pilotage", ["Auto (Yahoo Finance)", "Expert (Surcharge Manuelle)"])
        is_expert = "Expert" in input_mode
        st.divider()

        launch_analysis = False
        years = 5
        enable_mc = False
        mc_sims = 5000

        if not is_expert:
            st. header("4. Horizon")
            years = st.slider("Années de projection", 3, 15, 5)
            st.divider()

            if selected_mode. supports_monte_carlo:
                st.header("5. Analyse de Risque")
                enable_mc = st.toggle("Activer Monte Carlo", value=False)
                if enable_mc:
                    mc_sims = st.number_input("Simulations", 500, 10000, 2000, 500)
                st.divider()

            launch_analysis = st.button("Lancer le calcul", type="primary", use_container_width=True)

        st.markdown(
            """
            <div style="margin-top: 2rem; font-size: 0.8rem; color: #94a3b8; border-top: 0.5px solid #334155; padding-top: 1rem;">
                Developed by <br>
                <a href="https://www.linkedin.com/in/cl%C3%A9ment-barbier-409a341b6/" target="_blank" style="color: #6366f1; text-decoration: none; font-weight: 600;">Clément Barbier</a><br>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- AFFICHAGE DES RÉSULTATS (SANS BOUTON RETOUR) ---
    if st.session_state.active_request:
        run_workflow_and_display(st.session_state.active_request)

    elif is_expert:
        if not ticker:
            st.warning("Veuillez saisir un ticker dans la barre latérale.")
        else:
            expert_ui_mapping = {
                ValuationMode.FCFF_TWO_STAGE: render_expert_fcff_standard,
                ValuationMode.FCFF_NORMALIZED: render_expert_fcff_fundamental,
                ValuationMode.FCFF_REVENUE_DRIVEN: render_expert_fcff_growth,
                ValuationMode. RESIDUAL_INCOME_MODEL:  render_expert_rim,
                ValuationMode.GRAHAM_1974_REVISED: render_expert_graham
            }
            render_func = expert_ui_mapping.get(selected_mode)
            if render_func:
                request = render_func(ticker)
                if request:
                    st.session_state.active_request = request
                    st.rerun()

    elif launch_analysis:
        if not ticker:
            st.warning("Veuillez saisir un ticker valide.")
            return

        config_params = DCFParameters(
            risk_free_rate=0.0, market_risk_premium=0.0, corporate_aaa_yield=0.0,
            cost_of_debt=0.0, tax_rate=0.0, fcf_growth_rate=0.0,
            projection_years=years, enable_monte_carlo=enable_mc, num_simulations=mc_sims
        )

        request = ValuationRequest(
            ticker=ticker, projection_years=years, mode=selected_mode,
            input_source=InputSource.AUTO,
            manual_params=config_params,
            options={"enable_monte_carlo": enable_mc, "num_simulations": mc_sims}
        )
        st.session_state.active_request = request
        st. rerun()
    else:
        display_onboarding_guide()


if __name__ == "__main__":
    main()