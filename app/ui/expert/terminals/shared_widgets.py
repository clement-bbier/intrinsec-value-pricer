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
from typing import Dict, Any, Optional

import streamlit as st
import pandas as pd

from src.models import (
    DCFParameters,
    ValuationMode,
    TerminalValueMethod,
    ScenarioParameters,
    ScenarioVariant,
    BusinessUnit,
    SOTPMethod,
)
from src.i18n import SharedTexts, SOTPTexts
from src.config.settings import SIMULATION_CONFIG, VALUATION_CONFIG
from src.config.constants import UIWidgetDefaults, TechnicalDefaults

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. WIDGETS D'ENTRÉE DE BASE (Sections 1-2)
# ==============================================================================

def widget_projection_years(
    default: int = UIWidgetDefaults.DEFAULT_PROJECTION_YEARS,
    min_years: int = UIWidgetDefaults.MIN_PROJECTION_YEARS,
    max_years: int = UIWidgetDefaults.MAX_PROJECTION_YEARS,
    key_prefix: Optional[str] = None
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
    key_prefix : str, optional
        Préfixe pour les clés Streamlit (défaut: "projection").

    Returns
    -------
    int
        Nombre d'années sélectionné.
    """
    # Générer la clé si non fournie
    if key_prefix is None:
        key_prefix = "projection"

    return st.slider(
        SharedTexts.INP_PROJ_YEARS,
        min_value=min_years,
        max_value=max_years,
        value=default,
        key=f"{key_prefix}_years",
        help=SharedTexts.HELP_PROJ_YEARS
    )


def widget_growth_rate(
    label: str = None,
    min_val: float = UIWidgetDefaults.MIN_GROWTH_RATE,
    max_val: float = UIWidgetDefaults.MAX_GROWTH_RATE,
    default: Optional[float] = None,
    key_prefix: Optional[str] = None
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
    key_prefix : str, optional
        Préfixe pour les clés Streamlit (défaut: "growth").

    Returns
    -------
    Optional[float]
        Taux de croissance saisi ou None si vide.
    """
    # Générer la clé si non fournie
    if key_prefix is None:
        key_prefix = "growth"

    return st.number_input(
        label or SharedTexts.INP_GROWTH_G,
        min_value=min_val,
        max_value=max_val,
        value=default,
        format="%.3f",
        key=f"{key_prefix}_growth_rate",
        help=SharedTexts.HELP_GROWTH_RATE
    )


# ==============================================================================
# 2. WIDGET COÛT DU CAPITAL (Section 3)
# ==============================================================================

def widget_cost_of_capital(mode: ValuationMode, key_prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Affiche le widget de saisie du coût du capital (WACC ou Ke).

    Cette fonction génère une interface dynamique adaptée au mode de valorisation.
    Elle centralise la saisie des paramètres de risque (Rf, Beta, MRP) et les 
    paramètres de structure de capital (Kd, Tax) pour les modèles de firme.

    Parameters
    ----------
    mode : ValuationMode
        Instance définissant si la valorisation est 'Direct Equity' ou 'Firm'.
    key_prefix : str, optional
        Préfixe unique pour les clés `st.session_state`. 
        Par défaut, utilise `mode.name`.

    Returns
    -------
    Dict[str, Any]
        Dictionnaire contenant les entrées utilisateur collectées :
        - risk_free_rate (float | None)
        - manual_beta (float | None)
        - market_risk_premium (float | None)
        - manual_stock_price (float | None)
        - cost_of_debt (float | None, seulement si non Direct Equity)
        - tax_rate (float | None, seulement si non Direct Equity)
    """
    prefix = key_prefix or mode.name

    # 1. En-tête et Formule théorique
    st.markdown(SharedTexts.SEC_3_CAPITAL)
    
    formula = (
        SharedTexts.FORMULA_CAPITAL_KE
        if mode.is_direct_equity 
        else SharedTexts.FORMULA_CAPITAL_WACC
    )
    st.latex(formula)

    # 2. Saisie du prix (utile pour le calcul des poids E et D)
    manual_price = st.number_input(
        label=SharedTexts.INP_PRICE_WEIGHTS,
        min_value=0.0,
        max_value=100000.0,
        value=None,
        step=0.01,
        format="%.2f",
        help=SharedTexts.HELP_PRICE_WEIGHTS,
        key=f"{prefix}_price"
    )

    # 3. Paramètres de risque (CAPM)
    col_a, col_b = st.columns(2)
    
    rf = col_a.number_input(
        label=SharedTexts.INP_RF,
        min_value=0.0,
        max_value=0.20,
        value=None,
        step=0.001,
        format="%.3f",
        help=SharedTexts.HELP_RF,
        key=f"{prefix}_rf"
    )
    
    beta = col_b.number_input(
        label=SharedTexts.INP_BETA,
        min_value=0.0,
        max_value=5.0,
        value=None,
        step=0.01,
        format="%.2f",
        help=SharedTexts.HELP_BETA,
        key=f"{prefix}_beta"
    )
    
    mrp = col_a.number_input(
        label=SharedTexts.INP_MRP,
        min_value=0.0,
        max_value=0.20,
        value=None,
        step=0.001,
        format="%.3f",
        help=SharedTexts.HELP_MRP,
        key=f"{prefix}_mrp"
    )

    # Préparation du dictionnaire de sortie
    collected_data = {
        "risk_free_rate": rf,
        "manual_beta": beta,
        "market_risk_premium": mrp,
        "manual_stock_price": manual_price,
    }

    # 4. Paramètres spécifiques au WACC (Dette et Fiscalité)
    if not mode.is_direct_equity:
        kd = col_b.number_input(
            label=SharedTexts.INP_KD,
            min_value=0.0,
            max_value=0.20,
            value=None,
            step=0.001,
            format="%.3f",
            help=SharedTexts.HELP_KD,
            key=f"{prefix}_kd"
        )
        
        tau = col_a.number_input(
            label=SharedTexts.INP_TAX,
            min_value=0.0,
            max_value=0.60,
            value=None,
            step=0.01,
            format="%.2f",
            help=SharedTexts.HELP_TAX,
            key=f"{prefix}_tax"
        )
        
        collected_data.update({
            "cost_of_debt": kd,
            "tax_rate": tau
        })

    st.divider()
    return collected_data


# ==============================================================================
# 3. WIDGET VALEUR TERMINALE (Section 4)
# ==============================================================================

@st.fragment
def widget_terminal_value_dcf(key_prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Widget Étape 4 : Sélection et calibration de la Valeur Terminale (TV).

    Affiche la formule LaTeX de manière centrale sous la description,
    actualisée dynamiquement selon la méthode choisie.

    Parameters
    ----------
    key_prefix : str, optional
        Préfixe pour les clés st.session_state, par défaut "terminal".

    Returns
    -------
    Dict[str, Any]
        Paramètres TV : méthode, taux de croissance ou multiple.
    """
    prefix = key_prefix or "terminal"

    # 1. En-tête de section
    st.markdown(SharedTexts.SEC_4_TERMINAL)
    st.info(SharedTexts.SEC_4_DESC)

    # 2. Choix de la méthode (Radio)
    method = st.radio(
        SharedTexts.RADIO_TV_METHOD,
        options=[TerminalValueMethod.GORDON_GROWTH, TerminalValueMethod.EXIT_MULTIPLE],
        format_func=lambda x: (
            SharedTexts.TV_GORDON if x == TerminalValueMethod.GORDON_GROWTH
            else SharedTexts.TV_EXIT
        ),
        horizontal=True,
        key=f"{prefix}_method"
    )

    # 3. Formule dynamique centrée
    if method == TerminalValueMethod.GORDON_GROWTH:
        st.latex(SharedTexts.FORMULA_TV_GORDON)
    else:
        st.latex(SharedTexts.FORMULA_TV_EXIT)

    # 4. Saisie des données
    col_inp, _ = st.columns(2)

    if method == TerminalValueMethod.GORDON_GROWTH:
        gn = col_inp.number_input(
            SharedTexts.INP_PERP_G,
            min_value=0.0, max_value=0.05,
            value=None, format="%.3f",
            help=SharedTexts.HELP_PERP_G,
            key=f"{prefix}_gn"
        )
        st.divider()
        return {"terminal_method": method, "perpetual_growth_rate": gn}
    else:
        exit_m = col_inp.number_input(
            SharedTexts.INP_EXIT_MULT,
            min_value=0.0, max_value=100.0,
            value=None, format="%.1f",
            help=SharedTexts.HELP_EXIT_MULT,
            key=f"{prefix}_exit_mult"
        )
        st.divider()
        return {"terminal_method": method, "exit_multiple_value": exit_m}


def widget_terminal_value_rim(formula_latex: str, key_prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Widget pour la valeur terminale du modèle RIM (facteur de persistance).

    Le RIM utilise un facteur omega (ω) représentant la persistance
    des profits anormaux au-delà de l'horizon explicite.

    Parameters
    ----------
    formula_latex : str
        Formule LaTeX du RIM terminal value.
    key_prefix : str, optional
        Préfixe pour les clés Streamlit (défaut: "terminal").

    Returns
    -------
    Dict[str, Any]
        - terminal_method : EXIT_MULTIPLE (convention RIM)
        - exit_multiple_value : Facteur omega
    """
    # Générer le préfixe de clé si non fourni
    if key_prefix is None:
        key_prefix = "terminal"

    st.markdown(SharedTexts.SEC_4_TERMINAL)
    st.latex(formula_latex)

    col1, _ = st.columns(2)
    omega = col1.number_input(
        SharedTexts.INP_OMEGA,
        min_value=0.0,
        max_value=1.0,
        value=None,
        format="%.2f",
        help=SharedTexts.HELP_OMEGA,
        key=f"{key_prefix}_omega"
    )
    logger.debug("RIM terminal value: omega=%s", omega)
    st.divider()

    return {
        "terminal_method": TerminalValueMethod.EXIT_MULTIPLE,
        "exit_multiple_value": omega
    }


# ==============================================================================
# 4. WIDGET EQUITY BRIDGE (Section 5) Pitchbook Design
# ==============================================================================

@st.fragment
def widget_equity_bridge(
    formula_latex: str,  # Gardé pour ne pas décaler les arguments lors de l'appel
    mode: ValuationMode,
    key_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Widget Étape 5 : Interface unifiée d'Equity Bridge et Dilution SBC.
    Répare l'AttributeError en respectant l'ordre des arguments (formula, mode).
    """
    prefix = key_prefix or f"bridge_{mode.value}"
    is_direct_equity = mode.is_direct_equity

    # --- EN-TÊTE NARRATIF UNIQUE ---
    st.markdown(SharedTexts.SEC_5_BRIDGE)
    st.info(SharedTexts.SEC_5_DESC)
    st.latex(SharedTexts.FORMULA_BRIDGE)

    if is_direct_equity:
        shares = st.number_input(
            SharedTexts.INP_SHARES,
            value=None, format="%.0f", help=SharedTexts.HELP_SHARES,
            key=f"{prefix}_shares_direct"
        )
        return {"manual_shares_outstanding": shares}

    # PARTIE 1 : Structure
    st.markdown(SharedTexts.BRIDGE_COMPONENTS)
    c_d, c_c = st.columns(2)
    debt = c_d.number_input(SharedTexts.INP_DEBT, value=None, format="%.0f", key=f"{prefix}_debt")
    cash = c_c.number_input(SharedTexts.INP_CASH, value=None, format="%.0f", key=f"{prefix}_cash")

    # PARTIE 2 : Ajustements
    st.markdown(SharedTexts.BRIDGE_ADJUSTMENTS)
    c_m, c_p, c_s = st.columns(3)
    minorities = c_m.number_input(SharedTexts.INP_MINORITIES, value=None, format="%.0f", key=f"{prefix}_min")
    pensions = c_p.number_input(SharedTexts.INP_PENSIONS, value=None, format="%.0f", key=f"{prefix}_pen")
    shares = c_s.number_input(SharedTexts.INP_SHARES, value=None, format="%.0f", key=f"{prefix}_shares")

    # PARTIE 3 : Dilution (SBC)
    st.markdown(SharedTexts.BRIDGE_DILUTION)
    sbc_rate = st.number_input(
        SharedTexts.INP_SBC_DILUTION, 0.0, 0.10, 0.0, 0.005, format="%.3f",
        key=f"{prefix}_sbc_rate"
    )
    st.divider()

    return {
        "manual_total_debt": debt, "manual_cash": cash,
        "manual_shares_outstanding": shares, "manual_minority_interests": minorities,
        "manual_pension_provisions": pensions, "stock_based_compensation_rate": sbc_rate
    }

# ==============================================================================
# 5. WIDGET MONTE CARLO (Section 6 - Optionnel)
# ==============================================================================

def widget_monte_carlo(
        mode: ValuationMode,
        terminal_method: Optional[TerminalValueMethod] = None,
        key_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Widget pour la configuration Monte Carlo (Flux Continu).
    """
    if key_prefix is None:
        key_prefix = "mc"

    st.markdown(SharedTexts.SEC_6_MC)

    enable = st.toggle(
        SharedTexts.MC_CALIBRATION,
        value=False,
        help=SharedTexts.HELP_MC_ENABLE,
        key=f"{key_prefix}_enable"
    )

    if not enable:
        return {"enable_monte_carlo": False}

    # --- SUPPRESSION DU CONTENEUR POUR UN FLUX CONTINU ---

    # 1. Nombre de simulations
    sims = st.select_slider(
        SharedTexts.MC_ITERATIONS,
        options=[SIMULATION_CONFIG.min_simulations,
                 SIMULATION_CONFIG.default_simulations,
                 10000,
                 SIMULATION_CONFIG.max_simulations],
        value=SIMULATION_CONFIG.default_simulations,
        help=SharedTexts.HELP_MC_SIMS,
        key=f"{key_prefix}_sims"
    )

    # 2. Volatilités
    st.caption(SharedTexts.MC_VOLATILITIES)
    v_col1, v_col2 = st.columns(2)

    v0 = v_col1.number_input(
        SharedTexts.MC_VOL_BASE_FLOW,
        min_value=0.0, max_value=0.50, value=0.05, format="%.3f",
        help=SharedTexts.HELP_MC_VOL_FLOW,
        key=f"{key_prefix}_vol_flow"
    )

    vb = v_col2.number_input(
        SharedTexts.MC_VOL_BETA,
        min_value=0.0, max_value=1.0, value=0.10, format="%.3f",
        help=SharedTexts.HELP_MC_VOL_BETA,
        key=f"{key_prefix}_vol_beta"
    )

    vg = v_col1.number_input(
        SharedTexts.MC_VOL_G,
        min_value=0.0, max_value=0.20, value=0.02, format="%.3f",
        help=SharedTexts.HELP_MC_VOL_G,
        key=f"{key_prefix}_vol_growth"
    )

    # 3. Volatilité terminale (contextuelle)
    v_term = 0.0
    if mode == ValuationMode.RIM:
        v_term = v_col2.number_input(
            SharedTexts.LBL_VOL_OMEGA,
            min_value=0.0, max_value=0.20, value=0.05, format="%.3f",
            help=SharedTexts.HELP_MC_VOL_OMEGA,
            key=f"{key_prefix}_vol_omega"
        )
    elif terminal_method == TerminalValueMethod.GORDON_GROWTH:
        v_term = v_col2.number_input(
            SharedTexts.LBL_VOL_GN,
            min_value=0.0, max_value=0.05, value=0.01, format="%.3f",
            help=SharedTexts.HELP_MC_VOL_GN,
            key=f"{key_prefix}_vol_gn"
        )

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

def widget_peer_triangulation(key_prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Widget plat pour la cohorte de comparables.

    Returns
    -------
    Dict[str, Any]
        Dictionnaire contenant l'état d'activation et la liste des tickers.
    """
    if key_prefix is None:
        key_prefix = "peer"

    st.divider()
    st.markdown(SharedTexts.SEC_7_PEERS)

    enable = st.toggle(
        SharedTexts.LBL_PEER_ENABLE,
        value=False,
        help=SharedTexts.HELP_PEER_TRIANGULATION,
        key=f"{key_prefix}_peer_enable"
    )

    if not enable:
        return {"enable_peer_multiples": False, "manual_peers": None}

    raw_input = st.text_input(
        SharedTexts.INP_MANUAL_PEERS,
        placeholder=SharedTexts.PLACEHOLDER_PEERS,
        help=SharedTexts.HELP_MANUAL_PEERS,
        key=f"{key_prefix}_input"
    )

    peers_list = None
    if raw_input and raw_input.strip():
        peers_list = [t.strip().upper() for t in raw_input.split(",") if t.strip()]
        if peers_list:
            st.caption(SharedTexts.PEERS_SELECTED.format(peers=', '.join(peers_list)))

    return {
        "enable_peer_multiples": True,
        "manual_peers": peers_list,
    }


# ==============================================================================
# 7. WIDGET SCÉNARIOS (Section 8 - Optionnel)
# ==============================================================================

def widget_scenarios(mode: ValuationMode, key_prefix: Optional[str] = None) -> ScenarioParameters:
    """
    Widget pour l'analyse multi-scénarios déterministes (Flux Continu).

    Affiche les variantes Bull/Base/Bear à la suite sans bordures pour
    respecter l'homogénéité visuelle du terminal expert.

    Returns
    -------
    ScenarioParameters
        Objet configuré avec Bull/Base/Base ou désactivé.
    """
    if key_prefix is None:
        key_prefix = "scenario"

    st.markdown(SharedTexts.SEC_8_SCENARIOS)

    # Désactivé par défaut comme demandé
    enabled = st.toggle(
        SharedTexts.INP_SCENARIO_ENABLE,
        value=False,
        help=SharedTexts.HELP_SCENARIO_ENABLE,
        key=f"{key_prefix}_scenario_enable"
    )

    if not enabled:
        return ScenarioParameters(enabled=False)

    st.info(SharedTexts.SCENARIO_HINT)
    show_margin = mode == ValuationMode.FCFF_GROWTH

    def _render_variant(label: str, p_key: str, g_key: str, m_key: str, default_p: float):
        # Suppression du st.container(border=True)
        st.markdown(f"**{label}**")
        c1, c2, c3 = st.columns(3)

        # Saisie des probabilités et hypothèses
        p = c1.number_input(
            SharedTexts.INP_SCENARIO_PROBA,
            0.0, 100.0, default_p, 5.0,
            key=p_key
        ) / 100

        g = c2.number_input(
            SharedTexts.INP_SCENARIO_GROWTH,
            value=None, format="%.3f",
            key=g_key
        )

        # Marge conditionnelle pour le modèle Growth
        m = None
        if show_margin:
            m = c3.number_input(
                SharedTexts.INP_SCENARIO_MARGIN,
                None, format="%.2f",
                key=m_key
            )

        st.write("")  # Petit espacement vertical entre les variantes
        return p, g, m

    # Rendu des trois variantes à la suite
    p_bull, g_bull, m_bull = _render_variant(
        SharedTexts.LABEL_SCENARIO_BULL, f"{key_prefix}_p_bull",
        f"{key_prefix}_g_bull", f"{key_prefix}_m_bull", 25.0
    )
    p_base, g_base, m_base = _render_variant(
        SharedTexts.LABEL_SCENARIO_BASE, f"{key_prefix}_p_base",
        f"{key_prefix}_g_base", f"{key_prefix}_m_base", 50.0
    )
    p_bear, g_bear, m_bear = _render_variant(
        SharedTexts.LABEL_SCENARIO_BEAR, f"{key_prefix}_p_bear",
        f"{key_prefix}_g_bear", f"{key_prefix}_m_bear", 25.0
    )

    # Validation de la somme des probabilités
    total_proba = round(p_bull + p_base + p_bear, 2)
    if total_proba != 1.0:
        st.error(SharedTexts.ERR_SCENARIO_PROBA_SUM.format(sum=int(total_proba * 100)))
        return ScenarioParameters(enabled=False)

    try:
        return ScenarioParameters(
            enabled=True,
            bull=ScenarioVariant(
                label=SharedTexts.LBL_BULL, probability=p_bull,
                growth_rate=g_bull, target_fcf_margin=m_bull
            ),
            base=ScenarioVariant(
                label=SharedTexts.LBL_BASE, probability=p_base,
                growth_rate=g_base, target_fcf_margin=m_base
            ),
            bear=ScenarioVariant(
                label=SharedTexts.LBL_BEAR, probability=p_bear,
                growth_rate=g_bear, target_fcf_margin=m_bear
            ),
        )
    except Exception:
        st.error(SharedTexts.ERR_SCENARIO_INVALID)
        return ScenarioParameters(enabled=False)

# ==============================================================================
# 8. WIDGET SOTP (Sum-of-the-Parts - Optionnel)
# ==============================================================================

def widget_sotp(params: DCFParameters, key_prefix: Optional[str] = None) -> None:
    """
    Widget Étape 9 : Sum-of-the-parts (Flux Continu).
    Modifie l'objet params in-place pour stocker les segments.
    """
    prefix = key_prefix or "sotp"

    # 1. En-tête standardisé
    st.markdown(SharedTexts.SEC_9_SOTP)
    st.info(SharedTexts.SEC_9_DESC)

    # 2. Activation (Décoché par défaut)
    enabled = st.toggle(
        SharedTexts.LBL_SOTP_ENABLE,
        value=params.sotp.enabled,
        help=SharedTexts.HELP_SOTP_ENABLE,
        key=f"{prefix}_enabled"
    )

    params.sotp.enabled = enabled
    if not enabled:
        return

    # 3. Édition des segments (Sans container)
    st.markdown(SharedTexts.SEC_SOTP_SEGMENTS)

    current_data = [
        {
            SharedTexts.LBL_SEGMENT_NAME: bu.name,
            SharedTexts.LBL_SEGMENT_VALUE: bu.enterprise_value,
            SharedTexts.LBL_SEGMENT_METHOD: bu.method.value,
        }
        for bu in params.sotp.segments
    ]

    # Configuration du tableau dynamique
    edited_df = st.data_editor(
        pd.DataFrame(current_data if current_data else [{
            SharedTexts.LBL_SEGMENT_NAME: "Segment A",
            SharedTexts.LBL_SEGMENT_VALUE: 0.0,
            SharedTexts.LBL_SEGMENT_METHOD: SOTPMethod.DCF.value
        }]),
        num_rows="dynamic",
        width='stretch',
        key=f"{prefix}_editor",
        column_config={
            SharedTexts.LBL_SEGMENT_VALUE: st.column_config.NumberColumn(format="%.2f"),
            SharedTexts.LBL_SEGMENT_METHOD: st.column_config.SelectboxColumn(
                options=[m.value for m in SOTPMethod]
            ),
        }
    )

    # Mise à jour de l'objet métier
    params.sotp.segments = [
        BusinessUnit(
            name=row[SharedTexts.LBL_SEGMENT_NAME],
            enterprise_value=row[SharedTexts.LBL_SEGMENT_VALUE],
            method=SOTPMethod(row[SharedTexts.LBL_SEGMENT_METHOD])
        )
        for _, row in edited_df.iterrows() if row[SharedTexts.LBL_SEGMENT_NAME]
    ]

    # 4. Ajustements de holding
    st.write("")
    st.markdown(SharedTexts.SEC_SOTP_ADJUSTMENTS)
    params.sotp.conglomerate_discount = st.slider(
        SharedTexts.LBL_DISCOUNT,
        0, 50,
        int(params.sotp.conglomerate_discount * 100),
        5,
        key=f"{prefix}_discount"
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


def widget_sbc_dilution(default_val: Optional[float] = None, key_prefix: Optional[str] = None) -> float:
    """
    Widget pour la saisie de la dilution annuelle (SBC).

    Parameters
    ----------
    default_val : float, optional
        Valeur par défaut (souvent issue du mode Auto).
    key_prefix : str, optional
        Préfixe pour les clés Streamlit (défaut: "sbc").

    Returns
    -------
    float
        Taux de dilution sélectionné.
    """
    # Générer le préfixe de clé si non fourni
    if key_prefix is None:
        key_prefix = "sbc"

    st.markdown(f"**{SharedTexts.LABEL_DILUTION_SBC}**")

    # Input numérique pour la précision
    val = st.number_input(
        SharedTexts.INP_SBC_DILUTION,
        min_value=0.0,
        max_value=0.10,
        value=default_val if default_val is not None else 0.0,
        format="%.3f",
        step=0.005,
        help=SharedTexts.HELP_SBC_DILUTION,
        key=f"{key_prefix}_dilution"
    )

    # Message pédagogique dynamique
    st.info(SharedTexts.WARN_SBC_TECH)

    return val