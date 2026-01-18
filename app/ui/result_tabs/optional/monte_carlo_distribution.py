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
from core.i18n import UIMessages


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
            result.simulation_results is not None
            and len(result.simulation_results) > 0
        )
    
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Affiche la distribution Monte Carlo."""
        simulations = result.simulation_results or []
        currency = result.financials.currency

        st.markdown("**SIMULATION MONTE CARLO**")
        st.caption(f"{len(simulations):,} simulations exécutées")
        
        # Calculer les statistiques de base
        sim_array = np.array(simulations)
        mean_value = float(np.mean(sim_array))
        median_value = float(np.median(sim_array))
        std_value = float(np.std(sim_array))
        cv = std_value / mean_value if mean_value != 0 else 0

        # Statistiques de distribution
        with st.container(border=True):
            st.markdown("**Statistiques de Distribution**")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Moyenne", format_smart_number(mean_value, currency))
            col2.metric("Médiane", format_smart_number(median_value, currency))
            col3.metric("Écart-type", format_smart_number(std_value, currency))
            col4.metric("Coef. Variation", f"{cv:.1%}")

        # Utiliser les quantiles existants ou les calculer
        quantiles = result.quantiles or {}
        p5 = quantiles.get('P5', float(np.percentile(sim_array, 5)))
        p50 = quantiles.get('P50', median_value)
        p95 = quantiles.get('P95', float(np.percentile(sim_array, 95)))

        # Intervalles de confiance
        with st.container(border=True):
            st.markdown("**Intervalles de Confiance**")

            col1, col2, col3 = st.columns(3)

            col1.metric("P5 (Bear)", format_smart_number(p5, currency))
            col2.metric("P50 (Base)", format_smart_number(p50, currency))
            col3.metric("P95 (Bull)", format_smart_number(p95, currency))

        # Analyse de probabilité
        current_price = result.financials.current_price
        prob_above_current = np.mean(sim_array > current_price)
        upside_threshold = current_price * 1.20
        prob_upside_20pct = np.mean(sim_array > upside_threshold)

        with st.container(border=True):
            st.markdown("**Analyse de Probabilité**")

            col1, col2 = st.columns(2)
            col1.metric(
                "P(Valeur > Prix actuel)",
                f"{prob_above_current:.1%}"
            )
            col2.metric(
                "P(Upside > 20%)",
                f"{prob_upside_20pct:.1%}"
            )

        # Histogramme simple
        try:
            import altair as alt
            import pandas as pd

            df = pd.DataFrame({'value': simulations})

            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('value:Q', bin=alt.Bin(maxbins=50), title=f'Valeur par Action ({currency})'),
                y=alt.Y('count()', title='Fréquence'),
            ).properties(
                title="Distribution des Valeurs Intrinsèques",
                height=300
            )

            st.altair_chart(chart, width='stretch')

        except ImportError:
            st.info(UIMessages.CHART_UNAVAILABLE)
    
    def get_display_label(self) -> str:
        return self.LABEL
