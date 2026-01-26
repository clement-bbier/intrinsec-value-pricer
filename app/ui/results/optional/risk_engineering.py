"""
app/ui/results/optional/risk_engineering.py
PILLIER 4 — INGÉNIERIE DU RISQUE
===============================
Rôle : Unifie la simulation stochastique, les scénarios et le backtesting.
Design : Suppression des doublons de titres et activation des données réelles (ST-4.2).
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult
from src.i18n import PillarLabels, QuantTexts, BacktestTexts
from app.ui.results.base_result import ResultTabBase

# Moteurs de rendu internes
from .monte_carlo_distribution import MonteCarloDistributionTab
from .scenario_analysis import ScenarioAnalysisTab
from .historical_backtest import HistoricalBacktestTab
from app.ui.components.ui_charts import display_backtest_convergence_chart


class RiskEngineeringTab(ResultTabBase):
    """
    Pilier 4 : Ingénierie du risque.
    Gère l'affichage dynamique des briques de risque et de validation.
    """

    TAB_ID = "risk_engineering"
    LABEL = PillarLabels.PILLAR_4_RISK
    ORDER = 4
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu des composants de risque avec nettoyage visuel."""

        # --- 1. EN-TÊTE DE PILIER (Normalisé) ---
        st.markdown(f"### {PillarLabels.PILLAR_4_RISK}")
        st.caption(QuantTexts.MC_AUDIT_STOCH)
        st.write("")

        # --- 2. BLOC MONTE CARLO ---
        # Note : Le titre "Simulation de Monte Carlo" est supprimé ici
        # car il est déjà présent dans la synthèse du graphique.
        mc_tab = MonteCarloDistributionTab()
        if mc_tab.is_visible(result):
            mc_tab.render(result, **kwargs)
            st.divider()

        # --- 3. BLOC SCÉNARIOS (DÉTERMINISTES) ---
        sc_tab = ScenarioAnalysisTab()
        if sc_tab.is_visible(result):
            st.markdown(f"#### {QuantTexts.SCENARIO_TITLE}")
            sc_tab.render(result, **kwargs)
            st.divider()

        # --- 4. BLOC BACKTESTING (VALIDATION HISTORIQUE) ---
        st.markdown(f"#### {BacktestTexts.TITLE}")

        # Vérification de la présence réelle de points de backtest
        if result.backtest_report and result.backtest_report.points:
            # Rendu direct du graphique de convergence (Prédit vs Réel)
            display_backtest_convergence_chart(
                ticker=result.ticker,
                backtest_report=result.backtest_report,
                currency=result.financials.currency
            )
            # Rendu des métriques de précision (MAE, Alpha) via le sous-onglet
            bt_tab = HistoricalBacktestTab()
            bt_tab.render(result, **kwargs)
        else:
            # Message pédagogique si les données historiques sont manquantes (ex: IPO récente)
            st.info(BacktestTexts.HELP_BACKTEST)

    def is_visible(self, result: ValuationResult) -> bool:
        """L'onglet est toujours visible pour centraliser l'analyse de risque."""
        return True