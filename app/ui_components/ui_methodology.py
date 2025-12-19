"""
ui_methodology.py

MÉTHODOLOGIE & GOUVERNANCE — RAPPORT D’ANALYSTE
Version : V2.0 — Chapitres 6, 7 & 8 conformes

Rôle :
- Exposer la méthode de valorisation utilisée
- Justifier les hypothèses et cadres théoriques
- Expliciter l’audit et le Confidence Score
- Garantir l’alignement strict UI ↔ moteur

Principes :
- Pédagogie institutionnelle (CFA / Buy-Side)
- Zéro décoratif, 100 % explicatif
- Aucun texte sans ancrage méthodologique réel
"""

from __future__ import annotations

import streamlit as st
from typing import Iterable

from core.models import CompanyFinancials, DCFParameters
from core.methodology.texts import (
    SIMPLE_DCF_TITLE, SIMPLE_DCF_SECTIONS,
    FUNDAMENTAL_DCF_TITLE, FUNDAMENTAL_DCF_SECTIONS,
    MONTE_CARLO_TITLE, MONTE_CARLO_SECTIONS,
)


# ==============================================================================
# OUTILS DE RENDU — BLOCS MÉTHODOLOGIQUES
# ==============================================================================

def _render_sections(sections: Iterable[dict]) -> None:
    """
    Rendu standardisé de sections méthodologiques.

    Chaque section est une structure éditoriale contrôlée :
    - subtitle (optionnel)
    - markdown_blocks
    - latex_blocks
    """
    for section in sections:
        if section.get("subtitle"):
            st.markdown(section["subtitle"])

        for md in section.get("markdown_blocks", []):
            st.markdown(md)

        for latex in section.get("latex_blocks", []):
            st.latex(latex)


def _render_live_wacc_check(
    financials: CompanyFinancials,
    params: DCFParameters
) -> None:
    """
    Vérification traçable et pédagogique du calcul du WACC.

    Objectif :
    - démontrer la cohérence du coût du capital
    - rendre le calcul auditable en lecture seule
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

        # --- Coût de la dette après impôt ---
        kd_net = params.cost_of_debt * (1 - params.tax_rate)

        # --- Pondérations ---
        we, wd = params.target_equity_weight, params.target_debt_weight

        # --- WACC ---
        wacc = (
            params.wacc_override
            if params.wacc_override is not None
            else (we * ke + wd * kd_net)
        )

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
# 1. MÉTHODOLOGIES DE VALORISATION
# ==============================================================================

def display_simple_dcf_formula(
    financials: CompanyFinancials,
    params: DCFParameters
) -> None:
    """
    Méthode DCF Standard (FCFF Two-Stage).

    Usage :
    - entreprises matures
    - cash-flows relativement stables
    """
    st.markdown(SIMPLE_DCF_TITLE)
    _render_sections(SIMPLE_DCF_SECTIONS)
    _render_live_wacc_check(financials, params)


def display_fundamental_dcf_formula(
    financials: CompanyFinancials,
    params: DCFParameters
) -> None:
    """
    Méthode DCF Fondamentale (FCFF normalisé).

    Usage :
    - entreprises cycliques
    - lissage des flux économiques
    """
    st.markdown(FUNDAMENTAL_DCF_TITLE)
    _render_sections(FUNDAMENTAL_DCF_SECTIONS)
    _render_live_wacc_check(financials, params)


def display_monte_carlo_formula(
    financials: CompanyFinancials,
    params: DCFParameters
) -> None:
    """
    Extension Monte Carlo (Chapitre 7).

    Rappel normatif :
    - Monte Carlo ≠ méthode de valorisation
    - extension probabiliste des hypothèses uniquement
    """
    st.markdown(MONTE_CARLO_TITLE)
    _render_sections(MONTE_CARLO_SECTIONS)
    _render_live_wacc_check(financials, params)


# ==============================================================================
# 2. AUDIT & CONFIDENCE SCORE — CHAPITRE 6
# ==============================================================================

def display_audit_methodology() -> None:
    """
    Présentation institutionnelle de l’audit et du Confidence Score.

    Cette section correspond à la partie :
    “Model Governance & Validation”
    d’un rapport professionnel.
    """

    st.header("🛡️ Audit & Score de Confiance — Méthode Normalisée")

    st.markdown("""
    Le **Confidence Score** est un indicateur synthétique visant à mesurer
    le **niveau d’incertitude** associé à une valorisation financière.

    Il **ne remet jamais en cause la valeur intrinsèque calculée**,
    mais permet d’en apprécier la **robustesse**, conformément aux
    pratiques de gouvernance des modèles utilisées par les institutions
    financières (banques, asset managers, buy-side).
    """)

    # ------------------------------------------------------------------
    # FORMULE DU SCORE
    # ------------------------------------------------------------------
    st.markdown("### 🔢 Formule du score")

    st.latex(r"""
    \text{Confidence Score}
    = \sum_{i=1}^{4} w_i \times S_i
    \quad \text{avec} \quad \sum w_i = 1
    """)

    st.markdown("""
    où chaque $S_i$ représente le score d’un **pilier d’incertitude**,
    pondéré par un poids $w_i$ dépendant du **mode d’utilisation**
    (**AUTO** ou **EXPERT**).
    """)

    # ------------------------------------------------------------------
    # PILIERS D’INCERTITUDE
    # ------------------------------------------------------------------
    st.markdown("### 🧱 Piliers d’incertitude")

    st.markdown("""
    **1️⃣ Data Confidence**  
    Qualité, cohérence et fiabilité des données d’entrée  
    (sources publiées, proxies, données reconstruites).

    **2️⃣ Assumption Risk**  
    Sensibilité du résultat aux hypothèses clés  
    (croissance, WACC, marges, volatilité).

    **3️⃣ Model Risk**  
    Risque inhérent au modèle utilisé  
    (poids de la valeur terminale, extrapolation, heuristique).

    **4️⃣ Method Fit**  
    Adéquation entre la méthode de valorisation
    et le profil économique de l’entreprise analysée.
    """)

    # ------------------------------------------------------------------
    # RESPONSABILITÉ AUTO VS EXPERT
    # ------------------------------------------------------------------
    st.markdown("### ⚖️ Différence entre les modes AUTO et EXPERT")

    st.markdown("""
    **Mode AUTO**  
    - Hypothèses normatives et prudentes  
    - Proxies autorisés  
    - Score **pénalisant et conservateur**  
    - Responsabilité portée par le système  

    **Mode EXPERT**  
    - Hypothèses fournies par l’utilisateur  
    - Responsabilité **explicitement transférée**  
    - Les incohérences économiques restent **bloquantes**
    """)

    st.markdown("""
    > 📌 Le Confidence Score est **auditable**, **traçable** et
    **réplicable**, au même titre que le calcul de la valeur intrinsèque.
    """)
