"""
ui_methodology.py

MÉTHODOLOGIE, GOUVERNANCE & AUDIT — RAPPORT D’ANALYSTE
Version : V2.2 — Glass-Box UI / UX institutionnelle

Rôle :
- Exposer la méthode de valorisation utilisée
- Rendre explicites les hypothèses et formules
- Expliquer le raisonnement économique
- Présenter l’audit et le Confidence Score
- Garantir l’alignement strict UI ↔ moteur ↔ documentation

Principes :
- Pédagogie institutionnelle (CFA / Buy-Side)
- Lecture descendante : concept → formule → chiffre
- Aucune décoration gratuite, uniquement du sens
- Aucune information implicite
"""

from __future__ import annotations

import streamlit as st
from typing import Iterable, Optional

from core.models import CompanyFinancials, DCFParameters, ValuationResult
from app.ui_components.ui_charts import (
    display_simulation_chart,
    display_correlation_heatmap
)
from core.methodology.texts import (
    DCF_STANDARD_TITLE,
    DCF_STANDARD_SECTIONS,
    DCF_FUNDAMENTAL_TITLE,
    DCF_FUNDAMENTAL_SECTIONS,
    MONTE_CARLO_TITLE,
    MONTE_CARLO_SECTIONS,
)

# ==============================================================================
# OUTILS UI — BLOCS MÉTHODOLOGIQUES
# ==============================================================================

def _render_sections(sections: Iterable[dict]) -> None:
    """
    Rendu standardisé de blocs méthodologiques.

    Structure attendue par section :
    - subtitle (str | optional)
    - markdown_blocks (list[str])
    - latex_blocks (list[str])
    """

    for section in sections:
        if section.get("subtitle"):
            st.markdown(f"### {section['subtitle']}")

        for md in section.get("markdown_blocks", []):
            st.markdown(md)

        for latex in section.get("latex_blocks", []):
            st.latex(latex)


def _render_method_context(
    title: str,
    description: str,
    use_cases: list[str],
    limits: list[str],
) -> None:
    """
    Bloc UX standardisé : cadre conceptuel de la méthode.
    """

    st.subheader(title)

    st.markdown(description)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🎯 Cas d’usage typiques**")
        for uc in use_cases:
            st.markdown(f"- {uc}")

    with col2:
        st.markdown("**⚠️ Limites structurelles**")
        for lim in limits:
            st.markdown(f"- {lim}")

    st.divider()


def _render_live_wacc_check(
    financials: CompanyFinancials,
    params: DCFParameters
) -> None:
    """
    Vérification traçable et pédagogique du calcul du WACC.
    """

    with st.expander("🔍 Vérification détaillée du calcul du WACC", expanded=False):

        # --- Coût des fonds propres ---
        if params.manual_cost_of_equity is not None:
            ke = params.manual_cost_of_equity
            source_ke = "Manuel (Mode EXPERT)"
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

        wacc = (
            params.wacc_override
            if params.wacc_override is not None
            else (we * ke + wd * kd_net)
        )

        st.markdown(f"""
        **1️⃣ Coût des fonds propres ($K_e$)**  
        Source : *{source_ke}*

        $$ K_e = {formula_ke} = \\mathbf{{{ke:.2%}}} $$

        **2️⃣ Coût de la dette après impôt ($K_d$)**

        $$ K_d = {params.cost_of_debt:.2%} \\times (1 - {params.tax_rate:.0%})
        = \\mathbf{{{kd_net:.2%}}} $$

        **3️⃣ Coût moyen pondéré du capital (WACC)**

        $$ WACC = ({we:.0%} \\times K_e) + ({wd:.0%} \\times K_d)
        = \\mathbf{{{wacc:.2%}}} $$
        """)

# ==============================================================================
# MÉTHODES DE VALORISATION — UI / UX COMPLÈTE
# ==============================================================================

