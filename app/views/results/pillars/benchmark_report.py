"""
app/views/results/pillars/benchmark_report.py
PILLAR 3: SECTORAL BENCHMARK
============================
Role: Positions the company against its sector/peer group.
Focus: Relative Valuation (Multiples) and Operational Performance (Margins/ROE).
Style: Professional financial dashboard (Comparison only).
"""

from typing import Literal

import streamlit as st

from app.views.components.ui_charts import display_sector_comparison_chart
from app.views.components.ui_kpis import atom_benchmark_card
from src.i18n import BenchmarkTexts, PillarLabels
from src.models import ValuationResult


def _render_piotroski_section(company_stats) -> None:
    """
    Renders the Piotroski F-Score section.
    Encapsulated to keep the main view clean (SRP).
    """
    # Fallback de sécurité (Au cas où i18n n'est pas encore à jour)
    title = getattr(BenchmarkTexts, 'PIOTROSKI_TITLE', "Santé Financière (F-Score Piotroski)")
    desc = getattr(BenchmarkTexts, 'PIOTROSKI_DESC',
                   "Analyse de la solidité financière selon 9 critères (Rentabilité, Levier, Efficacité).")
    lbl_status = getattr(BenchmarkTexts, 'PIOTROSKI_LBL_STATUS', "Statut")

    st.divider()
    st.subheader(title)
    st.caption(desc)

    # Safe access to score (default to 0)
    # getattr returns None if attribute exists but is None, so we add 'or 0'
    f_score = getattr(company_stats, 'piotroski_score', 0) or 0

    # Business Logic: Score Interpretation
    interpretation = getattr(BenchmarkTexts, 'PIOTROSKI_STATUS_WEAK', "Fragile")
    detail_msg = getattr(BenchmarkTexts, 'PIOTROSKI_MSG_WEAK', "Fondamentaux de faible qualité. Profil risqué.")

    if f_score >= 7:
        interpretation = getattr(BenchmarkTexts, 'PIOTROSKI_STATUS_STRONG', "Solide")
        detail_msg = getattr(BenchmarkTexts, 'PIOTROSKI_MSG_STRONG', "Fondamentaux de haute qualité. Profil défensif.")
    elif f_score >= 4:
        interpretation = getattr(BenchmarkTexts, 'PIOTROSKI_STATUS_STABLE', "Moyen")
        detail_msg = getattr(BenchmarkTexts, 'PIOTROSKI_MSG_STABLE', "Fondamentaux moyens. Profil standard.")

    c1, c2 = st.columns([0.2, 0.8])

    with c1:
        st.metric(
            label=getattr(BenchmarkTexts, 'PIOTROSKI_LBL_SCORE', "Score F"),
            value=f"{f_score}/9",
            delta=interpretation,
            delta_color="normal"
        )

    with c2:
        st.write(f"**{lbl_status}: {interpretation}**")

        # Progress bar context
        health_txt = getattr(BenchmarkTexts, 'PIOTROSKI_LBL_HEALTH',
                             "Santé Fondamentale : {score} sur 9 points").format(score=f_score)
        # Ensure f_score is within bounds for progress bar
        progress_val = max(0.0, min(1.0, f_score / 9))
        st.progress(progress_val, text=health_txt)

        # Detail message (No emojis)
        if f_score >= 7:
            st.success(detail_msg, icon=None)
        elif f_score >= 4:
            st.warning(detail_msg, icon=None)
        else:
            st.error(detail_msg, icon=None)


