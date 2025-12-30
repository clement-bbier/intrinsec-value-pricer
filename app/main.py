"""
app/main.py
POINT D'ENTRÉE — INTERFACE UTILISATEUR
Refonte Jalon 1 : Standardisation sémantique, visuelle et correction contraste.
"""

import sys
import logging
from pathlib import Path
import streamlit as st

# --- INITIALISATION ENVIRONNEMENT ---
FILE_PATH = Path(__file__).resolve()
ROOT_PATH = FILE_PATH.parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from core.models import ValuationRequest, ValuationMode, InputSource, DCFParameters
from app.workflow import run_workflow_and_display

from app.ui_components.ui_inputs_expert import (
    render_expert_fcff_standard,
    render_expert_fcff_fundamental,
    render_expert_fcff_growth,
    render_expert_rim,
    render_expert_graham
)



# ==============================================================================
# CONFIGURATION DES LABELS (PROPRE & CENTRALISÉ)
# ==============================================================================
VALUATION_DISPLAY_NAMES = {
    ValuationMode.FCFF_TWO_STAGE: "FCFF Standard",
    ValuationMode.FCFF_NORMALIZED: "FCFF Fundamental",
    ValuationMode.FCFF_REVENUE_DRIVEN: "FCFF Growth",
    ValuationMode.RESIDUAL_INCOME_MODEL: "RIM",
    ValuationMode.GRAHAM_1974_REVISED: "Graham"
}

# ==============================================================================
# 1. CONFIGURATION & DESIGN SYSTEM (CSS CORRIGÉ)
# ==============================================================================

