"""
app/main.py

POINT D'ENTRÉE — INTERFACE UTILISATEUR
Version : V11.0 — DT-008 Resolution (Centralized Registry)

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
# Module ui_inputs_expert supprimé - terminaux déplacés vers app/ui/expert_terminals/
from app.workflow import run_workflow_and_display
from src.domain.models import (
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
from src.valuation.registry import StrategyRegistry, get_display_names

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

# Registre des terminaux expert (maintenu pour compatibilité)
EXPERT_UI_REGISTRY = {
    ValuationMode.FCFF_STANDARD: "render_expert_fcff_standard",
    ValuationMode.FCFF_NORMALIZED: "render_expert_fcff_normalized",
    ValuationMode.FCFF_GROWTH: "render_expert_fcff_growth",
    ValuationMode.FCFE: "render_expert_fcfe",
    ValuationMode.DDM: "render_expert_ddm",
    ValuationMode.RIM: "render_expert_rim",
    ValuationMode.GRAHAM: "render_expert_graham",
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
# GESTION DU STATE (Delegated to SessionManager)
# ==============================================================================

from app.state.session_manager import SessionManager


def _init_session_state() -> None:
    """Initialise les variables de session via le SessionManager."""
    SessionManager.init()


def _reset_on_config_change(current_config: str) -> None:
    """Reset la requête active si la configuration a changé."""
    SessionManager.on_config_change(current_config)


def _set_active_request(request: ValuationRequest) -> None:
    """Enregistre la requête active et relance l'app."""
    SessionManager.set_active_request(request)


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
    render_terminal_header()


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
    return "Expert" in input_mode


def _render_sidebar_projection_years() -> int:
    """
    Render the common projection years slider.

    This slider is shared between Auto and Expert modes to ensure
    a single source of truth for the projection horizon (DRY principle).

    Returns
    -------
    int
        Number of projection years selected.
    """
    st.header(SidebarTexts.SEC_4_HORIZON)
    years = st.slider(
        SidebarTexts.YEARS_LABEL,
        min_value=_MIN_PROJECTION_YEARS,
        max_value=_MAX_PROJECTION_YEARS,
        value=_DEFAULT_PROJECTION_YEARS,
    )
    st.divider()
    return years


