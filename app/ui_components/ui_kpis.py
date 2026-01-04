"""
app/ui_components/ui_kpis.py
RESTITUTION "GLASS BOX" — STANDARD INSTITUTIONNEL V6.6 (Certified)
Rôle : Affichage technique neutre. Support multi-unités et isolation MC.
"""

from typing import Optional, List, Any, Dict
import streamlit as st
from core.models import ValuationResult, CalculationStep, AuditReport
from app.ui_components.ui_glass_box_registry import STEP_METADATA

# ==============================================================================
# 1. ATOMES DE RENDU (ARCHITECTURE BRUTE)
# ==============================================================================

def atom_kpi_metric(label: str, value: str, delta: Optional[str] = None, delta_color: str = "normal", help_text: str = ""):
    """Affiche une métrique standardisée dans le bandeau supérieur."""
    st.metric(label, value, delta=delta, delta_color=delta_color, help=help_text)

def atom_calculation_card(index: int, label: str, formula: str, substitution: str, result: float, unit: str = ""):
    """Dessine une carte d'audit mathématique avec support d'unité."""
    with st.container(border=True):
        st.markdown(f"**Étape {index} : {label}**")
        c1, c2, c3 = st.columns([2.5, 4, 1.5])

        with c1:
            st.caption("Formule Théorique")
            if formula and formula != "N/A":
                st.latex(formula)
            else:
                st.markdown("*Donnée source*")

        with c2:
            st.caption("Application Numérique")
            if substitution:
                st.code(substitution, language="text")
            else:
                st.markdown("---")

        with c3:
            st.caption("Valeur Calculée")
            # Gestion intelligente de l'unité (Currency, %, x)
            unit_display = ""
            if unit == "currency": unit_display = "" # Géré par le formatage global ou laissé brut
            elif unit == "%": unit_display = " %" if result < 2 else "" # Sécurité taux
            elif unit == "x": unit_display = " x"

            st.markdown(f"### {result:,.2f}{unit_display}")

# ==============================================================================
# 2. NAVIGATION ET TRI (ISOLATION CHIRURGICALE)
# ==============================================================================

def display_valuation_details(result: ValuationResult, provider: Any = None) -> None:
    """Structure en onglets professionnels avec isolation MC par préfixe."""
    st.divider()

    # Isolation par préfixe technique : Vital pour la clarté de l'onglet 1
    core_steps = [s for s in result.calculation_trace if not s.label.startswith("MC_")]
    mc_steps = [s for s in result.calculation_trace if s.label.startswith("MC_")]

    tabs = st.tabs(["Audit Calcul", "Fiabilité du Résultat", "Analyse Monte Carlo"])

    with tabs[0]:
        st.markdown("#### Démonstration du Scénario Central")
        for idx, step in enumerate(core_steps, start=1):
            _render_smart_step(idx, step)

    with tabs[1]:
        if result.audit_report:
            _render_reliability_report(result.audit_report)

    with tabs[2]:
        if result.simulation_results:
            from app.ui_components.ui_charts import display_simulation_chart
            display_simulation_chart(result.simulation_results, result.market_price, result.financials.currency)

            with st.expander("Traitement statistique de l'incertitude", expanded=True):
                for idx, step in enumerate(mc_steps, start=1):
                    _render_smart_step(idx, step)
        else:
            st.info("Simulation Monte Carlo non activée.")

# ==============================================================================
# 3. MOTEUR DE RÉSOLUTION (LOOKUP DIRECT)
# ==============================================================================

def _render_smart_step(index: int, step: CalculationStep):
    """Injection directe depuis le registre avec support d'unité."""
    meta = STEP_METADATA.get(step.label, {})

    atom_calculation_card(
        index=index,
        label=meta.get("label", step.label),
        formula=meta.get("formula", step.theoretical_formula),
        substitution=step.numerical_substitution,
        result=step.result,
        unit=meta.get("unit", "")
    )

# ==============================================================================
# 4. RAPPORTS ET RÉSUMÉS
# ==============================================================================

def render_executive_summary(result: ValuationResult) -> None:
    """Top-Bar décisionnelle brute."""
    f = result.financials
    st.subheader(f"Rapport de Valorisation : {f.name} ({f.ticker})")

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            atom_kpi_metric("Prix de Marché", f"{result.market_price:,.2f} {f.currency}")
        with c2:
            atom_kpi_metric("Valeur Intrinsèque", f"{result.intrinsic_value_per_share:,.2f} {f.currency}")

def _render_reliability_report(report: AuditReport) -> None:
    """Rendu institutionnel du score de confiance avec journal de diagnostics."""
    st.markdown(f"### Audit de Fiabilité : {report.rating}")
    st.latex(r"Score = \sum (Score_{pilier} \times Poids)")

    if report.pillar_breakdown:
        st.markdown("#### Décomposition Mathématique")
        breakdown_data = []
        for ps in report.pillar_breakdown.pillars.values():
            breakdown_data.append({
                "Pilier": ps.pillar.value,
                "Score / 100": f"{ps.score:.1f}",
                "Poids": f"{ps.weight:.1%}",
                "Contribution": f"{ps.contribution:.1f}"
            })
        st.table(breakdown_data)

    if report.logs or report.pillar_breakdown:
        st.divider()
        st.markdown("#### Journal des Diagnostics Techniques")

        # Diagnostics par section pour une lecture structurée
        for pillar_key, ps in report.pillar_breakdown.pillars.items():
            if ps.diagnostics:
                with st.expander(f"Section : {ps.pillar.value.upper()}", expanded=True):
                    for d in ps.diagnostics:
                        sev = "ATTENTION" if any(x in d.upper() for x in ["ALERTE", "CRITIQUE", "INCOHÉRENCE"]) else "INFO"
                        st.markdown(f"**[{sev}]** {d}")

    if report.critical_warning:
        st.error("AVERTISSEMENT : Des incohérences majeures détectées peuvent invalider ce modèle.")

# ALIASES DE COMPATIBILITÉ
def display_main_kpis(result): render_executive_summary(result)
def display_dcf_summary(result, provider): display_valuation_details(result, provider)
def display_rim_summary(result, provider): display_valuation_details(result, provider)
def display_graham_summary(result, provider): display_valuation_details(result, provider)