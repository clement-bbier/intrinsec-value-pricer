"""
app/ui_components/ui_kpis.py

RESTITUTION "GLASS BOX" — VERSION V8.2 (SOLID & DYNAMIQUE)
Rôle : Affichage haute fidélité des résultats et audit mathématique.
Architecture : Composants atomiques et routage dynamique des diagnostics.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

import numpy as np
import streamlit as st

from core.models import AuditReport, CalculationStep, ValuationResult
from app.ui_components.ui_glass_box_registry import STEP_METADATA, get_step_metadata

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. COMPOSANTS ATOMIQUES (UI COMPONENTS)
# ==============================================================================

def atom_kpi_metric(label:  str, value: str, help_text: str = "") -> None:
    """Affiche une métrique clé dans le bandeau supérieur."""
    st.metric(label, value, help=help_text)


def atom_calculation_card(
    index: int,
    label: str,
    formula: str,
    substitution: str,
    result:  Optional[float],
    unit: str = "",
    interpretation: str = ""
) -> None:
    """Carte d'audit mathématique pour la preuve de calcul."""
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
            st.caption(f"Valeur ({unit})")
            if result is None:
                st.markdown("### N/A")
            elif result == 1.0 and "Initialisation" in label:
                st.write("**Validée**")
            else:
                st.markdown(f"### {result: ,.2f}")

        if interpretation:
            st.caption(f"Note d'analyse : {interpretation}")


# ==============================================================================
# 2. NAVIGATION ET AGGREGATION (VALUATION DETAILS)
# ==============================================================================

def display_valuation_details(result: ValuationResult, _provider: Any = None) -> None:
    """Orchestrateur des onglets de détails post-calcul."""
    st.divider()

    # Séparation des traces (Core vs Monte Carlo)
    core_steps = [s for s in result.calculation_trace if not s.step_key.startswith("MC_")]
    mc_steps = [s for s in result.calculation_trace if s. step_key.startswith("MC_")]

    # Définition des onglets dynamiques
    tab_labels = ["Preuve de Calcul", "Audit de Fiabilité"]

    # Vérification sécurisée pour Monte Carlo
    show_mc_tab = (
        result.request is not None
        and result.request.mode. supports_monte_carlo
        and result.params.enable_monte_carlo
        and mc_steps
    )

    if show_mc_tab:
        tab_labels.append("Analyse de Risque (MC)")

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        for idx, step in enumerate(core_steps, start=1):
            _render_smart_step(idx, step)

    with tabs[1]:
        _render_reliability_report(result. audit_report, result)

    if show_mc_tab:
        with tabs[2]:
            _render_monte_carlo_tab(result, mc_steps)


# ==============================================================================
# 3. ONGLET AUDIT (VERSION V8.2 DYNAMIQUE - GLASS BOX)
# ==============================================================================

