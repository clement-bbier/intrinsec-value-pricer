"""
app/ui/expert_terminals/shared_widgets.py

WIDGETS PARTAGÉS — Composants UI réutilisables entre terminaux experts.

Pattern : Single Responsibility (SOLID)
Style : Numpy docstrings

Conventions de nommage :
    - widget_*  : Widgets interactifs (retournent des données utilisateur)
    - build_*   : Constructeurs (transforment les données en objets métier)
    - display_* : Affichage pur (ne retournent rien, side-effects only)

Note : Les widgets reproduisent fidèlement les fonctionnalités du legacy
       (ui_inputs_expert.py) tout en améliorant la structure et la lisibilité.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

import streamlit as st
import pandas as pd

from core.models import (
    DCFParameters,
    ValuationMode,
    TerminalValueMethod,
    ScenarioParameters,
    ScenarioVariant,
    BusinessUnit,
    SOTPMethod,
    SOTPParameters,
)
from core.i18n import ExpertTerminalTexts, SOTPTexts
from core.config.settings import SIMULATION_CONFIG, VALUATION_CONFIG
from core.config.constants import UIWidgetDefaults, TechnicalDefaults

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. WIDGETS D'ENTRÉE DE BASE (Sections 1-2)
# ==============================================================================

def widget_projection_years(
    default: int = UIWidgetDefaults.DEFAULT_PROJECTION_YEARS,
    min_years: int = UIWidgetDefaults.MIN_PROJECTION_YEARS,
    max_years: int = UIWidgetDefaults.MAX_PROJECTION_YEARS,
    key: Optional[str] = None
) -> int:
    """
    Widget pour sélectionner le nombre d'années de projection.

    Parameters
    ----------
    default : int, optional
        Valeur par défaut, by default 5.
    min_years : int, optional
        Minimum autorisé, by default 3.
    max_years : int, optional
        Maximum autorisé, by default 15.
    key : str, optional
        Clé Streamlit unique pour le widget.

    Returns
    -------
    int
        Nombre d'années sélectionné.
    """
    return st.slider(
        ExpertTerminalTexts.SLIDER_PROJ_YEARS,
        min_value=min_years,
        max_value=max_years,
        value=default,
        key=key,
        help=ExpertTerminalTexts.HELP_PROJ_YEARS
    )


def widget_growth_rate(
    label: str = None,
    min_val: float = UIWidgetDefaults.MIN_GROWTH_RATE,
    max_val: float = UIWidgetDefaults.MAX_GROWTH_RATE,
    default: Optional[float] = None,
    key: Optional[str] = None
) -> Optional[float]:
    """
    Widget pour saisir un taux de croissance.

    Parameters
    ----------
    label : str, optional
        Label du champ.
    min_val : float, optional
        Valeur minimale.
    max_val : float, optional
        Valeur maximale.
    default : float, optional
        Valeur par défaut (None = Auto Yahoo).
    key : str, optional
        Clé Streamlit unique.

    Returns
    -------
    Optional[float]
        Taux de croissance saisi ou None si vide.
    """
    return st.number_input(
        label or ExpertTerminalTexts.INP_GROWTH_G,
        min_value=min_val,
        max_value=max_val,
        value=default,
        format="%.3f",
        key=key,
        help=ExpertTerminalTexts.HELP_GROWTH_RATE
    )


# ==============================================================================
# 2. WIDGET COÛT DU CAPITAL (Section 3)
# ==============================================================================

def widget_cost_of_capital(mode: ValuationMode) -> Dict[str, Any]:
    """
    Widget pour la saisie du coût du capital (WACC ou Ke).

    Affiche les inputs appropriés selon que le modèle valorise au niveau
    de la firme (WACC) ou directement au niveau equity (Ke).

    Parameters
    ----------
    mode : ValuationMode
        Mode de valorisation pour déterminer si c'est Direct Equity.

    Returns
    -------
    Dict[str, Any]
        Dictionnaire contenant les paramètres de taux saisis :
        - risk_free_rate : Taux sans risque
        - manual_beta : Beta
        - market_risk_premium : Prime de risque marché
        - manual_stock_price : Prix pour calcul des poids (optionnel)
        - cost_of_debt : Coût de la dette (si WACC)
        - tax_rate : Taux d'imposition (si WACC)
    """
    st.markdown(ExpertTerminalTexts.SEC_3_CAPITAL)

    is_direct_equity = mode.is_direct_equity

    # Formule affichée selon le type
    if is_direct_equity:
        st.latex(r"k_e = R_f + \beta \times MRP")
    else:
        st.latex(r"WACC = w_e [R_f + \beta(MRP)] + w_d [k_d(1-\tau)]")

    # Prix de l'action pour calcul des poids
    manual_price = st.number_input(
        ExpertTerminalTexts.INP_PRICE_WEIGHTS,
        min_value=0.0,
        max_value=10000.0,
        value=None,
        format="%.2f",
        help=ExpertTerminalTexts.HELP_PRICE_WEIGHTS
    )

    col_a, col_b = st.columns(2)

    rf = col_a.number_input(
        ExpertTerminalTexts.INP_RF,
        min_value=0.0,
        max_value=0.20,
        value=None,
        format="%.3f",
        help=ExpertTerminalTexts.HELP_RF
    )
    beta = col_b.number_input(
        ExpertTerminalTexts.INP_BETA,
        min_value=0.0,
        max_value=5.0,
        value=None,
        format="%.2f",
        help=ExpertTerminalTexts.HELP_BETA
    )
    mrp = col_a.number_input(
        ExpertTerminalTexts.INP_MRP,
        min_value=0.0,
        max_value=0.20,
        value=None,
        format="%.3f",
        help=ExpertTerminalTexts.HELP_MRP
    )

    result = {
        "risk_free_rate": rf,
        "manual_beta": beta,
        "market_risk_premium": mrp,
        "manual_stock_price": manual_price,
    }

    # Paramètres WACC supplémentaires (non Direct Equity)
    if not is_direct_equity:
        kd = col_b.number_input(
            ExpertTerminalTexts.INP_KD,
            min_value=0.0,
            max_value=0.20,
            value=None,
            format="%.3f",
            help=ExpertTerminalTexts.HELP_KD
        )
        tau = col_a.number_input(
            ExpertTerminalTexts.INP_TAX,
            min_value=0.0,
            max_value=0.60,
            value=None,
            format="%.2f",
            help=ExpertTerminalTexts.HELP_TAX
        )
        result.update({"cost_of_debt": kd, "tax_rate": tau})
    
    logger.debug(
        "Cost of capital inputs collected: mode=%s, is_direct_equity=%s",
        mode.value, is_direct_equity
    )

    st.divider()
    return result


# ==============================================================================
# 3. WIDGET VALEUR TERMINALE (Section 4)
# ==============================================================================

def widget_terminal_value_dcf(formula_latex: str) -> Dict[str, Any]:
    """
    Widget pour la sélection de la méthode de valeur terminale (DCF).

    Propose deux méthodes :
    - Gordon Growth Model (croissance perpétuelle)
    - Exit Multiple (multiple de sortie EV/EBITDA ou P/E)

    Parameters
    ----------
    formula_latex : str
        Formule LaTeX à afficher pour illustrer le concept.

    Returns
    -------
    Dict[str, Any]
        - terminal_method : TerminalValueMethod choisi
        - perpetual_growth_rate : Taux gn si Gordon
        - exit_multiple_value : Multiple si Exit
    """
    st.markdown(ExpertTerminalTexts.SEC_4_TERMINAL)
    st.latex(formula_latex)

    method = st.radio(
        ExpertTerminalTexts.RADIO_TV_METHOD,
        options=[TerminalValueMethod.GORDON_GROWTH, TerminalValueMethod.EXIT_MULTIPLE],
        format_func=lambda x: (
            ExpertTerminalTexts.TV_GORDON
            if x == TerminalValueMethod.GORDON_GROWTH
            else ExpertTerminalTexts.TV_EXIT
        ),
        horizontal=True
    )

    col1, _ = st.columns(2)

    if method == TerminalValueMethod.GORDON_GROWTH:
        gn = col1.number_input(
            ExpertTerminalTexts.INP_PERP_G,
            min_value=0.0,
            max_value=0.05,
            value=None,
            format="%.3f",
            help=ExpertTerminalTexts.HELP_PERP_G
        )
        st.divider()
        logger.debug("Terminal value: Gordon Growth selected, gn=%s", gn)
        return {"terminal_method": method, "perpetual_growth_rate": gn}
    else:
        exit_m = col1.number_input(
            ExpertTerminalTexts.INP_EXIT_MULT,
            min_value=0.0,
            max_value=100.0,
            value=None,
            format="%.1f",
            help=ExpertTerminalTexts.HELP_EXIT_MULT
        )
        st.divider()
        logger.debug("Terminal value: Exit Multiple selected, mult=%s", exit_m)
        return {"terminal_method": method, "exit_multiple_value": exit_m}


def widget_terminal_value_rim(formula_latex: str) -> Dict[str, Any]:
    """
    Widget pour la valeur terminale du modèle RIM (facteur de persistance).

    Le RIM utilise un facteur omega (ω) représentant la persistance
    des profits anormaux au-delà de l'horizon explicite.

    Parameters
    ----------
    formula_latex : str
        Formule LaTeX du RIM terminal value.

    Returns
    -------
    Dict[str, Any]
        - terminal_method : EXIT_MULTIPLE (convention RIM)
        - exit_multiple_value : Facteur omega
    """
    st.markdown(ExpertTerminalTexts.SEC_4_TERMINAL)
    st.latex(formula_latex)

    col1, _ = st.columns(2)
    omega = col1.number_input(
        ExpertTerminalTexts.INP_OMEGA,
        min_value=0.0,
        max_value=1.0,
        value=None,
        format="%.2f",
        help=ExpertTerminalTexts.HELP_OMEGA
    )
    logger.debug("RIM terminal value: omega=%s", omega)

    st.divider()
    return {
        "terminal_method": TerminalValueMethod.EXIT_MULTIPLE,
        "exit_multiple_value": omega
    }


# ==============================================================================
# 4. WIDGET EQUITY BRIDGE (Section 5)
# ==============================================================================

def widget_equity_bridge(
    formula_latex: str,
    mode: ValuationMode
) -> Dict[str, Any]:
    """
    Widget pour les ajustements de structure (Equity Bridge).

    Convertit l'Enterprise Value en Equity Value :
    Equity = EV - Dette + Cash - Minorities - Pensions

    Pour les modèles Direct Equity, seul le nombre d'actions est demandé.

    Parameters
    ----------
    formula_latex : str
        Formule LaTeX illustrant le bridge.
    mode : ValuationMode
        Mode pour déterminer si Direct Equity.

    Returns
    -------
    Dict[str, Any]
        Paramètres de bridge collectés (dette, cash, actions, etc.)
    """
    st.markdown(ExpertTerminalTexts.SEC_5_BRIDGE)
    st.latex(formula_latex)

    is_direct_equity = mode.is_direct_equity

    if is_direct_equity:
        # Direct Equity : seul le nombre d'actions est nécessaire
        shares = st.number_input(
            ExpertTerminalTexts.INP_SHARES,
            value=None,
            format="%.0f",
            help=ExpertTerminalTexts.HELP_SHARES
        )
        st.divider()
        return {"manual_shares_outstanding": shares}

    # Firm-Level : bridge complet EV -> Equity
    col1, col2, col3 = st.columns(3)

    debt = col1.number_input(
        ExpertTerminalTexts.INP_DEBT,
        value=None,
        format="%.0f",
        help=ExpertTerminalTexts.HELP_DEBT
    )
    cash = col2.number_input(
        ExpertTerminalTexts.INP_CASH,
        value=None,
        format="%.0f",
        help=ExpertTerminalTexts.HELP_CASH
    )
    shares = col3.number_input(
        ExpertTerminalTexts.INP_SHARES,
        value=None,
        format="%.0f",
        help=ExpertTerminalTexts.HELP_SHARES
    )

    minorities = col1.number_input(
        ExpertTerminalTexts.INP_MINORITIES,
        value=None,
        format="%.0f",
        help=ExpertTerminalTexts.HELP_MINORITIES
    )
    pensions = col2.number_input(
        ExpertTerminalTexts.INP_PENSIONS,
        value=None,
        format="%.0f",
        help=ExpertTerminalTexts.HELP_PENSIONS
    )

    st.divider()
    return {
        "manual_total_debt": debt,
        "manual_cash": cash,
        "manual_shares_outstanding": shares,
        "manual_minority_interests": minorities,
        "manual_pension_provisions": pensions,
    }


# ==============================================================================
# 5. WIDGET MONTE CARLO (Section 6 - Optionnel)
# ==============================================================================

def widget_monte_carlo(
    mode: ValuationMode,
    terminal_method: Optional[TerminalValueMethod] = None
) -> Dict[str, Any]:
    """
    Widget pour la configuration Monte Carlo.

    Permet de calibrer les volatilités des variables clés pour
    générer une distribution de valeurs intrinsèques.

    Parameters
    ----------
    mode : ValuationMode
        Mode pour adapter les volatilités (RIM vs DCF).
    terminal_method : TerminalValueMethod, optional
        Méthode TV pour afficher la bonne volatilité terminale.

    Returns
    -------
    Dict[str, Any]
        Configuration Monte Carlo :
        - enable_monte_carlo : bool
        - num_simulations : int
        - base_flow_volatility : float
        - beta_volatility : float
        - growth_volatility : float
        - terminal_growth_volatility : float (si applicable)
    """
    st.markdown(ExpertTerminalTexts.SEC_6_MC)

    enable = st.toggle(
        ExpertTerminalTexts.MC_CALIBRATION,
        value=False,
        help=ExpertTerminalTexts.HELP_MC_ENABLE
    )

    if not enable:
        return {"enable_monte_carlo": False}

    with st.container(border=True):
        # 1. Nombre de simulations
        col_iter, _ = st.columns([2, 2])
        sims = col_iter.select_slider(
            ExpertTerminalTexts.MC_ITERATIONS,
            options=[SIMULATION_CONFIG.min_simulations,
                    SIMULATION_CONFIG.default_simulations,
                    10000,
                    SIMULATION_CONFIG.max_simulations],
            value=SIMULATION_CONFIG.default_simulations,
            help=ExpertTerminalTexts.HELP_MC_SIMS
        )
        st.divider()

        # 2. Volatilités
        st.caption("**Calibration des volatilites (ecarts-types)**")
        v_col1, v_col2 = st.columns(2)

        # Volatilité flux de base (Y0)
        v0 = v_col1.number_input(
            ExpertTerminalTexts.MC_VOL_BASE_FLOW,
            min_value=0.0,
            max_value=0.50,
            value=0.05,
            format="%.3f",
            help=ExpertTerminalTexts.HELP_MC_VOL_FLOW
        )

        # Volatilité Beta
        vb = v_col2.number_input(
            ExpertTerminalTexts.MC_VOL_BETA,
            min_value=0.0,
            max_value=1.0,
            value=0.10,
            format="%.3f",
            help=ExpertTerminalTexts.HELP_MC_VOL_BETA
        )

        # Volatilité croissance
        vg = v_col1.number_input(
            ExpertTerminalTexts.MC_VOL_G,
            min_value=0.0,
            max_value=0.20,
            value=0.02,
            format="%.3f",
            help=ExpertTerminalTexts.HELP_MC_VOL_G
        )

        # 3. Volatilité terminale (contextuelle)
        v_term = 0.0
        if mode == ValuationMode.RIM:
            v_term = v_col2.number_input(
                ExpertTerminalTexts.LBL_VOL_OMEGA,
                min_value=0.0,
                max_value=0.20,
                value=0.05,
                format="%.3f",
                help=ExpertTerminalTexts.HELP_MC_VOL_OMEGA
            )
        elif terminal_method == TerminalValueMethod.GORDON_GROWTH:
            v_term = v_col2.number_input(
                ExpertTerminalTexts.LBL_VOL_GN,
                min_value=0.0,
                max_value=0.05,
                value=0.01,
                format="%.3f",
                help=ExpertTerminalTexts.HELP_MC_VOL_GN
            )
        else:
            v_col2.empty()

        return {
            "enable_monte_carlo": True,
            "num_simulations": sims,
            "base_flow_volatility": v0,
            "beta_volatility": vb,
            "growth_volatility": vg,
            "terminal_growth_volatility": v_term,
        }


# ==============================================================================
# 6. WIDGET PEER TRIANGULATION (Section 7 - Optionnel)
# ==============================================================================

def widget_peer_triangulation() -> Dict[str, Any]:
    """
    Widget pour la sélection des peers et triangulation par multiples.

    Permet à l'utilisateur de spécifier manuellement une cohorte
    de comparables pour la valorisation relative.

    Returns
    -------
    Dict[str, Any]
        - enable_peer_multiples : bool
        - manual_peers : List[str] ou None
    """
    with st.expander(ExpertTerminalTexts.SEC_7_PEERS, expanded=False):
        enable = st.checkbox(
            "Activer la triangulation par multiples",
            value=True,
            help=ExpertTerminalTexts.HELP_PEER_TRIANGULATION
        )

        if not enable:
            return {"enable_peer_multiples": False, "manual_peers": None}

        raw_input = st.text_input(
            ExpertTerminalTexts.INP_MANUAL_PEERS,
            placeholder="ex: AAPL, MSFT, GOOG",
            help=ExpertTerminalTexts.HELP_MANUAL_PEERS
        )

        peers_list = None
        if raw_input.strip():
            peers_list = [t.strip().upper() for t in raw_input.split(",") if t.strip()]
            if peers_list:
                st.caption(f"*Peers sélectionnés : {', '.join(peers_list)}*")

        return {
            "enable_peer_multiples": True,
            "manual_peers": peers_list,
        }


# ==============================================================================
# 7. WIDGET SCÉNARIOS (Section 8 - Optionnel)
# ==============================================================================

def widget_scenarios(mode: ValuationMode) -> ScenarioParameters:
    """
    Widget pour l'analyse de scénarios déterministes (Bull/Base/Bear).

    Permet de définir des variantes avec probabilités et paramètres
    différenciés pour chaque scénario.

    Parameters
    ----------
    mode : ValuationMode
        Mode pour adapter les inputs (ex: marge FCF pour FCFF_GROWTH).

    Returns
    -------
    ScenarioParameters
        Configuration des scénarios (enabled, bull, base, bear).
    """
    with st.expander(ExpertTerminalTexts.SEC_8_SCENARIOS, expanded=False):
        enabled = st.toggle(
            ExpertTerminalTexts.INP_SCENARIO_ENABLE,
            value=False,
            help=ExpertTerminalTexts.HELP_SCENARIO_ENABLE
        )

        if not enabled:
            return ScenarioParameters(enabled=False)

        st.caption(ExpertTerminalTexts.SCENARIO_HINT)

        show_margin = mode == ValuationMode.FCFF_GROWTH

        # Bull Case
        with st.container(border=True):
            st.markdown(f"**{ExpertTerminalTexts.LABEL_SCENARIO_BULL}**")
            c1, c2, c3 = st.columns(3)
            p_bull = c1.number_input(
                ExpertTerminalTexts.INP_SCENARIO_PROBA,
                min_value=0.0, max_value=100.0, value=25.0, step=5.0,
                key="sc_p_bull"
            ) / 100
            g_bull = c2.number_input(
                ExpertTerminalTexts.INP_SCENARIO_GROWTH,
                value=None, format="%.3f", key="sc_g_bull"
            )
            m_bull = None
            if show_margin:
                m_bull = c3.number_input(
                    ExpertTerminalTexts.INP_SCENARIO_MARGIN,
                    value=None, format="%.2f", key="sc_m_bull"
                )

        # Base Case
        with st.container(border=True):
            st.markdown(f"**{ExpertTerminalTexts.LABEL_SCENARIO_BASE}**")
            c1, c2, c3 = st.columns(3)
            p_base = c1.number_input(
                ExpertTerminalTexts.INP_SCENARIO_PROBA,
                min_value=0.0, max_value=100.0, value=50.0, step=5.0,
                key="sc_p_base"
            ) / 100
            g_base = c2.number_input(
                ExpertTerminalTexts.INP_SCENARIO_GROWTH,
                value=None, format="%.3f", key="sc_g_base"
            )
            m_base = None
            if show_margin:
                m_base = c3.number_input(
                    ExpertTerminalTexts.INP_SCENARIO_MARGIN,
                    value=None, format="%.2f", key="sc_m_base"
                )

        # Bear Case
        with st.container(border=True):
            st.markdown(f"**{ExpertTerminalTexts.LABEL_SCENARIO_BEAR}**")
            c1, c2, c3 = st.columns(3)
            p_bear = c1.number_input(
                ExpertTerminalTexts.INP_SCENARIO_PROBA,
                min_value=0.0, max_value=100.0, value=25.0, step=5.0,
                key="sc_p_bear"
            ) / 100
            g_bear = c2.number_input(
                ExpertTerminalTexts.INP_SCENARIO_GROWTH,
                value=None, format="%.3f", key="sc_g_bear"
            )
            m_bear = None
            if show_margin:
                m_bear = c3.number_input(
                    ExpertTerminalTexts.INP_SCENARIO_MARGIN,
                    value=None, format="%.2f", key="sc_m_bear"
                )

        # Validation des probabilités
        total_prob = p_bull + p_base + p_bear
        if abs(total_prob - 1.0) > TechnicalDefaults.PROBABILITY_TOLERANCE:
            st.warning(
                f"Somme des probabilites = {total_prob:.0%}. "
                "Doit etre egale a 100%."
            )

        return ScenarioParameters(
            enabled=True,
            bull=ScenarioVariant(
                label="Bull",
                growth_rate=g_bull,
                target_fcf_margin=m_bull,
                probability=p_bull
            ),
            base=ScenarioVariant(
                label="Base",
                growth_rate=g_base,
                target_fcf_margin=m_base,
                probability=p_base
            ),
            bear=ScenarioVariant(
                label="Bear",
                growth_rate=g_bear,
                target_fcf_margin=m_bear,
                probability=p_bear
            ),
        )


# ==============================================================================
# 8. WIDGET SOTP (Sum-of-the-Parts - Optionnel)
# ==============================================================================

def widget_sotp(params: DCFParameters) -> None:
    """
    Widget pour la configuration Sum-of-the-Parts.

    Permet de définir des segments d'activité avec leurs valeurs
    respectives et d'appliquer une décote de conglomérat.

    Parameters
    ----------
    params : DCFParameters
        Paramètres à modifier in-place avec la config SOTP.

    Notes
    -----
    Ce widget modifie `params.sotp` directement (side-effect).
    """
    with st.expander(SOTPTexts.TITLE, expanded=False):
        params.sotp.enabled = st.toggle(
            SOTPTexts.SEC_SEGMENTS,
            value=params.sotp.enabled,
            help=SOTPTexts.HELP_SOTP if hasattr(SOTPTexts, 'HELP_SOTP') else None
        )

        if not params.sotp.enabled:
            return

        # Données actuelles ou défaut
        current_data = [
            {
                SOTPTexts.LBL_SEGMENT_NAME: bu.name,
                SOTPTexts.LBL_SEGMENT_VALUE: bu.enterprise_value,
                SOTPTexts.LBL_SEGMENT_REVENUE: getattr(bu, 'revenue', 0.0),
                SOTPTexts.LBL_SEGMENT_METHOD: bu.method.value,
            }
            for bu in params.sotp.segments
        ]

        if not current_data:
            current_data = [{
                SOTPTexts.LBL_SEGMENT_NAME: "Segment A",
                SOTPTexts.LBL_SEGMENT_VALUE: 0.0,
                SOTPTexts.LBL_SEGMENT_REVENUE: 0.0,
                SOTPTexts.LBL_SEGMENT_METHOD: SOTPMethod.DCF.value,
            }]

        # Éditeur de données
        edited_df = st.data_editor(
            pd.DataFrame(current_data),
            num_rows="dynamic",
            width='stretch',
            key="sotp_editor",
            column_config={
                SOTPTexts.LBL_SEGMENT_VALUE: st.column_config.NumberColumn(
                    format="%.2f"
                ),
                SOTPTexts.LBL_SEGMENT_METHOD: st.column_config.SelectboxColumn(
                    options=[m.value for m in SOTPMethod]
                ),
            }
        )

        # Mise à jour des segments
        params.sotp.segments = [
            BusinessUnit(
                name=row[SOTPTexts.LBL_SEGMENT_NAME],
                enterprise_value=row[SOTPTexts.LBL_SEGMENT_VALUE],
                method=SOTPMethod(row[SOTPTexts.LBL_SEGMENT_METHOD]),
            )
            for _, row in edited_df.iterrows()
            if row[SOTPTexts.LBL_SEGMENT_NAME]
        ]

        # Décote de conglomérat
        st.markdown(SOTPTexts.SEC_ADJUSTMENTS if hasattr(SOTPTexts, 'SEC_ADJUSTMENTS') else "**Ajustements**")
        params.sotp.conglomerate_discount = st.slider(
            SOTPTexts.LBL_DISCOUNT if hasattr(SOTPTexts, 'LBL_DISCOUNT') else "Decote conglomerat (%)",
            min_value=0,
            max_value=50,
            value=int(params.sotp.conglomerate_discount * 100),
            step=5,
            help=ExpertTerminalTexts.HELP_SOTP_DISCOUNT
        ) / 100.0


# ==============================================================================
# 9. CONSTRUCTEUR DE PARAMÈTRES
# ==============================================================================

def build_dcf_parameters(collected_data: Dict[str, Any]) -> DCFParameters:
    """
    Construit un objet DCFParameters à partir des données collectées.

    Fusionne les données des widgets avec des valeurs par défaut
    et utilise la méthode from_legacy pour la conversion.

    Parameters
    ----------
    collected_data : Dict[str, Any]
        Données brutes collectées par les widgets.

    Returns
    -------
    DCFParameters
        Objet paramètres structuré pour le moteur de valorisation.

    Notes
    -----
    Les valeurs None sont ignorées et les defaults sont appliqués
    via DCFParameters.from_legacy().
    """
    defaults = {
        "projection_years": VALUATION_CONFIG.default_projection_years,
        "terminal_method": TerminalValueMethod.GORDON_GROWTH,
        "enable_monte_carlo": False,
        "num_simulations": SIMULATION_CONFIG.default_simulations,
        "base_flow_volatility": 0.05,
        "beta_volatility": SIMULATION_CONFIG.default_volatility_beta,
        "growth_volatility": SIMULATION_CONFIG.default_volatility_growth,
    }

    # Fusion avec filtrage des None
    merged = {
        **defaults,
        **{k: v for k, v in collected_data.items() if v is not None}
    }

    logger.debug(
        "Building DCFParameters with %d non-null inputs",
        len([v for v in collected_data.values() if v is not None])
    )

    return DCFParameters.from_legacy(merged)
