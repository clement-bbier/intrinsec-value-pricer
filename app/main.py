"""
app/main.py

POINT D'ENTRÉE — INTERFACE UTILISATEUR
Point d'entrée - Registre centralisé

Principes appliqués :
- Conservation intégrale de la logique V9.1
- Registre centralisé (DT-007/008/009) au lieu de registres manuels
- Support de la nouvelle segmentation Direct Equity

Note DT-008: Les registres VALUATION_DISPLAY_NAMES et EXPERT_UI_REGISTRY
sont maintenant générés depuis core/valuation/registry.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Callable, Dict

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

from app.assets.style_system import inject_institutional_design
from app.workflow import run_workflow_and_display
from src.models import (
    DCFParameters,
    InputSource,
    ValuationMode,
    ValuationRequest,
    CoreRateParameters,
    GrowthParameters,
    MonteCarloConfig, SOTPParameters
)

# IMPORT DU RÉFÉRENTIEL TEXTUEL
from src.i18n import (
    CommonTexts,
    SidebarTexts,
    OnboardingTexts,
    FeedbackMessages
)

# IMPORT DU REGISTRE CENTRALISÉ (DT-008)
from src.valuation.registry import get_display_names

# Import de la factory pour la correction du registre
from app.ui.expert.factory import create_expert_terminal

# ==============================================================================
# CONFIGURATION & LOGGING
# ==============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# REGISTRES DE CONFIGURATION (FACADE VERS REGISTRE CENTRALISÉ)
# ==============================================================================

# DT-008: Ces registres sont maintenant des facades vers le registre centralisé
VALUATION_DISPLAY_NAMES: Dict[ValuationMode, str] = get_display_names()

def _expert_render_wrapper(mode: ValuationMode, ticker: str):
    """Wrapper pour rendre le terminal expert via la factory."""
    return create_expert_terminal(mode, ticker).render()

# Registre des terminaux expert
EXPERT_UI_REGISTRY: Dict[ValuationMode, Callable] = {
    mode: _expert_render_wrapper for mode in ValuationMode
}


# Fonction supprimée - terminaux déplacés vers app/ui/expert_terminals/


# Registre legacy supprimé - terminaux déplacés vers app/ui/expert_terminals/

# ==============================================================================
# CONSTANTES UI (DT-011: Centralisées dans core/config)
# ==============================================================================

from src.config import MonteCarloDefaults, SystemDefaults

_DEFAULT_TICKER = CommonTexts.DEFAULT_TICKER
_DEFAULT_PROJECTION_YEARS = SystemDefaults.DEFAULT_PROJECTION_YEARS
_MIN_PROJECTION_YEARS = SystemDefaults.MIN_PROJECTION_YEARS
_MAX_PROJECTION_YEARS = SystemDefaults.MAX_PROJECTION_YEARS
_MIN_MC_SIMULATIONS = MonteCarloDefaults.MIN_SIMULATIONS
_MAX_MC_SIMULATIONS = MonteCarloDefaults.MAX_SIMULATIONS
_DEFAULT_MC_SIMULATIONS = MonteCarloDefaults.DEFAULT_SIMULATIONS
_MC_SIMULATIONS_STEP = MonteCarloDefaults.STEP_SIMULATIONS


# ==============================================================================
# GESTION DU STATE
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
# SETUP PAGE
# ==============================================================================

def _setup_page() -> None:
    """Configure la page Streamlit avec le design institutionnel."""
    st.set_page_config(
        page_title=CommonTexts.APP_TITLE,
        page_icon="📊",
        layout="wide",
    )
    inject_institutional_design()

# ==============================================================================
# SIDEBAR — INPUTS UTILISATEUR
# ==============================================================================

def _render_sidebar_ticker() -> str:
    """Rend le champ de saisie du ticker."""
    st.header(SidebarTexts.SEC_1_COMPANY)
    ticker = st.text_input(SidebarTexts.TICKER_LABEL, value=_DEFAULT_TICKER)
    st.divider()
    return ticker.strip().upper()


def _render_sidebar_methodology() -> ValuationMode:
    """Rend le sélecteur de méthodologie."""
    st.header(SidebarTexts.SEC_2_METHODOLOGY)
    selected_name = st.selectbox(
        SidebarTexts.METHOD_LABEL,
        options=list(VALUATION_DISPLAY_NAMES.values()),
    )
    st.divider()
    return next(
        mode for mode, name in VALUATION_DISPLAY_NAMES.items()
        if name == selected_name
    )


def _render_sidebar_source() -> bool:
    """Rend le sélecteur de source de données. Retourne True si mode Expert."""
    st.header(SidebarTexts.SEC_3_SOURCE)
    input_mode = st.radio(
        SidebarTexts.STRATEGY_LABEL,
        options=SidebarTexts.SOURCE_OPTIONS,
    )
    st.divider()
    return input_mode == SidebarTexts.SOURCE_OPTIONS[1]


def _render_sidebar_auto_options(mode: ValuationMode) -> Dict:
    """Rend les options spécifiques au mode Auto."""
    st.header(SidebarTexts.SEC_4_HORIZON)
    years = st.slider(
        SidebarTexts.YEARS_LABEL,
        min_value=_MIN_PROJECTION_YEARS,
        max_value=_MAX_PROJECTION_YEARS,
        value=_DEFAULT_PROJECTION_YEARS,
    )
    st.divider()
    return {"years": years,
        "enable_mc": False,
        "mc_sims": _DEFAULT_MC_SIMULATIONS}


def _render_sidebar_footer() -> None:
    """Rend le footer de la sidebar."""
    st.markdown(
        f"""
        <div style="margin-top: 2rem; font-size: 0.8rem; color: #94a3b8; 
                    border-top: 0.5px solid #334155; padding-top: 1rem;">
            {CommonTexts.DEVELOPED_BY} <br>
            <a href="https://www.linkedin.com/in/cl%C3%A9ment-barbier-409a341b6/" 
               target="_blank" 
               style="color: #6366f1; text-decoration:  none; font-weight: 600;">
               {CommonTexts.AUTHOR_NAME}
            </a><br>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# CONTENT — AFFICHAGE PRINCIPAL
