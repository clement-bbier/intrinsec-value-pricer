import streamlit as st
import pandas as pd
from typing import List

from core.models import (
    DCFValuationResult,
    DDMValuationResult,
    GrahamValuationResult,
    AuditReport,
    AuditLog
)


# --- UTILS DE FORMATAGE ---

def format_currency(value: float, currency: str) -> str:
    """Formatage financier compact (M/B)."""
    if value is None:
        return "-"

    abs_val = abs(value)
    if abs_val >= 1e9:
        return f"{value / 1e9:,.2f}B {currency}"
    elif abs_val >= 1e6:
        return f"{value / 1e6:,.2f}M {currency}"
    else:
        return f"{value:,.0f} {currency}"


def render_financial_badge(label: str, value: str, score: float = 100) -> None:
    """
    Affiche un badge style 'Terminal' avec CSS injecté.
    Couleurs : Vert (>75), Jaune (50-75), Rouge (<50).
    """
    if score >= 80:
        bg_color = "#1b5e20"  # Dark Green
        text_color = "#e8f5e9"
    elif score >= 50:
        bg_color = "#f57f17"  # Dark Orange/Yellow
        text_color = "#fffde7"
    else:
        bg_color = "#b71c1c"  # Dark Red
        text_color = "#ffebee"

    html = f"""
    <div style="
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background-color: {bg_color};
        color: {text_color};
        padding: 4px 12px;
        border-radius: 4px;
        font-family: 'Roboto Mono', monospace;
        font-size: 0.9em;
        font-weight: 600;
        margin-bottom: 5px;
    ">
        <span style="margin-right: 8px; opacity: 0.8;">{label}</span>
        <span>{value}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# --- AFFICHAGE PAR STRATÉGIE ---

def display_dcf_summary(res: DCFValuationResult) -> None:
    """Affichage standard pour DCF (Simple, Fundamental, Growth, Monte Carlo)."""

    # 1. KPIs Principaux
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("WACC", f"{res.wacc:.2%}", help="Coût Moyen Pondéré du Capital")
    with c2:
        st.metric("Croissance Perp.", f"{res.params.perpetual_growth_rate:.2%}", help="Hypothèse Terminale (g)")
    with c3:
        st.metric("Enterprise Value", format_currency(res.enterprise_value, res.financials.currency))
    with c4:
        st.metric("Equity Value", format_currency(res.equity_value, res.financials.currency))

    # 2. Tableau de Flux (Projections)
    st.subheader("Projections de Flux de Trésorerie (FCF)")

    # Construction DataFrame
    years = range(1, len(res.projected_fcfs) + 1)
    df = pd.DataFrame({
        "Année": [f"Year {y}" for y in years],
        "FCF Projeté": res.projected_fcfs,
        "Facteur Actu.": res.discount_factors,
        "Valeur Actuelle (PV)": [f * d for f, d in zip(res.projected_fcfs, res.discount_factors)]
    })

    # Formatage colonne
    st.dataframe(
        df.style.format({
            "FCF Projeté": "{:,.0f}",
            "Facteur Actu.": "{:.4f}",
            "Valeur Actuelle (PV)": "{:,.0f}"
        }),
        use_container_width=True,
        hide_index=True
    )

    # 3. Breakdown de la Valeur (Terminal Value Weight)
    pv_explicit = res.sum_discounted_fcf
    pv_terminal = res.discounted_terminal_value
    total_ev = res.enterprise_value

    if total_ev > 0:
        pct_terminal = pv_terminal / total_ev
        st.caption(f"Poids de la Valeur Terminale : {pct_terminal:.1%} (Explicit: {1 - pct_terminal:.1%})")
        if pct_terminal > 0.8:
            st.warning("Attention : >80% de la valeur repose sur l'infini (Terminal Value). Sensibilité élevée.")


def display_ddm_summary(res: DDMValuationResult) -> None:
    """Affichage spécifique Banques (DDM)."""

    # 1. KPIs
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Cost of Equity (Ke)", f"{res.cost_of_equity:.2%}", help="Pas de WACC pour les banques")
    with c2:
        st.metric("Croissance Perp.", f"{res.params.perpetual_growth_rate:.2%}")
    with c3:
        st.metric("Equity Value", format_currency(res.equity_value, res.financials.currency))

    # 2. Tableau Dividendes
    st.subheader("Projections de Dividendes")

    df = pd.DataFrame({
        "Année": range(1, len(res.projected_dividends) + 1),
        "Dividende Attendu": res.projected_dividends,
        "Facteur (Ke)": res.discount_factors,
        "PV Dividende": [d * f for d, f in zip(res.projected_dividends, res.discount_factors)]
    })

    st.dataframe(
        df.style.format({
            "Dividende Attendu": "{:,.2f}",
            "Facteur (Ke)": "{:.4f}",
            "PV Dividende": "{:,.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )


def display_graham_summary(res: GrahamValuationResult) -> None:
    """Affichage formule de Graham."""

    st.info("ℹ️ La méthode de Graham est une approche heuristique 'Deep Value', sans projection de flux.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("EPS (Bénéfice/Action)", f"{res.eps_used:.2f}")
    with c2:
        st.metric("BVPS (Actif Net/Action)", f"{res.book_value_used:.2f}")
    with c3:
        st.metric("Multiplicateur", f"{res.graham_multiplier}")

    st.markdown("---")
    st.markdown(
        f"#### Formule : $V = \\sqrt{{ {res.graham_multiplier} \\times {res.eps_used:.2f} \\times {res.book_value_used:.2f} }}$")


# --- AUDIT REPORT ---

def display_audit_report(report: AuditReport) -> None:
    """Affichage sobre et tabulaire du rapport d'audit."""

    with st.expander(f"Détail de l'Audit ({len(report.logs)} points)", expanded=False):
        # Conversion des logs en DataFrame pour un affichage propre
        if not report.logs:
            st.success("Aucune anomalie détectée.")
            return

        data = []
        for log in report.logs:
            data.append({
                "Sévérité": log.severity.upper(),
                "Catégorie": log.category,
                "Message": log.message,
                "Impact Score": f"{log.penalty}"
            })

        df_audit = pd.DataFrame(data)

        # Coloration conditionnelle simple via pandas styler si besoin,
        # ou simple affichage dataframe Streamlit
        st.dataframe(
            df_audit,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Sévérité": st.column_config.TextColumn(
                    "Niveau",
                    help="CRITICAL, HIGH, WARN, INFO",
                    width="small"
                ),
                "Impact Score": st.column_config.NumberColumn(
                    "Pénalité",
                    format="%d pts"
                )
            }
        )

        if report.critical_warning:
            st.error("RÉSULTAT NON FIABLE : Des erreurs critiques ont été détectées (voir tableau ci-dessus).")