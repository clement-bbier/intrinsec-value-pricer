"""
app/ui/result_tabs/optional/monte_carlo_distribution.py
Onglet — Distribution Monte Carlo

Visible uniquement si une simulation Monte Carlo a été exécutée.
"""

from typing import Any

import streamlit as st
import numpy as np

from core.models import ValuationResult
from app.ui.base import ResultTabBase
from app.ui.result_tabs.components.kpi_cards import format_smart_number


class MonteCarloDistributionTab(ResultTabBase):
    """Onglet des résultats Monte Carlo."""
    
    TAB_ID = "monte_carlo"
    LABEL = "Monte Carlo"
    ICON = ""
    ORDER = 8
    IS_CORE = False
    
    def is_visible(self, result: ValuationResult) -> bool:
        """Visible si Monte Carlo exécuté."""
        return (
            result.monte_carlo_result is not None
            and result.monte_carlo_result.simulations_count > 0
        )
    
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Affiche la distribution Monte Carlo."""
        mc = result.monte_carlo_result
        currency = result.financials.currency
        
        st.markdown("**SIMULATION MONTE CARLO**")
        st.caption(f"{mc.simulations_count:,} simulations exécutées")
        
        # Statistiques de distribution
        with st.container(border=True):
            st.markdown("**Statistiques de Distribution**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Moyenne", format_smart_number(mc.mean_value, currency))
            col2.metric("Médiane", format_smart_number(mc.median_value, currency))
            col3.metric("Écart-type", format_smart_number(mc.std_value, currency))
            col4.metric("Coef. Variation", f"{mc.cv:.1%}")
        
        # Percentiles
        with st.container(border=True):
            st.markdown("**Intervalles de Confiance**")
            
            col1, col2, col3 = st.columns(3)
            
            col1.metric("P5 (Bear)", format_smart_number(mc.percentile_5, currency))
            col2.metric("P50 (Base)", format_smart_number(mc.percentile_50, currency))
            col3.metric("P95 (Bull)", format_smart_number(mc.percentile_95, currency))
        
        # Probabilités
        with st.container(border=True):
            st.markdown("**Analyse de Probabilité**")
            
            current_price = result.financials.current_price
            
            col1, col2 = st.columns(2)
            col1.metric(
                "P(Valeur > Prix actuel)",
                f"{mc.prob_above_current:.1%}"
            )
            col2.metric(
                "P(Upside > 20%)",
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
                    annotation_text="Prix actuel"
                )
                
                # Ligne de la valeur intrinsèque
                fig.add_vline(
                    x=result.intrinsic_value,
                    line_dash="solid",
                    line_color="green",
                    annotation_text="Valeur DCF"
                )
                
                fig.update_layout(
                    title="Distribution des Valeurs Intrinsèques",
                    xaxis_title=f"Valeur par action ({currency})",
                    yaxis_title="Fréquence",
                    showlegend=False,
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, width='stretch')
                
            except ImportError:
                st.info("Installer plotly pour afficher l'histogramme.")
    
    def get_display_label(self) -> str:
        return self.LABEL