# ==============================================================================

def _render_onboarding_guide() -> None:
    """
    Guide d'onboarding — Design institutionnel homogène.
    Utilise des conteneurs avec bordures pour toutes les sections clés.
    """
    # 1. HEADER & ACCROCHE (Hero Section)
    st.header(CommonTexts.APP_TITLE)
    st.markdown(OnboardingTexts.INTRO_INFO)
    st.caption(OnboardingTexts.COMPLIANCE_BODY)
    st.divider()

    # 2. MÉTHODES DE VALORISATION (Homogénéisé avec bordures)
    st.subheader(OnboardingTexts.TITLE_METHODS)
    st.markdown(OnboardingTexts.DESC_METHODS)
    m_cols = st.columns(4)
    methods = [
        (OnboardingTexts.MODEL_DCF_TITLE, r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+Wacc)^t} + \frac{TV_n}{(1+Wacc)^n}",
         OnboardingTexts.MODEL_DCF_DESC),
        (OnboardingTexts.MODEL_EQUITY_TITLE, r"P = \sum_{t=1}^{n} \frac{FCFE_t}{(1+k_e)^t} + \frac{TV_n}{(1+k_e)^n}",
         OnboardingTexts.MODEL_EQUITY_DESC),
        (OnboardingTexts.MODEL_RIM_TITLE, r"V_0 = BV_0 + \sum \frac{NI_t - (k_e \cdot BV_{t-1})}{(1+k_e)^t}",
         OnboardingTexts.MODEL_RIM_DESC),
        (OnboardingTexts.MODEL_GRAHAM_TITLE, r"V_0 = EPS \times (8.5 + 2g) \times \frac{4.4}{Y}",
         OnboardingTexts.MODEL_GRAHAM_DESC)
    ]
    for col, (title, latex, desc) in zip(m_cols, methods):
        with col:
            with st.container(border=True):
                st.markdown(title)
                st.latex(latex)
                st.markdown(f"<div style='min-height: 100px;'><small style='color: #64748b;'>{desc}</small></div>",
                            unsafe_allow_html=True)
    st.divider()

    # 3. FLUX DE DONNÉES PAR MODE D'ANALYSE
    st.subheader(OnboardingTexts.TITLE_PROCESS)
    p_cols = st.columns(3)
    processes = [
        (OnboardingTexts.STRATEGY_ACQUISITION_TITLE, OnboardingTexts.STRATEGY_ACQUISITION_DESC),
        (OnboardingTexts.STRATEGY_MANUAL_TITLE, OnboardingTexts.STRATEGY_MANUAL_DESC),
        (OnboardingTexts.STRATEGY_FALLBACK_TITLE, OnboardingTexts.STRATEGY_FALLBACK_DESC)
    ]
    for col, (title, desc) in zip(p_cols, processes):
        with col:
            with st.container(border=True):
                st.markdown(title)
                st.markdown(
                    f"<div style='min-height: 110px;'><small style='color: #64748b;'>{desc}</small></div>",
                    unsafe_allow_html=True)
    st.divider()

    # 4. ARCHITECTURE DES RÉSULTATS (Les 5 Piliers)
    st.subheader(OnboardingTexts.TITLE_RESULTS)
    st.markdown(OnboardingTexts.DESC_RESULTS)
    r_cols = st.columns(5)
    results_pillars = [
        (OnboardingTexts.TAB_1_TITLE, OnboardingTexts.TAB_1_DESC),
        (OnboardingTexts.TAB_2_TITLE, OnboardingTexts.TAB_2_DESC),
        (OnboardingTexts.TAB_3_TITLE, OnboardingTexts.TAB_3_DESC),
        (OnboardingTexts.TAB_4_TITLE, OnboardingTexts.TAB_4_DESC),
        (OnboardingTexts.TAB_5_TITLE, OnboardingTexts.TAB_5_DESC)
    ]
    for col, (title, desc) in zip(r_cols, results_pillars):
        with col:
            with st.container(border=True):
                st.markdown(title)
                st.markdown(
                    f"<div style='min-height: 110px;'><small style='color: #64748b;'>{desc}</small></div>",
                    unsafe_allow_html=True)
    st.divider()

    # 5. SYSTÈME DE DIAGNOSTIC (Footer)
    st.subheader(OnboardingTexts.DIAGNOSTIC_HEADER)
    d1, d2, d3 = st.columns(3)
    d1.error(OnboardingTexts.DIAGNOSTIC_BLOQUANT)
    d2.warning(OnboardingTexts.DIAGNOSTIC_WARN)
    d3.info(OnboardingTexts.DIAGNOSTIC_INFO)

