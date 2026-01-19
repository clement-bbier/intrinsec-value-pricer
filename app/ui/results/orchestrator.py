"""
app/ui/result_tabs/orchestrator.py

ORCHESTRATEUR — GESTION CENTRALISÉE DES ONGLETS DE RÉSULTATS

Version : V2.0 — ST-3.4 Session Optimization
Rôle : Coordination et rendu des onglets de résultats post-calcul
Pattern : Mediator (GoF) + Factory Method + Session State Cache
Style : Numpy docstrings

Risques financiers : Coordination d'affichage, pas de calculs

ST-3.4 : OPTIMISATION DE LA GESTION DE SESSION
===============================================
Pour éviter les recalculs inutiles lors des changements d'onglet :
- Mise en cache des distributions Monte Carlo dans st.session_state
- Utilisation d'un hash du résultat pour invalider le cache si nécessaire
- Navigation fluide sans latence perceptible

Responsabilités :
1. Collecter tous les onglets (core + optional)
2. Filtrer selon la visibilité (conditions métier)
3. Trier par ordre de priorité (ORDER attribute)
4. Rendre avec st.tabs() et gestion d'erreurs
5. ST-3.4: Gérer le cache de session pour les calculs lourds

Architecture :
- Core tabs : Toujours visibles (executive, inputs, calculation, audit)
- Optional tabs : Conditionnels (multiples, sotp, scenarios, backtest, mc)
"""

from __future__ import annotations

import hashlib
from typing import List, Any, Optional, Dict

import streamlit as st

from src.domain.models import ValuationResult
from src.domain.models.pitchbook import PitchbookData
from app.ui.base import ResultTabBase
from src.i18n import UIMessages

# Import des onglets core
from app.ui.results.core.executive_summary import ExecutiveSummaryTab
from app.ui.results.core.inputs_summary import InputsSummaryTab
from app.ui.results.core.calculation_proof import CalculationProofTab
from app.ui.results.core.audit_report import AuditReportTab

# Import des onglets optionnels
from app.ui.results.optional.peer_multiples import PeerMultiplesTab
from app.ui.results.optional.sotp_breakdown import SOTPBreakdownTab
from app.ui.results.optional.scenario_analysis import ScenarioAnalysisTab
from app.ui.results.optional.historical_backtest import HistoricalBacktestTab
from app.ui.results.optional.monte_carlo_distribution import MonteCarloDistributionTab


# ============================================================================
# CONSTANTES DE SESSION (ST-3.4)
# ============================================================================

SESSION_KEY_RESULT_HASH = "result_cache_hash"
SESSION_KEY_MC_DATA = "cached_monte_carlo_data"
SESSION_KEY_ACTIVE_TAB = "active_result_tab"
SESSION_KEY_RENDER_CONTEXT = "render_context_cache"


def _compute_result_hash(result: ValuationResult) -> str:
    """
    Calcule un hash unique pour un résultat de valorisation.
    
    Utilisé pour détecter si le résultat a changé et invalider le cache.
    
    Parameters
    ----------
    result : ValuationResult
        Le résultat à hasher.
    
    Returns
    -------
    str
        Hash MD5 tronqué (16 caractères).
    """
    # Composantes critiques pour l'identité du résultat
    key_components = (
        result.ticker,
        result.intrinsic_value_per_share,
        result.market_price,
        result.mode.value,
        len(result.simulation_results) if result.simulation_results else 0,
    )
    hash_input = str(key_components).encode('utf-8')
    return hashlib.md5(hash_input).hexdigest()[:16]


def _init_session_cache() -> None:
    """
    Initialise les clés de cache de session si absentes.
    
    Notes
    -----
    Appelé au début de chaque render() pour garantir que les clés existent.
    """
    if SESSION_KEY_RESULT_HASH not in st.session_state:
        st.session_state[SESSION_KEY_RESULT_HASH] = None
    if SESSION_KEY_MC_DATA not in st.session_state:
        st.session_state[SESSION_KEY_MC_DATA] = None
    if SESSION_KEY_ACTIVE_TAB not in st.session_state:
        st.session_state[SESSION_KEY_ACTIVE_TAB] = 0
    if SESSION_KEY_RENDER_CONTEXT not in st.session_state:
        st.session_state[SESSION_KEY_RENDER_CONTEXT] = {}


