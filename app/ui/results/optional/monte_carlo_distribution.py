"""
app/ui/results/optional/monte_carlo_distribution.py
Pillier 4 — Ingénierie du Risque : Distribution Monte Carlo.
Rôle : Visualisation de la dispersion stochastique et des métriques de VaR.
"""

from typing import Any, Dict
import streamlit as st

from src.models import ValuationResult
from src.i18n import QuantTexts, KPITexts, CommonTexts
from src.utilities.formatting import format_smart_number
from app.ui.results.base_result import ResultTabBase
from app.ui.components.ui_charts import display_simulation_chart

class MonteCarloDistributionTab(ResultTabBase):
    """
    Pillier 4 : Analyse de Risque Probabiliste.
    Consomme les statistiques pré-calculées par l'orchestrateur.
    """

    TAB_ID = "monte_carlo"
    LABEL = KPITexts.TAB_MC
    ORDER = 8
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """Visible uniquement si des résultats de simulation sont présents."""
        return bool(result.simulation_results and len(result.simulation_results) > 0)

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu de l'analyse de distribution et du Hub de Risque."""

        # 1. Récupération des statistiques injectées par l'orchestrateur (Performance)
        stats = kwargs.get("mc_stats")
        currency = result.financials.currency

        st.markdown(f"**{QuantTexts.MC_TITLE}**")

        # Sous-titre technique : Configuration de la simulation
        config_sub = QuantTexts.MC_CONFIG_SUB.format(
            sims=len(result.simulation_results),
            sig_b=result.params.monte_carlo.sigma_beta,
            sig_g=result.params.monte_carlo.sigma_growth,
            rho=result.params.monte_carlo.rho
        )
        st.caption(config_sub)
        st.write("")

        # 2. HUB DE RISQUE (Statistiques de Dispersion)
        if stats:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns(4)

                # Médiane (P50) - Point d'ancrage central
                c1.metric(
                    label=QuantTexts.MC_MEDIAN,
                    value=format_smart_number(stats["median"], currency=currency)
                )

                # Value-at-Risk (VaR 95%) - Risque de queue
                c2.metric(
                    label=QuantTexts.MC_VAR,
                    value=format_smart_number(stats["var_95"], currency=currency),
                    help=KPITexts.HELP_VAR
                )

                # Écart-type - Volatilité de la valorisation
                c3.metric(
                    label="VOLATILITÉ (σ)",
                    value=format_smart_number(stats["std"], currency=currency)
                )

                # Coefficient de Variation (Risque relatif)
                cv = stats["std"] / stats["median"] if stats["median"] != 0 else 0
                c4.metric(
                    label="COEF. VARIATION",
                    value=f"{cv:.1%}"
                )

        # 3. VISUALISATION GRAPHIQUE (Organisme ui_charts)
        # Intègre automatiquement la ligne du prix de marché et les quantiles
        st.write("")
        display_simulation_chart(
            simulation_results=result.simulation_results,
            market_price=result.market_price,
            currency=currency
        )

        # 4. ANALYSE DE PROBABILITÉ (OPPORTUNITÉ VS RISQUE)
        st.write("")
        with st.container(border=True):
            st.markdown(f"**{QuantTexts.MC_DOWNSIDE.upper()}**")

            # Calculs rapides sur le vecteur de simulation
            sim_array = [v for v in result.simulation_results if v is not None]
            prob_above = sum(1 for v in sim_array if v > result.market_price) / len(sim_array)

            p_col1, p_col2 = st.columns(2)

            # Probabilité de gain (Valeur > Prix)
            p_col1.metric(
                label="Probabilité d'Undervaluation",
                value=f"{prob_above:.1%}",
                delta="Opportunité" if prob_above > 0.5 else "Risque",
                delta_color="normal" if prob_above > 0.5 else "inverse"
            )

            # Intervalle de Confiance 80% (P10 - P90)
            if stats:
                range_str = f"{format_smart_number(stats['p10'])} — {format_smart_number(stats['p90'])}"
                p_col2.metric(
                    label=QuantTexts.MC_FILTER_SUB.format(valid=len(sim_array), total=len(sim_array)),
                    value=range_str,
                    help="Fourchette de probabilité à 80% (P10 à P90)."
                )

    def get_display_label(self) -> str:
        """Retourne le label i18n pour l'orchestrateur."""
        return self.LABEL