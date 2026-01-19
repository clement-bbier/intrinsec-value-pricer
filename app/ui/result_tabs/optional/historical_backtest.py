"""
app/ui/result_tabs/optional/historical_backtest.py

ONGLET — BACKTEST HISTORIQUE (VALIDATION RÉTROSPECTIVE)

Rôle : Validation historique de la pertinence des hypothèses de valorisation
Pattern : ResultTabBase (Template Method)
Style : Numpy docstrings

Version : V1.1 — DT-019 Resolution (Correction backtest_result → backtest_report)
Risques financiers : Analyse de performance passée, pas de calculs nouveaux

Dépendances critiques :
- streamlit >= 1.28.0
- core.models.ValuationResult.backtest_report
- core.models.BacktestResult

Visible uniquement si backtest_report contient des données historiques.
Présente : métriques de performance, hit rate, erreurs par période.
"""

from __future__ import annotations

from typing import Any

import streamlit as st
import pandas as pd

from core.models import ValuationResult
from core.config.constants import TechnicalDefaults
from core.i18n import UIMessages
from app.ui.base import ResultTabBase


class HistoricalBacktestTab(ResultTabBase):
    """
    Onglet de validation historique des valorisations.

    Présente les performances rétrospectives du modèle de valorisation
    en comparant les prédictions passées avec les prix de marché réels.

    Attributes
    ----------
    TAB_ID : str
        Identifiant unique "historical_backtest".
    LABEL : str
        Label affiché "Backtest".
    ICON : str
        Icône vide (style sobre).
    ORDER : int
        Position d'affichage (7ème onglet).
    IS_CORE : bool
        False - onglet optionnel (visible si données de backtest disponibles).

    Notes
    -----
    Évalue la robustesse des hypothèses de valorisation sur données historiques.
    Calcule automatiquement l'upside historique par rapport aux prix passés.
    Présente métriques de précision : hit rate, erreurs absolues et relatives.
    """

    TAB_ID = "historical_backtest"
    LABEL = "Backtest"
    ICON = ""
    ORDER = 7
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """
        Détermine si l'onglet doit être affiché.

        Vérifie la présence de données de backtest historique.

        Parameters
        ----------
        result : ValuationResult
            Résultat de valorisation à analyser.

        Returns
        -------
        bool
            True si backtest_report existe et contient des périodes.
        """
        return (
            result.backtest_report is not None
            and len(result.backtest_report.points) > 0
        )

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche l'analyse de validation historique.

        Présente les métriques de performance du modèle sur données passées
        et le détail période par période des prédictions vs réalité.

        Parameters
        ----------
        result : ValuationResult
            Résultat contenant backtest_report avec les données historiques.
        **kwargs : Any
            Paramètres additionnels (non utilisés).

        Notes
        -----
        Calcule l'upside historique : (valeur_prédite - prix_marché_passé) / prix_marché_passé.
        Utilise les prix historiques du backtest_report pour éviter les données manquantes.
        Protège contre les périodes incomplètes en vérifiant la présence des attributs.
        """
        bt = result.backtest_report

        st.markdown("**VALIDATION HISTORIQUE**")
        st.caption("Performance du modèle sur les périodes passées")

        # Métriques globales
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(4)

            periods_count = len(bt.points)
            # Calcul du hit rate : proportion de périodes où le modèle a correctement identifié la sous-valorisation
            hit_rate = sum(1 for p in bt.points if p.was_undervalued) / periods_count if periods_count > 0 else 0.0
            # Erreur médiane absolue
            median_error = sorted([abs(p.error_pct) for p in bt.points])[periods_count // 2] if periods_count > 0 else 0.0

            col1.metric("Périodes testées", periods_count)
            col2.metric("Hit Rate", f"{hit_rate:.0%}")
            col3.metric("Erreur Médiane", f"{median_error:.1%}")
            col4.metric("MAE", f"{bt.mean_absolute_error:.1%}")

        # Détail par période
        if bt.points:
            with st.container(border=True):
                st.markdown("**Détail par Période**")

                periods_data = []
                for point in bt.points:
                    # Sécurité : vérifier que tous les attributs requis sont présents
                    if not hasattr(point, 'valuation_date') or not hasattr(point, 'intrinsic_value') or not hasattr(point, 'market_price') or not hasattr(point, 'error_pct'):
                        continue

                    periods_data.append({
                        "Date": point.valuation_date.strftime("%Y-%m"),
                        "Valeur Prédite": f"{point.intrinsic_value:,.2f}",
                        "Prix Marché": f"{point.market_price:,.2f}",
                        "Erreur": f"{point.error_pct:+.1%}",
                        "Verdict": "OK" if abs(point.error_pct) < TechnicalDefaults.BACKTEST_ERROR_THRESHOLD else "ÉCART",
                    })

                if periods_data:
                    df = pd.DataFrame(periods_data)
                    st.dataframe(df, hide_index=True, width='stretch')
                else:
                    st.info(UIMessages.NO_VALID_PERIOD_DATA)

    def get_display_label(self) -> str:
        """
        Retourne le label d'affichage de l'onglet.

        Returns
        -------
        str
            Label "Backtest".
        """
        return self.LABEL
