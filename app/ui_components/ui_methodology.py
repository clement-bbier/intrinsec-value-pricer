import streamlit as st
import pandas as pd
from core.models import CompanyFinancials, DCFParameters, InputSource
# Import complet des textes centralisés
from core.methodology.texts import (
    SIMPLE_DCF_TITLE, SIMPLE_DCF_SECTIONS,
    FUNDAMENTAL_DCF_TITLE, FUNDAMENTAL_DCF_SECTIONS,
    MONTE_CARLO_TITLE, MONTE_CARLO_SECTIONS,
    AUDIT_TITLE, AUDIT_INTRO, AUDIT_AUTO_BLOCKS, AUDIT_MANUAL_BLOCKS
)


# --- HELPER D'AFFICHAGE ---

def _render_sections(sections) -> None:
    """Affiche les blocs de texte statiques (Générique)."""
    for section in sections:
        if section.get("subtitle"):
            st.markdown(section.get("subtitle"))
        for md in section.get("markdown_blocks", []):
            st.markdown(md)
        for latex in section.get("latex_blocks", []):
            st.latex(latex)


def _render_live_wacc_check(f: CompanyFinancials, p: DCFParameters):
    """
    Affiche le détail du calcul du WACC avec les VRAIS chiffres.
    """
    with st.expander("Vérifier le calcul du WACC (Vos Chiffres)", expanded=False):
        # Détection des poids
        if p.target_equity_weight > 0:
            we, wd = p.target_equity_weight, p.target_debt_weight
            source_w = "Cibles (Expert)"
        else:
            mcap = f.current_price * f.shares_outstanding
            total = mcap + f.total_debt
            we = mcap / total if total > 0 else 1.0
            wd = f.total_debt / total if total > 0 else 0.0
            source_w = "Marché (Auto)"

        # Détection du Ke
        if p.manual_cost_of_equity is not None:
            ke = p.manual_cost_of_equity
            ke_formula = f"{ke:.1%}"
            source_ke = "Manuel"
        else:
            ke = p.risk_free_rate + f.beta * p.market_risk_premium
            ke_formula = f"{p.risk_free_rate:.1%} + {f.beta:.2f} \\times {p.market_risk_premium:.1%}"
            source_ke = "CAPM"

        kd_net = p.cost_of_debt * (1 - p.tax_rate)

        st.markdown(f"""
        **1. Coût de l'Equity ($K_e$) - Source: {source_ke}**
        $$ K_e = {ke_formula} = \\mathbf{{{ke:.2%}}} $$

        **2. Coût de la Dette Net ($K_d$)**
        $$ K_d (net) = {p.cost_of_debt:.1%} \\times (1 - {p.tax_rate:.0%}) = \\mathbf{{{kd_net:.2%}}} $$

        **3. Pondérations - Source: {source_w}**
        $$ E\% = {we:.1%} \\quad | \\quad D\% = {wd:.1%} $$

        **4. WACC Final**
        $$ WACC = ({we:.1%} \\times {ke:.1%}) + ({wd:.1%} \\times {kd_net:.1%}) $$
        """)


def _render_expert_inputs_summary(p: DCFParameters):
    """Affiche un récapitulatif des inputs manuels."""
    st.info(
        "**Mode Expert Actif** : Les valeurs ci-dessous ont été forcées manuellement.\n\n"
        f"- **Croissance (g)** : {p.fcf_growth_rate:.1%} (puis fade vers {p.perpetual_growth_rate:.1%})\n"
        f"- **Risque (WACC)** : Cible Equity {p.target_equity_weight:.0%} / Dette {p.target_debt_weight:.0%}"
    )


# --- FONCTIONS PRINCIPALES (VUES) ---

def display_simple_dcf_formula(financials: CompanyFinancials, params: DCFParameters) -> None:
    """Vue Méthode 1."""
    st.markdown(SIMPLE_DCF_TITLE)
    if params.manual_fcf_base:
        st.warning(f"Note : FCF de base surchargé manuellement à {params.manual_fcf_base:,.0f}")
    _render_sections(SIMPLE_DCF_SECTIONS)
    _render_live_wacc_check(financials, params)


def display_fundamental_dcf_formula(financials: CompanyFinancials, params: DCFParameters) -> None:
    """Vue Méthode 2."""
    st.markdown(FUNDAMENTAL_DCF_TITLE)

    if params.target_equity_weight > 0 or params.manual_cost_of_equity is not None:
        _render_expert_inputs_summary(params)

    _render_sections(FUNDAMENTAL_DCF_SECTIONS)

    with st.expander("Détail du FCFF Normatif (Point de départ)", expanded=False):
        st.write("Le FCFF utilisé est une moyenne pondérée des 5 dernières années (si disponible).")
        st.metric("FCFF Retenu ($FCFF_0$)", f"{financials.fcf_fundamental_smoothed:,.0f} {financials.currency}")

    _render_live_wacc_check(financials, params)


def display_monte_carlo_formula(financials: CompanyFinancials, params: DCFParameters) -> None:
    """Vue Méthode 3."""
    st.markdown(MONTE_CARLO_TITLE)
    _render_sections(MONTE_CARLO_SECTIONS)

    st.markdown("#### 4. Vos Paramètres de Simulation")
    st.markdown(f"""
    La simulation utilise vos inputs comme pivots centraux :
    * **Pivot Beta** : {financials.beta:.2f} (Volatilité $\sigma=${params.beta_volatility:.1%})
    * **Pivot Croissance** : {params.fcf_growth_rate:.1%} (Volatilité $\sigma=${params.growth_volatility:.1%})
    """)
    _render_live_wacc_check(financials, params)


def display_audit_methodology():
    """Vue Audit (Alimentée par texts.py)."""
    st.markdown(AUDIT_TITLE)
    st.info(AUDIT_INTRO)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Mode Automatique")
        for block in AUDIT_AUTO_BLOCKS:
            st.markdown(block)

    with c2:
        st.markdown("#### Mode Manuel (Expert)")
        for block in AUDIT_MANUAL_BLOCKS:
            st.markdown(block)