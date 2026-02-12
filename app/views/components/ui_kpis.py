"""
app/ui/components/ui_kpis.py
ATOMIC COMPONENTS — Minimalist style, zero emojis.
Role: Standardized KPI, Metric Cards, and Benchmark visualizations.
Aggnostic of specific business logic (Audit/Comparison), focused on rendering data.
"""

from __future__ import annotations

from typing import Literal

import streamlit as st

from src.i18n.fr.ui.results import KPITexts

# On retire les dépendances "Audit" (AuditStep, AuditTexts) pour rendre le fichier générique.

def atom_kpi_metric(label, value, delta=None, delta_color="normal", help_text=None):
    """
    Composant UI robuste pour les KPIs.
    Agit comme un 'Adapter' pour protéger l'app des changements d'API Streamlit.
    """
    # MAPPING DE SÉCURITÉ : On traduit tes couleurs métier en standards Streamlit
    color_map = {
        "green": "normal",  # Vert pour positif
        "red": "inverse",  # Rouge pour positif (ou inversion selon contexte)
        "orange": "off",  # Gris (Streamlit ne supporte pas l'orange en delta)
        "gray": "off",
        "normal": "normal",
        "inverse": "inverse",
        "off": "off"
    }

    # Si la couleur demandée n'est pas connue, on met "off" par sécurité (éviter le crash)
    safe_color = color_map.get(delta_color, "off")

    st.metric(
        label=label,
        value=str(value),
        delta=str(delta) if delta is not None else None,
        delta_color=safe_color,
        help=help_text
    )

def render_score_gauge(score: float, label: str, context_label: str = "PERFORMANCE") -> None:
    """
    Generic gauge for scores (0-100).
    Can be used for: Comparison Score, Financial Health, Digital Maturity.
    """
    # Determination of color based on generic quartiles
    if score >= 75:
        color = "green"
    elif score >= 50:
        color = "blue"  # Blue is often better for "neutral/good" in benchmarks than orange
    elif score >= 25:
        color = "orange"
    else:
        color = "red"

    with st.container(border=True):
        c1, c2 = st.columns([0.7, 0.3])
        c1.markdown(f"**{context_label.upper()}**")
        c2.markdown(
            f"<div style='text-align:right; color:{color}; font-weight:bold;'>{score:.1f}/100</div>",
            unsafe_allow_html=True,
        )

        st.progress(score / 100)

        st.caption(label)

def atom_benchmark_card(
    label: str,
    company_value: str,
    market_value: str,
    status: Literal["LEADER", "ALIGNÉ", "RETARD", "N/A"],
    status_color: Literal["green", "blue", "orange", "red", "gray"] = "gray",
    description: str = ""
) -> None:
    """
    Comparison Card: Displays Company Data vs Market/Sector Data.
    Replaces the old 'Audit Card'.
    """
    with st.container(border=True):
        # Header: Label + Status Badge
        col_head, col_badge = st.columns([0.7, 0.3])
        col_head.markdown(f"**{label.upper()}**")
        col_badge.markdown(
            f"<div style='text-align:right; color:{status_color}; font-weight:bold;"
            f" font-size:0.9em; border:1px solid {status_color}; border-radius:4px;"
            f" padding:2px 6px; display:inline-block;'>{status}</div>",
            unsafe_allow_html=True,
        )

        if description:
            st.caption(description)

        st.divider()

        # Comparison Grid
        c1, c2 = st.columns(2)

        # Left: Company (You)
        with c1:
            label_html = f"<span style='color:gray; font-size:0.8em;'>{KPITexts.LABEL_YOUR_DATA}</span>"
            st.markdown(label_html, unsafe_allow_html=True)
            st.markdown(f"**{company_value}**")

        # Right: Market (Them)
        with c2:
            label_html = f"<span style='color:gray; font-size:0.8em;'>{KPITexts.LABEL_SECTOR_AVERAGE}</span>"
            st.markdown(label_html, unsafe_allow_html=True)
            st.markdown(f"{market_value}")
