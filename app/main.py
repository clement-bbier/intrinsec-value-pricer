"""
app/main.py

POINT D'ENTRÉE — INTERFACE UTILISATEUR
Version :  V9.0 — Clean Architecture & SOLID

Principes appliqués :
- Single Responsibility :  Chaque fonction a une responsabilité unique
- Open/Closed : Extensible via EXPERT_UI_REGISTRY sans modifier le code
- Dependency Inversion : Configuration externalisée dans les constantes
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Callable, Dict, Optional

import streamlit as st

# ==============================================================================
# CONFIGURATION DU PATH
# ==============================================================================

_FILE_PATH = Path(__file__).resolve()
_ROOT_PATH = _FILE_PATH.parent.parent

if str(_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(_ROOT_PATH))

# ==============================================================================
# IMPORTS APPLICATIFS
# ==============================================================================

from app.assets.style_system import inject_institutional_design, render_terminal_header
from app.ui_components.ui_inputs_expert import (
    render_expert_fcff_standard,
    render_expert_fcff_fundamental,
    render_expert_fcff_growth,
    render_expert_rim,
    render_expert_graham,
)
from app.workflow import run_workflow_and_display
from core.models import DCFParameters, InputSource, ValuationMode, ValuationRequest

# ==============================================================================
# CONFIGURATION & LOGGING
# ==============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# REGISTRES DE CONFIGURATION (Open/Closed Principle)
# ==============================================================================

VALUATION_DISPLAY_NAMES:  Dict[ValuationMode, str] = {
    ValuationMode.FCFF_TWO_STAGE: "FCFF Standard",
    ValuationMode.FCFF_NORMALIZED:  "FCFF Fundamental",
    ValuationMode.FCFF_REVENUE_DRIVEN:  "FCFF Growth",
    ValuationMode.RESIDUAL_INCOME_MODEL: "RIM",
    ValuationMode.GRAHAM_1974_REVISED: "Graham",
}

EXPERT_UI_REGISTRY: Dict[ValuationMode, Callable[[str], Optional[ValuationRequest]]] = {
    ValuationMode.FCFF_TWO_STAGE: render_expert_fcff_standard,
    ValuationMode.FCFF_NORMALIZED: render_expert_fcff_fundamental,
    ValuationMode.FCFF_REVENUE_DRIVEN: render_expert_fcff_growth,
    ValuationMode.RESIDUAL_INCOME_MODEL: render_expert_rim,
    ValuationMode.GRAHAM_1974_REVISED: render_expert_graham,
}

# ==============================================================================
# CONSTANTES UI
# ==============================================================================

_DEFAULT_TICKER = "AAPL"
_DEFAULT_PROJECTION_YEARS = 5
_MIN_PROJECTION_YEARS = 1
_MAX_PROJECTION_YEARS = 15
_MIN_MC_SIMULATIONS = 100
_MAX_MC_SIMULATIONS = 20000
_DEFAULT_MC_SIMULATIONS = 5000
_MC_SIMULATIONS_STEP = 200


# ==============================================================================
# GESTION DU STATE (Single Responsibility)
# ==============================================================================

def _init_session_state() -> None:
    """Initialise les variables de session si absentes."""
    defaults = {
        "active_request": None,
        "last_config": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset_on_config_change(current_config: str) -> None:
    """Reset la requête active si la configuration a changé."""
    if st.session_state.last_config != current_config:
        st.session_state.active_request = None
        st.session_state.last_config = current_config


def _set_active_request(request: ValuationRequest) -> None:
    """Enregistre la requête active et relance l'app."""
    st.session_state.active_request = request
    st.rerun()


# ==============================================================================
# SETUP PAGE (Single Responsibility)
# ==============================================================================

def _setup_page() -> None:
    """Configure la page Streamlit avec le design institutionnel."""
    st.set_page_config(
        page_title="Intrinsic Value Pricer",
        page_icon="📊",
        layout="wide",
    )
    inject_institutional_design()
    render_terminal_header()


# ==============================================================================
# SIDEBAR — INPUTS UTILISATEUR (Single Responsibility)
# ==============================================================================

