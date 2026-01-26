"""
app/ui/results/optional/peer_multiples.py
PILLIER 5 — ANALYSE DE MARCHÉ & SEGMENTS (SOTP)
===============================================
Architecture : Composant Versatile Grade-A.
Fusion ST-4.2 : Regroupement de l'Analyse de Marché et de la Décomposition SOTP.
"""

from __future__ import annotations
from typing import Any
import streamlit as st
import pandas as pd

from src.models import ValuationResult
from src.i18n import MarketTexts, KPITexts, PillarLabels, SOTPTexts
from src.utilities.formatting import format_smart_number
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_kpis import atom_kpi_metric
from app.ui.components.ui_charts import display_football_field, display_sotp_waterfall

class MarketAnalysisTab(ResultTabBase):
    """
    Onglet fusionné : Analyse de marché & Somme des parties.
    Centralise la vision relative et la segmentation opérationnelle.
    """

    TAB_ID = "market_analysis"
    LABEL = PillarLabels.PILLAR_5_MARKET  # Doit être "Analyse de marché & SOTP"
    ORDER = 5
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si des pairs existent OU si le SOTP est activé."""
        has_peers = (
            result.multiples_triangulation is not None
            and len(result.multiples_triangulation.multiples_data.peers) > 0
        )
        has_sotp = bool(result.params.sotp and result.params.sotp.enabled)
        return has_peers or has_sotp

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu versatile de l'analyse de marché et segmentation."""

        # --- EN-TÊTE ---
        st.markdown(f"### {PillarLabels.PILLAR_5_MARKET}")
        st.caption(KPITexts.RELATIVE_VAL_DESC)
        st.write("")

        # 1. SECTION : MULTIPLES DE MARCHÉ (Triangulation)
        if result.multiples_triangulation and result.multiples_triangulation.multiples_data.peers:
            self._render_multiples_section(result)
            # Séparateur visuel si le SOTP suit
            if result.params.sotp and result.params.sotp.enabled:
                st.divider()

        # 2. SECTION : SOMME DES PARTIES (SOTP)
        if result.params.sotp and result.params.sotp.enabled:
            self._render_sotp_section(result)

    @staticmethod
    def _render_multiples_section(result: ValuationResult) -> None:
        """Rendu de la triangulation face aux comparables boursiers."""
        md = result.multiples_triangulation.multiples_data
        currency = result.financials.currency

        st.markdown(f"#### {MarketTexts.MARKET_TITLE}") # Ex: "Positionnement sectoriel"
        st.caption(f"{len(md.peers)} {MarketTexts.COL_PEER}s | Source: {md.source}")

        # Graphique Football Field (Triangulation)
        display_football_field(result)
        st.write("")

        # KPIs de valorisation relative
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                atom_kpi_metric(
                    label=f"Valeur via {KPITexts.LABEL_FOOTBALL_FIELD_EBITDA}",
                    value=format_smart_number(md.implied_value_ev_ebitda, currency)
                )
            with c2:
                atom_kpi_metric(
                    label=f"Valeur via {KPITexts.LABEL_FOOTBALL_FIELD_PE}",
                    value=format_smart_number(md.implied_value_pe, currency)
                )

        st.write("")
        # Tableau des multiples comparatifs
        with st.container(border=True):
            st.markdown(f"**{MarketTexts.COL_MULTIPLE}s comparatifs**")

            comparison_data = [
                {
                    "Ratio": KPITexts.LABEL_FOOTBALL_FIELD_EBITDA,
                    "Médiane": f"{md.median_ev_ebitda:.1f}x" if md.median_ev_ebitda else "—",
                    "Cible": f"{result.financials.ev_ebitda_ratio:.1f}x" if result.financials.ev_ebitda_ratio else "—"
                },
                {
                    "Ratio": KPITexts.LABEL_FOOTBALL_FIELD_PE,
                    "Médiane": f"{md.median_pe:.1f}x" if md.median_pe else "—",
                    "Cible": f"{result.financials.pe_ratio:.1f}x" if result.financials.pe_ratio else "—"
                }
            ]
            # Correction : Utilisation de width='stretch' pour Streamlit 2026
            st.dataframe(pd.DataFrame(comparison_data), hide_index=True, width="stretch")

    @staticmethod
    def _render_sotp_section(result: ValuationResult) -> None:
        """Rendu de la cascade de valeur par segments (Waterfall)."""
        st.markdown(f"#### {SOTPTexts.TITLE}") # Ex: "Décomposition Sum-of-the-parts"
        st.caption(SOTPTexts.DESC_SOTP_VALUATION)

        # Graphique Waterfall SOTP
        display_sotp_waterfall(result)