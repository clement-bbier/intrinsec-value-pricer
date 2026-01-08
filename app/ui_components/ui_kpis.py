"""
app/ui_components/ui_kpis.py
RESTITUTION "GLASS BOX" — VERSION V7.0 (SÉCURISÉE)
Rôle : Affichage haute fidélité des résultats et audit mathématique.
Note : Respect du paradigme "None = N/A" vs "0.0 = Valeur".
"""

from typing import Optional, List, Any, Dict
import numpy as np
import streamlit as st
from core.models import ValuationResult, CalculationStep, AuditReport
from app.ui_components.ui_glass_box_registry import STEP_METADATA


# ==============================================================================
# 1. ATOMES DE RENDU (SÉCURISÉS)
# ==============================================================================

def atom_kpi_metric(label: str, value: str, help_text: str = ""):
    """Affichage d'une métrique clé dans le bandeau supérieur."""
    st.metric(label, value, help=help_text)

def atom_calculation_card(index: int, label: str, formula: str, substitution: str, result: Optional[float], unit: str = "", interpretation: str = ""):
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
                st.code(substitution, language="text")
            else:
                st.markdown("---")

        with c3:
            st.caption(f"Valeur ({unit})")
            if result is None:
                st.markdown("### N/A")
            elif result == 1.0 and "Initialisation" in label:
                st.write("**Validée**")
            else:
                # Sécurité : Formatage uniquement si numérique
                st.markdown(f"### {result:,.2f}")

        if interpretation:
            st.caption(f"Note d'analyse : {interpretation}")

# ==============================================================================
# 2. NAVIGATION ET TRI (ARCHITECTURE MODULAIRE)
# ==============================================================================

def display_valuation_details(result: ValuationResult, provider: Any = None) -> None:
    st.divider()

    # 1. On sépare les traces
    core_steps = [s for s in result.calculation_trace if not s.step_key.startswith("MC_")]
    mc_steps = [s for s in result.calculation_trace if s.step_key.startswith("MC_")]

    # 2. On définit les onglets dynamiquement selon la compatibilité du modèle
    tab_labels = ["Preuve de Calcul", "Audit de Fiabilité"]

    # L'onglet MC n'est ajouté QUE si le modèle le supporte ET que l'option était active
    show_mc_tab = result.request.mode.supports_monte_carlo and result.params.enable_monte_carlo
    if show_mc_tab:
        tab_labels.append("Analyse de Risque (MC)")

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        for idx, step in enumerate(core_steps, start=1):
            _render_smart_step(idx, step)

    with tabs[1]:
        _render_reliability_report(result.audit_report)

    if show_mc_tab:
        with tabs[2]:
            _render_monte_carlo_tab(result, mc_steps)

# ==============================================================================
# 3. COMPOSANTS DE L'ONGLET RISQUE (MONTE CARLO)
# ==============================================================================

