"""
app/views/components/ui_charts.py
VISUALIZATION ENGINE
====================
Role: High-precision graphical rendering (Altair/Plotly).
Architecture: Stateless View Components.
"""

from __future__ import annotations
import logging
from typing import List, Optional, Callable

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from src.models import ValuationResult
from src.models.results.options import BacktestResults
from src.i18n import (
    KPITexts,
    QuantTexts,
    SOTPTexts,
    ChartTexts,
    BacktestTexts
)

logger = logging.getLogger(__name__)

# ============================================================================
# 1. MARKET DATA VISUALIZATION
# ============================================================================

@st.fragment
def display_price_chart(ticker: str, price_history: Optional[pd.DataFrame]) -> None:
    """Streamlined price history rendering."""
    if price_history is None or price_history.empty:
        st.info("Données de prix historiques indisponibles.")
        return

    df = price_history.copy()
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors='coerce')
    df = df.reset_index()

    # Dynamic column detection
    date_col = next((c for c in df.columns if str(c).lower() in ['date', 'index']), None)
    price_col = "Close" if "Close" in df.columns else None

    if not date_col or not price_col:
        return

    df = df.rename(columns={date_col: "date", price_col: "price"}).dropna()

    chart = alt.Chart(df).mark_area(
        line={'color':'#3b82f6'},
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color='#3b82f6', offset=0),
                   alt.GradientStop(color='rgba(255,255,255,0)', offset=1)],
            x1=1, x2=1, y1=1, y2=0
        )
    ).encode(
        x=alt.X('date:T', title=None, axis=alt.Axis(format='%Y-%m', labelColor='#64748b')),
        y=alt.Y('price:Q', scale=alt.Scale(zero=False), title=None, axis=alt.Axis(labelColor='#64748b')),
        tooltip=[
            alt.Tooltip('date:T', format='%Y-%m-%d', title="Date"),
            alt.Tooltip('price:Q', format=',.2f', title=KPITexts.LABEL_PRICE)
        ]
    ).properties(height=300).interactive()

    # Unique key based on ticker to avoid Streamlit conflicts
    st.altair_chart(chart, use_container_width=True, key=f"price_chart_{ticker}")


# ============================================================================
# 2. QUANTITATIVE ANALYSIS: MONTE CARLO
# ============================================================================