def _render_reliability_report(report: Optional[AuditReport], result:  ValuationResult) -> None:
    """Rendu analytique dynamique basé sur les piliers d'audit réels."""
    if not report:
        st.info("Aucun rapport d'audit généré pour cette simulation.")
        return

    # =========================================================================
    # 1. BANDEAU DE CERTITUDE
    # =========================================================================
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown(f"### Score d'Audit Global :  {report.global_score:.1f} / 100")
    with c2:
        st. metric("Rating Score", report.rating)
    with c3:
        coverage = (report.audit_coverage or 0.0) * 100
        st.metric("Couverture", f"{coverage:.0f}%")

    st.divider()

    # =========================================================================
    # 2. TABLE DE VÉRIFICATION DYNAMIQUE
    # =========================================================================
    st.markdown("#### Table de Vérification des Invariants")

    # En-têtes fixes
    h1, h2, h3, h4 = st.columns([2.5, 2.5, 3, 1.5])
    h1.caption("INDICATEUR")
    h2.caption("RÈGLE NORMATIVE")
    h3.caption("PREUVE NUMÉRIQUE")
    h4.caption("VERDICT")

    # Parcours des piliers d'audit fournis par l'auditeur
    if report.pillar_breakdown and report.pillar_breakdown.pillars:
        for _pillar_type, score_obj in report.pillar_breakdown.pillars.items():
            for diag_message in score_obj.diagnostics:

                # Identification de la clé dans STEP_METADATA
                test_key = _map_message_to_meta_key(diag_message)
                meta = get_step_metadata(test_key)

                if not meta:
                    meta = {"label": "Test Spécifique", "formula": r"\text{N/A}"}

                # Extraction de la preuve numérique
                substitution = _format_numerical_evidence(test_key, result)

                # Détermination du statut visuel
                alert_keywords = ["ALERTE", "RISQUE", "DIVERGENCE", "FRAGILE", "HORS", "CRITIQUE", "DÉFICIT"]
                is_alert = any(k in diag_message. upper() for k in alert_keywords)
                status_text = "Alerte" if is_alert else "Conforme"
                color = "red" if is_alert else "green"

                with st.container():
                    r1, r2, r3, r4 = st.columns([2.5, 2.5, 3, 1.5])
                    r1.markdown(f"**{meta['label']}**", help=meta. get('description', ''))
                    r2.latex(meta['formula'])
                    r3.info(substitution)
                    r4.markdown(f":{color}[**{status_text}**]")

    # =========================================================================
    # 3. REGISTRE DES DIAGNOSTICS DÉTAILLÉS
    # =========================================================================
    relevant_logs = [log for log in report.logs if "attribute" not in log.message. lower()]

    if relevant_logs:
        st.divider()
        with st.expander("Consulter les notes d'audit détaillées", expanded=report.global_score < 40):
            for log in relevant_logs:
                if log.severity == "CRITICAL":
                    st.error(f"**[{log.category}]** {log.message}")
                elif log.severity == "WARNING":
                    st.warning(f"**[{log.category}]** {log.message}")
                else:
                    st.info(f"**[{log.category}]** {log.message}")


# ==============================================================================
# 4. HELPERS DE MAPPING & EVIDENCE (UNIFIÉ V8.2)
# ==============================================================================

def _map_message_to_meta_key(message:  str) -> str:
    """
    Mapping unifié : diagnostic texte → clé AUDIT_* du registre.
    Toutes les clés retournées sont des clés modernes (namespace AUDIT_).
    """
    m = message.upper()

    # =========================================================================
    # Data Confidence
    # =========================================================================
    if "BETA" in m or "BÊTA" in m:
        return "AUDIT_BETA_COHERENCE"
    if "ICR" in m or "SOLVABILITÉ" in m:
        return "AUDIT_SOLVENCY_ICR"
    if "TRÉSORERIE > CAPITALISATION" in m or "NET-NET" in m:
        return "AUDIT_CASH_MCAP"
    if "LIQUIDITÉ" in m or "SMALL-CAP" in m:
        return "AUDIT_LIQUIDITY"
    if "LEVIER" in m:
        return "AUDIT_LEVERAGE"

    # =========================================================================
    # Assumption Risk
    # =========================================================================
    if "CONVERGENCE MACRO" in m or "G PERPÉTUEL" in m and "RF" in m:
        return "AUDIT_G_RF_CONVERGENCE"
    if "PLANCHER" in m and "RF" in m:
        return "AUDIT_RF_FLOOR"
    if "CAPEX" in m or "RÉINVESTISSEMENT" in m:
        return "AUDIT_CAPEX_DA"
    if "CROISSANCE" in m and ("HORS" in m or "AGRESSIVE" in m):
        return "AUDIT_GROWTH_LIMIT"
    if "PAYOUT" in m or "DISTRIBUTION" in m:
        return "AUDIT_PAYOUT_STABILITY"

    # =========================================================================
    # Model Risk
    # =========================================================================
    if "WACC" in m and ("BAS" in m or "MINIMUM" in m or "PLANCHER" in m):
        return "AUDIT_WACC_FLOOR"
    if "VALEUR TERMINALE" in m or "CONCENTRATION" in m and "TV" in m:
        return "AUDIT_TV_CONCENTRATION"
    if "G >=" in m or "GORDON" in m or ("G" in m and "WACC" in m):
        return "AUDIT_G_WACC"

    # =========================================================================
    # Method Fit
    # =========================================================================
    if "SPREAD" in m or "ROE" in m and "KE" in m:
        return "AUDIT_ROE_KE_SPREAD"
    if "P/B" in m or "BOOK VALUE" in m:
        return "AUDIT_PB_RATIO"

    return "AUDIT_UNKNOWN"


