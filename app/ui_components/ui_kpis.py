import streamlit as st
import pandas as pd
from typing import Optional

from core.models import (
    ValuationResult,
    CalculationStep,
    ValuationMode,
    DCFValuationResult,
    RIMValuationResult,
    GrahamValuationResult,
    AuditReport
)


# ==============================================================================
# 1. COMPOSANT : KPI PRINCIPAUX (Haut de page)
# ==============================================================================

def display_main_kpis(result: ValuationResult) -> None:
    """
    Affiche les cartes de résultats synthétiques (Valeur, Prix, Potentiel, Score).
    Style : Sobriété Financière (Bloomberg Terminal style).
    """

    # --- 1. Préparation des Données ---
    intrinsic_val = result.intrinsic_value_per_share
    market_price = result.market_price
    currency = result.financials.currency

    upside = result.upside_pct
    upside_color = "normal"
    if upside is not None:
        upside_color = "off" if upside < 0 else "normal"  # Streamlit delta color logic

    audit_score = 0
    audit_rating = "N/A"
    if result.audit_report:
        audit_score = int(result.audit_report.global_score)
        audit_rating = result.audit_report.rating

    # --- 2. Affichage en Colonnes ---
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            label="Valeur Intrinsèque",
            value=f"{intrinsic_val:,.2f} {currency}",
            help="Juste valeur estimée par le modèle (par action)."
        )

    with c2:
        st.metric(
            label="Prix de Marché",
            value=f"{market_price:,.2f} {currency}",
            help="Dernier prix de clôture connu."
        )

    with c3:
        if upside is not None:
            st.metric(
                label="Potentiel (Upside)",
                value=f"{upside:+.1%}",
                delta=f"{upside:+.1%}",
                delta_color=upside_color,
                help="Écart entre la valeur intrinsèque et le prix de marché."
            )
        else:
            st.metric(label="Potentiel", value="N/A")

    with c4:
        st.metric(
            label="Score de Confiance",
            value=f"{audit_score}/100",
            delta=audit_rating,
            delta_color="off",
            help="Note technique évaluant la cohérence des hypothèses et la qualité des données."
        )

    st.divider()


# ==============================================================================
# 2. COMPOSANT : MOTEUR DE CALCUL (GLASS BOX)
# ==============================================================================

def display_calculation_engine(result: ValuationResult) -> None:
    """
    Affiche la trace d'audit complète : Formules, Substitutions, Résultats.
    C'est le cœur de l'expérience 'Glass Box'.
    """
    st.subheader("🔍 Moteur de Calcul (Trace d'Audit)")

    if not result.calculation_trace:
        st.warning("⚠️ Aucune trace de calcul disponible pour ce modèle.")
        return

    # Conteneur principal scrollable (visuellement propre)
    with st.container():
        mode_name = result.request.mode.value if result.request else 'Standard'
        st.caption(f"Démonstration pas-à-pas pour la méthode : **{mode_name}**")

        # On itère sur chaque étape enregistrée par le moteur
        for i, step in enumerate(result.calculation_trace, 1):
            _render_step(i, step)

        st.caption("--- Fin du Calcul ---")


def _render_step(index: int, step: CalculationStep) -> None:
    """
    Rendu graphique d'une étape de calcul unique.
    Format : Titre | Formule (LaTeX) | Substitution | Résultat
    """
    with st.expander(f"{index}. {step.label}", expanded=True):
        cols = st.columns([2, 3, 2])

        # Colonne 1 : La Formule Théorique
        with cols[0]:
            st.markdown("**Formule Théorique**")
            if step.formula and step.formula != "N/A":
                # On nettoie un peu le LaTeX si besoin
                clean_formula = step.formula.replace("$", "")
                st.latex(clean_formula)
            else:
                st.text("—")

        # Colonne 2 : L'application Numérique
        with cols[1]:
            st.markdown("**Application Numérique**")
            st.code(f"{step.values}", language="text")
            if step.description:
                st.caption(f"ℹ️ {step.description}")

        # Colonne 3 : Le Résultat
        with cols[2]:
            st.markdown("**Résultat**")
            st.metric(
                label="",
                value=f"{step.result:,.2f} {step.unit}"
            )


# ==============================================================================
# 3. COMPOSANT : DÉTAILS SPÉCIFIQUES (Onglets)
# ==============================================================================

def display_valuation_details(result: ValuationResult) -> None:
    """
    Zone principale d'affichage des détails (Onglets).
    Orchestre l'affichage de la preuve, de l'audit et des paramètres.
    """

    tab_trace, tab_audit, tab_params = st.tabs([
        "🧮 Preuve de Calcul",
        "🛡️ Rapport d'Audit",
        "⚙️ Paramètres Utilisés"
    ])

    # --- ONGLET 1 : TRACE D'AUDIT (GLASS BOX) ---
    with tab_trace:
        display_calculation_engine(result)

    # --- ONGLET 2 : RAPPORT D'AUDIT ---
    with tab_audit:
        if result.audit_report:
            _display_audit_report(result.audit_report)
        else:
            st.info("Audit non disponible.")

    # --- ONGLET 3 : PARAMÈTRES ---
    with tab_params:
        _display_parameters_summary(result)


def _display_audit_report(report: AuditReport) -> None:
    """Affichage du rapport d'audit (Logs & Pénalités)."""
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"### Note Globale : {int(report.global_score)}/100")
        st.metric("Rating", report.rating)

        st.markdown("#### Détails par catégorie")
        for cat, score in report.breakdown.items():
            st.text(f"{cat}: {int(score)}/100")

    with col2:
        st.markdown("#### Journal d'Audit")
        if not report.logs:
            st.success("Aucune anomalie détectée.")

        for log in report.logs:
            icon = "✅"
            if log.severity == "CRITICAL":
                icon = "⛔"
            elif log.severity == "HIGH":
                icon = "🔴"
            elif log.severity == "WARN":
                icon = "🟠"
            elif log.severity == "INFO":
                icon = "🔵"

            st.markdown(f"{icon} **[{log.category}]** {log.message} *(Impact: {log.penalty})*")


def _display_parameters_summary(result: ValuationResult) -> None:
    """Résumé des paramètres clés utilisés."""
    p = result.params
    f = result.financials

    st.markdown("#### 1. Paramètres de Marché & Risque")
    c1, c2, c3 = st.columns(3)
    c1.metric("Taux Sans Risque (Rf)", f"{p.risk_free_rate:.2%}")
    c2.metric("Prime de Risque (MRP)", f"{p.market_risk_premium:.2%}")
    c3.metric("Beta Utilisé", f"{f.beta:.2f}")

    st.markdown("#### 2. Croissance & Structure")
    c4, c5, c6 = st.columns(3)
    c4.metric("Croissance (g)", f"{p.fcf_growth_rate:.2%}")
    c5.metric("Croissance Perpétuelle", f"{p.perpetual_growth_rate:.2%}")
    c6.metric("Coût de la Dette", f"{p.cost_of_debt:.2%}")

    # Affichage spécifique si RIM ou Graham
    if isinstance(result, RIMValuationResult):
        st.markdown("#### 3. Spécifique RIM (Banques)")
        st.write(f"Book Value/Share: {result.current_book_value:.2f}")
        st.write(f"Coût des Fonds Propres (Ke): {result.cost_of_equity:.2%}")

    elif isinstance(result, GrahamValuationResult):
        st.markdown("#### 3. Spécifique Graham 1974")
        st.write(f"Yield AAA: {result.aaa_yield_used:.2%}")
        st.write(f"EPS Normalisé: {result.eps_used:.2f}")