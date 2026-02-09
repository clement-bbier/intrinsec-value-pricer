"""
app/views/results/pillars/scenario_analysis.py
PILLAR 4 — SUB-COMPONENT: DETERMINISTIC SCENARIO ANALYSIS
=========================================================
Role: Bull/Base/Bear comparison and mathematical expectation calculation.
Architecture: Injectable Grade-A component.
"""

from typing import Any, Literal
import streamlit as st
import pandas as pd

from src.models import ValuationResult
from src.i18n import QuantTexts, KPITexts
from src.core.formatting import format_smart_number
from app.views.components.ui_kpis import atom_kpi_metric
from app.views.components.ui_charts import display_scenario_comparison_chart

class ScenarioAnalysisTab:
    """
    Rendering component for multi-scenario analysis.
    Typically integrated vertically within the RiskEngineering tab.
    Architecture: Stateless Component.
    """

    @staticmethod
    def is_visible(result: ValuationResult) -> bool:
        """Visible only if the scenario engine generated variants."""
        # Vérification de l'activation ET de la présence des résultats
        if not result.params.extensions.scenarios.enabled:
            return False
        return result.results.extensions.scenarios is not None

    @staticmethod
    def render(result: ValuationResult, **_kwargs: Any) -> None:
        """
        Renders the scenario synthesis with comparative chart, table and weighted expectation.
        Note: _kwargs is strictly typed but unused.
        """
        # Accès sécurisé aux résultats
        scenarios_res = result.results.extensions.scenarios
        if not scenarios_res:
            return

        currency = result.financials.currency
        market_price = result.market_price or 0.0

        # --- SECTION HEADER ---
        st.markdown(f"#### {QuantTexts.SCENARIO_TITLE}")
        st.caption(KPITexts.LABEL_SCENARIO_RANGE)

        # --- 1. VISUAL COMPARISON (CHART VIA UI_CHARTS) ---
        # Préparation des données pour le composant UI générique
        chart_data = []
        for variant in scenarios_res.outcomes:
             chart_data.append({
                "Scenario": variant.label,
                "Value": variant.intrinsic_value,
                "Upside": variant.upside_pct,
                "Color": "green" if variant.upside_pct > 0 else "red"
            })

        # Appel au moteur de visualisation (DRY / SoC)
        display_scenario_comparison_chart(
            scenarios_data=chart_data,
            market_price=market_price,
            currency=currency
        )

        st.write("")

        # --- 2. COMPARATIVE TABLE (DETAILED VIEW) ---
        with st.container(border=True):
            table_data = []
            for variant in scenarios_res.outcomes:
                table_data.append({
                    QuantTexts.COL_SCENARIO: variant.label,
                    QuantTexts.COL_PROBABILITY: variant.probability,
                    QuantTexts.COL_VALUE_PER_SHARE: variant.intrinsic_value,
                    QuantTexts.COL_UPSIDE: variant.upside_pct
                })

            df = pd.DataFrame(table_data)

            # Institutional Column Configuration
            column_config = {
                QuantTexts.COL_SCENARIO: st.column_config.TextColumn(width="medium"),
                QuantTexts.COL_PROBABILITY: st.column_config.NumberColumn(format="%.0f%%"),
                QuantTexts.COL_VALUE_PER_SHARE: st.column_config.NumberColumn(format=f"%.2f {currency}"),
                QuantTexts.COL_UPSIDE: st.column_config.ProgressColumn(
                    label=QuantTexts.COL_UPSIDE,
                    format="%.1%+",
                    min_value=-0.5,
                    max_value=0.5,
                    color="blue" # Le bleu est neutre, le signe +/- indique le sens
                )
            }

            st.dataframe(
                df,
                hide_index=True,
                column_config=column_config,
                use_container_width=True
            )

        # --- 3. WEIGHTED SYNTHESIS (EXPECTED VALUE HUB) ---
        expected_val = scenarios_res.expected_intrinsic_value
        if expected_val > 0:
            st.write("")
            with st.container(border=True):
                col_val, col_upside = st.columns(2)

                with col_val:
                    # Mathematical expectation of the intrinsic value
                    atom_kpi_metric(
                        label=QuantTexts.METRIC_WEIGHTED_VALUE,
                        value=format_smart_number(expected_val, currency=currency),
                        help_text=KPITexts.HELP_IV
                    )

                with col_upside:
                    # Weighted Potential (Expected Upside)
                    weighted_upside = (expected_val / market_price - 1) if market_price > 0 else 0

                    # Typage explicite pour satisfaire le linter
                    color_delta: Literal["normal", "inverse"] = "normal" if weighted_upside > 0 else "inverse"

                    atom_kpi_metric(
                        label=QuantTexts.METRIC_WEIGHTED_UPSIDE,
                        value=f"{weighted_upside:+.1%}",
                        delta=f"{weighted_upside:+.1%}",
                        delta_color=color_delta,
                        help_text=KPITexts.HELP_MOS
                    )