def _render_sidebar_auto_options(mode: ValuationMode) -> Dict:
    """Rend les options spécifiques au mode Auto (excluding projection years)."""
    enable_mc = False
    mc_sims = _DEFAULT_MC_SIMULATIONS

    if mode.supports_monte_carlo:
        st.header(SidebarTexts.SEC_5_RISK)
        enable_mc = st.toggle(SidebarTexts.MC_TOGGLE_LABEL, value=False)
        if enable_mc:
            mc_sims = st.number_input(
                SidebarTexts.MC_SIMS_LABEL,
                min_value=_MIN_MC_SIMULATIONS,
                max_value=_MAX_MC_SIMULATIONS,
                value=_DEFAULT_MC_SIMULATIONS,
                step=_MC_SIMULATIONS_STEP,
            )
        st.divider()

    return {
        "enable_mc": enable_mc,
        "mc_sims": mc_sims,
    }


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
    Guide d'onboarding — Restitution intégrale pilotée par OnboardingTexts.
    Version : V10.0 (Sprint 3)
    """
    # --- Introduction ---
    st.info(OnboardingTexts.INTRO_INFO)
    st.divider()

    # --- SECTION A : MÉTHODOLOGIES ---
    st.subheader(OnboardingTexts.TITLE_A)
    st.markdown(OnboardingTexts.DESC_A)

    # Grille de 4 colonnes pour les modèles financiers
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(OnboardingTexts.MODEL_DCF_TITLE)
        st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")
        st.markdown(f"<small style='color: #64748b;'>{OnboardingTexts.MODEL_DCF_DESC}</small>", unsafe_allow_html=True)

    with m2:
        st.markdown(OnboardingTexts.MODEL_EQUITY_TITLE)
        st.latex(r"P = \sum_{t=1}^{n} \frac{FCFE_t}{(1+k_e)^t} + \frac{TV_n}{(1+k_e)^n}")
        st.markdown(f"<small style='color: #64748b;'>{OnboardingTexts.MODEL_EQUITY_DESC}</small>", unsafe_allow_html=True)

    with m3:
        st.markdown(OnboardingTexts.MODEL_RIM_TITLE)
        st.latex(r"V_0 = BV_0 + \sum_{t=1}^{n} \frac{RI_t}{(1+k_e)^t} + \frac{TV_{RI}}{(1+k_e)^n}")
        st.markdown(f"<small style='color: #64748b;'>{OnboardingTexts.MODEL_RIM_DESC}</small>", unsafe_allow_html=True)

    with m4:
        st.markdown(OnboardingTexts.MODEL_GRAHAM_TITLE)
        st.latex(r"V_0 = EPS \times (8.5 + 2g) \times \frac{4.4}{Y}")
        st.markdown(f"<small style='color: #64748b;'>{OnboardingTexts.MODEL_GRAHAM_DESC}</small>", unsafe_allow_html=True)

    st.divider()

    # --- SECTION B : RISQUE & PILOTAGE ---
    st.subheader(OnboardingTexts.TITLE_B)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(OnboardingTexts.PILOTAGE_TITLE)
        st.caption(OnboardingTexts.PILOTAGE_DESC)
    with c2:
        st.markdown(OnboardingTexts.MC_TITLE)
        st.caption(OnboardingTexts.MC_DESC)

    st.divider()

    # --- SECTION C : GOUVERNANCE ---
    st.subheader(OnboardingTexts.TITLE_C)
    g1, g2 = st.columns([2, 3])
    with g1:
        st.markdown(OnboardingTexts.AUDIT_TITLE)
        st.caption(OnboardingTexts.AUDIT_DESC)
    with g2:
        st.markdown(OnboardingTexts.TRACE_TITLE)
        st.caption(OnboardingTexts.TRACE_DESC)

    st.divider()

    # --- FOOTER : DIAGNOSTIC ---
    st.markdown(f"**{OnboardingTexts.DIAGNOSTIC_HEADER}**")
    d1, d2, d3 = st.columns(3)
    d1.error(OnboardingTexts.DIAG_BLOQUANT)
    d2.warning(OnboardingTexts.DIAG_WARN)
    d3.info(OnboardingTexts.DIAG_INFO)


def _handle_expert_mode(ticker: str, mode: ValuationMode, projection_years: int) -> None:
    """Gère l'affichage et le lancement en mode Expert."""
    if not ticker:
        st.warning(FeedbackMessages.TICKER_REQUIRED_SIDEBAR)
        return

    # Sprint 2: Utilisation de la factory pour les terminaux isolés
    from app.ui.expert.factory import create_expert_terminal
    terminal = create_expert_terminal(mode, ticker)
    terminal.set_projection_years(projection_years)
    request = terminal.render()
    if request:
        _set_active_request(request)


def _handle_auto_launch(ticker: str, mode: ValuationMode, options: Dict, projection_years: int) -> None:
    """Gère le lancement en mode Auto avec support des scénarios par défaut."""
    if not ticker:
        st.warning(FeedbackMessages.TICKER_INVALID)
        return

    options.setdefault("manual_peers", [])

    # Instanciation segmentée avec Scénarios désactivés par défaut (Sprint 5)
    from src.domain.models import ScenarioParameters  # Import local si nécessaire

    config_params = DCFParameters(
        rates=CoreRateParameters(),
        growth=GrowthParameters(projection_years=projection_years),
        monte_carlo=MonteCarloConfig(
            enable_monte_carlo=options["enable_mc"],
            num_simulations=options["mc_sims"]
        ),
        scenarios=ScenarioParameters(enabled=False),
        sotp = SOTPParameters(enabled=False)
    )

    request = ValuationRequest(
        ticker=ticker,
        projection_years=projection_years,
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

        # Common projection years slider (shared between Auto and Expert)
        projection_years = _render_sidebar_projection_years()

        # Reset if configuration changes (ticker, mode, source, or years)
        current_config = f"{ticker}_{is_expert}_{selected_mode.value}_{projection_years}"
        _reset_on_config_change(current_config)

        # Options spécifiques au mode Auto
        auto_options = {}
        launch_analysis = False

        if not is_expert:
            auto_options = _render_sidebar_auto_options(selected_mode)
            launch_analysis = st.button(
                CommonTexts.RUN_BUTTON,
                type="primary",
                width='stretch',
            )

        _render_sidebar_footer()

    # =========================================================================
    # CONTENT — Affichage principal
    # =========================================================================
    if SessionManager.get_active_request():
        run_workflow_and_display(SessionManager.get_active_request())

    elif is_expert:
        _handle_expert_mode(ticker, selected_mode, projection_years)

    elif launch_analysis:
        _handle_auto_launch(ticker, selected_mode, auto_options, projection_years)

    else:
        _render_onboarding_guide()


# ==============================================================================
# EXÉCUTION
# ==============================================================================

if __name__ == "__main__":
    main()
