"""
app/ui/results/components/kpi_cards.py
Organisme gérant l'affichage des résultats de valorisation.
Note : Version institutionnelle épurée.
"""

import streamlit as st
from src.models import ValuationResult
from src.i18n import KPITexts, TooltipsTexts
from src.utilities.formatting import format_smart_number
from app.ui.components.ui_kpis import atom_kpi_metric

def render_valuation_summary_cards(result: ValuationResult):
    """Affiche le bandeau supérieur des KPIs de valorisation (4 colonnes)."""
    cols = st.columns(4)

    with cols[0]:
        # Switch dynamique entre WACC (Entité) et Ke (Actionnaire)
        label = KPITexts.WACC_LABEL if result.is_entity_approach else KPITexts.KE_LABEL
        help_t = TooltipsTexts.WACC_HELP if result.is_entity_approach else TooltipsTexts.KE_HELP
        atom_kpi_metric(
            label=label,
            value=format_smart_number(result.discount_rate, is_pct=True),
            help_text=help_t
        )

    with cols[1]:
        atom_kpi_metric(
            label=KPITexts.GROWTH_G_LABEL,
            value=format_smart_number(result.terminal_growth_rate, is_pct=True),
            help_text=TooltipsTexts.GROWTH_G
        )

    with cols[2]:
        atom_kpi_metric(
            label=KPITexts.MARKET_CAP_LABEL,
            value=format_smart_number(result.market_cap, currency=result.currency),
            help_text="Capitalisation boursière à la date d'analyse."
        )

    with cols[3]:
        # Marge de sécurité avec indicateur de sens (normal/inverse)
        upside = result.upside
        atom_kpi_metric(
            label=KPITexts.MARGIN_SAFETY_LABEL,
            value=format_smart_number(upside, is_pct=True),
            delta=format_smart_number(upside, is_pct=True),
            delta_color="normal" if upside > 0 else "inverse",
            help_text=KPITexts.HELP_MOS
        )

def render_instrument_details(result: ValuationResult):
    """
    Affiche les détails de la valeur intrinsèque (Equity Value & Price Per Share).
    Utilisé dans le résumé exécutif pour la section 'Prix vs Valeur'.
    """
    with st.container(border=True):
        col_equity, col_price = st.columns(2)

        with col_equity:
            # Valeur totale des fonds propres
            atom_kpi_metric(
                label=KPITexts.EQUITY_VALUE_LABEL,
                value=format_smart_number(result.equity_value, currency=result.currency),
                help_text=None
            )

        with col_price:
            # Valeur intrinsèque par action (Le "Cours Cible" théorique)
            atom_kpi_metric(
                label=KPITexts.INTRINSIC_PRICE_LABEL,
                value=format_smart_number(result.intrinsic_price, currency=result.currency),
                help_text=KPITexts.HELP_IV
            )