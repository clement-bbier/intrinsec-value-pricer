"""
app/ui_components/ui_kpis.py

RESTITUTION PRINCIPALE — RAPPORT D’ANALYSTE
Version : V2.2 — Compatibilité Workflow V3 & Enrichissement

Rôle :
- Page de garde & résumé exécutif
- Accès structuré au détail (drill-down)
- Alignement strict UI ↔ moteur
- Zéro décoratif, 100 % informationnel
"""

from typing import Optional, Any
import streamlit as st

from core.models import (
    ValuationResult,
    CalculationStep,
    AuditReport,
    AuditPillar,
    DCFValuationResult,
    RIMValuationResult,
    GrahamValuationResult,
    DDMValuationResult
)

# ==============================================================================
# 0. COMPOSANTS VISUELS PARTAGÉS (Helpers)
# ==============================================================================

def render_financial_badge(label: str, value: str, score: float = 100) -> None:
    """
    Affiche un badge visuel type 'score' ou 'rating' avec code couleur.
    Utilisé par le workflow pour afficher le Score Audit.
    """
    # Définition de la couleur selon le score
    if score >= 75:
        color = "green"
    elif score >= 50:
        color = "orange"
    else:
        color = "red"

    # Rendu visuel propre
    st.markdown(
        f"""
        <div style="
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 5px 10px;
            text-align: center;
            background-color: #f9f9f9;
        ">
            <small style="color: #666; text-transform: uppercase;">{label}</small><br>
            <strong style="color: {color}; font-size: 1.2em;">{value}</strong>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==============================================================================
# 1. PAGE DE GARDE — SYNTHÈSE EXÉCUTIVE
# ==============================================================================

def display_main_kpis(result: ValuationResult) -> None:
    """
    PAGE 1 — Synthèse exécutive.
    Comparable à une factsheet buy-side.
    Note : Le workflow V3 peut parfois reconstruire ces métriques manuellement,
    mais cette fonction reste disponible pour un usage autonome.
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

    st.subheader("Résumé exécutif")

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
                help="Indicateur de confiance (Audit)."
            )
        else:
            st.metric("Confidence Score", "N/A")

    st.divider()


# ==============================================================================
# 2. ADAPTATEURS DE MODÈLES (V3 Workflow Hooks)
# ==============================================================================
# Ces fonctions permettent au workflow.py d'appeler des affichages spécifiques
# sans connaître les détails internes de ui_kpis.py.

def display_dcf_summary(result: DCFValuationResult) -> None:
    """Affiche le détail complet pour un modèle DCF."""
    st.caption("Détails du modèle : Discounted Cash Flow (DCF)")
    display_valuation_details(result)

def display_rim_summary(result: RIMValuationResult) -> None:
    """Affiche le détail complet pour un modèle RIM (Banques)."""
    st.caption("Détails du modèle : Residual Income Model (RIM)")
    display_valuation_details(result)

def display_graham_summary(result: GrahamValuationResult) -> None:
    """Affiche le détail complet pour un modèle Graham."""
    st.caption("Détails du modèle : Graham Intrinsic Value")
    display_valuation_details(result)

def display_ddm_summary(result: DDMValuationResult) -> None:
    """Affiche le détail complet pour un modèle DDM."""
    st.caption("Détails du modèle : Dividend Discount Model (DDM)")
    display_valuation_details(result)

def display_audit_report(report: AuditReport) -> None:
    """Wrapper pour afficher le rapport d'audit seul."""
    _display_confidence_audit(report)


# ==============================================================================
# 3. CORPS DU RAPPORT — NAVIGATION STRUCTURÉE
# ==============================================================================

