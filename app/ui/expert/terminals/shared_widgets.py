"""
app/ui/expert_terminals/shared_widgets.py

WIDGETS PARTAGÉS — Composants UI réutilisables entre terminaux experts.

Pattern : Single Responsibility (SOLID)
Style : Numpy docstrings

Conventions de nommage :
    - widget_* : Widgets interactifs (retournent des données utilisateur)
    - build_* : Constructeurs (transforment les données en objets métier)
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
from src.i18n import SharedTexts
from src.config.settings import SIMULATION_CONFIG, VALUATION_CONFIG
from src.config.constants import UIWidgetDefaults

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
    Affiche un curseur (slider) pour sélectionner l'horizon de projection.

    Cette fonction utilise les bornes définies dans la configuration centrale
    pour garantir la cohérence des modèles DCF.

    Parameters
    ----------
    default : int, optional
        Valeur initiale du slider (défaut issu de UIWidgetDefaults).
    min_years : int, optional
        Borne inférieure de projection (défaut issu de UIWidgetDefaults).
    max_years : int, optional
        Borne supérieure de projection (défaut issu de UIWidgetDefaults).
    key_prefix : str, optional
        Préfixe unique pour la clé Streamlit (ex: "FCFF_STANDARD").

    Returns
    -------
    int
        Le nombre d'années de projection (t) sélectionné.
    """
    # Sécurisation de la clé pour st.session_state
    prefix = key_prefix or "projection"

    return st.slider(
        label=SharedTexts.INP_PROJ_YEARS,
        min_value=min_years,
        max_value=max_years,
        value=default,
        step=1,
        help=SharedTexts.HELP_PROJ_YEARS,
        key=f"{prefix}_years"
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
    Saisie des paramètres d'actualisation (WACC ou Ke).

    Délègue l'en-tête à la classe de base pour éviter les doublons visuels.
    Affiche dynamiquement la formule LaTeX adaptée au mode.
    """
    prefix = key_prefix or mode.name

    # Formule théorique dynamique
    st.latex(
        SharedTexts.FORMULA_CAPITAL_KE if mode.is_direct_equity
        else SharedTexts.FORMULA_CAPITAL_WACC
    )

    # Saisie du prix de référence
    manual_price = st.number_input(
        SharedTexts.INP_PRICE_WEIGHTS, 0.0, 100000.0, None, 0.01, "%.2f",
        help=SharedTexts.HELP_PRICE_WEIGHTS, key=f"{prefix}_price"
    )

    col_a, col_b = st.columns(2)
    rf = col_a.number_input(SharedTexts.INP_RF, 0.0, 0.2, None, 0.001, "%.3f", SharedTexts.HELP_RF, f"{prefix}_rf")
    beta = col_b.number_input(SharedTexts.INP_BETA, 0.0, 5.0, None, 0.01, "%.2f", SharedTexts.HELP_BETA, f"{prefix}_beta")
    mrp = col_a.number_input(SharedTexts.INP_MRP, 0.0, 0.2, None, 0.001, "%.3f", SharedTexts.HELP_MRP, f"{prefix}_mrp")

    data = {"risk_free_rate": rf, "manual_beta": beta, "market_risk_premium": mrp, "manual_stock_price": manual_price}

    if not mode.is_direct_equity:
        kd = col_b.number_input(SharedTexts.INP_KD, 0.0, 0.2, None, 0.001, "%.3f", SharedTexts.HELP_KD, f"{prefix}_kd")
        tau = col_a.number_input(SharedTexts.INP_TAX, 0.0, 0.6, None, 0.01, "%.2f", SharedTexts.HELP_TAX, f"{prefix}_tax")
        data.update({"cost_of_debt": kd, "tax_rate": tau})

    st.divider()
    return data

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
    st.latex(formula_latex)

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
        SharedTexts.INP_SBC_DILUTION, 0.0, 0.10, None, 0.005, format="%.3f",
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
    custom_vols: Optional[Dict[str, str]] = None,
    key_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Widget de calibration stochastique (Monte Carlo) avec injection i18n dynamique.

    Adapte les libellés de volatilité selon le modèle (EPS pour Graham, NI pour RIM,
    FCF pour DCF) en utilisant exclusivement le référentiel SharedTexts.
    """
    prefix = key_prefix or "mc"

    # 1. EN-TÊTE ET DESCRIPTION (i18n)
    st.markdown(SharedTexts.SEC_6_MC)
    st.info(SharedTexts.SEC_6_DESC_MC)

    # 2. TOGGLE D'ACTIVATION
    enable = st.toggle(SharedTexts.MC_CALIBRATION, value=False, key=f"{prefix}_enable")
    if not enable:
        return {"enable_monte_carlo": False}

    # 3. PROFONDEUR DE SIMULATION
    sims = st.select_slider(
        SharedTexts.MC_ITERATIONS,
        options=[1000, 5000, 10000, 20000],
        value=5000,
        key=f"{prefix}_sims"
    )
    st.caption(SharedTexts.MC_VOL_INCERTITUDE)

    # 4. GRILLE DE SAISIE (Double colonne institutionnelle)
    v_col1, v_col2 = st.columns(2)

    # --- LOGIQUE I18N CONTEXTUELLE ---
    # Sélection du label pour le flux de base (Ancrage Year 0)
    if mode == ValuationMode.GRAHAM:
        label_base = SharedTexts.MC_VOL_EPS  # Ex: "Incertitude sur le BPA (EPS)"
    elif mode == ValuationMode.RIM:
        label_base = SharedTexts.MC_VOL_NI   # Ex: "Incertitude sur le Résultat Net"
    elif mode == ValuationMode.DDM:
        label_base = SharedTexts.MC_VOL_DIV  # Ex: "Incertitude sur le Dividende"
    else:
        label_base = SharedTexts.MC_VOL_BASE_FLOW # Ex: "Incertitude sur le FCF"

    # 5. COLONNE 1 : VOLATILITÉS OPÉRATIONNELLES
    v_base = v_col1.number_input(
        label_base,
        min_value=0.0, max_value=0.5,
        value=None, format="%.3f",
        key=f"{prefix}_vol_flow",
        help=SharedTexts.HELP_VOL_BASE # Assurez-vous que cette clé existe
    )

    # Sélection du label pour la croissance (g ou ω)
    label_growth = SharedTexts.LBL_VOL_OMEGA if mode == ValuationMode.RIM else SharedTexts.MC_VOL_G
    v_growth = v_col1.number_input(
        label_growth,
        min_value=0.0, max_value=0.2,
        value=None, format="%.3f",
        key=f"{prefix}_vol_growth"
    )

    # 6. COLONNE 2 : RISQUES DE MARCHÉ & SORTIE
    v_beta = None
    # Verrouillage financier : Graham n'utilise pas le Bêta
    if mode != ValuationMode.GRAHAM:
        v_beta = v_col2.number_input(
            SharedTexts.MC_VOL_BETA,
            min_value=0.0, max_value=1.0,
            value=None, format="%.3f",
            key=f"{prefix}_vol_beta"
        )

    v_exit_m = None
    # Verrouillage financier : Uniquement si la sortie est par multiple
    if terminal_method == TerminalValueMethod.EXIT_MULTIPLE:
        v_exit_m = v_col2.number_input(
            SharedTexts.LBL_VOL_EXIT_M, # Ex: "Volatilité du multiple terminal"
            min_value=0.0, max_value=0.4,
            value=None, format="%.3f",
            key=f"{prefix}_vol_exit_m"
        )

    # 7. CONSTRUCTION DU DICTIONNAIRE DE RÉPONSE (Contractualisé avec engines.py)
    return {
        "enable_monte_carlo": True,
        "num_simulations": sims,
        "base_flow_volatility": v_base,
        "beta_volatility": v_beta,
        "growth_volatility": v_growth,
        "exit_multiple_volatility": v_exit_m
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

    st.markdown(SharedTexts.SEC_7_PEERS)
    st.info(SharedTexts.SEC_7_DESC_PEERS)

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
    """Analyse multi-scénarios déterministes."""
    prefix = key_prefix or "scenario"
    st.markdown(SharedTexts.SEC_8_SCENARIOS)
    st.info(SharedTexts.SEC_8_DESC_SCENARIOS)

    enabled = st.toggle(SharedTexts.INP_SCENARIO_ENABLE, False, key=f"{prefix}_enable")
    if not enabled:
        return ScenarioParameters(enabled=False)

    show_margin = (mode == ValuationMode.FCFF_GROWTH)

    def _render_variant(label: str, case_id: str, default_p: float):
        st.markdown(f"**{label}**")
        c1, c2, c3 = st.columns(3)
        p = c1.number_input(SharedTexts.INP_SCENARIO_PROBA, 0.0, 100.0, default_p, 5.0, key=f"{prefix}_p_{case_id}") / 100
        g = c2.number_input(SharedTexts.INP_SCENARIO_GROWTH, value=None, format="%.3f", key=f"{prefix}_g_{case_id}")
        m = c3.number_input(SharedTexts.INP_SCENARIO_MARGIN, value=None, format="%.2f", key=f"{prefix}_m_{case_id}") if show_margin else None
        return p, g, m

    p_bull, g_bull, m_bull = _render_variant(SharedTexts.LABEL_SCENARIO_BULL, "bull", 25.0)
    p_base, g_base, m_base = _render_variant(SharedTexts.LABEL_SCENARIO_BASE, "base", 50.0)
    p_bear, g_bear, m_bear = _render_variant(SharedTexts.LABEL_SCENARIO_BEAR, "bear", 25.0)

    if round(p_bull + p_base + p_bear, 2) != 1.0:
        st.error(SharedTexts.ERR_SCENARIO_PROBA_SUM.format(sum=int((p_bull+p_base+p_bear)*100)))
        return ScenarioParameters(enabled=False)

    # CORRECTION : Utilisation impérative de Keyword Arguments pour Pydantic
    return ScenarioParameters(
        enabled=True,
        bull=ScenarioVariant(label=SharedTexts.LBL_BULL, probability=p_bull, growth_rate=g_bull, target_fcf_margin=m_bull),
        base=ScenarioVariant(label=SharedTexts.LBL_BASE, probability=p_base, growth_rate=g_base, target_fcf_margin=m_base),
        bear=ScenarioVariant(label=SharedTexts.LBL_BEAR, probability=p_bear, growth_rate=g_bear, target_fcf_margin=m_bear)
    )

# ==============================================================================
# 8. WIDGET SOTP (Sum-of-the-Parts - Optionnel)
# ==============================================================================

def widget_sotp(params: DCFParameters, is_conglomerate: bool = False, key_prefix: Optional[str] = None) -> None:
    """
    Widget Etape 9 : Segmentation SOTP avec arbitrage de pertinence (ST-4.2).

    Cette fonction permet de diviser la valeur totale entre différentes Business Units.
    Elle inclut un test de pertinence pour limiter l'usage du SOTP aux structures
    diversifiees ou aux besoins de decomposition specifiques.

    Parameters
    ----------
    params : DCFParameters
        Objet de parametres a peupler pour le moteur de calcul.
    is_conglomerate : bool, optional
        Indique si l'entreprise est identifiee comme un conglomerat (defaut: False).
    key_prefix : str, optional
        Prefixe pour garantir l'unicite des cles dans le session_state.
    """
    prefix = key_prefix or "sotp"

    # --- EN-TETE ET DESCRIPTION ---
    st.markdown(SharedTexts.SEC_9_SOTP)
    st.info(SharedTexts.SEC_9_DESC)

    # --- ARBITRAGE DE PERTINENCE ---
    # Si l'entreprise n'est pas un conglomerat, on affiche un avertissement preventif
    if not is_conglomerate:
        st.warning(SharedTexts.WARN_SOTP_RELEVANCE)

    # --- ACTIVATION DU MODULE ---
    enabled = st.toggle(
        SharedTexts.LBL_SOTP_ENABLE,
        value=params.sotp.enabled,
        key=f"{prefix}_enable",
        help=SharedTexts.HELP_SOTP_ENABLE
    )
    params.sotp.enabled = enabled

    if not enabled:
        return

    # --- CONFIGURATION DU TABLEAU DE SEGMENTS ---
    # Initialisation avec typage float64 pour prevenir les FutureWarnings de pandas
    df_init = pd.DataFrame([{
        SharedTexts.LBL_SEGMENT_NAME: "Segment A",
        SharedTexts.LBL_SEGMENT_VALUE: 0.0,
        SharedTexts.LBL_SEGMENT_METHOD: SOTPMethod.DCF.value
    }]).astype({SharedTexts.LBL_SEGMENT_VALUE: 'float64'})

    # Editeur de donnees dynamique (Pitchbook style)
    edited_df = st.data_editor(
        df_init,
        num_rows="dynamic",
        width='stretch',
        key=f"{prefix}_editor"
    )

    # --- EXTRACTION ET VALIDATION PYDANTIC ---
    # Utilisation d'arguments nommes pour la compatibilite BusinessUnit
    params.sotp.segments = [
        BusinessUnit(
            name=row[SharedTexts.LBL_SEGMENT_NAME],
            enterprise_value=row[SharedTexts.LBL_SEGMENT_VALUE],
            method=SOTPMethod(row[SharedTexts.LBL_SEGMENT_METHOD])
        )
        for _, row in edited_df.iterrows() if row[SharedTexts.LBL_SEGMENT_NAME]
    ]

    # --- AJUSTEMENTS DE HOLDING ---
    st.markdown(SharedTexts.SEC_SOTP_ADJUSTMENTS)

    # Calcul de la valeur initiale en pourcentage pour le slider
    current_discount = int(params.sotp.conglomerate_discount * 100)

    params.sotp.conglomerate_discount = st.slider(
        SharedTexts.LBL_DISCOUNT,
        min_value=0,
        max_value=50,
        value=current_discount,
        step=5,
        key=f"{prefix}_discount"
    ) / 100.0

# ==============================================================================
# 9. CONSTRUCTEUR DE PARAMÈTRES
# ==============================================================================

def build_dcf_parameters(collected_data: Dict[str, Any]) -> DCFParameters:
    """Constructeur final avec constantes validées."""
    defaults = {
        "projection_years": VALUATION_CONFIG.default_projection_years,
        "terminal_method": TerminalValueMethod.GORDON_GROWTH,
        "enable_monte_carlo": False,
        "num_simulations": SIMULATION_CONFIG.default_simulations,
        "base_flow_volatility": UIWidgetDefaults.DEFAULT_BASE_FLOW_VOLATILITY,
        "beta_volatility": SIMULATION_CONFIG.default_volatility_beta,
        "growth_volatility": SIMULATION_CONFIG.default_volatility_growth,
    }
    merged = {**defaults, **{k: v for k, v in collected_data.items() if v is not None}}
    return DCFParameters.from_legacy(merged)