def _handle_expert_mode(ticker: str, mode: ValuationMode, external_launch: bool = False) -> None:
    """
    Gère l'affichage du terminal expert et le lancement de la valorisation.

    Parameters
    ----------
    ticker : str
        Symbole boursier de l'entreprise.
    mode : ValuationMode
        Méthodologie de valorisation sélectionnée.
    external_launch : bool, optional
        Indique si le calcul est déclenché par un composant externe (ex: Sidebar), par défaut False.
    """
    if not ticker:
        st.warning(FeedbackMessages.TICKER_REQUIRED_SIDEBAR)
        return

    from app.ui.expert.factory import create_expert_terminal
    terminal = create_expert_terminal(mode, ticker)

    # Toujours afficher le formulaire (widgets persistent dans st.session_state)
    terminal.render()

    # Si déclenchement externe (bouton sidebar), extraire et lancer le calcul
    if external_launch:
        request = terminal.build_request()
        if request:
            _set_active_request(request)


def _handle_auto_launch(ticker: str, mode: ValuationMode, options: Dict) -> None:
    """Gère le lancement en mode Auto avec support des scénarios par défaut."""
    if not ticker:
        st.warning(FeedbackMessages.TICKER_INVALID)
        return

    options.setdefault("manual_peers", [])

    # Instanciation segmentée avec Scénarios désactivés par défaut
    from src.models import ScenarioParameters  # Import local si nécessaire

    config_params = DCFParameters(
        rates=CoreRateParameters(),
        growth=GrowthParameters(projection_years=options["years"]),
        monte_carlo=MonteCarloConfig(
            enable_monte_carlo=options["enable_mc"],
            num_simulations=options["mc_sims"]
        ),
        scenarios=ScenarioParameters(enabled=False),
        sotp = SOTPParameters(enabled=False)
    )

    request = ValuationRequest(
        ticker=ticker,
        projection_years=options["years"],
        mode=mode,
        input_source=InputSource.AUTO,
        manual_params=config_params,
        options=options
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
            CommonTexts.RUN_BUTTON,
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
        _handle_expert_mode(ticker, selected_mode, external_launch=launch_analysis)

    elif launch_analysis:
        _handle_auto_launch(ticker, selected_mode, auto_options)

    else:
        _render_onboarding_guide()


# ==============================================================================
# EXÉCUTION
# ==============================================================================

if __name__ == "__main__":
    main()