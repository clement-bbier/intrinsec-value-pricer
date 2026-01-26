"""
app/ui/results/optional/sotp_breakdown.py
Pillier 5 — Analyse de Marché : Décomposition SOTP.
Rôle : Visualiser la 'cascade' de valeur des Business Units.
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult
from src.i18n import MarketTexts, SOTPTexts, KPITexts
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_charts import display_sotp_waterfall # Votre cascade Plotly

class SOTPBreakdownTab(ResultTabBase):
    """
    Onglet Sum-of-the-Parts.
    Décompose l'EV en Business Units et applique l'Equity Bridge.
    """

    TAB_ID = "sotp_breakdown"
    LABEL = MarketTexts.TITLE_SEGMENTATION
    ORDER = 9
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si le mode SOTP est activé dans les paramètres."""
        return bool(result.params.sotp and result.params.sotp.enabled)

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu de la cascade de valeur SOTP."""
        st.markdown(f"**{SOTPTexts.TITLE}**")
        st.caption(MarketTexts.CAPTION_SEGMENTATION)

        # --- 1. LA CASCADE VISUELLE (VOTRE COMPOSANT PLOTLY) ---
        display_sotp_waterfall(result)

        # --- 2. RÉSUMÉ DES CONTRIBUTIONS ---
        st.write("")
        with st.container(border=True):
            col_id, col_val, col_pct = st.columns([2, 2, 1])

            # En-têtes i18n
            col_id.markdown(f"*{MarketTexts.COL_SEGMENT}*")
            col_val.markdown(f"*{MarketTexts.COL_VALUE}*")
            col_pct.markdown(f"*{MarketTexts.COL_CONTRIBUTION}*")
            st.divider()

            raw_ev_sum = sum(seg.enterprise_value for seg in result.params.sotp.segments)

            for seg in result.params.sotp.segments:
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.markdown(f"**{seg.name}**")
                c2.markdown(f"{seg.enterprise_value:,.0f} {result.financials.currency}")

                contrib = (seg.enterprise_value / raw_ev_sum) if raw_ev_sum > 0 else 0
                c3.markdown(f"{contrib:.1%}")

        st.caption(f"**{KPITexts.NOTE_ANALYSIS}** : {SOTPTexts.HELP_SOTP}")