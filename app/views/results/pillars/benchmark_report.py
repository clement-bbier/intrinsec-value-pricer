"""
app/views/results/pillars/benchmark_report.py
PILLAR 3: SECTORAL BENCHMARK
============================
Role: Positions the company against its sector/peer group.
Focus: Relative Valuation (Multiples) and Operational Performance (Margins/ROE).
Style: Professional financial dashboard (Comparison only).
"""

import streamlit as st

from app.views.components.ui_charts import display_sector_comparison_chart
from app.views.components.ui_kpis import atom_benchmark_card
from src.i18n import BenchmarkTexts, PillarLabels
from src.models import ValuationResult


def _safe_float(val: float | None) -> float:
    """
    Returns 0.0 when the value is None.

    Parameters
    ----------
    val : float | None
        The value to safely coerce.

    Returns
    -------
    float
        The original value, or 0.0 if None.
    """
    return val if val is not None else 0.0


def _render_piotroski_section(company_stats) -> None:
    """
    Renders the Piotroski F-Score section.

    Parameters
    ----------
    company_stats : CompanyStats
        The computed company financial statistics.
    """
    st.divider()
    st.subheader(BenchmarkTexts.PIOTROSKI_TITLE)
    st.caption(BenchmarkTexts.PIOTROSKI_DESC)

    # Direct attribute access — Resolver guarantees non-None for piotroski_score
    f_score = company_stats.piotroski_score if company_stats.piotroski_score is not None else 0

    # Business Logic: Score Interpretation
    if f_score >= 7:
        interpretation = BenchmarkTexts.PIOTROSKI_STATUS_STRONG
        detail_msg = BenchmarkTexts.PIOTROSKI_MSG_STRONG
    elif f_score >= 4:
        interpretation = BenchmarkTexts.PIOTROSKI_STATUS_STABLE
        detail_msg = BenchmarkTexts.PIOTROSKI_MSG_STABLE
    else:
        interpretation = BenchmarkTexts.PIOTROSKI_STATUS_WEAK
        detail_msg = BenchmarkTexts.PIOTROSKI_MSG_WEAK

    c1, c2 = st.columns([0.2, 0.8])

    with c1:
        st.metric(
            label=BenchmarkTexts.PIOTROSKI_LBL_SCORE,
            value=f"{f_score}/9",
            delta=interpretation,
            delta_color="normal"
        )

    with c2:
        st.write(f"**{BenchmarkTexts.PIOTROSKI_LBL_STATUS}: {interpretation}**")

        health_txt = BenchmarkTexts.PIOTROSKI_LBL_HEALTH.format(score=f_score)
        progress_val = max(0.0, min(1.0, f_score / 9))
        st.progress(progress_val, text=health_txt)

        if f_score >= 7:
            st.success(detail_msg, icon=None)
        elif f_score >= 4:
            st.warning(detail_msg, icon=None)
        else:
            st.error(detail_msg, icon=None)


def render_benchmark_view(result: ValuationResult) -> None:
    """
    Renders the Sector Benchmark View.

    Parameters
    ----------
    result : ValuationResult
        The complete valuation result containing market context data.
    """
    # 1. Access Data
    market = result.market_context
    if not market:
        st.info(BenchmarkTexts.NO_REPORT)
        return

    # Direct attribute access — Resolver guarantees these fields
    company_stats = result.company_stats

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
    def get_val_status(company_val: float, sector_val: float) -> tuple[str, str]:
        if company_val > sector_val:
            return BenchmarkTexts.STATUS_LAGGING, "orange"
        return BenchmarkTexts.STATUS_LEADER, "green"

    # P/E Ratio
    with col_v1:
        c_pe = _safe_float(company_stats.pe_ratio)
        s_pe = _safe_float(market.multiples.pe_ratio)
        val_status, val_color = get_val_status(c_pe, s_pe)

        atom_benchmark_card(
            label="P/E Ratio",
            company_value=f"{c_pe:.1f}x",
            market_value=f"{s_pe:.1f}x",
            status=val_status,
            status_color=val_color,
            description=BenchmarkTexts.DESC_PREMIUM_DISCOUNT
        )

    # EV/EBITDA
    with col_v2:
        c_eve = _safe_float(company_stats.ev_ebitda)
        s_eve = _safe_float(market.multiples.ev_ebitda)
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
        c_pb = _safe_float(company_stats.pb_ratio)
        s_pb = _safe_float(market.multiples.pb_ratio)

        if s_pb > 0:
            val_status_pb, val_color_pb = get_val_status(c_pb, s_pb)
            atom_benchmark_card(
                label="P/B Ratio",
                company_value=f"{c_pb:.1f}x",
                market_value=f"{s_pb:.1f}x",
                status=val_status_pb,
                status_color=val_color_pb
            )

    # Chart visualization
    st.markdown(f"##### {BenchmarkTexts.CHART_TITLE_VALUATION}")

    c_pe_val = _safe_float(company_stats.pe_ratio)
    s_pe_val = _safe_float(market.multiples.pe_ratio)
    c_eve_val = _safe_float(company_stats.ev_ebitda)
    s_eve_val = _safe_float(market.multiples.ev_ebitda)

    valuation_metrics = {
        "P/E": {"company": c_pe_val, "sector": s_pe_val},
        "EV/EBITDA": {"company": c_eve_val, "sector": s_eve_val}
    }

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

    def get_perf_status(company_val: float, sector_val: float) -> tuple[str, str]:
        if company_val > sector_val:
            return BenchmarkTexts.STATUS_LEADER, "green"
        return BenchmarkTexts.STATUS_LAGGING, "red"

    # FCF Margin
    with col_p1:
        c_m = _safe_float(company_stats.fcf_margin)
        s_m = _safe_float(market.performance.fcf_margin)
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
        c_roe = _safe_float(company_stats.roe)
        s_roe = _safe_float(market.performance.roe)
        perf_status_roe, perf_color_roe = get_perf_status(c_roe, s_roe)

        atom_benchmark_card(
            label="ROE",
            company_value=f"{c_roe:.1%}",
            market_value=f"{s_roe:.1%}",
            status=perf_status_roe,
            status_color=perf_color_roe
        )

    # Growth
    with col_p3:
        c_g = _safe_float(company_stats.revenue_growth)
        s_g = _safe_float(market.performance.revenue_growth)
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
