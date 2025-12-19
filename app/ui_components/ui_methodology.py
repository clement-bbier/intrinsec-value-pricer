"""
ui_methodology.py

Documentation méthodologique — Chapitre 6
Audit comme méthode normalisée et explicable.

Objectifs :
- Expliquer la logique de valorisation (DCF, Graham, Monte Carlo)
- Expliquer le rôle du Confidence Score
- Formaliser les piliers d’incertitude
- Aligner la restitution avec les standards CFA / institutions
"""

import streamlit as st
from core.models import CompanyFinancials, DCFParameters
from core.methodology.texts import (
    SIMPLE_DCF_TITLE, SIMPLE_DCF_SECTIONS,
    FUNDAMENTAL_DCF_TITLE, FUNDAMENTAL_DCF_SECTIONS,
    MONTE_CARLO_TITLE, MONTE_CARLO_SECTIONS,
)


# ==============================================================================
# OUTILS DE RENDU
# ==============================================================================

def _render_sections(sections) -> None:
    for section in sections:
        if section.get("subtitle"):
            st.markdown(section["subtitle"])
        for md in section.get("markdown_blocks", []):
            st.markdown(md)
        for latex in section.get("latex_blocks", []):
            st.latex(latex)


def _render_live_wacc_check(financials: CompanyFinancials, params: DCFParameters) -> None:
    """
    Vérification pédagogique et traçable du calcul du WACC.
    """
    with st.expander("🔍 Vérification détaillée du calcul du WACC", expanded=False):
        if params.manual_cost_of_equity is not None:
            ke = params.manual_cost_of_equity
            source_ke = "Manuel (Expert)"
            formula_ke = f"{ke:.2%}"
        else:
            ke = params.risk_free_rate + financials.beta * params.market_risk_premium
            source_ke = "CAPM"
            formula_ke = (
                f"{params.risk_free_rate:.2%} + "
                f"{financials.beta:.2f} × {params.market_risk_premium:.2%}"
            )

        kd_net = params.cost_of_debt * (1 - params.tax_rate)
        we, wd = params.target_equity_weight, params.target_debt_weight
        wacc = params.wacc_override if params.wacc_override else (we * ke + wd * kd_net)

        st.markdown(f"""
        ### 1️⃣ Coût des fonds propres ($K_e$) — *{source_ke}*
        $$ K_e = {formula_ke} = \\mathbf{{{ke:.2%}}} $$

        ### 2️⃣ Coût de la dette après impôt ($K_d$)
        $$ K_d = {params.cost_of_debt:.2%} × (1 - {params.tax_rate:.0%})
        = \\mathbf{{{kd_net:.2%}}} $$

        ### 3️⃣ Coût moyen pondéré du capital (WACC)
        $$ WACC = ({we:.0%} × K_e) + ({wd:.0%} × K_d)
        = \\mathbf{{{wacc:.2%}}} $$
        """)


# ==============================================================================
# 1. MÉTHODOLOGIE DE VALORISATION
# ==============================================================================

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


# ==============================================================================
# 2. MÉTHODOLOGIE D’AUDIT — CHAPITRE 6
# ==============================================================================

def display_audit_methodology() -> None:
    """
    Présentation institutionnelle du Confidence Score.
    """

    st.header("🛡️ Audit & Score de Confiance — Méthode Normalisée")

    st.markdown("""
    Le **Confidence Score** est un indicateur synthétique visant à mesurer
    le **niveau d’incertitude** associé à une valorisation financière.

    Il **ne remet pas en cause la valeur intrinsèque calculée**,
    mais permet d’en apprécier la **robustesse**, conformément aux pratiques
    de gouvernance des modèles utilisées par les institutions financières.
    """)

    st.markdown("### 🔢 Formule du score")

    st.latex(r"""
    \text{Confidence Score}
    = \sum_{i=1}^{4} w_i \times S_i
    \quad \text{avec} \quad \sum w_i = 1
    """)

    st.markdown("""
    où chaque $S_i$ représente le score d’un **pilier d’incertitude**,
    pondéré par un poids $w_i$ dépendant du **mode d’utilisation**
    (AUTO ou EXPERT).
    """)

    st.markdown("### 🧱 Piliers d’incertitude")

    st.markdown("""
    **1️⃣ Data Confidence**  
    Qualité, cohérence et fiabilité des données d’entrée
    (sources, proxies, données reconstruites).

    **2️⃣ Assumption Risk**  
    Sensibilité du résultat aux hypothèses clés
    (croissance, WACC, marges, volatilité).

    **3️⃣ Model Risk**  
    Risque inhérent au modèle utilisé
    (dépendance à la valeur terminale, extrapolation, heuristique).

    **4️⃣ Method Fit**  
    Adéquation entre la méthode de valorisation et le profil économique
    de l’entreprise analysée.
    """)

    st.markdown("### ⚖️ Différence AUTO vs EXPERT")

    st.markdown("""
    - **Mode AUTO**  
      Hypothèses normatives, proxies autorisés.  
      Le score est **pénalisant et conservateur**.

    - **Mode EXPERT**  
      Hypothèses fournies par l’utilisateur.  
      La **responsabilité est transférée** : la qualité des données est
      informative, mais les incohérences économiques restent bloquantes.
    """)

    st.markdown("""
    > 📌 Le Confidence Score est **auditable**, **traçable** et
    **réplicable**, au même titre que le calcul de la valeur intrinsèque.
    """)

