"""
app/ui/result_tabs/optional/scenario_analysis.py

ONGLET — ANALYSE DE SCÉNARIOS (BULL/BASE/BEAR)

Rôle : Affichage des résultats de valorisation sous différents scénarios
Pattern : ResultTabBase (Template Method)
Style : Numpy docstrings

Version : V2.0 — ST-2.2 (Correction interface scenario_synthesis)
Risques financiers : Affichage de valorisations alternatives, pas de calculs

Dépendances critiques :
- streamlit >= 1.28.0
- core.models.ValuationResult.scenario_synthesis
- core.models.scenarios.ScenarioSynthesis

Visible uniquement si scenario_synthesis contient des variants.
Présente : tableau comparatif, valeurs pondérées, upside par scénario.
"""

from typing import Any

import streamlit as st
import pandas as pd
import numpy as np

# Supprimer l'avertissement de dépréciation pandas
pd.set_option('future.no_silent_downcasting', True)

from src.domain.models import ValuationResult
from app.ui.base import ResultTabBase
from src.utilities.formatting import format_smart_number


class ScenarioAnalysisTab(ResultTabBase):
    """
    Onglet d'analyse de scénarios déterministes.

    Présente les résultats de valorisation sous différents scénarios
    (Bull/Base/Bear) avec probabilités, valeurs intrinsèques et
    calculs d'upside par rapport au prix de marché.

    Attributes
    ----------
    TAB_ID : str
        Identifiant unique "scenario_analysis".
    LABEL : str
        Label affiché "Scénarios".
    ICON : str
        Icône vide (style sobre).
    ORDER : int
        Position d'affichage (6ème onglet).
    IS_CORE : bool
        False - onglet optionnel (visible si scénarios présents).

    Notes
    -----
    Utilise result.scenario_synthesis pour accéder aux données.
    Calcule automatiquement l'upside par rapport au prix de marché.
    Présente la valeur pondérée selon les probabilités des scénarios.
    """
    
    TAB_ID = "scenario_analysis"
    LABEL = "Scénarios"
    ICON = ""
    ORDER = 6
    IS_CORE = False
    
    def is_visible(self, result: ValuationResult) -> bool:
        """
        Détermine si l'onglet doit être affiché.

        Vérifie la présence de données de scénarios dans le résultat.

        Parameters
        ----------
        result : ValuationResult
            Résultat de valorisation à analyser.

        Returns
        -------
        bool
            True si scenario_synthesis existe et contient des variants.
        """
        return (
            result.scenario_synthesis is not None
            and len(result.scenario_synthesis.variants) > 0
        )
    
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche l'analyse complète des scénarios déterministes.

        Présente un tableau comparatif de tous les scénarios calculés
        avec leurs caractéristiques et valeurs, plus la synthèse pondérée.

        Parameters
        ----------
        result : ValuationResult
            Résultat contenant scenario_synthesis avec les variants.
        **kwargs : Any
            Paramètres additionnels (non utilisés).

        Notes
        -----
        Calcule l'upside de chaque scénario par rapport au prix de marché.
        Utilise expected_value pour la valorisation pondérée.
        Gère les cas où market_price pourrait être nul.
        """
        scenario_synthesis = result.scenario_synthesis
        currency = result.financials.currency

        st.markdown("**ANALYSE DE SCÉNARIOS**")
        st.caption("Valorisation sous différentes hypothèses de croissance")

        # Tableau des scénarios
        with st.container(border=True):
            scenario_data = []
            for scenario in scenario_synthesis.variants:
                # Calcul de l'upside par rapport au prix de marché
                market_price = result.financials.current_price
                if market_price is not None and market_price > 0:
                    upside_pct = (scenario.intrinsic_value - market_price) / market_price
                else:
                    upside_pct = 0.0

                scenario_data.append({
                    "Scénario": scenario.label.upper(),
                    "Probabilité": scenario.probability,  # Valeur brute float
                    "Croissance": scenario.growth_used,   # Valeur brute float
                    "Marge FCF": scenario.margin_used if scenario.margin_used and scenario.margin_used != 0 else None,  # Valeur brute ou None
                    "Valeur/Action": scenario.intrinsic_value,  # Valeur brute float
                    "Upside": upside_pct,  # Valeur brute float
                })

            df = pd.DataFrame(scenario_data)

            # Traitement des données pour robustesse
            df['Marge FCF'] = df['Marge FCF'].fillna(np.nan).infer_objects(copy=False)

            # Configuration des colonnes avec formatage Streamlit
            column_config = {
                "Probabilité": st.column_config.NumberColumn(format="%.0f%%"),
                "Croissance": st.column_config.NumberColumn(format="%.1f%%"),
                "Marge FCF": st.column_config.NumberColumn(format="%.1f%%"),
                "Valeur/Action": st.column_config.NumberColumn(format=f"%.2f {currency}"),
                "Upside": st.column_config.NumberColumn(format="%.1f%%"),  # Format sans signe + pour éviter les crashes
            }

            st.dataframe(df, hide_index=True, width='stretch', column_config=column_config)

        # Valeur pondérée
        expected_value = scenario_synthesis.expected_value
        if expected_value > 0:
            market_price = result.financials.current_price
            if market_price is not None and market_price > 0:
                weighted_upside = (expected_value - market_price) / market_price
            else:
                weighted_upside = 0.0

            with st.container(border=True):
                col1, col2 = st.columns(2)
                col1.metric(
                    "Valeur Pondérée",
                    format_smart_number(expected_value, currency)
                )
                col2.metric(
                    "Upside Pondéré",
                    f"{weighted_upside:+.1%}"
                )
    
    def get_display_label(self) -> str:
        return self.LABEL
