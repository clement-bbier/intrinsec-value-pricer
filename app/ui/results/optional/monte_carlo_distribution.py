"""
app/ui/results/optional/monte_carlo_distribution.py
PILLIER 4 — SOUS-COMPOSANT : DISTRIBUTION MONTE CARLO (Versatile)
=================================================================
Rôle : Visualisation de la dispersion stochastique et des métriques de VaR.
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult
from src.i18n import QuantTexts, KPITexts, AuditTexts
from src.utilities.formatting import format_smart_number
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_charts import display_simulation_chart

class MonteCarloDistributionTab(ResultTabBase):
    """
    Composant de rendu pour la simulation de Monte Carlo.
    Intégré verticalement dans l'onglet RiskEngineering.
    """

    TAB_ID = "monte_carlo"
    LABEL = KPITexts.TAB_MC
    ORDER = 4
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Condition de présence des données de simulation."""
        return bool(result.simulation_results and len(result.simulation_results) > 0)

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu institutionnel du Hub de Risque Monte Carlo."""

        stats = kwargs.get("mc_stats")
        currency = result.financials.currency

        # --- EN-TÊTE DE SECTION (Standardisé ####) ---
        st.markdown(f"#### {QuantTexts.MC_TITLE}")

        config_sub = QuantTexts.MC_CONFIG_SUB.format(
            sims=len(result.simulation_results),
            sig_b=result.params.monte_carlo.beta_volatility,
            sig_g=result.params.monte_carlo.growth_volatility,
            rho=result.params.monte_carlo.correlation_beta_growth
        )
        st.caption(config_sub)
        st.write("")

        # 1. HUB DE RISQUE (Dispersion)
        if stats:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(QuantTexts.MC_MEDIAN, format_smart_number(stats["median"], currency=currency))
                c2.metric(QuantTexts.MC_VAR, format_smart_number(stats["var_95"], currency=currency), help=KPITexts.HELP_VAR)
                # i18n pour VOLATILITÉ
                c3.metric(AuditTexts.H_INDICATOR, format_smart_number(stats["std"], currency=currency))
                # i18n pour COEF VARIATION
                cv = stats["std"] / stats["median"] if stats["median"] != 0 else 0
                c4.metric(QuantTexts.MC_TAIL_RISK, f"{cv:.1%}")

        # 2. GRAPHIQUE (Plotly/Altair)
        st.write("")
        display_simulation_chart(
            ticker=result.ticker,
            simulation_results=result.simulation_results,
            market_price=result.market_price,
            currency=currency
        )

        # 3. ANALYSE DE PROBABILITÉ (Zéro texte brut)
        st.write("")
        with st.container(border=True):
            st.markdown(f"**{QuantTexts.MC_DOWNSIDE.upper()}**")

            sim_array = [v for v in result.simulation_results if v is not None]
            if sim_array:
                prob_above = sum(1 for v in sim_array if v > result.market_price) / len(sim_array)
                p_col1, p_col2 = st.columns(2)

                # Probabilité d'Undervaluation (i18n dynamique)
                p_col1.metric(
                    label=AuditTexts.H_VERDICT,
                    value=f"{prob_above:.1%}",
                    delta=KPITexts.LABEL_MOS if prob_above > 0.5 else QuantTexts.MC_DOWNSIDE,
                    delta_color="normal" if prob_above > 0.5 else "inverse"
                )

                # Intervalle de Confiance 80% (P10 - P90)
                if stats:
                    range_str = f"{format_smart_number(stats['p10'])} — {format_smart_number(stats['p90'])}"
                    p_col2.metric(
                        label=QuantTexts.MC_FILTER_SUB.format(valid=len(sim_array), total=len(sim_array)),
                        value=range_str
                    )

    def get_display_label(self) -> str:
        return self.LABEL