def render_benchmark_view(result: ValuationResult) -> None:
    """
    Renders the Sector Benchmark View.
    """
    # 1. Access Data
    market = result.market_context
    if not market:
        st.info(BenchmarkTexts.NO_REPORT)
        return

    # Connect to company stats
    company_stats = getattr(result, 'company_stats', None)

    # 2. Header: Market Context
    st.header(PillarLabels.PILLAR_3_BENCHMARK)

    # Context Banner
    with st.container(border=True):
        c1, c2, c3 = st.columns([0.4, 0.3, 0.3])
        with c1:
            st.caption(BenchmarkTexts.LBL_SECTOR_REF)
            st.markdown(f"### {market.sector_name}")
            st.caption(f"{BenchmarkTexts.LBL_BENCHMARK_ID}: {market.reference_ticker}")
        with c2:
            st.caption(BenchmarkTexts.LBL_RF)
            st.markdown(f"**{market.risk_free_rate:.2%}**")
        with c3:
            st.caption(BenchmarkTexts.LBL_ERP)
            st.markdown(f"**{market.equity_risk_premium:.2%}**")

    st.divider()

    # 3. Valuation Multiples Comparison
    st.subheader(BenchmarkTexts.SUBTITLE_VALUATION)
    st.caption(BenchmarkTexts.DESC_VALUATION)

    col_v1, col_v2, col_v3 = st.columns(3)

    # --- Helper Logic for Status (Valuation) ---
    def get_val_status(company_val: float, sector_val: float) -> tuple[
        Literal["LEADER", "RETARD"], Literal["green", "orange"]]:
        # Handle zeros or negatives strictly if needed, but simple comparison fits
        if company_val > sector_val:
            # Expensive -> "RETARD" (Orange) in terms of value opportunity
            return "RETARD", "orange"
        # Cheap -> "LEADER" (Green)
        return "LEADER", "green"

    # P/E Ratio
    with col_v1:
        # FIX: Ensure we never pass None to logic. getattr returns None if key exists but is None.
        c_pe = getattr(company_stats, 'pe_ratio', 0.0) or 0.0
        s_pe = market.multiples.pe_ratio or 0.0
        val_status, val_color = get_val_status(c_pe, s_pe)

        atom_benchmark_card(
            label="P/E Ratio",
            company_value=f"{c_pe:.1f}x",
            market_value=f"{s_pe:.1f}x",
            status=val_status,
            status_color=val_color,
            description="Premium = Cher (Orange) | Discount = Occasion (Vert)"
        )

    # EV/EBITDA
    with col_v2:
        c_eve = getattr(company_stats, 'ev_ebitda', 0.0) or 0.0
        s_eve = market.multiples.ev_ebitda or 0.0
        val_status_ev, val_color_ev = get_val_status(c_eve, s_eve)

        atom_benchmark_card(
            label="EV/EBITDA",
            company_value=f"{c_eve:.1f}x",
            market_value=f"{s_eve:.1f}x",
            status=val_status_ev,
            status_color=val_color_ev
        )

    # P/B Ratio
    with col_v3:
        c_pb = getattr(company_stats, 'pb_ratio', 0.0) or 0.0
        s_pb = market.multiples.pb_ratio or 0.0

        # Only show P/B if the sector has relevant data, else it looks empty
        if s_pb > 0:
            val_status_pb, val_color_pb = get_val_status(c_pb, s_pb)
            atom_benchmark_card(
                label="P/B Ratio",
                company_value=f"{c_pb:.1f}x",
                market_value=f"{s_pb:.1f}x",
                status=val_status_pb,
                status_color=val_color_pb
            )

    # Visualisation Graphique
    st.markdown(f"##### {BenchmarkTexts.CHART_TITLE_VALUATION}")

    # Re-access safely for the chart
    c_pe_val = getattr(company_stats, 'pe_ratio', 0.0) or 0.0
    s_pe_val = market.multiples.pe_ratio or 0.0
    c_eve_val = getattr(company_stats, 'ev_ebitda', 0.0) or 0.0
    s_eve_val = market.multiples.ev_ebitda or 0.0

    valuation_metrics = {
        "P/E": {"company": c_pe_val, "sector": s_pe_val},
        "EV/EBITDA": {"company": c_eve_val, "sector": s_eve_val}
    }

    # Access ticker safely
    ticker_symbol = result.request.parameters.structure.ticker

    display_sector_comparison_chart(
        ticker_symbol,
        market.sector_name,
        valuation_metrics,
        suffix="x"
    )

    st.divider()

    # 4. Operational Performance Comparison
    st.subheader(BenchmarkTexts.SUBTITLE_PERFORMANCE)
    st.caption(BenchmarkTexts.DESC_PERFORMANCE)

    col_p1, col_p2, col_p3 = st.columns(3)

    # --- Helper Logic for Performance ---
    def get_perf_status(company_val: float, sector_val: float) -> tuple[
        Literal["LEADER", "RETARD"], Literal["green", "red"]]:
        if company_val > sector_val:
            return "LEADER", "green"
        return "RETARD", "red"

    # Marge FCF
    with col_p1:
        c_m = getattr(company_stats, 'fcf_margin', 0.0) or 0.0
        s_m = market.performance.fcf_margin or 0.0
        perf_status, perf_color = get_perf_status(c_m, s_m)

        atom_benchmark_card(
            label="Marge FCF",
            company_value=f"{c_m:.1%}",
            market_value=f"{s_m:.1%}",
            status=perf_status,
            status_color=perf_color
        )

    # ROE
    with col_p2:
        c_roe = getattr(company_stats, 'roe', 0.0) or 0.0
        s_roe = market.performance.roe or 0.0
        perf_status_roe, perf_color_roe = get_perf_status(c_roe, s_roe)

        atom_benchmark_card(
            label="ROE",
            company_value=f"{c_roe:.1%}",
            market_value=f"{s_roe:.1%}",
            status=perf_status_roe,
            status_color=perf_color_roe
        )

    # Croissance
    with col_p3:
        c_g = getattr(company_stats, 'revenue_growth', 0.0) or 0.0
        s_g = market.performance.revenue_growth or 0.0
        perf_status_g, perf_color_g = get_perf_status(c_g, s_g)

        atom_benchmark_card(
            label="CAGR (3Y)",
            company_value=f"{c_g:.1%}",
            market_value=f"{s_g:.1%}",
            status=perf_status_g,
            status_color=perf_color_g
        )

    # 5. Financial Strength (Piotroski)
    _render_piotroski_section(company_stats)