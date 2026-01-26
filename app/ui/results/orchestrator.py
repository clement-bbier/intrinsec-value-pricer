"""
app/ui/results/orchestrator.py
ORCHESTRATEUR — GESTION DES 5 PILIERS DE RÉSULTATS (Version Versatile)
======================================================================
Rôle : Coordonne le Golden Header et la distribution des données vers
les onglets thématiques. Fusion ST-4.2 : Analyse de marché & SOTP.
"""

from __future__ import annotations
import hashlib
import logging
import numpy as np
from typing import List, Any, Type

import streamlit as st

from src.models import ValuationResult, ValuationMode
from src.i18n import UIMessages, KPITexts, AuditTexts
from src.utilities.formatting import format_smart_number
from .base_result import ResultTabBase

# --- PILLIERS CORE ---
from app.ui.results.core.inputs_summary import InputsSummaryTab
from app.ui.results.core.calculation_proof import CalculationProofTab
from app.ui.results.core.audit_report import AuditReportTab

# --- PILLIERS OPTIONNELS & VERSATILES ---
from app.ui.results.optional.risk_engineering import RiskEngineeringTab
from app.ui.results.optional.peer_multiples import MarketAnalysisTab

logger = logging.getLogger(__name__)

SESSION_KEY_RESULT_HASH = "valuation_context_hash"
SESSION_KEY_MC_DATA = "stats_monte_carlo_cache"

class ResultTabOrchestrator:
    """
    Chef d'orchestre de l'interface de résultats.
    Gère la hiérarchie institutionnelle des 5 Piliers restructurés.
    """

    # L'ordre définit la séquence de lecture de l'analyste (Fusion SOTP incluse)
    _THEMATIC_TABS_CLASSES: List[Type[ResultTabBase]] = [
        InputsSummaryTab,        # Pilier 1 : Données d'entrée
        CalculationProofTab,     # Pilier 2 : Preuve de calcul
        AuditReportTab,          # Pilier 3 : Audit de fiabilité
        RiskEngineeringTab,      # Pilier 4 : Ingénierie du risque
        MarketAnalysisTab        # Pilier 5 : Analyse de marché & SOTP
    ]

    def __init__(self):
        self._tabs = [TabClass() for TabClass in self._THEMATIC_TABS_CLASSES]

    @staticmethod
    def _render_global_header(result: ValuationResult) -> None:
        """Rendu du bandeau d'identité fixe (Golden Header)."""
        f = result.financials
        currency = f.currency

        with st.container(border=True):
            col_id, col_val, col_audit = st.columns([2, 2.5, 1.5])

            with col_id:
                st.markdown(f"### {f.ticker}")
                st.caption(f"{f.name} | {f.sector}")

            with col_val:
                upside = result.upside_pct or 0.0
                # Correction syntaxique i18n pour les couleurs
                color = "green" if upside > 0 else "red"

                st.markdown(f"**{KPITexts.LABEL_IV}**")
                val_str = format_smart_number(result.intrinsic_value_per_share, currency=currency)
                diff_str = f"{upside:+.1%}"

                st.markdown(f"## {val_str} (:{color}[{diff_str}])")
                st.caption(f"{KPITexts.LABEL_PRICE} : {result.market_price:,.2f} {currency}")

            with col_audit:
                if result.audit_report:
                    rating = result.audit_report.rating
                    badge_color = "#10b981" if rating.startswith("A") else "#f59e0b" if rating.startswith("B") else "#ef4444"

                    st.markdown(f"<div style='text-align:right;'>{KPITexts.EXEC_CONFIDENCE}</div>", unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='text-align:right; font-size: 2.5rem; font-weight: bold; color: {badge_color};'>"
                        f"{rating}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"<div style='text-align:right;'>{AuditTexts.DEFAULT_FORMULA}</div>", unsafe_allow_html=True)

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Coordonne le rendu dynamique des onglets avec gestion du cache technique."""
        self._render_global_header(result)
        st.write("")

        # 1. Gestion du Cache (Statique)
        self._handle_cache_invalidation(result)
        self._cache_technical_data(result)

        mc_stats = st.session_state.get(SESSION_KEY_MC_DATA)
        if mc_stats:
            kwargs["mc_stats"] = mc_stats

        # 2. Filtrage & Rendu des Onglets
        visible_tabs = self._filter_relevant_tabs(result)
        if not visible_tabs:
            st.warning(UIMessages.NO_TABS_TO_DISPLAY)
            return

        # Normalisation : Les labels sont extraits et affichés en Sentence case par les onglets eux-mêmes
        tab_labels = [tab.get_display_label() for tab in visible_tabs]
        st_tabs = st.tabs(tab_labels)

        for st_tab, tab_instance in zip(st_tabs, visible_tabs):
            with st_tab:
                try:
                    tab_instance.render(result, **kwargs)
                except Exception as e:
                    logger.error(f"Render Error [{tab_instance.TAB_ID}]: {str(e)}")
                    st.error(f"{UIMessages.CHART_UNAVAILABLE}")

    def _filter_relevant_tabs(self, result: ValuationResult) -> List[ResultTabBase]:
        """Filtre les onglets selon le mode de valorisation (ex: Graham vs DCF)."""
        filtered = []
        is_graham = (result.mode == ValuationMode.GRAHAM)

        for tab in self._tabs:
            if not tab.is_visible(result):
                continue

            # Graham exclut l'analyse de marché relative (Pilier 5)
            if is_graham and isinstance(tab, MarketAnalysisTab):
                continue

            filtered.append(tab)

        return sorted(filtered, key=lambda t: t.ORDER)

    @staticmethod
    def _handle_cache_invalidation(result: ValuationResult) -> None:
        """Invalide le cache si le contexte de valorisation change."""
        ctx_payload = (result.ticker, result.intrinsic_value_per_share,
                       result.mode.value if result.mode else "NONE",
                       len(result.simulation_results) if result.simulation_results else 0)

        current_hash = hashlib.md5(str(ctx_payload).encode()).hexdigest()[:12]

        if st.session_state.get(SESSION_KEY_RESULT_HASH) != current_hash:
            st.session_state[SESSION_KEY_RESULT_HASH] = current_hash
            st.session_state[SESSION_KEY_MC_DATA] = None

    @staticmethod
    def _cache_technical_data(result: ValuationResult) -> None:
        """Calcule et met en cache les statistiques Monte Carlo pour optimiser l'UI."""
        if result.simulation_results and not st.session_state.get(SESSION_KEY_MC_DATA):
            data = np.array([r for r in result.simulation_results if r is not None])
            if data.size > 0:
                st.session_state[SESSION_KEY_MC_DATA] = {
                    "median": np.median(data),
                    "p10": np.percentile(data, 10),
                    "p90": np.percentile(data, 90),
                    "std": np.std(data),
                    "var_95": np.percentile(data, 5)
                }