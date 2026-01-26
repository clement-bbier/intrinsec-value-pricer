"""
app/ui/results/optional/peer_multiples.py
Pillier 5 — Analyse de Marché : Valorisation Relative par Comparables.
Rôle : Triangulation entre la valeur intrinsèque et les multiples de marché.
"""

from __future__ import annotations
from typing import Any
import streamlit as st
import pandas as pd

from src.models import ValuationResult
from src.i18n import MarketTexts, KPITexts, CommonTexts
from src.utilities.formatting import format_smart_number
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_kpis import atom_kpi_metric
from app.ui.components.ui_charts import display_football_field

class PeerMultiplesTab(ResultTabBase):
    """
    Onglet de valorisation relative.
    Compare la cible à une cohorte de pairs sectoriels.
    """

    TAB_ID = "peer_multiples"
    LABEL = "Valorisation Relative" # Peut être lié à MarketTexts.MARKET_TITLE
    ORDER = 4
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """L'onglet est visible si une cohorte de pairs est présente."""
        return (
            result.multiples_triangulation is not None
            and len(result.multiples_triangulation.multiples_data.peers) > 0
        )

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu institutionnel de la triangulation relative."""
        md = result.multiples_triangulation.multiples_data
        currency = result.financials.currency

        st.markdown(f"**{MarketTexts.MARKET_TITLE}**")
        st.caption(f"Analyse basée sur un panel de {len(md.peers)} {MarketTexts.COL_PEER.lower()}s.")

        # --- 1. TRIANGULATION VISUELLE (FOOTBALL FIELD) ---
        # Appel de votre nouveau composant haute précision
        display_football_field(result)
        st.write("")

        # --- 2. RÉSUMÉ DES VALEURS IMPLICITES ---
        if md.implied_value_ev_ebitda or md.implied_value_pe:
            with st.container(border=True):
                st.markdown(f"**{KPITexts.SUB_CALCULATED}**")
                c1, c2 = st.columns(2)

                if md.implied_value_ev_ebitda:
                    with c1:
                        atom_kpi_metric(
                            label=f"Value via {KPITexts.LABEL_FOOTBALL_FIELD_EBITDA}",
                            value=format_smart_number(md.implied_value_ev_ebitda, currency)
                        )

                if md.implied_value_pe:
                    with c2:
                        atom_kpi_metric(
                            label=f"Value via {KPITexts.LABEL_FOOTBALL_FIELD_PE}",
                            value=format_smart_number(md.implied_value_pe, currency)
                        )

        # --- 3. TABLEAU COMPARATIF DES RATIOS (TARGET VS SECTOR) ---
        st.write("")
        with st.container(border=True):
            st.markdown(f"**{MarketTexts.COL_MULTIPLE}S COMPARATIFS**")

            # Construction des lignes avec les labels i18n de KPITexts
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
                },
                {
                    "Ratio": "Price-to-Book (P/B)", # Peut être ajouté à KPITexts
                    "Médiane": f"{md.median_pb:.1f}x" if md.median_pb else "—",
                    "Cible": f"{result.financials.pb_ratio:.1f}x" if result.financials.pb_ratio else "—"
                }
            ]

            df_comp = pd.DataFrame(comparison_data)
            st.dataframe(df_comp, hide_index=True, use_container_width=True)

        # Note de synthèse (i18n)
        st.caption(f"**{CommonTexts.INTERPRETATION_LABEL}** : {KPITexts.RELATIVE_VAL_DESC}")

    def get_display_label(self) -> str:
        return self.LABEL