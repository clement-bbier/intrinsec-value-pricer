"""
app/ui/result_tabs/core/inputs_summary.py
Onglet — Récapitulatif des Hypothèses

Migration depuis ui_kpis.py._render_inputs_tab()
Affiche les données d'entrée utilisées pour le calcul avec la même structure.
"""

from typing import Any

import streamlit as st

from core.models import ValuationResult
from core.i18n import KPITexts
from app.ui.base import ResultTabBase
from app.ui.result_tabs.components.kpi_cards import format_smart_number


class InputsSummaryTab(ResultTabBase):
    """
    Onglet des hypothèses d'entrée.

    Migration exacte de _render_inputs_tab() depuis ui_kpis.py
    pour garantir l'identicité fonctionnelle.
    """

    TAB_ID = "inputs_summary"
    LABEL = "Hypotheses"
    ICON = ""
    ORDER = 1
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche les données d'entrée utilisées pour la valorisation.

        Suit exactement la même logique que _render_inputs_tab dans ui_kpis.py
        pour garantir la compatibilité.
        """
        f, p = result.financials, result.params

        st.markdown(f"**{KPITexts.SECTION_INPUTS_HEADER}**")
        st.caption(KPITexts.SECTION_INPUTS_CAPTION)

        # Section Identité (même structure que ui_kpis.py)
        with st.expander(KPITexts.SEC_A_IDENTITY.upper(), expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"**{KPITexts.LABEL_TICKER}**\n\n`{f.ticker}`")
            c2.markdown(f"**{KPITexts.LABEL_NAME}**\n\n`{f.name}`")
            c3.markdown(f"**{KPITexts.LABEL_SECTOR}**\n\n{f.sector or '—'}")
            c4.markdown(f"**{KPITexts.LABEL_COUNTRY}**\n\n{f.country or '—'}")

        # Section Financières (même structure que ui_kpis.py)
        with st.expander(KPITexts.SEC_B_FINANCIALS.upper(), expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(KPITexts.LABEL_PRICE, f"{f.current_price:,.2f} {f.currency}")
            c2.metric(KPITexts.LABEL_MCAP, format_smart_number(f.market_cap, f.currency))
            c3.metric(KPITexts.LABEL_REV, format_smart_number(f.revenue_ttm))
            c4.metric(KPITexts.LABEL_NI, format_smart_number(f.net_income_ttm))

        # Section Modèle (même logique que ui_kpis.py)
        with st.expander(KPITexts.SEC_C_MODEL.upper(), expanded=True):
            r, g = p.rates, p.growth
            is_direct_equity = result.request.mode.is_direct_equity if result.request else False

            if is_direct_equity:
                # Mode Equity Direct (Ke)
                c1, c2, c3 = st.columns(3)
                c1.metric(KPITexts.LABEL_RF, f"{r.risk_free_rate:.2%}" if r.risk_free_rate else "Auto")
                c2.metric(KPITexts.LABEL_BETA, f"{r.manual_beta:.2f}" if r.manual_beta else "Auto")
                c3.metric(KPITexts.LABEL_KE, f"{r.cost_of_equity:.2%}")
            else:
                # Mode Enterprise Value (WACC)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(KPITexts.LABEL_RF, f"{r.risk_free_rate:.2%}" if r.risk_free_rate else "Auto")
                c2.metric(KPITexts.LABEL_BETA, f"{r.manual_beta:.2f}" if r.manual_beta else "Auto")
                c3.metric(KPITexts.LABEL_MRP, f"{r.market_risk_premium:.2%}" if r.market_risk_premium else "Auto")
                c4.metric(KPITexts.LABEL_KD, f"{r.cost_of_debt:.2%}" if r.cost_of_debt else "Auto")

            # Paramètres de croissance
            c1, c2, c3 = st.columns(3)
            c1.metric(KPITexts.LABEL_GROWTH, f"{g.fcf_growth_rate:.2%}" if g.fcf_growth_rate else "Auto")
            c2.metric(KPITexts.LABEL_PERP_G, f"{g.perpetual_growth_rate:.2%}" if g.perpetual_growth_rate else "Auto")
            c3.metric(KPITexts.LABEL_EXIT_MULT, f"{p.terminal_value.exit_multiple_value:.1f}x" if p.terminal_value.exit_multiple_value else "Auto")
            
            params_data = {
                "Années de projection": p.projection_years,
                "Taux sans risque (Rf)": f"{p.rates.risk_free_rate:.2%}" if p.rates.risk_free_rate else "Auto",
                "Prime de risque marché": f"{p.rates.market_risk_premium:.2%}" if p.rates.market_risk_premium else "Auto",
                "Croissance Phase 1": f"{p.growth.fcf_growth_rate:.2%}" if p.growth.fcf_growth_rate else "Auto",
                "Croissance perpétuelle (g)": f"{p.growth.perpetual_growth_rate:.2%}" if p.growth.perpetual_growth_rate else "Auto",
            }
            
            st.table(pd.DataFrame(params_data.items(), columns=["Paramètre", "Valeur"]))
    
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
