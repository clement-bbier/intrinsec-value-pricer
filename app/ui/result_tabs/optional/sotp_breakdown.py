"""
app/ui/result_tabs/optional/sotp_breakdown.py
Onglet — Sum-of-the-Parts (SOTP)

Migration depuis ui_kpis.py._render_sotp_tab()
Visible uniquement si une valorisation SOTP est disponible.
"""

from typing import Any

import streamlit as st
import pandas as pd

from core.models import ValuationResult
from core.i18n import SOTPTexts
from app.ui.base import ResultTabBase
from app.ui.result_tabs.components.kpi_cards import format_smart_number


class SOTPBreakdownTab(ResultTabBase):
    """
    Onglet de décomposition SOTP.

    Migration exacte de _render_sotp_tab() depuis ui_kpis.py
    pour garantir l'identicité fonctionnelle.
    """

    TAB_ID = "sotp_breakdown"
    LABEL = SOTPTexts.TITLE
    ICON = ""
    ORDER = 5
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si SOTP disponible."""
        return (
            result.params.sotp.enabled
            and len(result.params.sotp.segments) > 0
        )

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche la décomposition SOTP.

        Suit exactement la même logique que _render_sotp_tab dans ui_kpis.py.
        """
        from app.ui_components.ui_charts import display_sotp_waterfall

        st.markdown(f"#### {SOTPTexts.TITLE}")
        display_sotp_waterfall(result)

        st.divider()
        st.caption(SOTPTexts.LBL_BU_DETAILS)

        df_sotp = pd.DataFrame([
            {
                SOTPTexts.LBL_SEGMENT_NAME: b.name,
                SOTPTexts.LBL_SEGMENT_VALUE: format_smart_number(b.enterprise_value, result.financials.currency),
                SOTPTexts.LBL_SEGMENT_METHOD: b.method.value
            } for b in result.params.sotp.segments
        ])
        st.table(df_sotp)