def display_valuation_details(result: ValuationResult) -> None:
    """
    Corps principal du rapport d’analyste.
    Génère les onglets : Calcul, Audit, Paramètres.
    """

    st.subheader("Analyse détaillée")

    tab_calc, tab_audit, tab_params = st.tabs([
        "🧮 Calcul — Glass Box",
        "🛡️ Audit & Confiance",
        "⚙️ Hypothèses & paramètres"
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
# 4. DÉMONSTRATION — GLASS BOX
# ==============================================================================

def _display_calculation_trace(result: ValuationResult) -> None:
    """
    Démonstration complète et traçable du calcul.
    """

    st.markdown("### Démonstration du calcul — Glass Box")

    if not result.calculation_trace:
        st.warning("Aucune trace de calcul disponible.")
        return

    if result.request:
        st.caption(f"Méthode utilisée : **{result.request.mode.value}**")

    for idx, step in enumerate(result.calculation_trace, start=1):
        _render_calculation_step(idx, step)

    st.caption("Fin de la démonstration du calcul.")


def _render_calculation_step(index: int, step: CalculationStep) -> None:
    """
    Rendu standardisé d’une étape de calcul.
    """

    with st.expander(f"{index}. {step.label}", expanded=True):
        c1, c2, c3 = st.columns([2, 3, 2])

        with c1:
            st.markdown("**Formule théorique**")
            if step.theoretical_formula and step.theoretical_formula != "N/A":
                # Nettoyage basique du LaTeX pour Streamlit
                formula = step.theoretical_formula.replace("$", "")
                st.latex(formula)
            else:
                st.text("—")

        with c2:
            st.markdown("**Application numérique**")
            st.code(step.numerical_substitution, language="text")
            if step.interpretation:
                st.caption(step.interpretation)

        with c3:
            st.markdown("**Résultat**")
            st.metric(
                label="Résultat",
                value=f"{step.result:,.2f} {step.unit}",
                label_visibility="collapsed"
            )


# ==============================================================================
# 5. AUDIT & CONFIANCE — CHAPITRE 6
# ==============================================================================

def _display_confidence_audit(report: AuditReport) -> None:
    """
    Restitution institutionnelle du Confidence Score.
    """

    st.markdown("### Audit de confiance — Méthode normalisée")

    c1, c2 = st.columns([1, 2])

    with c1:
        st.metric("Score global", f"{int(report.global_score)}/100")
        st.metric("Rating", report.rating)

        if report.pillar_breakdown:
            st.markdown("**Formule d’agrégation**")
            st.code(
                report.pillar_breakdown.aggregation_formula,
                language="text"
            )

    with c2:
        if not report.pillar_breakdown:
            st.warning("Détail par pilier indisponible.")
            return

        for pillar, ps in report.pillar_breakdown.pillars.items():
            # Gestion sécurisée de l'affichage du nom du pilier
            pillar_name = pillar.value if isinstance(pillar, AuditPillar) else str(pillar)

            with st.expander(
                f"{pillar_name} — {int(ps.score)}/100",
                expanded=True
            ):
                st.markdown(
                    f"""
                    **Score du pilier** : {int(ps.score)}/100  
                    **Pondération** : {ps.weight:.0%}  
                    **Contribution** : {ps.contribution:.1f} points
                    """
                )

                if ps.diagnostics:
                    st.markdown("**Diagnostics**")
                    for d in ps.diagnostics:
                        st.markdown(f"- {d}")
                else:
                    st.success("Aucune anomalie détectée sur ce pilier.")


# ==============================================================================
# 6. HYPOTHÈSES & PARAMÈTRES
# ==============================================================================

def _display_parameters_summary(result: ValuationResult) -> None:
    """
    Résumé structuré des hypothèses utilisées.
    """

    p = result.params
    f = result.financials

    st.markdown("### Paramètres de marché et de risque")
    c1, c2, c3 = st.columns(3)
    c1.metric("Taux sans risque (Rf)", f"{p.risk_free_rate:.2%}")
    c2.metric("Prime de risque (MRP)", f"{p.market_risk_premium:.2%}")
    c3.metric("Beta utilisé", f"{f.beta:.2f}")

    st.markdown("### Hypothèses de croissance & structure")
    c4, c5, c6 = st.columns(3)
    c4.metric("Croissance FCF", f"{p.fcf_growth_rate:.2%}")
    c5.metric("Croissance terminale", f"{p.perpetual_growth_rate:.2%}")
    c6.metric("Coût de la dette", f"{p.cost_of_debt:.2%}")

    if isinstance(result, DCFValuationResult):
        st.markdown("### Spécifique DCF")
        st.write(f"WACC : {result.wacc:.2%}")
        st.write(
            f"Valeur d’entreprise : "
            f"{result.enterprise_value:,.0f} {f.currency}"
        )

    if isinstance(result, RIMValuationResult):
        st.markdown("### Spécifique RIM (Banques)")
        st.write(
            f"Valeur comptable initiale : "
            f"{result.current_book_value:,.2f} {f.currency}"
        )
        st.write(f"Coût des fonds propres : {result.cost_of_equity:.2%}")

    if isinstance(result, GrahamValuationResult):
        st.markdown("### Spécifique Graham (1974)")
        st.write(f"EPS utilisé : {result.eps_used:.2f}")
        st.write(f"Taux AAA utilisé : {result.aaa_yield_used:.2%}")