def _render_sidebar_ticker() -> str:
    """Rend le champ de saisie du ticker."""
    st.header("1. Choix de l'entreprise")
    ticker = st.text_input("Ticker (Yahoo Finance)", value=_DEFAULT_TICKER)
    st.divider()
    return ticker.strip().upper()


def _render_sidebar_methodology() -> ValuationMode:
    """Rend le sélecteur de méthodologie."""
    st.header("2. Choix de la méthodologie")
    selected_name = st.selectbox(
        "Méthode de Valorisation",
        options=list(VALUATION_DISPLAY_NAMES.values()),
    )
    st.divider()
    return next(
        mode for mode, name in VALUATION_DISPLAY_NAMES.items()
        if name == selected_name
    )


def _render_sidebar_source() -> bool:
    """Rend le sélecteur de source de données. Retourne True si mode Expert."""
    st.header("3. Source des données")
    input_mode = st.radio(
        "Stratégie de pilotage",
        options=["Auto (Yahoo Finance)", "Expert (Surcharge Manuelle)"],
    )
    st.divider()
    return "Expert" in input_mode


def _render_sidebar_auto_options(mode: ValuationMode) -> Dict:
    """Rend les options spécifiques au mode Auto."""
    st.header("4. Horizon")
    years = st.slider(
        "Années de projection",
        min_value=_MIN_PROJECTION_YEARS,
        max_value=_MAX_PROJECTION_YEARS,
        value=_DEFAULT_PROJECTION_YEARS,
    )
    st.divider()

    enable_mc = False
    mc_sims = _DEFAULT_MC_SIMULATIONS

    if mode.supports_monte_carlo:
        st.header("5. Analyse de Risque")
        enable_mc = st.toggle("Activer Monte Carlo", value=False)
        if enable_mc:
            mc_sims = st.number_input(
                "Simulations",
                min_value=_MIN_MC_SIMULATIONS,
                max_value=_MAX_MC_SIMULATIONS,
                value=_DEFAULT_MC_SIMULATIONS,
                step=_MC_SIMULATIONS_STEP,
            )
        st.divider()

    return {
        "years": years,
        "enable_mc": enable_mc,
        "mc_sims": mc_sims,
    }