def setup_page():
    """
    Configure l'identité visuelle, le système de design (CSS)
    et les mentions de conformité du terminal.
    """
    # 1. Configuration de base de la fenêtre
    st.set_page_config(
        page_title="Intrinsic Value Pricer",
        page_icon="📊",
        layout="wide"
    )

    # 2. Injection du Design System (CSS)
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* --- BASE & TYPOGRAPHIE --- */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Inter', sans-serif !important;
            color: #1e293b;
        }
        .stApp { background-color: #ECF0F8; }

        /* --- SIDEBAR : BLEU NUIT INSTITUTIONNEL --- */
        section[data-testid="stSidebar"] {
            background-color: #1F3056 !important;
        }

        /* Contraste des textes sidebar (Blanc Slate) */
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, 
        section[data-testid="stSidebar"] label p, 
        section[data-testid="stSidebar"] .stMarkdown p {
            color: #f1f5f9 !important;
        }

        /* CORRECTIF : Visibilité des diviseurs dans la sidebar */
        section[data-testid="stSidebar"] hr {
            border-top: 1.5px solid rgba(241, 245, 249, 0.3) !important;
            margin: 1.2rem 0 !important;
            opacity: 1 !important;
        }

        /* --- WIDGETS & ACTIONS --- */
        /* Flèche de repli en rouge (Action) */
        button[data-testid="collapsedControl"] {
            color: #ef4444 !important;
        }

        /* Inputs transparents pour laisser respirer le fond bleu */
        section[data-testid="stSidebar"] .stSelectbox, 
        section[data-testid="stSidebar"] .stTextInput {
            background-color: transparent !important;
        }

        /* --- COMPOSANTS DE DONNÉES --- */
        /* Metrics Cards Premium (Main Container) */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px !important;
            padding: 1rem !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        }

        /* Badge Projet Personnel */
        .project-badge {
            background-color: #f1f5f9;
            color: #64748b;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-left: 15px;
            display: inline-block;
            border: 1px solid #e2e8f0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 3. En-tête : Titre et Badge
    st.markdown(
        """
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <h1 style="margin: 0; font-weight: 700; color: #1e293b;">Intrinsic Value Pricer</h1>
            <span class="project-badge">Projet Personnel Public</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. Note de conformité (Disclaimer)
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <p style="font-size: 0.85rem; color: #64748b; font-style: italic; line-height: 1.4; margin: 0;">
                <b>Note de conformité</b> : Ces estimations constituent des simulations prospectives basées sur des modèles d’analyse intrinsèque. 
                La précision du prix théorique dépend strictement de la qualité des entrées fournies et des paramètres de risque sélectionnés. 
                Ce travail à visée pédagogique ne constitue pas un conseil en investissement.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.divider()

# ==============================================================================
# 2. COMPOSANTS D'AFFICHAGE (GUIDE)
# ==============================================================================

def display_onboarding_guide():
    """
    Guide d'onboarding conforme aux standards d'analyse fondamentale.
    Référence méthodologique : Aswath Damodaran (NYU Stern).
    """

    # Message d'accueil simplifié
    st.info("Estimez la valeur intrinsèque d’une entreprise et comparez-la à son prix de marché.")

    st.divider()

    # --- SECTION 1 : MÉTHODOLOGIE ---
    st.subheader("A. Sélection de la Méthodologie")
    st.markdown(
        "Chaque méthodologie vise à modéliser la réalité économique d'une entreprise à un instant donné, "
        "conditionnellement à un ensemble d'hypothèses financières, "
        "selon les principes de "
        "[l’évaluation intrinsèque](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm) :"
    )

    m1, m2, m3 = st.columns(3)

    with m1:
        st.markdown("**Modèles DCF (FCFF)**")
        st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")
        st.markdown("""
                    <small style="color: #64748b;">
                    • <b>Standard</b> : Approche de Damodaran pour entreprises matures aux flux de trésorerie prévisibles.<br>
                    • <b>Fundamental</b> : Adapté aux cycliques ; utilise des flux normalisés pour gommer la volatilité d'un cycle économique complet.<br>
                    • <b>Growth</b> : Modèle "Revenue-Driven" pour la Tech ; simule la convergence des marges vers un profil normatif à l'équilibre.
                    </small>
                    """, unsafe_allow_html=True)

    with m2:
        st.markdown("**Residual Income (RIM)**")
        st.latex(r"V_0 = BV_0 + \sum_{t=1}^{n} \frac{RI_t}{(1+k_e)^t} + \frac{TV_{RI}}{(1+k_e)^n}")
        st.markdown("""
                    <small style="color: #64748b;">
                    Standard académique (Penman/Ohlson) pour les <b>Banques et Assurances</b> dont la valeur repose sur l'actif net.<br>
                    Additionne la valeur comptable actuelle et la valeur actuelle de la richesse créée au-delà du coût d'opportunité des fonds propres.
                    </small>
                    """, unsafe_allow_html=True)

    with m3:
        st.markdown("**Modèle de Graham**")
        st.latex(r"V_0 = EPS \times (8.5 + 2g) \times \frac{4.4}{Y}")
        st.markdown("""
                    <small style="color: #64748b;">
                    Estimation "Value" (1974 Revised) liant la capacité bénéficiaire actuelle aux conditions de crédit de haute qualité (AAA).<br>
                    Définit un prix de référence basé sur le multiple de croissance historique et l'ajustement au rendement obligataire actuel.
                    </small>
                    """, unsafe_allow_html=True)

    st.divider()

    # --- SECTION 2 : PILOTAGE & RISQUE ---
    st.subheader("B. Pilotage & Gestion du Risque")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Pilotage des Données (Auto vs Expert)**")
        st.caption(
            "Le mode **Auto** extrait les données de Yahoo Finance (infra extensible à d'autres "
            "providers via le code). Le mode **Expert** offre une autonomie totale en permettant de "
            "surcharger chaque variable : taux (Rf, MRP, Kd), Beta et structure bilancielle."
        )

    with c2:
        st.markdown("**Analyse Probabiliste (Monte Carlo)**")
        st.caption(
            "La valeur intrinsèque est présentée comme une distribution. "
            "L'extension Monte Carlo simule des variations sur la croissance et le risque "
            "pour définir une probabilité d'occurrence des scénarios."
        )

    st.divider()

    # --- SECTION 3 : GOUVERNANCE ---
    st.subheader("C. Gouvernance & Transparence")

    g1, g2 = st.columns([2, 3])

    with g1:
        st.markdown("**Audit Reliability Score**")
        st.caption(
            "Indicateur mesurant la cohérence des inputs. "
            "Un score faible indique une dépendance à des estimations volatiles ou incertaines."
        )

    with g2:
        st.markdown("**Valuation Traceability**")
        st.caption(
            "Chaque étape est détaillé dans l'onglet 'Calcul'. "
            "Cela permet de suivre l'intégralité du calcul : formules théoriques et "
            "applications numériques."
        )

    st.divider()

    st.markdown("Système de Diagnostic :")
    d1, d2, d3 = st.columns(3)
    d1.error("**Bloquant** : Erreur de donnée ou paramètre manquant.")
    d2.warning("**Avertissement** : Hypothèse divergente (ex: g > WACC).")
    d3.info("**Information** : Note ou recommandation.")

# ==============================================================================
# 3. LOGIQUE PRINCIPALE
# ==============================================================================

def main():
    setup_page()

    # --- A. SIDEBAR : INTERFACE DE SAISIE ---
    with st.sidebar:
        st.header("1. Choix de l'entreprise")
        ticker = st.text_input("Ticker (Yahoo Finance)", value="AAPL").strip().upper()

        st.divider()

        st.header("2. Choix de la méthodologie")

        # --- BLOC D'HARMONISATION DES NOMS ---
        selected_display_name = st.selectbox(
            "Méthode de Valorisation",
            options=list(VALUATION_DISPLAY_NAMES.values())
        )
        # Récupération de l'Enum correspondant pour la logique interne
        selected_mode = next(
            mode for mode, name in VALUATION_DISPLAY_NAMES.items()
            if name == selected_display_name
        )

        st.divider()

        st.header("3. Source des données")
        input_mode = st.radio(
            "Stratégie de pilotage",
            ["Auto (Yahoo Finance)", "Expert (Surcharge Manuelle)"],
        )
        is_expert = "Expert" in input_mode

        st.divider()

        # Variables de session/exécution
        launch_analysis = False
        years = 5
        enable_mc = False
        mc_sims = 5000

        if not is_expert:
            st.header("4. Horizon")
            years = st.slider("Années de projection", 3, 15, 5)

            st.divider()

            st.header("5. Analyse de Risque Probabiliste")
            enable_mc = st.toggle("Activer Monte Carlo", value=False)
            if enable_mc:
                mc_sims = st.number_input("Simulations", 500, 10000, 2000, 500)

            st.divider()
            launch_analysis = st.button("Lancer le calcul", type="primary", use_container_width=True)

        # Footer Crédits
        st.markdown(
            """
            <div style="margin-top: 2rem; font-size: 0.8rem; color: #94a3b8; border-top: 0.5px solid #334155; padding-top: 1rem;">
                Developed by <br>
                <a href="https://www.linkedin.com/in/cl%C3%A9ment-barbier-409a341b6/" target="_blank" style="color: #6366f1; text-decoration: none; font-weight: 600;">Clément Barbier</a><br>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- B. ZONE D'EXÉCUTION (DÉLÉGATION) ---
    if is_expert:
        if not ticker:
            st.warning("Veuillez saisir un ticker dans la barre latérale.")
        else:
            # Nouveau routeur vers les interfaces spécialisées
            expert_ui_mapping = {
                ValuationMode.FCFF_TWO_STAGE: render_expert_fcff_standard,
                ValuationMode.FCFF_NORMALIZED: render_expert_fcff_fundamental,
                ValuationMode.FCFF_REVENUE_DRIVEN: render_expert_fcff_growth,
                ValuationMode.RESIDUAL_INCOME_MODEL: render_expert_rim,
                ValuationMode.GRAHAM_1974_REVISED: render_expert_graham
            }

            render_func = expert_ui_mapping.get(selected_mode)

            if render_func:
                # Appel de la fonction de rendu dédiée à la méthode
                request = render_func(ticker)

                if request:
                    run_workflow_and_display(request)

    elif launch_analysis:
        if not ticker:
            st.warning("Veuillez saisir un ticker valide.")
            return

        # Configuration par défaut pour le mode Auto
        config_params = DCFParameters(
            risk_free_rate=0.0, market_risk_premium=0.0, corporate_aaa_yield=0.0,
            cost_of_debt=0.0, tax_rate=0.0, fcf_growth_rate=0.0,
            projection_years=years, enable_monte_carlo=enable_mc, num_simulations=mc_sims
        )

        request = ValuationRequest(
            ticker=ticker, projection_years=years, mode=selected_mode,
            input_source=InputSource.AUTO, manual_params=config_params
        )

        run_workflow_and_display(request)

    else:
        display_onboarding_guide()

if __name__ == "__main__":
    main()