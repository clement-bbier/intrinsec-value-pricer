"""
ui_kpis.py

Restitution utilisateur — Chapitre 6
Audit comme méthode normalisée et explicable.

Principes :
- Même niveau de transparence que la valeur intrinsèque
- Score de confiance = formule auditable
- Piliers visibles, pondérations visibles
- Diagnostics traçables
- Style institutionnel (CFA / Asset Management)
"""

from typing import Optional, Dict
import streamlit as st
import pandas as pd

from core.models import (
    ValuationResult,
    CalculationStep,
    AuditReport,
    AuditPillar,
    DCFValuationResult,
    RIMValuationResult,
    GrahamValuationResult
)


# ==============================================================================
# 1. KPI PRINCIPAUX — SYNTHÈSE EXÉCUTIVE
# ==============================================================================

def display_main_kpis(result: ValuationResult) -> None:
    """
    Bandeau exécutif : Valeur, Prix, Upside, Confidence Score.
    Comparable à un factsheet institutionnel.
    """

    f = result.financials
    currency = f.currency

    intrinsic = result.intrinsic_value_per_share
    market = result.market_price
    upside = result.upside_pct

    audit_score = None
    audit_rating = "N/A"
    if result.audit_report:
        audit_score = int(result.audit_report.global_score)
        audit_rating = result.audit_report.rating

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Valeur intrinsèque",
            f"{intrinsic:,.2f} {currency}",
            help="Estimation centrale issue du modèle de valorisation."
        )

    with c2:
        st.metric(
            "Prix de marché",
            f"{market:,.2f} {currency}",
            help="Dernier prix observé sur le marché."
        )

    with c3:
        if upside is not None:
            st.metric(
                "Potentiel (Upside)",
                f"{upside:+.1%}",
                delta=f"{upside:+.1%}",
                delta_color="normal" if upside >= 0 else "off",
                help="Écart relatif entre valeur intrinsèque et prix de marché."
            )
        else:
            st.metric("Potentiel", "N/A")

    with c4:
        if audit_score is not None:
            st.metric(
                "Confidence Score",
                f"{audit_score}/100",
                delta=audit_rating,
                delta_color="off",
                help=(
                    "Indicateur synthétique du niveau de confiance attaché à la valorisation. "
                    "Score agrégé à partir de piliers d’incertitude mesurés."
                )
            )
        else:
            st.metric("Confidence Score", "N/A")

    st.divider()


# ==============================================================================
# 2. ZONE PRINCIPALE — ONGLETÉE
# ==============================================================================

def display_valuation_details(result: ValuationResult) -> None:
    """
    Zone centrale de restitution détaillée.
    """

    tab_calc, tab_audit, tab_params = st.tabs([
        "🧮 Démonstration de calcul",
        "🛡️ Audit & Confiance",
        "⚙️ Paramètres utilisés"
    ])

    with tab_calc:
        _display_calculation_trace(result)

    with tab_audit:
        if result.audit_report:
            _display_confidence_audit(result.audit_report)
        else:
            st.info("Aucun audit disponible pour ce résultat.")

    with tab_params:
        _display_parameters_summary(result)


# ==============================================================================
# 3. GLASS BOX — TRACE DE CALCUL
# ==============================================================================

def _display_calculation_trace(result: ValuationResult) -> None:
    """
    Démonstration pas-à-pas du calcul (Glass Box).
    """

    st.subheader("Trace de calcul — Glass Box")

    if not result.calculation_trace:
        st.warning("Aucune trace de calcul disponible pour ce modèle.")
        return

    if result.request:
        st.caption(f"Méthode utilisée : **{result.request.mode.value}**")

    for i, step in enumerate(result.calculation_trace, start=1):
        _render_calculation_step(i, step)

    st.caption("Fin de la démonstration.")