def _render_sidebar_footer() -> None:
    """Rend le footer de la sidebar."""
    st.markdown(
        """
        <div style="margin-top: 2rem; font-size: 0.8rem; color: #94a3b8; 
                    border-top: 0.5px solid #334155; padding-top: 1rem;">
            Developed by <br>
            <a href="https://www.linkedin.com/in/cl%C3%A9ment-barbier-409a341b6/" 
               target="_blank" 
               style="color: #6366f1; text-decoration:  none; font-weight: 600;">
               Clément Barbier
            </a><br>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# CONTENT — AFFICHAGE PRINCIPAL (Single Responsibility)
# ==============================================================================

def _render_onboarding_guide() -> None:
    """Guide d'onboarding — Contenu intégral préservé."""
    st.info("Estimez la valeur intrinsèque d'une entreprise et comparez-la à son prix de marché.")
    st.divider()

    st.subheader("A. Sélection de la Méthodologie")
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
        st.markdown(
            """
            <small style="color: #64748b;">
            • <b>Standard</b> : Approche de Damodaran pour entreprises matures aux flux de trésorerie prévisibles. <br>
            • <b>Fundamental</b> : Adapté aux cycliques ; utilise des flux normalisés pour gommer la volatilité d'un cycle économique complet.<br>
            • <b>Growth</b> : Modèle "Revenue-Driven" pour la Tech ; simule la convergence des marges vers un profil normatif à l'équilibre.
            </small>
            """,
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown("**Residual Income (RIM)**")
        st.latex(r"V_0 = BV_0 + \sum_{t=1}^{n} \frac{RI_t}{(1+k_e)^t} + \frac{TV_{RI}}{(1+k_e)^n}")
        st.markdown(
            """
            <small style="color: #64748b;">
            Standard académique (Penman/Ohlson) pour les <b>Banques et Assurances</b> dont la valeur repose sur l'actif net.<br>
            Additionne la valeur comptable actuelle et la valeur actuelle de la richesse créée au-delà du coût d'opportunité des fonds propres.
            </small>
            """,
            unsafe_allow_html=True,
        )

    with m3:
        st.markdown("**Modèle de Graham**")
        st.latex(r"V_0 = EPS \times (8.5 + 2g) \times \frac{4.4}{Y}")
        st.markdown(
            """
            <small style="color: #64748b;">
            Estimation "Value" (1974 Revised) liant la capacité bénéficiaire actuelle aux conditions de crédit de haute qualité (AAA).<br>
            Définit un prix de référence basé sur le multiple de croissance historique et l'ajustement au rendement obligataire actuel.
            </small>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.subheader("B. Pilotage & Gestion du Risque")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Pilotage des Données (Auto vs Expert)**")
        st.caption(
            "Le mode **Auto** extrait les données de Yahoo Finance...  "
            "Le mode **Expert** offre une autonomie totale..."
        )
    with c2:
        st.markdown("**Analyse Probabiliste (Monte Carlo)**")
        st.caption(
            "La valeur intrinsèque est présentée comme une distribution...  "
            "simule des variations sur la croissance et le risque..."
        )

    st.divider()

    st.subheader("C.Gouvernance & Transparence")
    g1, g2 = st.columns([2, 3])
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


def _handle_expert_mode(ticker: str, mode: ValuationMode) -> None:
    """Gère l'affichage et le lancement en mode Expert."""
    if not ticker:
        st.warning("Veuillez saisir un ticker dans la barre latérale.")
        return

    render_func = EXPERT_UI_REGISTRY.get(mode)
    if render_func:
        request = render_func(ticker)
        if request:
            _set_active_request(request)


def _handle_auto_launch(ticker: str, mode: ValuationMode, options: Dict) -> None:
    """Gère le lancement en mode Auto."""
    if not ticker:
        st.warning("Veuillez saisir un ticker valide.")
        return

    config_params = DCFParameters(
        risk_free_rate=0.0,
        market_risk_premium=0.0,
        corporate_aaa_yield=0.0,
        cost_of_debt=0.0,
        tax_rate=0.0,
        fcf_growth_rate=0.0,
        projection_years=options["years"],
        enable_monte_carlo=options["enable_mc"],
        num_simulations=options["mc_sims"],
    )

    request = ValuationRequest(
        ticker=ticker,
        projection_years=options["years"],
        mode=mode,
        input_source=InputSource.AUTO,
        manual_params=config_params,
        options={
            "enable_monte_carlo": options["enable_mc"],
            "num_simulations": options["mc_sims"],
        },
    )

    _set_active_request(request)


# ==============================================================================
# POINT D'ENTRÉE PRINCIPAL
# ==============================================================================

def main() -> None:
    """Point d'entrée principal de l'application."""
    _setup_page()
    _init_session_state()

    # =========================================================================
    # SIDEBAR — Collecte des inputs
    # =========================================================================
    with st.sidebar:
        ticker = _render_sidebar_ticker()
        selected_mode = _render_sidebar_methodology()
        is_expert = _render_sidebar_source()

        # Reset si la configuration change
        current_config = f"{ticker}_{is_expert}_{selected_mode.value}"
        _reset_on_config_change(current_config)

        # Options spécifiques au mode Auto
        auto_options = {}
        launch_analysis = False

        if not is_expert:
            auto_options = _render_sidebar_auto_options(selected_mode)
            launch_analysis = st.button(
                "Lancer le calcul",
                type="primary",
                width="stretch",
            )

        _render_sidebar_footer()

    # =========================================================================
    # CONTENT — Affichage principal
    # =========================================================================
    if st.session_state.active_request:
        run_workflow_and_display(st.session_state.active_request)

    elif is_expert:
        _handle_expert_mode(ticker, selected_mode)

    elif launch_analysis:
        _handle_auto_launch(ticker, selected_mode, auto_options)

    else:
        _render_onboarding_guide()


# ==============================================================================
# EXÉCUTION
# ==============================================================================

if __name__ == "__main__":
    main()