def _render_monte_carlo_tab(result: ValuationResult, mc_steps: List[CalculationStep]):
    """Rendu expert de l'analyse Monte Carlo."""
    if result.params.enable_monte_carlo and (result.simulation_results is None or len(result.simulation_results) == 0):
        st.warning("La simulation de Monte Carlo n'a pas pu converger (Paramètres instables ou autre).")
        return

    if not result.params.enable_monte_carlo:
        st.info("Analyse de risque probabiliste non activée pour cette valorisation.")
        return

    from app.ui_components.ui_charts import (
        display_simulation_chart,
        display_correlation_heatmap
    )

    f = result.financials
    p = result.params

    # --- CALCULS STATISTIQUES RÉELS (Sécurisés) ---
    sims = np.array(result.simulation_results)
    prob_overvalued = (sims < result.market_price).mean() if result.market_price else 0.0

    # Récupération sécurisée des quantiles
    q = result.quantiles or {}
    p50 = q.get('P50', 0.0)
    p10 = q.get('P10', 0.0)

    st.markdown("#### Analyse de Conviction Probabiliste")

    # Bandeau de métriques réelles
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Downside Risk (IV < Prix)", f"{prob_overvalued:.1%}")
    with c2:
        st.metric("Médiane (P50)", f"{p50:,.2f}")
    with c3:
        st.metric("Risque de Queue (P10)", f"{p10:,.2f}")

    # 1. VISUALISATION DE LA DISTRIBUTION
    display_simulation_chart(result.simulation_results, result.market_price, f.currency)

    # 2. AUDIT DE ROBUSTESSE & STRESS TEST
    st.divider()
    col_sens, col_stress = st.columns([1.5, 2.5])

    with col_sens:
        st.markdown("**Sensibilité Corrélation (ρ)**")
        if result.rho_sensitivity:
            sens_data = [
                {"Scénario": k, "IV (P50)": f"{v:,.2f}"}
                for k, v in result.rho_sensitivity.items()
            ]
            st.table(sens_data)
            st.caption("Analyse de stabilité : Impact de l'indépendance des variables.")
        else:
            st.caption("Données de sensibilité non disponibles.")

    with col_stress:
        st.markdown("**Scénario de Stress (Bear Case)**")
        if result.stress_test_value is not None:
            # Respect de la devise et du format
            val_stress = result.stress_test_value
            st.warning(f"**Valeur Plancher : {val_stress:,.2f} {f.currency}**")
            st.markdown(
                f"""
                <div style="font-size: 0.85rem; color: #64748b; border-left: 2px solid #eab308; padding-left: 1rem;">
                <b>Paramètres forcés :</b> Croissance nulle (g=0%), Risque élevé (β=1.5).<br>
                Ce scénario simule une dégradation brutale des fondamentaux pour tester la résilience.
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.info("Stress test non exécuté.")

    # 3. ANALYSE DES CORRÉLATIONS
    with st.expander("Audit des Hypothèses Statistiques", expanded=False):
        col_matrice, col_info = st.columns([1.2, 2.8])
        with col_matrice:
            # On passe la corrélation par défaut si nulle
            rho_val = p.correlation_beta_growth if p.correlation_beta_growth is not None else -0.3
            display_correlation_heatmap(rho=rho_val)
        with col_info:
            st.write("**Calibration de la simulation :**")
            # Formatage safe des volatilités
            v_beta = p.beta_volatility if p.beta_volatility is not None else 0.0
            v_g = p.growth_volatility if p.growth_volatility is not None else 0.0
            st.caption(f"• Volatilité Beta : {v_beta:.1%}")
            st.caption(f"• Volatilité Croissance (g) : {v_g:.1%}")
            st.caption(f"• Corrélation (ρ) : {rho_val:.2f}")
            st.info("La corrélation négative standard prévient les scénarios financiers incohérents.")

    # 4. GLASS BOX STATISTIQUE
    with st.expander("Détail du traitement statistique (Audit)", expanded=False):
        for idx, step in enumerate(mc_steps, start=1):
            _render_smart_step(idx, step)

# ==============================================================================
# 4. MOTEURS DE RÉSOLUTION ET RAPPORTS
# ==============================================================================

def _render_smart_step(index: int, step: CalculationStep):
    """Lookup corrigé utilisant la clé technique step_key."""
    meta = STEP_METADATA.get(step.step_key, {})

    atom_calculation_card(
        index=index,
        label=meta.get("label", step.label),
        formula=meta.get("formula", step.theoretical_formula),
        substitution=step.numerical_substitution,
        result=step.result,
        unit=meta.get("unit", ""),
        interpretation=step.interpretation
    )

def render_executive_summary(result: ValuationResult) -> None:
    """Synthèse décisionnelle supérieure."""
    f = result.financials
    st.subheader(f"Dossier de Valorisation : {f.name} ({f.ticker})")

    # Calcul de l'affichage de la valeur intrinsèque (Sécurisé)
    iv = result.intrinsic_value_per_share
    iv_display = f"{iv:,.2f} {f.currency}" if iv is not None else "N/A"

    price_display = f"{result.market_price:,.2f} {f.currency}" if result.market_price is not None else "N/A"

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            atom_kpi_metric("Cours Actuel", price_display)
        with c2:
            atom_kpi_metric("Valeur Intrinsèque", iv_display)
        with c3:
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
                # Sévérité dynamique
                sev_label = "ALERTE" if log.severity in ["CRITICAL", "WARNING", "HIGH"] else "INFO"
                st.markdown(f"**[{sev_label}]** {log.message}")

    if report.critical_warning:
        st.error("ARRET CRITIQUE : Des failles méthodologiques majeures ont été identifiées.")

# ALIASES POUR COMPATIBILITÉ RÉTROACTIVE
def display_main_kpis(result): render_executive_summary(result)
def display_dcf_summary(result, provider): display_valuation_details(result, provider)
def display_rim_summary(result, provider): display_valuation_details(result, provider)
def display_graham_summary(result, provider): display_valuation_details(result, provider)