def _render_calculation_step(index: int, step: CalculationStep) -> None:
    """
    Rendu institutionnel d’une étape de calcul.
    """

    with st.expander(f"{index}. {step.label}", expanded=True):
        c1, c2, c3 = st.columns([2, 3, 2])

        with c1:
            st.markdown("**Formule théorique**")
            if step.theoretical_formula and step.theoretical_formula != "N/A":
                st.latex(step.theoretical_formula.replace("$", ""))
            else:
                st.text("—")

        with c2:
            st.markdown("**Application numérique**")
            st.code(step.numerical_substitution, language="text")
            if step.interpretation:
                st.caption(step.interpretation)

        with c3:
            st.markdown("**Résultat**")
            st.metric("", f"{step.result:,.2f} {step.unit}")


# ==============================================================================
# 4. AUDIT — MÉTHODE NORMALISÉE (CHAPITRE 6)
# ==============================================================================

def _display_confidence_audit(report: AuditReport) -> None:
    """
    Restitution complète du score de confiance :
    - score global
    - piliers
    - pondérations
    - diagnostics
    """

    st.subheader("Audit de confiance — Méthode normalisée")

    c1, c2 = st.columns([1, 2])

    # --- SYNTHÈSE ---
    with c1:
        st.metric("Score global", f"{int(report.global_score)}/100")
        st.metric("Rating", report.rating)

        st.markdown("**Formule utilisée**")
        st.code(
            report.pillar_breakdown.aggregation_formula
            if report.pillar_breakdown else "—",
            language="text"
        )

    # --- DÉTAIL PAR PILIER ---
    with c2:
        if not report.pillar_breakdown:
            st.warning("Détail par pilier indisponible.")
            return

        for pillar, ps in report.pillar_breakdown.pillars.items():
            with st.expander(f"{pillar.value} — {int(ps.score)}/100", expanded=True):
                st.markdown(
                    f"""
                    **Score du pilier** : {int(ps.score)}/100  
                    **Pondération** : {ps.weight:.0%}  
                    **Contribution au score final** : {ps.contribution:.1f} pts
                    """
                )

                if ps.diagnostics:
                    st.markdown("**Diagnostics**")
                    for d in ps.diagnostics:
                        st.markdown(f"- {d}")
                else:
                    st.success("Aucune anomalie détectée sur ce pilier.")


# ==============================================================================
# 5. PARAMÈTRES UTILISÉS
# ==============================================================================

def _display_parameters_summary(result: ValuationResult) -> None:
    """
    Résumé structuré des paramètres clés utilisés par le modèle.
    """

    p = result.params
    f = result.financials

    st.markdown("### Paramètres de marché et de risque")
    c1, c2, c3 = st.columns(3)
    c1.metric("Taux sans risque (Rf)", f"{p.risk_free_rate:.2%}")
    c2.metric("Prime de risque (MRP)", f"{p.market_risk_premium:.2%}")
    c3.metric("Beta utilisé", f"{f.beta:.2f}")

    st.markdown("### Hypothèses de croissance et de structure")
    c4, c5, c6 = st.columns(3)
    c4.metric("Croissance FCF", f"{p.fcf_growth_rate:.2%}")
    c5.metric("Croissance terminale", f"{p.perpetual_growth_rate:.2%}")
    c6.metric("Coût de la dette", f"{p.cost_of_debt:.2%}")

    if isinstance(result, DCFValuationResult):
        st.markdown("### Spécifique DCF")
        st.write(f"WACC : {result.wacc:.2%}")
        st.write(f"Valeur d’entreprise : {result.enterprise_value:,.0f} {f.currency}")

    if isinstance(result, RIMValuationResult):
        st.markdown("### Spécifique RIM (Banques)")
        st.write(f"Valeur comptable initiale : {result.current_book_value:,.2f}")
        st.write(f"Coût des fonds propres : {result.cost_of_equity:.2%}")

    if isinstance(result, GrahamValuationResult):
        st.markdown("### Spécifique Graham (1974)")
        st.write(f"EPS utilisé : {result.eps_used:.2f}")
        st.write(f"Taux AAA utilisé : {result.aaa_yield_used:.2%}")
