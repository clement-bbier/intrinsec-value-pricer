"""
app/ui/results/core/inputs_summary.py
ONGLET — CONFIGURATION & HYPOTHÈSES (Pillier 1)
Rôle : Transparence totale sur les données financières et paramètres modèles.
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult, ValuationMode
from src.i18n import (
    KPITexts,
    DDMTexts,
    RegistryTexts,
    AuditTexts
)
from src.utilities.formatting import format_smart_number
from app.ui.results.base_result import ResultTabBase

class InputsSummaryTab(ResultTabBase):
    """
    Pillier 1 : Inventaire exhaustif des données.
    Layout : FactSheet Institutionnelle réactive au modèle.
    """

    TAB_ID = "inputs_summary"
    LABEL = KPITexts.TAB_INPUTS
    ORDER = 1
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """Rendu de la fiche de diligence financière avec injection i18n intégrale."""
        f = result.financials
        p = result.params
        mode = result.request.mode if result.request else None

        st.markdown(f"### {KPITexts.SECTION_INPUTS_HEADER}")
        st.caption(KPITexts.SECTION_INPUTS_CAPTION)
        st.write("")

        # --- 1. IDENTITÉ & STRUCTURE DE MARCHÉ ---
        with st.container(border=True):
            st.markdown(f"**{KPITexts.SEC_A_IDENTITY}**")
            c1, c2, c3 = st.columns(3)
            with c1:
                self._render_kv(KPITexts.LABEL_NAME, f.name)
                self._render_kv(KPITexts.LABEL_TICKER, f.ticker)
            with c2:
                self._render_kv(KPITexts.LABEL_SECTOR, f.sector)
                self._render_kv(KPITexts.LABEL_COUNTRY, f.country)
            with c3:
                self._render_kv(KPITexts.LABEL_CURRENCY, f.currency)
                self._render_kv(KPITexts.LABEL_SHARES, format_smart_number(f.shares_outstanding))

        # --- 2. PERFORMANCE OPÉRATIONNELLE (TTM) ---
        st.write("")
        with st.container(border=True):
            st.markdown(f"**{KPITexts.SUB_PERF}**")
            c1, c2, c3, c4 = st.columns(4)
            with c1: self._render_kv(KPITexts.LABEL_REV, format_smart_number(f.revenue_ttm, currency=f.currency))
            with c2: self._render_kv(KPITexts.LABEL_EBIT, format_smart_number(f.ebit_ttm, currency=f.currency))
            with c3: self._render_kv(KPITexts.LABEL_NI, format_smart_number(f.net_income_ttm, currency=f.currency))
            with c4: self._render_kv(KPITexts.LABEL_EPS, f"{f.eps_ttm:.2f} {f.currency}")

            st.divider()

            # Réactivité de la section Flux/Distribution (Zéro str)
            if mode == ValuationMode.DDM:
                st.caption(RegistryTexts.DDM_GROWTH_L)
                c1, c2, c3 = st.columns(3)
                div_total = f.dividend_share * f.shares_outstanding if f.dividend_share else 0
                with c1: self._render_kv(DDMTexts.INP_DIVIDEND_BASE, f"{f.dividend_share:.2f} {f.currency}")
                with c2: self._render_kv(RegistryTexts.DDM_BASE_L, format_smart_number(div_total, currency=f.currency))
            else:
                st.caption(KPITexts.SUB_CASH)
                c1, c2, c3 = st.columns(3)
                with c1: self._render_kv(KPITexts.LABEL_FCF_LAST, format_smart_number(f.fcf, currency=f.currency))
                with c2: self._render_kv(KPITexts.LABEL_CAPEX, format_smart_number(f.capex, currency=f.currency))
                with c3: self._render_kv(KPITexts.LABEL_DA, format_smart_number(f.depreciation_and_amortization, currency=f.currency))

        # --- 3. STRUCTURE DU CAPITAL (DETTE, CASH & BOOK VALUE) ---
        st.write("")
        with st.container(border=True):
            st.markdown(f"**{KPITexts.SUB_CAPITAL}**")
            c1, c2, c3 = st.columns(3)
            with c1:
                self._render_kv(KPITexts.LABEL_CASH, format_smart_number(f.cash_and_equivalents, currency=f.currency))
                self._render_kv(KPITexts.LABEL_DEBT, format_smart_number(f.total_debt, currency=f.currency))
            with c2:
                # Mise en avant de la Book Value pour modèles bilanciels
                bv_prefix = ":blue" if mode in [ValuationMode.RIM, ValuationMode.GRAHAM] else ""
                self._render_kv(f"{bv_prefix}[{KPITexts.LABEL_BVPS}]", f"{f.book_value_per_share:.2f} {f.currency}")
                self._render_kv(KPITexts.LABEL_MINORITIES, format_smart_number(f.minority_interests, currency=f.currency))
            with c3:
                # Utilisation des constantes de couleur d'audit
                net_debt_color = AuditTexts.COLOR_WARNING if f.net_debt > 0 else AuditTexts.COLOR_SUCCESS
                self._render_kv(f"{net_debt_color}[{KPITexts.LABEL_NET_DEBT}]", format_smart_number(f.net_debt, currency=f.currency))
                self._render_kv(KPITexts.LABEL_PENSIONS, format_smart_number(f.pension_provisions, currency=f.currency))

        # --- 4. PARAMÈTRES DU MODÈLE (RATES & GROWTH) ---
        st.write("")
        with st.container(border=True):
            st.markdown(f"**{KPITexts.SEC_C_MODEL}**")
            c1, c2 = st.columns(2)

            with c1:
                st.caption(KPITexts.SUB_RATES)
                self._render_kv(KPITexts.LABEL_RF, f"{p.rates.risk_free_rate:.2%}")
                self._render_kv(KPITexts.LABEL_BETA, f"{p.rates.manual_beta or f.beta:.2f}")
                self._render_kv(KPITexts.LABEL_MRP, f"{p.rates.market_risk_premium:.2%}")

                if mode == ValuationMode.GRAHAM:
                    self._render_kv(f"{AuditTexts.COLOR_WARNING}[{KPITexts.LABEL_AAA_YIELD}]", f"{p.growth.exit_multiple_value:.2%}")

            with c2:
                st.caption(KPITexts.SUB_GROWTH)
                self._render_kv(KPITexts.LABEL_G, f"{p.growth.fcf_growth_rate:.2%}")
                self._render_kv(KPITexts.LABEL_GN, f"{p.growth.perpetual_growth_rate:.2%}")

                if mode == ValuationMode.RIM:
                    self._render_kv(f"{AuditTexts.COLOR_WARNING}[{KPITexts.LABEL_OMEGA}]", f"{p.growth.exit_multiple_value:.2f}")

                # Dilution SBC (Utilisation systématique du label i18n)
                sbc_val = p.growth.annual_dilution_rate
                sbc_color = AuditTexts.COLOR_WARNING if sbc_val > 0 else ""
                self._render_kv(f"{sbc_color}[{KPITexts.LABEL_SBC_RATE}]", f"{sbc_val:.2%}")

    @staticmethod
    def _render_kv(label: str, value: Any) -> None:
        """Rendu d'une ligne Clé-Valeur épurée (Méthode statique)."""
        col_l, col_v = st.columns([0.65, 0.35])
        col_l.markdown(f"<span style='color: #64748b; font-size: 0.85rem;'>{label}</span>", unsafe_allow_html=True)
        col_v.markdown(f"<div style='text-align: right; font-weight: 600; font-size: 0.9rem;'>{value if value is not None else '—'}</div>", unsafe_allow_html=True)