def display_standard_dcf_formula(
    financials: CompanyFinancials,
    params: DCFParameters
) -> None:
    """
    DCF Standard — FCFF Two-Stage
    """

    _render_method_context(
        title="DCF Standard — FCFF Two-Stage",
        description="""
        Cette méthode estime la valeur intrinsèque en projetant directement
        les **Free Cash Flows to Firm (FCFF)**, suivis d’une valeur terminale
        basée sur une croissance perpétuelle prudente.
        """,
        use_cases=[
            "Entreprises matures",
            "Cash-flows stables et prévisibles",
            "Secteurs peu cycliques",
        ],
        limits=[
            "Sensibilité élevée à la valeur terminale",
            "Peu adaptée aux sociétés en hypercroissance",
        ],
    )

    st.markdown(DCF_STANDARD_TITLE)
    _render_sections(DCF_STANDARD_SECTIONS)
    _render_live_wacc_check(financials, params)


def display_fundamental_dcf_formula(
    financials: CompanyFinancials,
    params: DCFParameters
) -> None:
    """
    DCF Fondamental — FCFF reconstruit
    """

    _render_method_context(
        title="DCF Fondamental — FCFF reconstruit",
        description="""
        Cette méthode reconstruit les flux économiques à partir de l’EBIT,
        afin d’obtenir un **FCFF normalisé**, plus robuste pour les
        entreprises cycliques ou industrielles.
        """,
        use_cases=[
            "Entreprises industrielles",
            "Secteurs cycliques",
            "Analyse de long terme",
        ],
        limits=[
            "Dépend fortement de la qualité des données comptables",
            "Plus complexe à paramétrer",
        ],
    )

    st.markdown(DCF_FUNDAMENTAL_TITLE)
    _render_sections(DCF_FUNDAMENTAL_SECTIONS)
    _render_live_wacc_check(financials, params)

def display_monte_carlo_formula(financials: CompanyFinancials, params: DCFParameters) -> None:
    """Explique la théorie pure du Monte Carlo sans afficher les résultats live."""
    _render_method_context(
        title="Extension Monte Carlo — Analyse probabiliste",
        description="Le Monte Carlo est une extension probabiliste appliquée aux hypothèses...",
        use_cases=["Analyse du risque", "Intervalle de confiance"],
        limits=["Sensibilité aux lois", "Ne corrige pas un mauvais modèle"]
    )
    st.markdown(MONTE_CARLO_TITLE)
    _render_sections(MONTE_CARLO_SECTIONS)

# ==============================================================================
# AUDIT & CONFIDENCE SCORE — UX INSTITUTIONNELLE
# ==============================================================================

def display_audit_methodology() -> None:
    """
    Présentation institutionnelle de l’audit et du Confidence Score.
    """

    st.header("🛡️ Audit & Score de Confiance")

    st.markdown("""
    Le **Confidence Score** mesure la **robustesse économique**
    d’une valorisation, et non son potentiel de performance.
    Il est conçu comme un **outil de gouvernance des modèles**.
    """)

    st.subheader("🔢 Formule du score")

    st.latex(r"""
    \text{Confidence Score}
    = \sum_{i=1}^{4} w_i \times S_i
    \quad \text{avec} \quad \sum w_i = 1
    """)

    st.subheader("🧱 Piliers d’incertitude")

    st.markdown("""
    - **Data Confidence** : qualité et fiabilité des données
    - **Assumption Risk** : sensibilité aux hypothèses
    - **Model Risk** : structure mathématique du modèle
    - **Method Fit** : adéquation méthode / entreprise
    """)

    st.subheader("⚖️ Responsabilité AUTO vs EXPERT")

    st.markdown("""
    **Mode AUTO**
    - Hypothèses normatives
    - Responsabilité portée par le moteur
    - Score conservateur

    **Mode EXPERT**
    - Hypothèses utilisateur
    - Responsabilité explicitement transférée
    - Les incohérences économiques restent bloquantes
    """)

    st.info(
        "Le Confidence Score est **auditable**, **traçable** et "
        "**réplicable**, au même titre que le calcul de la valeur intrinsèque."
    )
