"""
app/main.py

POINT D'ENTRÉE DE L'APPLICATION (V3 - STANDARD)
Responsabilité : Interface de saisie & Délégation au Workflow.
Enrichi avec un Guide Utilisateur complet (Onboarding).
"""

import sys
from pathlib import Path
import logging
import streamlit as st

# ==============================================================================
# 0. SETUP ENVIRONNEMENT & PATHS
# ==============================================================================

FILE_PATH = Path(__file__).resolve()
ROOT_PATH = FILE_PATH.parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# 1. IMPORTS
# ==============================================================================

from core.models import (
    ValuationRequest,
    ValuationMode,
    InputSource,
    DCFParameters
)

# C'est lui le chef d'orchestre maintenant :
from app.workflow import run_workflow_and_display
# Import du formulaire Expert
from app.ui_components.ui_inputs_expert import display_expert_request


# ==============================================================================
# 2. CONFIGURATION UI
# ==============================================================================

def setup_page():
    st.set_page_config(
        page_title="Intrinsic Value Pricer V3",
        page_icon="📊",
        layout="wide"
    )
    st.title("📊 Intrinsic Value Pricer")
    st.markdown(
        """
        <style>
        .block-container {padding-top: 2rem;}
        .stAlert {margin-top: 1rem;}
        </style>
        """,
        unsafe_allow_html=True
    )
    st.caption("Architecture V3 • Glass Box • Audit Normatif • Gestion d'Erreurs Intelligente")
    st.markdown("---")


# ==============================================================================
# 3. COMPOSANT : GUIDE DE DÉMARRAGE (ONBOARDING)
# ==============================================================================

def display_onboarding_guide():
    """Affiche le guide utilisateur lorsque l'application est en attente."""

    st.info("👋 Bienvenue ! Configurez votre analyse dans la barre latérale pour commencer.")

    st.subheader("📘 Guide de Démarrage")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 1. Comment utiliser l'outil ?")
        st.markdown("""
        1. **Ticker** : Entrez le symbole Yahoo Finance (ex: `AAPL`, `AIR.PA`).
        2. **Méthode** : Choisissez le modèle adapté au secteur :
            - *Standard* : Entreprises matures.
            - *Growth* : Tech & forte croissance.
            - *Fundamental* : Industries cycliques.
            - *RIM* : Banques & Assurances.
            - *Graham* : Approche "Value" stricte.
        3. **Options** : Ajustez l'horizon de projection ou activez **Monte Carlo** pour mesurer le risque.
        """)

    with col2:
        st.markdown("### 2. Comprendre les Résultats")
        st.markdown("""
        - **Glass Box** 🧮 : Pas de boîte noire. Cliquez sur l'onglet "Calcul" pour voir chaque formule appliquée.
        - **Audit Score** 🛡️ : Un score de fiabilité sur 100.
            - 🟢 **> 75** : Analyse robuste.
            - 🔴 **< 50** : Données insuffisantes ou incohérentes.
        """)

    st.divider()

    st.markdown("### 3. Système de Diagnostic Intelligent (V3)")
    st.markdown("L'application ne plante plus. Elle **dialogue** avec vous via des codes couleur :")

    c_err, c_warn, c_info = st.columns(3)

    with c_err:
        st.error("**⛔ ROUGE : Bloquant**")
        st.caption("Action impossible (ex: Ticker inconnu, Donnée manquante).")
        st.caption("👉 *Action : Corrigez l'orthographe ou changez de modèle.*")

    with c_warn:
        st.warning("**⚠️ ORANGE : Avertissement**")
        st.caption("Calcul possible mais risqué (ex: Croissance > WACC).")
        st.caption("👉 *Action : Vérifiez vos hypothèses manuelles.*")

    with c_info:
        st.info("**ℹ️ BLEU : Information**")
        st.caption("Détail contextuel ou substitution mineure.")
        st.caption("👉 *Action : Aucune, pour information seulement.*")


# ==============================================================================
# 4. APPLICATION PRINCIPALE
# ==============================================================================

