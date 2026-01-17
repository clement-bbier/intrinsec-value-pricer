"""
app/ui/expert_terminals/shared_widgets.py
WIDGETS PARTAGÉS — Composants UI réutilisables entre terminaux.

Fonctions préfixées par leur rôle :
- widget_*  : Widgets interactifs (retournent des données)
- build_*   : Constructeurs (transforment les données)
- display_* : Affichage pur (ne retournent rien)
"""

from __future__ import annotations

from typing import Dict, Any, Optional

import streamlit as st

from core.models import (
    DCFParameters,
    TerminalValueMethod,
    ScenarioVariant,
)
from core.i18n import ExpertTerminalTexts
from core.config import MonteCarloDefaults


def widget_projection_years(default: int = 5, max_years: int = 15) -> int:
    """Widget pour sélectionner le nombre d'années de projection."""
    return st.number_input(
        ExpertTerminalTexts.INP_PROJ_YEARS,
        min_value=1,
        max_value=max_years,
        value=default,
        help="Horizon de projection explicite"
    )


def widget_monte_carlo() -> Dict[str, Any]:
    """
    Widget Monte Carlo dans un expander.
    
    Returns
    -------
    Dict avec les clés : enable_monte_carlo, num_simulations, rho, volatilities
    """
    with st.expander("Simulation Monte Carlo", expanded=False):
        enable = st.checkbox(
            "Activer les simulations stochastiques",
            value=False,
            help="Génère une distribution de valeurs intrinsèques"
        )
        
        if not enable:
            return {"enable_monte_carlo": False}
        
        col1, col2 = st.columns(2)
        
        num_sims = col1.number_input(
            "Nombre de simulations",
            min_value=MonteCarloDefaults.MIN_SIMULATIONS,
            max_value=MonteCarloDefaults.MAX_SIMULATIONS,
            value=MonteCarloDefaults.DEFAULT_SIMULATIONS,
            step=MonteCarloDefaults.STEP_SIMULATIONS,
        )
        
        rho = col2.slider(
            "Corrélation (ρ)",
            min_value=-1.0,
            max_value=1.0,
            value=MonteCarloDefaults.DEFAULT_RHO,
            step=0.05,
            help="Corrélation entre les variables aléatoires"
        )
        
        st.caption("**Volatilités**")
        c1, c2, c3 = st.columns(3)
        vol_flow = c1.number_input("σ Flux", min_value=0.01, max_value=0.50, value=0.05, format="%.2f")
        vol_beta = c2.number_input("σ Beta", min_value=0.01, max_value=0.50, value=0.10, format="%.2f")
        vol_growth = c3.number_input("σ Croissance", min_value=0.01, max_value=0.30, value=0.02, format="%.2f")
        
        return {
            "enable_monte_carlo": True,
            "num_simulations": int(num_sims),
            "rho": rho,
            "base_flow_volatility": vol_flow,
            "beta_volatility": vol_beta,
            "growth_volatility": vol_growth,
        }


def widget_scenarios() -> Dict[str, Any]:
    """
    Widget Scénarios Bull/Base/Bear dans un expander.
    
    Returns
    -------
    Dict avec les configurations de scénarios.
    """
    with st.expander("Analyse de Scenarios", expanded=False):
        enable = st.checkbox(
            "Activer l'analyse Bull/Base/Bear",
            value=False,
            help="Compare 3 scénarios avec probabilités"
        )
        
        if not enable:
            return {"scenarios_enabled": False}
        
        st.caption("**Probabilités** (somme = 100%)")
        col1, col2, col3 = st.columns(3)
        
        p_bull = col1.slider("Bull", 0.0, 0.6, 0.25, 0.05)
        p_base = col2.slider("Base", 0.2, 0.8, 0.50, 0.05)
        p_bear = col3.slider("Bear", 0.0, 0.6, 0.25, 0.05)
        
        # Normalisation automatique
        total = p_bull + p_base + p_bear
        if total > 0:
            p_bull, p_base, p_bear = p_bull/total, p_base/total, p_bear/total
            st.caption(f"*Normalisé : Bull {p_bull:.0%}, Base {p_base:.0%}, Bear {p_bear:.0%}*")
        
        st.caption("**Croissance par scénario**")
        c1, c2, c3 = st.columns(3)
        g_bull = c1.number_input("g Bull", -0.20, 0.40, 0.08, 0.01, format="%.2f")
        g_base = c2.number_input("g Base", -0.20, 0.40, 0.04, 0.01, format="%.2f")
        g_bear = c3.number_input("g Bear", -0.20, 0.40, 0.00, 0.01, format="%.2f")
        
        return {
            "scenarios_enabled": True,
            "scenario_bull": ScenarioVariant(probability=p_bull, growth_rate=g_bull),
            "scenario_base": ScenarioVariant(probability=p_base, growth_rate=g_base),
            "scenario_bear": ScenarioVariant(probability=p_bear, growth_rate=g_bear),
        }


def widget_peer_multiples() -> Dict[str, Any]:
    """
    Widget pour activer/configurer la triangulation par multiples.
    """
    with st.expander("Triangulation par Multiples", expanded=False):
        enable = st.checkbox(
            "Activer la valorisation relative",
            value=True,
            help="Compare avec les multiples des pairs sectoriels"
        )
        
        if not enable:
            return {"enable_peer_multiples": False}
        
        manual_peers = st.text_input(
            "Tickers des pairs (optionnel)",
            placeholder="MSFT, GOOG, META",
            help="Laissez vide pour auto-découverte"
        )
        
        peers_list = None
        if manual_peers.strip():
            peers_list = [t.strip().upper() for t in manual_peers.split(",")]
        
        return {
            "enable_peer_multiples": True,
            "manual_peers": peers_list,
        }


def build_dcf_parameters(collected_data: Dict[str, Any]) -> DCFParameters:
    """
    Construit un DCFParameters à partir des données collectées.
    
    Parameters
    ----------
    collected_data : Dict
        Données brutes des widgets.
    
    Returns
    -------
    DCFParameters
        Paramètres structurés pour le moteur.
    """
    defaults = {
        "projection_years": 5,
        "terminal_method": TerminalValueMethod.GORDON_GROWTH,
        "enable_monte_carlo": False,
        "num_simulations": 5000,
        "base_flow_volatility": 0.05,
        "beta_volatility": 0.10,
        "growth_volatility": 0.02,
    }
    
    # Fusion avec filtrage des None
    merged = {
        **defaults,
        **{k: v for k, v in collected_data.items() if v is not None}
    }
    
    return DCFParameters.from_legacy(merged)
