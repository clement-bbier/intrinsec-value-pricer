"""
app/ui_components/ui_kpis.py
RESTITUTION "GLASS BOX" — STANDARD INSTITUTIONNEL V6.6 (Audit-Grade)
Rôle : Affichage technique neutre. Isolation statistique et lookup dynamique.
"""

from typing import Optional, List, Any, Dict
import streamlit as st
from core.models import ValuationResult, CalculationStep, AuditReport
from app.ui_components.ui_glass_box_registry import STEP_METADATA

# ==============================================================================
# 1. ATOMES DE RENDU (ARCHITECTURE BRUTE)
# ==============================================================================

def atom_kpi_metric(label: str, value: str, help_text: str = ""):
    """Affichage d'une métrique clé dans le bandeau supérieur."""
    st.metric(label, value, help=help_text)

def atom_calculation_card(index: int, label: str, formula: str, substitution: str, result: float, interpretation: str = ""):
    """Carte d'audit mathématique isolée pour la preuve de calcul."""
    with st.container(border=True):
        st.markdown(f"**Etape {index} : {label}**")
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
                # Utilisation d'un bloc de code pour préserver les symboles mathématiques (ex: ×)
                st.code(substitution, language="text")
            else:
                st.markdown("---")

        with c3:
            st.caption("Valeur Calculée")
            st.markdown(f"### {result:,.2f}")

        if interpretation:
            st.caption(f"Note d'analyse : {interpretation}")

# ==============================================================================
# 2. NAVIGATION ET TRI (ISOLATION STATISTIQUE)
# ==============================================================================

def display_valuation_details(result: ValuationResult, provider: Any = None) -> None:
    """Structure de restitution organisée en trois piliers : Preuve, Fiabilité, Risque."""
    st.divider()

    # TRI CHIRURGICAL : On sépare les étapes de calcul métier des étapes statistiques (MC_)
    # On se base sur le label qui contient la clé technique (ex: MC_CONFIG)
    core_steps = [s for s in result.calculation_trace if not s.step_key.startswith("MC_")]
    mc_steps = [s for s in result.calculation_trace if s.step_key.startswith("MC_")]

    tabs = st.tabs(["Preuve de Calcul", "Audit de Fiabilité", "Analyse de Risque (MC)"])

    with tabs[0]:
        st.markdown("#### Démonstration mathématique du scénario central")
        for idx, step in enumerate(core_steps, start=1):
            _render_smart_step(idx, step)

    with tabs[1]:
        if result.audit_report:
            _render_reliability_report(result.audit_report)
        else:
            st.info("Rapport d'audit non disponible pour ce modèle.")

    with tabs[2]:
        if result.simulation_results:
            from app.ui_components.ui_charts import display_simulation_chart

            st.markdown("#### Simulation de Monte Carlo")
            # Rendu du graphique de distribution
            display_simulation_chart(result.simulation_results, result.market_price, result.financials.currency)

            with st.expander("Détail du traitement statistique", expanded=False):
                for idx, step in enumerate(mc_steps, start=1):
                    _render_smart_step(idx, step)
        else:
            st.info("Analyse de risque probabiliste non activée pour cette requête.")

# ==============================================================================
# 3. MOTEUR DE RÉSOLUTION (LOOKUP REGISTRE)
# ==============================================================================

def _render_smart_step(index: int, step: CalculationStep):
    """Lookup corrigé utilisant la clé technique step_key."""
    # Correction : On cherche la clé technique (ex: MC_CONFIG) et non le label long
    meta = STEP_METADATA.get(step.step_key, {})

    atom_calculation_card(
        index=index,
        label=meta.get("label", step.label),
        formula=meta.get("formula", step.theoretical_formula),
        substitution=step.numerical_substitution,
        result=step.result,
        interpretation=step.interpretation
    )

# ==============================================================================
# 4. RAPPORTS EXÉCUTIFS
# ==============================================================================

def render_executive_summary(result: ValuationResult) -> None:
    """Synthèse décisionnelle supérieure."""
    f = result.financials
    st.subheader(f"Dossier de Valorisation : {f.name} ({f.ticker})")

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            atom_kpi_metric("Cours Actuel", f"{result.market_price:,.2f} {f.currency}")
        with c2:
            atom_kpi_metric("Valeur Intrinsèque", f"{result.intrinsic_value_per_share:,.2f} {f.currency}")
        with c3:
            # Affichage de la notation d'audit si disponible
            rating = result.audit_report.rating if result.audit_report else "N/A"
            atom_kpi_metric("Indice de Confiance", rating)

def _render_reliability_report(report: AuditReport) -> None:
    """Décomposition du score d'audit par piliers normatifs."""
    st.markdown(f"### Score Global : {report.global_score:.1f}/100")
    st.latex(r"Confidence = \sum (Score_{pillar} \times Weight)")

    if report.pillar_breakdown:
        breakdown_data = []
        for ps in report.pillar_breakdown.pillars.values():
            breakdown_data.append({
                "Domaine d'Audit": ps.pillar.value,
                "Score": f"{ps.score:.1f}",
                "Pondération": f"{ps.weight:.1%}",
                "Impact final": f"{ps.contribution:.1f}"
            })
        st.table(breakdown_data)

    if report.logs:
        with st.expander("Registre des Diagnostics d'Audit", expanded=True):
            for log in report.logs:
                sev = "ALERTE" if log.severity in ["CRITICAL", "WARNING", "HIGH"] else "INFO"
                st.markdown(f"**[{sev}]** {log.message}")

    if report.critical_warning:
        st.error("ARRET CRITIQUE : Des failles méthodologiques majeures ont été identifiées.")

# ALIASES POUR COMPATIBILITÉ RÉTROACTIVE
def display_main_kpis(result): render_executive_summary(result)
def display_dcf_summary(result, provider): display_valuation_details(result, provider)
def display_rim_summary(result, provider): display_valuation_details(result, provider)
def display_graham_summary(result, provider): display_valuation_details(result, provider)