def _format_numerical_evidence(key: str, res: ValuationResult) -> str:
    """
    Récupère les métriques injectées pour l'affichage numérique.
    Toutes les clés sont désormais au format AUDIT_*.
    """
    f = res.financials

    try:
        # =====================================================================
        # Data Confidence
        # =====================================================================
        if key == "AUDIT_BETA_COHERENCE":
            return f"Beta extrait : {f.beta:.2f}"

        if key == "AUDIT_SOLVENCY_ICR":
            val = getattr(res, 'icr_observed', None)
            return f"EBIT / Intérêts : {val:.2f}x" if val is not None else "Donnée N/A"

        if key == "AUDIT_CASH_MCAP":
            ratio = (f.cash_and_equivalents / f.market_cap) if f.market_cap else 0
            return f"Cash/MCap : {ratio:.1%}"

        if key == "AUDIT_LIQUIDITY":
            return f"MCap :  {f.market_cap:,. 0f} {f.currency}"

        if key == "AUDIT_LEVERAGE":
            val = getattr(res, 'leverage_observed', None)
            return f"Dette/EBIT : {val:.2f}x" if val is not None else "N/A"

        # =====================================================================
        # Assumption Risk
        # =====================================================================
        if key == "AUDIT_G_RF_CONVERGENCE":
            g = res.params.perpetual_growth_rate or 0
            rf = res.params.risk_free_rate or 0
            return f"g:{g:.1%} vs Rf:{rf:.1%}"

        if key == "AUDIT_RF_FLOOR":
            rf = res.params.risk_free_rate or 0
            return f"Rf :  {rf:.2%}"

        if key == "AUDIT_CAPEX_DA":
            val = getattr(res, 'capex_to_da_ratio', None)
            return f"Ratio CapEx/D&A : {val:.1%}" if val is not None else "Donnée N/A"

        if key == "AUDIT_GROWTH_LIMIT":
            g = res.params.fcf_growth_rate or 0
            return f"Taux g : {g:.1%}"

        if key == "AUDIT_PAYOUT_STABILITY":
            val = getattr(res, 'payout_ratio_observed', None)
            return f"Payout Ratio : {val:.1%}" if val is not None else "Donnée N/A"

        # =====================================================================
        # Model Risk
        # =====================================================================
        if key == "AUDIT_WACC_FLOOR":
            w = getattr(res, 'wacc', 0) or 0
            return f"WACC Calculé : {w:.2%}"

        if key == "AUDIT_TV_CONCENTRATION":
            val = getattr(res, 'terminal_value_weight', None)
            return f"Poids TV : {val:.1%}" if val is not None else "N/A"

        if key == "AUDIT_G_WACC":
            w = getattr(res, 'wacc', 0) or 0
            g = res.params.perpetual_growth_rate or 0
            return f"g:{g:.1%} vs WACC:{w:.1%}"

        # =====================================================================
        # Method Fit
        # =====================================================================
        if key == "AUDIT_ROE_KE_SPREAD":
            val = getattr(res, 'spread_roe_ke', None)
            return f"Spread ROE-Ke : {val:.2%}" if val is not None else "N/A"

        if key == "AUDIT_PB_RATIO":
            val = getattr(res, 'pb_ratio_observed', None)
            return f"P/B Observé : {val:.2f}x" if val is not None else "N/A"

    except Exception as e:
        logger.error(f"Erreur extraction preuve pour {key}: {e}")
        return "Erreur source"

    return "Vérification OK"


