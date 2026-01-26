"""
app/ui/results/optional/sotp_breakdown.py
PILLIER 5 — SOUS-COMPOSANT : DÉCOMPOSITION SOTP (Sum-of-the-Parts)
=================================================================
Rôle : Visualiser la 'cascade' de valeur des Business Units et le bridge.
Architecture : Composant injectable Grade-A.
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult
from src.i18n import MarketTexts, SOTPTexts, KPITexts
from src.utilities.formatting import format_smart_number
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_charts import display_sotp_waterfall

class SOTPBreakdownTab(ResultTabBase):
    """
    Composant de rendu pour la décomposition par segments.
    Intégré verticalement dans l'onglet MarketAnalysis.
    """

    TAB_ID = "sotp_breakdown"
    LABEL = MarketTexts.TITLE_SEGMENTATION
    ORDER = 5 # Aligné sur le Pilier 5
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si le mode SOTP est activé et contient des segments."""
        return bool(
            result.params.sotp and
            result.params.sotp.enabled and
            result.params.sotp.segments
        )

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu de la cascade de valeur et de la table de contribution."""

        # --- EN-TÊTE DE SECTION (Standardisé ####) ---
        st.markdown(f"#### {SOTPTexts.TITLE}")
        st.caption(MarketTexts.CAPTION_SEGMENTATION)

        # 1. LA CASCADE VISUELLE (Plotly Waterfall)
        display_sotp_waterfall(result)

        # 2. TABLEAU RÉSUMÉ DES CONTRIBUTIONS
        self._render_contribution_table(result)

        # Note d'analyse institutionnelle
        st.write("")
        st.caption(f"**{KPITexts.NOTE_ANALYSIS}** : {SOTPTexts.HELP_SOTP}")

    @staticmethod
    def _render_contribution_table(result: ValuationResult) -> None:
        """Rendu du tableau de détail des Business Units (Static Method)."""
        segments = result.params.sotp.segments
        currency = result.financials.currency

        with st.container(border=True):
            # En-têtes stylisés via i18n
            h1, h2, h3 = st.columns([2, 2, 1])
            h1.markdown(f"<small style='color: #64748b;'>{MarketTexts.COL_SEGMENT}</small>", unsafe_allow_html=True)
            h2.markdown(f"<small style='color: #64748b; text-align: right;'>{MarketTexts.COL_VALUE}</small>", unsafe_allow_html=True)
            h3.markdown(f"<small style='color: #64748b; text-align: right;'>{MarketTexts.COL_CONTRIBUTION}</small>", unsafe_allow_html=True)
            st.divider()

            raw_ev_sum = sum(seg.enterprise_value for seg in segments)

            for seg in segments:
                c1, c2, c3 = st.columns([2, 2, 1])

                # Nom du Segment
                c1.markdown(f"**{seg.name}**")

                # Valeur formatée
                val_formatted = format_smart_number(seg.enterprise_value, currency=currency)
                c2.markdown(f"<div style='text-align: right;'>{val_formatted}</div>", unsafe_allow_html=True)

                # Contribution relative
                contrib = (seg.enterprise_value / raw_ev_sum) if raw_ev_sum > 0 else 0
                c3.markdown(f"<div style='text-align: right;'>{contrib:.1%}")

            # Ligne de Somme (Audit Check)
            if len(segments) > 1:
                st.divider()
                f1, f2, f3 = st.columns([2, 2, 1])
                f1.markdown(f"*{MarketTexts.METRIC_GROSS_VALUE}*")
                f2.markdown(f"<div style='text-align: right;'><b>{format_smart_number(raw_ev_sum, currency=currency)}</b></div>", unsafe_allow_html=True)
                f3.markdown("<div style='text-align: right;'>100%</div>", unsafe_allow_html=True)