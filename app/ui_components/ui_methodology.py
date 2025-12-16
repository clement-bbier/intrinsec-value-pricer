import streamlit as st
from core.models import CompanyFinancials, DCFParameters
from core.methodology.texts import (
    SIMPLE_DCF_TITLE, SIMPLE_DCF_SECTIONS,
    FUNDAMENTAL_DCF_TITLE, FUNDAMENTAL_DCF_SECTIONS,
    MONTE_CARLO_TITLE, MONTE_CARLO_SECTIONS,
    AUDIT_TITLE, AUDIT_INTRO
)


def _render_sections(sections) -> None:
    for section in sections:
        if section.get("subtitle"):
            st.markdown(section.get("subtitle"))
        for md in section.get("markdown_blocks", []):
            st.markdown(md)
        for latex in section.get("latex_blocks", []):
            st.latex(latex)


def _render_live_wacc_check(f: CompanyFinancials, p: DCFParameters):
    with st.expander("Vérifier le calcul du WACC (Données Réelles)", expanded=False):
        if p.manual_cost_of_equity is not None:
            ke = p.manual_cost_of_equity
            source_ke = "Manuel"
            formula_ke = f"{ke:.1%}"
        else:
            ke = p.risk_free_rate + f.beta * p.market_risk_premium
            source_ke = "CAPM"
            formula_ke = f"{p.risk_free_rate:.1%} + {f.beta:.2f} \\times {p.market_risk_premium:.1%}"

        kd_net = p.cost_of_debt * (1 - p.tax_rate)
        we, wd = p.target_equity_weight, p.target_debt_weight

        st.markdown(f"""
        **1. Coût de l'Equity ($K_e$) [{source_ke}]**
        $$ K_e = {formula_ke} = \\mathbf{{{ke:.2%}}} $$

        **2. Coût de la Dette Net ($K_d$)**
        $$ K_d (net) = {p.cost_of_debt:.1%} \\times (1 - {p.tax_rate:.0%}) = \\mathbf{{{kd_net:.2%}}} $$

        **3. WACC**
        $$ WACC = ({we:.1%} \\times K_e) + ({wd:.1%} \\times K_d) = \\mathbf{{{p.wacc_override if p.wacc_override else (we * ke + wd * kd_net):.2%}}} $$
        """)


def display_simple_dcf_formula(financials: CompanyFinancials, params: DCFParameters) -> None:
    st.markdown(SIMPLE_DCF_TITLE)
    _render_sections(SIMPLE_DCF_SECTIONS)
    _render_live_wacc_check(financials, params)


def display_fundamental_dcf_formula(financials: CompanyFinancials, params: DCFParameters) -> None:
    st.markdown(FUNDAMENTAL_DCF_TITLE)
    _render_sections(FUNDAMENTAL_DCF_SECTIONS)
    _render_live_wacc_check(financials, params)


def display_monte_carlo_formula(financials: CompanyFinancials, params: DCFParameters) -> None:
    st.markdown(MONTE_CARLO_TITLE)
    _render_sections(MONTE_CARLO_SECTIONS)
    _render_live_wacc_check(financials, params)