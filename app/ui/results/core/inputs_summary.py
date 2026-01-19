"""
app/ui/result_tabs/core/inputs_summary.py
Onglet — Récapitulatif des Hypothèses

Affiche les données d'entrée utilisées pour le calcul :
- Données financières (FCF, Revenus, etc.)
- Paramètres de valorisation (WACC, g, etc.)
"""

from typing import Any

import streamlit as st
import pandas as pd

from src.domain.models import ValuationResult
from src.i18n import KPITexts
from app.ui.base import ResultTabBase


class InputsSummaryTab(ResultTabBase):
    """Onglet des hypothèses d'entrée."""
    
    TAB_ID = "inputs_summary"
    LABEL = "Hypotheses"
    ICON = ""
    ORDER = 1
    IS_CORE = True
    
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Affiche les données d'entrée."""
        f = result.financials
        p = result.params
        
        st.markdown(f"**{KPITexts.SECTION_INPUTS_HEADER}**")
        st.caption(KPITexts.SECTION_INPUTS_CAPTION)

        # Section 1 : Donnees Financieres
        with st.container(border=True):
            st.markdown("**Donnees Financieres**")

            col1, col2 = st.columns(2)

            with col1:
                data_left = {
                    "Entreprise": f.name,
                    "Ticker": f.ticker,
                    "Devise": f.currency,
                    "Prix actuel": f"{f.current_price:,.2f}",
                    "Market Cap": self._format_number(f.market_cap),
                }
                df_left = pd.DataFrame(data_left.items(), columns=["Métrique", "Valeur"])
                df_left["Valeur"] = df_left["Valeur"].astype(str)
                st.table(df_left)

            with col2:
                data_right = {
                    "Revenue TTM": self._format_number(f.revenue_ttm),
                    "EBIT TTM": self._format_number(f.ebit_ttm),
                    "FCF TTM": self._format_number(f.fcf),
                    "Beta": f"{f.beta:.2f}" if f.beta else "—",
                }
                df_right = pd.DataFrame(data_right.items(), columns=["Métrique", "Valeur"])
                df_right["Valeur"] = df_right["Valeur"].astype(str)
                st.table(df_right)

        # Section 2 : Parametres de Valorisation
        with st.container(border=True):
            st.markdown("**Parametres du Modele**")

            params_data = {
                "Années de projection": p.projection_years,
                "Taux sans risque (Rf)": f"{p.rates.risk_free_rate:.2%}" if p.rates.risk_free_rate else "Auto",
                "Prime de risque marché": f"{p.rates.market_risk_premium:.2%}" if p.rates.market_risk_premium else "Auto",
                "Croissance Phase 1": f"{p.growth.fcf_growth_rate:.2%}" if p.growth.fcf_growth_rate else "Auto",
                "Croissance perpétuelle (g)": f"{p.growth.perpetual_growth_rate:.2%}" if p.growth.perpetual_growth_rate else "Auto",
            }

            df_params = pd.DataFrame(params_data.items(), columns=["Paramètre", "Valeur"])
            df_params["Valeur"] = df_params["Valeur"].astype(str)
            st.table(df_params)
    
    @staticmethod
    def _format_number(value: float) -> str:
        """Formate un nombre en notation lisible."""
        if value is None:
            return "—"
        abs_val = abs(value)
        if abs_val >= 1e12:
            return f"{value/1e12:,.1f} T"
        if abs_val >= 1e9:
            return f"{value/1e9:,.1f} B"
        if abs_val >= 1e6:
            return f"{value/1e6:,.1f} M"
        return f"{value:,.0f}"