def _should_invalidate_cache(result: ValuationResult) -> bool:
    """
    Détermine si le cache doit être invalidé.
    
    Parameters
    ----------
    result : ValuationResult
        Le résultat actuel.
    
    Returns
    -------
    bool
        True si le résultat a changé et le cache doit être vidé.
    """
    current_hash = _compute_result_hash(result)
    cached_hash = st.session_state.get(SESSION_KEY_RESULT_HASH)
    
    if cached_hash != current_hash:
        # Résultat a changé, mettre à jour le hash et invalider
        st.session_state[SESSION_KEY_RESULT_HASH] = current_hash
        st.session_state[SESSION_KEY_MC_DATA] = None
        st.session_state[SESSION_KEY_RENDER_CONTEXT] = {}
        return True
    
    return False


def cache_monte_carlo_data(result: ValuationResult) -> None:
    """
    Met en cache les données Monte Carlo pour éviter les recalculs.
    
    Parameters
    ----------
    result : ValuationResult
        Résultat contenant les simulations MC.
    
    Financial Impact
    ----------------
    Évite de recalculer les statistiques MC lors de la navigation
    entre onglets, améliorant significativement la réactivité.
    """
    if result.simulation_results and not st.session_state.get(SESSION_KEY_MC_DATA):
        import numpy as np
        
        values = result.simulation_results
        st.session_state[SESSION_KEY_MC_DATA] = {
            "count": len(values),
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std": float(np.std(values)),
            "p10": float(np.percentile(values, 10)),
            "p25": float(np.percentile(values, 25)),
            "p75": float(np.percentile(values, 75)),
            "p90": float(np.percentile(values, 90)),
        }


def get_cached_mc_stats() -> Optional[Dict[str, float]]:
    """
    Récupère les statistiques MC depuis le cache.
    
    Returns
    -------
    Optional[Dict[str, float]]
        Statistiques préalculées ou None si non disponibles.
    """
    return st.session_state.get(SESSION_KEY_MC_DATA)