@st.fragment
def display_simulation_chart(simulation_results: List[float], currency: str) -> None:
    """Stochastic distribution visualization."""
    if not simulation_results:
        st.warning(QuantTexts.MC_FAILED)
        return

    values = np.array(simulation_results)
    p50, p10, p90 = np.median(values), np.percentile(values, 10), np.percentile(values, 90)
    df_sim = pd.DataFrame({"value": values})

    # Histogram
    hist = alt.Chart(df_sim).mark_bar(color="#94a3b8", opacity=0.6).encode(
        x=alt.X("value:Q", bin=alt.Bin(maxbins=50), title=f"{ChartTexts.SIM_AXIS_X.format(currency=currency)}"),
        y=alt.Y("count()", title=ChartTexts.SIM_AXIS_Y)
    )

    # Anchors (Median & Confidence Interval)
    rule_p50 = alt.Chart(pd.DataFrame({'x': [p50]})).mark_rule(color="#1e293b", strokeWidth=2).encode(x='x')
    rule_ci = alt.Chart(pd.DataFrame({'x': [p10, p90]})).mark_rule(color="#ef4444", strokeDash=[4, 4]).encode(x='x')

    st.altair_chart(alt.layer(hist, rule_p50, rule_ci).properties(height=320), use_container_width=True)

    # Stats Summary HTML block
    st.markdown(f"""
    <div style="font-size: 0.85rem; color: #64748b; padding: 10px; border-left: 3px solid #1e293b; background: #f8fafc; border-radius: 4px; margin-top: 10px;">
        {len(values):,} {QuantTexts.MC_TITLE} | 
        {QuantTexts.MC_MEDIAN} : <b>{p50:,.2f} {currency}</b> |
        {QuantTexts.CONFIDENCE_INTERVAL} 80% : {p10:,.2f} — {p90:,.2f}
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# 3. STRATEGY: FOOTBALL FIELD
# ============================================================================

@st.fragment
def display_football_field(result: ValuationResult) -> None:
    """Visual triangulation between intrinsic and relative models."""
    data = []

    # 1. Intrinsic Model (Anchor)
    iv_mid = result.results.common.intrinsic_value_per_share

    # Use generic bounds if MC not available
    iv_low = iv_mid * 0.9
    iv_high = iv_mid * 1.1

    # Try to fetch robust bounds from MC if available
    if result.results.extensions.monte_carlo:
        qs = result.results.extensions.monte_carlo.quantiles
        iv_low = qs.get("P10", iv_low)
        iv_high = qs.get("P90", iv_high)

    data.append({
        "method": ChartTexts.SENS_TITLE,
        "low": iv_low, "high": iv_high, "mid": iv_mid, "color": "#1e293b"
    })

    # 2. Relative Valuation (Peers)
    if result.results.extensions.peers:
        peers_res = result.results.extensions.peers
        prices = peers_res.implied_prices

        # Mapping labels from KPITexts
        labels_map = {
            "P/E": KPITexts.LABEL_FOOTBALL_FIELD_PE,
            "EV/EBITDA": KPITexts.LABEL_FOOTBALL_FIELD_EBITDA,
            "EV/Revenue": KPITexts.LABEL_FOOTBALL_FIELD_REV
        }

        for key, val in prices.items():
            if val > 0:
                label = labels_map.get(key, key)
                data.append({
                    "method": label,
                    "low": val * 0.85,
                    "high": val * 1.15,
                    "mid": val,
                    "color": "#94a3b8"
                })

    if not data:
        return

    df = pd.DataFrame(data)

    base = alt.Chart(df).encode(y=alt.Y("method", title=None, sort=None))

    # Range bars
    bars = base.mark_bar(size=20).encode(
        x="low:Q", x2="high:Q", color=alt.Color("color:N", scale=None)
    )

    # Median ticks
    ticks = base.mark_tick(color="white", size=18, thickness=2).encode(x="mid:Q")

    # Current Price Marker
    current_price = result.request.parameters.structure.current_price
    price_line = alt.Chart(pd.DataFrame({"x": [current_price]})).mark_rule(
        color="#ef4444", strokeWidth=2, strokeDash=[4, 4]
    ).encode(x="x:Q")

    st.altair_chart((bars + ticks + price_line).properties(height=250), use_container_width=True)


# ============================================================================
# 4. SENSITIVITY: HEATMAP WACC/G
# ============================================================================

@st.fragment
def display_sensitivity_heatmap(
    base_rate: float,
    base_growth: float,
    calculator_func: Callable[[float, float], float],
    currency: str = "EUR",
    is_direct_equity: bool = False
) -> None:
    """
    Two-dimensional sensitivity matrix (Stress Test).
    Generates a 5x5 grid varying Rate (+/- 1%) and Growth (+/- 0.5%).
    """
    label_y = QuantTexts.AXIS_WACC if not is_direct_equity else "Ke (Cost of Equity)"
    label_x = QuantTexts.AXIS_GROWTH

    # Generate ranges centered on base assumptions
    rate_range = np.linspace(base_rate - 0.01, base_rate + 0.01, 5)
    growth_range = np.linspace(base_growth - 0.005, base_growth + 0.005, 5)

    grid = []
    for r in rate_range:
        for g in growth_range:
            # Basic sanity check: Rate > Growth to avoid negative/infinite denominator in perpetuity
            if r <= g:
                continue

            # Execute injection of parameters into the valuation model
            try:
                val = calculator_func(r, g)
                grid.append({"rate": r, "growth": g, "val": val})
            except (ZeroDivisionError, ValueError, ArithmeticError) as e:
                logger.warning(
                    f"Sensitivity calc skipped for [Rate: {r:.2%}, Growth: {g:.2%}] - Reason: {e}"
                )
                continue

    if not grid:
        st.warning("Impossible de générer la matrice de sensibilité (Taux <= Croissance).")
        return

    df = pd.DataFrame(grid)
    median_val = float(df['val'].median())

    base = alt.Chart(df).encode(
        x=alt.X('growth:O', title=label_x, axis=alt.Axis(format='.2%')),
        y=alt.Y('rate:O', title=label_y, axis=alt.Axis(format='.2%'))
    )

    # Heatmap rectangles
    rects = base.mark_rect().encode(
        color=alt.Color('val:Q', scale=alt.Scale(scheme='blues'), legend=None),
        tooltip=[
            alt.Tooltip('rate:O', format='.2%', title=label_y),
            alt.Tooltip('growth:O', format='.2%', title=label_x),
            alt.Tooltip('val:Q', format=',.2f', title=f"IV ({currency})")
        ]
    )

    # Text overlay
    text = base.mark_text(baseline='middle').encode(
        text=alt.Text('val:Q', format=',.0f'),
        color=alt.condition(
            alt.datum.val > median_val,
            alt.value('white'),
            alt.value('black')
        )
    )

    st.altair_chart((rects + text).properties(height=350), use_container_width=True)


# ============================================================================
# 5. SEGMENTATION & BACKTESTING
# ============================================================================

@st.fragment
def display_sotp_waterfall(result: ValuationResult) -> None:
    """Valuation waterfall by segments (SOTP)."""
    sotp = result.results.extensions.sotp
    if not sotp:
        return

    labels, values, measures = [], [], []

    # Segments
    for name, val in sotp.segment_values.items():
        labels.append(name)
        values.append(val)
        measures.append("relative")

    # Holding Discount
    gross_total = sum(sotp.segment_values.values())
    net_total = sotp.total_enterprise_value
    discount_val = net_total - gross_total

    if abs(discount_val) > 1.0:
        labels.append(SOTPTexts.LABEL_HOLDING_DISCOUNT)
        values.append(discount_val)
        measures.append("relative")

    # Subtotal EV
    labels.append(SOTPTexts.LBL_ENTERPRISE_VALUE)
    values.append(0)
    measures.append("total")

    # Bridge to Equity (Debt/Cash)
    cap = result.request.parameters.common.capital
    if cap.total_debt:
        labels.append(KPITexts.LABEL_DEBT)
        values.append(-cap.total_debt)
        measures.append("relative")

    if cap.cash_and_equivalents:
        labels.append(KPITexts.LABEL_CASH)
        values.append(cap.cash_and_equivalents)
        measures.append("relative")

    # Final Equity
    labels.append(KPITexts.EQUITY_VALUE_LABEL)
    values.append(0)
    measures.append("total")

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#ef4444"}},
        increasing={"marker": {"color": "#3b82f6"}},
        totals={"marker": {"color": "#1e293b"}}
    ))

    fig.update_layout(
        height=450,
        font=dict(family="Inter", size=11),
        margin=dict(t=40, b=20, l=20, r=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True)


@st.fragment
def display_backtest_convergence_chart(backtest_report: Optional[BacktestResults], currency: str) -> None:
    """Historical convergence chart."""
    if not backtest_report or not backtest_report.points:
        st.info(BacktestTexts.NO_BACKTEST_FOUND)
        return

    data = []
    for p in backtest_report.points:
        # CORRECTION : Utilisation des bons attributs LABEL_xxx au lieu de LBL_xxx
        data.append({
            "date": p.valuation_date,
            "type": BacktestTexts.LABEL_HIST_IV,
            "val": p.calculated_iv
        })
        data.append({
            "date": p.valuation_date,
            "type": BacktestTexts.LABEL_REAL_PRICE,
            "val": p.market_price
        })

    df = pd.DataFrame(data)

    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('date:T', axis=alt.Axis(format='%Y-%m', title=None)),
        y=alt.Y('val:Q', scale=alt.Scale(zero=False), title=f"Prix ({currency})"),
        color=alt.Color('type:N', legend=alt.Legend(title=None, orient='top')),
        tooltip=['date:T', 'type:N', alt.Tooltip('val:Q', format=',.2f')]
    ).properties(height=350).interactive()

    st.altair_chart(chart, use_container_width=True)