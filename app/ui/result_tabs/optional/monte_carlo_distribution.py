"""
app/ui/result_tabs/optional/monte_carlo_distribution.py
Onglet — Distribution Monte Carlo

Migration depuis ui_kpis.py._render_monte_carlo_tab()
Visible uniquement si une simulation Monte Carlo a été exécutée.
"""

from typing import Any, List

import streamlit as st

from core.models import ValuationResult, CalculationStep
from core.i18n import AuditTexts
from app.ui.base import ResultTabBase


class MonteCarloDistributionTab(ResultTabBase):
    """
    Onglet des résultats Monte Carlo.

    Migration exacte de _render_monte_carlo_tab() depuis ui_kpis.py
    pour garantir l'identicité fonctionnelle.
    """

    TAB_ID = "monte_carlo"
    LABEL = AuditTexts.MC_TITLE
    ICON = ""
    ORDER = 8
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si Monte Carlo exécuté."""
        return (
            result.params.monte_carlo.enable_monte_carlo
            and result.simulation_results is not None
        )

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche la distribution Monte Carlo.

        Suit exactement la même logique que _render_monte_carlo_tab dans ui_kpis.py.
        """
        # Extraire les étapes MC des étapes de calcul
        mc_steps = [s for s in result.calculation_trace if s.step_key.startswith("MC_")]

        from app.ui_components.ui_charts import display_simulation_chart
        if not result.simulation_results: return

        st.markdown(AuditTexts.MC_TITLE)
        q = result.quantiles or {}
        c1, c2, c3 = st.columns(3)
        c1.metric(AuditTexts.MC_MEDIAN, f"{q.get('P50', 0.0):,.2f}")
        c2.metric(AuditTexts.MC_TAIL_RISK, f"{q.get('P10', 0.0):,.2f}")
        c3.metric("VALID RATIO", f"{getattr(result, 'mc_valid_ratio', 0):.1%}")

        display_simulation_chart(result.simulation_results, result.market_price, result.financials.currency)

        with st.expander(AuditTexts.MC_AUDIT_STOCH):
            from app.ui.result_tabs.components.step_renderer import render_calculation_step
            for idx, step in enumerate(mc_steps, start=1):
                render_calculation_step(idx, step)
            col4.metric(KPITexts.METRIC_CV, f"{mc.cv:.1%}")
        
        # Percentiles
        with st.container(border=True):
            st.markdown(f"**{KPITexts.TITLE_CI}**")

            col1, col2, col3 = st.columns(3)

            col1.metric(KPITexts.METRIC_P5, format_smart_number(mc.percentile_5, currency))
            col2.metric(KPITexts.METRIC_P50, format_smart_number(mc.percentile_50, currency))
            col3.metric(KPITexts.METRIC_P95, format_smart_number(mc.percentile_95, currency))
        
        # Probabilités
        with st.container(border=True):
            st.markdown(f"**{KPITexts.TITLE_PROBA_ANALYSIS}**")

            current_price = result.financials.current_price

            col1, col2 = st.columns(2)
            col1.metric(
                KPITexts.PROBA_ABOVE_CURRENT,
                f"{mc.prob_above_current:.1%}"
            )
            col2.metric(
                KPITexts.PROBA_UPSIDE_20,
                f"{mc.prob_upside_20pct:.1%}" if hasattr(mc, 'prob_upside_20pct') else "—"
            )
        
        # Histogramme (si plotly disponible)
        if mc.distribution is not None and len(mc.distribution) > 0:
            try:
                import plotly.graph_objects as go
                
                fig = go.Figure(data=[go.Histogram(
                    x=mc.distribution,
                    nbinsx=50,
                    marker_color='#1f77b4',
                    opacity=0.75
                )])
                
                # Ligne du prix actuel
                fig.add_vline(
                    x=current_price,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=KPITexts.CHART_ANNOTATION_CURRENT
                )
                
                # Ligne de la valeur intrinsèque
                fig.add_vline(
                    x=result.intrinsic_value,
                    line_dash="solid",
                    line_color="green",
                    annotation_text=KPITexts.CHART_ANNOTATION_DCF
                )
                
                fig.update_layout(
                    title=KPITexts.CHART_TITLE_DISTRIBUTION,
                    xaxis_title=f"Valeur par action ({currency})",
                    yaxis_title="Fréquence",
                    showlegend=False,
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except ImportError:
                st.info("Installer plotly pour afficher l'histogramme.")
    
    def get_display_label(self) -> str:
        return self.LABEL
