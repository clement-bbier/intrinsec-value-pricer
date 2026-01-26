"""
app/ui/results/optional/scenario_analysis.py
PILLIER 4 — SOUS-COMPOSANT : ANALYSE DE SCÉNARIOS DÉTERMINISTES
==============================================================
Rôle : Comparaison Bull/Base/Bear et calcul de l'espérance mathématique.
Architecture : Composant injectable Grade-A.
"""

from typing import Any
import streamlit as st
import pandas as pd

from src.models import ValuationResult
from src.i18n import QuantTexts, KPITexts
from src.utilities.formatting import format_smart_number
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_kpis import atom_kpi_metric

class ScenarioAnalysisTab(ResultTabBase):
    """
    Composant de rendu pour l'analyse multi-scénarios.
    Intégré verticalement dans l'onglet RiskEngineering.
    """

    TAB_ID = "scenario_analysis"
    LABEL = KPITexts.TAB_SCENARIOS
    ORDER = 4 # Aligné sur le Pilier 4
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """L'onglet est visible si le moteur de scénarios a généré des variantes."""
        return (
            result.scenario_synthesis is not None
            and len(result.scenario_synthesis.variants) > 0
        )

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu de la synthèse des scénarios avec triangulation visuelle."""
        synthesis = result.scenario_synthesis
        currency = result.financials.currency
        market_price = result.market_price

        # --- EN-TÊTE DE SECTION (Standardisé ####) ---
        st.markdown(f"#### {QuantTexts.SCENARIO_TITLE}")
        st.caption(KPITexts.LABEL_SCENARIO_RANGE)
        st.write("")

        # --- 1. TABLEAU COMPARATIF (DETAILED VIEW) ---
        with st.container(border=True):
            data = []
            for variant in synthesis.variants:
                # Calcul de l'upside spécifique au scénario
                upside = (variant.intrinsic_value / market_price - 1) if market_price > 0 else 0

                data.append({
                    QuantTexts.COL_SCENARIO: variant.label.upper(),
                    QuantTexts.COL_PROBABILITY: variant.probability,
                    QuantTexts.COL_GROWTH: variant.growth_used,
                    QuantTexts.COL_MARGIN_FCF: variant.margin_used if variant.margin_used else 0.0,
                    QuantTexts.COL_VALUE_PER_SHARE: variant.intrinsic_value,
                    QuantTexts.COL_UPSIDE: upside
                })

            df = pd.DataFrame(data)

            # Configuration des colonnes (Standard Institutionnel)
            column_config = {
                QuantTexts.COL_PROBABILITY: st.column_config.NumberColumn(format="%.0f%%"),
                QuantTexts.COL_GROWTH: st.column_config.NumberColumn(format="%.2f%%"),
                QuantTexts.COL_MARGIN_FCF: st.column_config.NumberColumn(format="%.2f%%"),
                QuantTexts.COL_VALUE_PER_SHARE: st.column_config.NumberColumn(format=f"%.2f {currency}"),
                QuantTexts.COL_UPSIDE: st.column_config.ProgressColumn(
                    label=QuantTexts.COL_UPSIDE,
                    format="%.1%+",
                    min_value=-1.0,
                    max_value=1.0,
                    color="blue" # Couleur neutre institutionnelle
                )
            }

            st.dataframe(
                df,
                hide_index=True,
                width="stretch",
                column_config=column_config,
                use_container_width=True
            )

        # --- 2. SYNTHÈSE PONDÉRÉE (EXPECTED VALUE HUB) ---
        expected_val = synthesis.expected_value
        if expected_val > 0:
            st.write("")
            with st.container(border=True):
                col_val, col_upside = st.columns(2)

                with col_val:
                    atom_kpi_metric(
                        label=QuantTexts.METRIC_WEIGHTED_VALUE,
                        value=format_smart_number(expected_val, currency=currency),
                        help_text=KPITexts.HELP_IV
                    )

                with col_upside:
                    weighted_upside = (expected_val / market_price - 1) if market_price > 0 else 0
                    # Utilisation des deltas i18n
                    atom_kpi_metric(
                        label=QuantTexts.METRIC_WEIGHTED_UPSIDE,
                        value=f"{weighted_upside:+.1%}",
                        delta=f"{weighted_upside:+.1%}",
                        delta_color="normal" if weighted_upside > 0 else "inverse",
                        help_text=KPITexts.HELP_MOS
                    )

    def get_display_label(self) -> str:
        return self.LABEL