class ResultTabOrchestrator:
    """
    Orchestrateur centralisé des onglets de résultats.

    Implémente le pattern Mediator pour coordonner l'affichage des différents
    onglets de résultats. Gère le cycle de vie complet : instanciation,
    filtrage, tri et rendu avec gestion d'erreurs.

    Attributes
    ----------
    _ALL_TABS : List[type]
        Liste ordonnée des classes d'onglets (core + optional).
    _tabs : List[ResultTabBase]
        Instances des onglets après instanciation.

    Class Attributes
    ----------------
    Core tabs (toujours visibles) :
        - ExecutiveSummaryTab (résumé exécutif)
        - InputsSummaryTab (récapitulatif inputs)
        - CalculationProofTab (preuve de calcul)
        - AuditReportTab (rapport d'audit)

    Optional tabs (conditionnels) :
        - PeerMultiplesTab (triangulation sectorielle)
        - SOTPBreakdownTab (décomposition SOTP)
        - ScenarioAnalysisTab (analyse scénarios)
        - HistoricalBacktestTab (backtest historique)
        - MonteCarloDistributionTab (distribution MC)

    Examples
    --------
    >>> orchestrator = ResultTabOrchestrator()
    >>> orchestrator.render(result, provider=data_provider)

    Notes
    -----
    L'ordre d'affichage est déterminé par l'attribut ORDER de chaque onglet.
    Les erreurs dans un onglet n'affectent pas les autres onglets.
    """
    
    # Tous les onglets disponibles (dans l'ordre souhaité)
    _ALL_TABS: List[type] = [
        # Core (toujours visibles)
        ExecutiveSummaryTab,
        InputsSummaryTab,
        CalculationProofTab,
        AuditReportTab,
        # Optional (conditionnels)
        PeerMultiplesTab,
        SOTPBreakdownTab,
        ScenarioAnalysisTab,
        HistoricalBacktestTab,
        MonteCarloDistributionTab,
    ]
    
    def __init__(self):
        """Instancie tous les onglets."""
        self._tabs: List[ResultTabBase] = [TabClass() for TabClass in self._ALL_TABS]
    
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche les onglets visibles avec gestion optimisée du cache (ST-3.4).
        
        Parameters
        ----------
        result : ValuationResult
            Résultat de valorisation.
        **kwargs
            Contexte additionnel (provider, etc.).
        
        Notes
        -----
        ST-3.4 : La navigation entre onglets n'invalide pas le cache.
        Seul un nouveau calcul (nouveau résultat) réinitialise le cache.
        
        Financial Impact
        ----------------
        L'optimisation du cache permet une navigation fluide sans latence,
        améliorant la productivité de l'analyste.
        """
        # ══════════════════════════════════════════════════════════════════
        # ST-3.4 : INITIALISATION ET GESTION DU CACHE
        # ══════════════════════════════════════════════════════════════════
        _init_session_cache()
        
        # Vérifier si le cache doit être invalidé (nouveau résultat)
        cache_invalidated = _should_invalidate_cache(result)
        
        # Mettre en cache les données Monte Carlo si disponibles
        if result.simulation_results:
            cache_monte_carlo_data(result)
        
        # Injecter les stats MC cachées dans le contexte pour les onglets
        cached_mc = get_cached_mc_stats()
        if cached_mc:
            kwargs["cached_mc_stats"] = cached_mc
        
        # ══════════════════════════════════════════════════════════════════
        # FILTRAGE ET TRI DES ONGLETS
        # ══════════════════════════════════════════════════════════════════
        visible_tabs = [tab for tab in self._tabs if tab.is_visible(result)]
        
        if not visible_tabs:
            st.warning(UIMessages.NO_TABS_TO_DISPLAY)
            return
        
        # Trier par ordre de priorité
        visible_tabs.sort(key=lambda t: t.ORDER)
        
        # ══════════════════════════════════════════════════════════════════
        # RENDU AVEC ST.TABS — Pas de recalcul sur changement d'onglet
        # ══════════════════════════════════════════════════════════════════
        tab_labels = [tab.get_display_label() for tab in visible_tabs]
        st_tabs = st.tabs(tab_labels)
        
        # Rendre chaque onglet avec gestion d'erreurs isolée
        for st_tab, tab_instance in zip(st_tabs, visible_tabs):
            with st_tab:
                try:
                    tab_instance.render(result, **kwargs)
                except Exception as e:
                    st.error(f"Erreur dans l'onglet {tab_instance.LABEL}: {str(e)}")
        
        # ══════════════════════════════════════════════════════════════════
        # ST-5.2 : BOUTON DE TÉLÉCHARGEMENT PITCHBOOK PDF
        # ══════════════════════════════════════════════════════════════════
        st.divider()
        self._render_pdf_download_button(result, **kwargs)
    
    def get_visible_count(self, result: ValuationResult) -> int:
        """Nombre d'onglets visibles pour ce résultat."""
        return sum(1 for tab in self._tabs if tab.is_visible(result))
    
    def clear_cache(self) -> None:
        """
        Vide manuellement le cache de session (ST-3.4).
        
        Utile pour forcer un recalcul complet des statistiques.
        """
        st.session_state[SESSION_KEY_RESULT_HASH] = None
        st.session_state[SESSION_KEY_MC_DATA] = None
        st.session_state[SESSION_KEY_RENDER_CONTEXT] = {}
    
    def _render_pdf_download_button(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche le bouton de téléchargement du Pitchbook PDF (ST-5.2).
        
        Parameters
        ----------
        result : ValuationResult
            Résultat de valorisation.
        **kwargs
            Contexte additionnel (provider, etc.).
        
        Notes
        -----
        Le PDF est généré à la demande pour éviter les calculs inutiles.
        La génération utilise fpdf2 et prend généralement < 5 secondes.
        """
        try:
            from src.reporting.pdf_generator import generate_pitchbook_pdf, FPDF_AVAILABLE
            
            if not FPDF_AVAILABLE:
                st.info("📄 Export PDF indisponible (fpdf2 non installé)")
                return
            
            # Récupérer le provider s'il est fourni
            provider = kwargs.get("provider")
            company_name = ""
            sector = ""
            
            if provider and hasattr(provider, "last_financials"):
                financials = provider.last_financials
                if financials:
                    company_name = getattr(financials, "company_name", result.ticker)
                    sector = getattr(financials, "sector", "N/A")
            
            # Bouton de téléchargement
            if st.button("📄 Télécharger le Rapport Pitchbook (PDF)", type="secondary"):
                with st.spinner("Génération du Pitchbook en cours..."):
                    # Créer le DTO
                    pitchbook_data = PitchbookData.from_valuation_result(
                        result=result,
                        company_name=company_name or result.ticker,
                        sector=sector
                    )
                    
                    # Générer le PDF
                    pdf_bytes = generate_pitchbook_pdf(pitchbook_data)
                    
                    # Proposer le téléchargement
                    st.download_button(
                        label="⬇️ Cliquez pour télécharger",
                        data=pdf_bytes,
                        file_name=f"pitchbook_{result.ticker}_{result.mode.value}.pdf",
                        mime="application/pdf",
                        key="pdf_download_btn"
                    )
                    st.success("✅ Pitchbook généré avec succès !")
                    
        except ImportError:
            st.info("📄 Export PDF indisponible (module manquant)")
        except Exception as e:
            st.error(f"Erreur lors de la génération du PDF : {str(e)}")