def main():
    setup_page()

    # --- A. SIDEBAR : PARAMÈTRES DE LA REQUÊTE ---
    with st.sidebar:
        st.header("1. Cible & Méthode")

        # 1. Ticker
        ticker = st.text_input(
            "Ticker (Yahoo Finance)",
            value="AAPL",
            help="Ex: AAPL, AIR.PA, MC.PA, TSLA"
        ).strip().upper()

        # 2. Mode de Valorisation
        mode_options = [m.value for m in ValuationMode]
        mode_label = st.selectbox("Méthode de Valorisation", options=mode_options)
        selected_mode = next(m for m in ValuationMode if m.value == mode_label)

        st.markdown("---")

        # 3. SÉLECTEUR DE MODE (NOUVEAUTÉ)
        st.header("2. Source des Données")
        input_mode = st.radio(
            "Mode de pilotage",
            ["Automatique (Yahoo)", "Expert (Manuel)"],
            help="Auto: Données financières et macro live.\nExpert: Vous saisissez tous les taux."
        )

        is_expert = input_mode == "Expert (Manuel)"

        # CONTENU DYNAMIQUE SELON LE MODE
        launch_analysis = False
        years = 5
        enable_mc = False
        mc_sims = 2000

        if not is_expert:
            # --- MODE AUTO : Options simples ---
            st.header("2. Horizon & Options")
            years = st.slider("Années de projection explicite", 3, 15, 5)

            # 4. Monte Carlo (Optionnel)
            show_mc_options = selected_mode in [
                ValuationMode.FCFF_TWO_STAGE,
                ValuationMode.FCFF_NORMALIZED,
                ValuationMode.FCFF_REVENUE_DRIVEN,
                ValuationMode.RESIDUAL_INCOME_MODEL,
                ValuationMode.GRAHAM_1974_REVISED
            ]

            if show_mc_options:
                st.caption("Analyse Probabiliste")
                enable_mc = st.toggle("Activer Monte Carlo", value=False)
                if enable_mc:
                    mc_sims = st.number_input(
                        "Nombre de simulations",
                        min_value=500, max_value=10000, value=2000, step=500
                    )

            st.markdown("---")
            launch_analysis = st.button("Lancer l'Analyse", type="primary", use_container_width=True)


    # --- B. EXÉCUTION (DÉLÉGATION AU WORKFLOW) ---

    if is_expert:
        # --- MODE EXPERT : Affiche le grand formulaire ---
        # Si l'utilisateur clique sur le bouton DANS le formulaire, une Request est retournée
        expert_request = display_expert_request(default_ticker=ticker, selected_mode=selected_mode)

        if expert_request:
            run_workflow_and_display(expert_request)
        elif not ticker:
             st.info("Veuillez entrer un ticker dans la barre latérale.")
        else:
             st.info("👈 Configurez vos hypothèses manuelles ci-dessus et cliquez sur **Lancer l'analyse (EXPERT)**.")

    elif launch_analysis:
        # --- MODE AUTO : Exécution directe via Sidebar ---
        if not ticker:
            st.warning("Veuillez saisir un ticker valide.")
            return

        # 1. Construction des paramètres manuels (Configuration)
        config_params = DCFParameters(
            risk_free_rate=0.0,
            market_risk_premium=0.0,
            corporate_aaa_yield=0.0,
            cost_of_debt=0.0,
            tax_rate=0.0,
            fcf_growth_rate=0.0,
            projection_years=years,
            enable_monte_carlo=enable_mc,
            num_simulations=mc_sims
        )

        # 2. Création de la requête normalisée
        request = ValuationRequest(
            ticker=ticker,
            projection_years=years,
            mode=selected_mode,
            input_source=InputSource.AUTO,
            manual_params=config_params
        )

        # 3. APPEL DU WORKFLOW
        run_workflow_and_display(request)

    elif not is_expert:
        # AFFICHER LE GUIDE D'ACCUEIL SI RIEN N'EST LANCÉ
        display_onboarding_guide()

if __name__ == "__main__":
    main()