# ==============================================================================
# 5. ONGLET MONTE CARLO (PROBABILISTE)
# ==============================================================================

def _render_monte_carlo_tab(result: ValuationResult, mc_steps: List[CalculationStep]) -> None:
    """Rendu probabiliste de l'analyse Monte Carlo."""
    from app.ui_components.ui_charts import display_simulation_chart, display_correlation_heatmap

    if result.simulation_results is None or len(result.simulation_results) == 0:
        st. warning("La simulation n'a pas pu converger (Paramètres instables).")
        return

    f, p = result.financials, result.params
    sims = np.array(result.simulation_results)
    prob_overvalued = (sims < result.market_price).mean() if result.market_price else 0.0
    q = result.quantiles or {}

    # =========================================================================
    # Métriques principales
    # =========================================================================
    st.markdown("#### Analyse de Conviction Probabiliste")

    c1, c2, c3 = st.columns(3)
    c1.metric("Downside Risk (IV < Prix)", f"{prob_overvalued:.1%}")
    c2.metric("Médiane (P50)", f"{q.get('P50', 0.0):,.2f}")
    c3.metric("Risque de Queue (P10)", f"{q.get('P10', 0.0):,.2f}")

    display_simulation_chart(result. simulation_results, result.market_price, f. currency)

    st.divider()

    # =========================================================================
    # Sensibilité et Stress Test
    # =========================================================================
    col_sens, col_stress = st.columns([1.5, 2.5])

    with col_sens:
        st.markdown("**Sensibilité Corrélation (ρ)**")
        if result.rho_sensitivity:
            sens_data = [{"Scénario": k, "IV (P50)": f"{v: ,.2f}"} for k, v in result. rho_sensitivity.items()]
            st.table(sens_data)
        else:
            st.caption("Données non disponibles.")

    with col_stress:
        st.markdown("**Scénario de Stress (Bear Case)**")
        if result.stress_test_value is not None:
            st.warning(f"**Valeur Plancher : {result.stress_test_value: ,.2f} {f.currency}**")
            st.caption("Paramètres :  g=0%, β=1.5.  Simulation de rupture des fondamentaux.")

    # =========================================================================
    # Audit des Hypothèses Statistiques
    # =========================================================================
    with st.expander("Audit des Hypothèses Statistiques", expanded=False):
        col_mat, col_inf = st.columns([1.2, 2.8])

        with col_mat:
            display_correlation_heatmap(rho=p.correlation_beta_growth or -0.3)

        with col_inf:
            beta_vol = p.beta_volatility or 0.0
            growth_vol = p.growth_volatility or 0.0
            st. caption(f"Volatilité Beta : {beta_vol:.1%}")
            st.caption(f"Volatilité Croissance : {growth_vol:.1%}")
            st.info("La corrélation négative standard prévient les scénarios financiers incohérents.")

    # =========================================================================
    # Détail du traitement stochastique
    # =========================================================================
    with st.expander("Détail du traitement stochastique (Audit)", expanded=False):
        for idx, step in enumerate(mc_steps, start=1):
            _render_smart_step(idx, step)


# ==============================================================================
# 6. RÉSUMÉ EXÉCUTIF
# ==============================================================================

def render_executive_summary(result: ValuationResult) -> None:
    """Synthèse décisionnelle supérieure."""
    f = result.financials
    st.subheader(f"Dossier de Valorisation : {f.name} ({f.ticker})")

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


def _render_smart_step(index: int, step: CalculationStep) -> None:
    """Lookup dynamique dans STEP_METADATA."""
    meta = get_step_metadata(step.step_key)
    atom_calculation_card(
        index=index,
        label=meta.get("label", step.label),
        formula=meta.get("formula", step.theoretical_formula),
        substitution=step.numerical_substitution,
        result=step.result,
        unit=meta.get("unit", ""),
        interpretation=step.interpretation
    )
