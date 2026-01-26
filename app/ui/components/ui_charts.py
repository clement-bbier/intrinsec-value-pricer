"""
app/ui_components/ui_charts.py
MOTEUR DE VISUALISATION — TERMINAL DE VALORISATION
Rôle : Rendu graphique haute précision (Altair/Plotly) avec isolation ST-3.2.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Callable

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from src.i18n import (
    ChartTexts,
    KPITexts,
    SOTPTexts,
    BacktestTexts,
    QuantTexts,
    CommonTexts,
    UIMessages
)
from src.models import ValuationResult, BacktestResult
from src.config.constants import TechnicalDefaults

logger = logging.getLogger(__name__)

# ============================================================================
# 1. ANALYSE TECHNIQUE : HISTORIQUE DE PRIX
# ============================================================================

def display_price_chart(ticker: str, price_history: Optional[pd.DataFrame]) -> None:
    """Rendu épuré de l'historique de cours (Style Bloomberg)."""
    if price_history is None or price_history.empty:
        st.info(UIMessages.CHART_UNAVAILABLE)
        return

    # Préparation rigoureuse du DataFrame
    df = price_history.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors='coerce')
    df = df.reset_index()

    # Détection dynamique des colonnes (Zéro hardcoding)
    date_col = next((c for c in df.columns if str(c).lower() in ['date', 'index']), None)
    price_col = "Close" if "Close" in df.columns else None

    if not date_col or not price_col:
        st.warning(UIMessages.CHART_UNAVAILABLE)
        return

    df = df.rename(columns={date_col: "date", price_col: "price"}).dropna()

    chart = alt.Chart(df).mark_line(color='#1E3056', strokeWidth=1.5).encode(
        x=alt.X('date:T', title=None, axis=alt.Axis(format='%Y-%m', labelColor='#64748b')),
        y=alt.Y('price:Q', scale=alt.Scale(zero=False), title=None, axis=alt.Axis(labelColor='#64748b')),
        tooltip=[
            alt.Tooltip('date:T', format='%Y-%m-%d', title=CommonTexts.TABLE_HEADER_METRIC),
            alt.Tooltip('price:Q', format=',.2f', title=KPITexts.LABEL_PRICE)
        ]
    ).properties(
        height=300,
        title=ChartTexts.PRICE_HISTORY_TITLE.format(ticker=ticker)
    ).interactive()

    st.altair_chart(chart, use_container_width=True)


# ============================================================================
# 2. ANALYSE QUANTITATIVE : MONTE CARLO (KDE & VAR)
# ============================================================================

@st.fragment
def display_simulation_chart(simulation_results: List[float], market_price: float, currency: str) -> None:
    """Distribution stochastique avec visualisation de la Value-at-Risk (VaR)."""
    if not simulation_results:
        st.warning(QuantTexts.MC_FAILED)
        return

    values = np.array([v for v in simulation_results if v is not None and not np.isnan(v)])
    if values.size == 0: return

    # Calcul des ancres institutionnelles
    p50 = np.median(values)
    p10 = np.percentile(values, 10)
    p90 = np.percentile(values, 90)

    df_sim = pd.DataFrame({"value": values})

    # 1. Histogramme de densité
    hist = alt.Chart(df_sim).mark_bar(color="#94a3b8", opacity=0.6).encode(
        x=alt.X("value:Q", bin=alt.Bin(maxbins=50), title=ChartTexts.SIM_AXIS_X.format(currency=currency)),
        y=alt.Y("count()", title=None)
    )

    # 2. Lignes de démarcation (Médiane & Quantiles)
    rule_p50 = alt.Chart(pd.DataFrame({'x': [p50]})).mark_rule(color="#1e293b", strokeWidth=2).encode(x='x')
    rule_ci = alt.Chart(pd.DataFrame({'x': [p10, p90]})).mark_rule(color="#ef4444", strokeDash=[4, 4]).encode(x='x')

    # 3. Ligne de prix de marché
    price_marker = alt.Chart(pd.DataFrame({'x': [market_price]})).mark_rule(color="#3b82f6", strokeWidth=2).encode(x='x')

    final_layer = alt.layer(hist, rule_p50, rule_ci, price_marker).properties(height=320)
    st.altair_chart(final_layer, use_container_width=True)

    # Note de synthèse probabiliste (i18n)
    st.markdown(f"""
    <div style="font-size: 0.85rem; color: #64748b; padding: 10px; border-left: 3px solid #1e293b; background: #f8fafc;">
        <b>{QuantTexts.MC_TITLE}</b> : {len(values):,} itérations | 
        {QuantTexts.MC_MEDIAN} : <b>{p50:,.2f} {currency}</b> | 
        CI 80% : {p10:,.2f} — {p90:,.2f}
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# 3. STRATÉGIE : FOOTBALL FIELD (TRIANGULATION)
# ============================================================================

@st.fragment
def display_football_field(result: ValuationResult) -> None:
    """Visualisation de la triangulation entre modèles intrinsèques et relatifs."""
    st.markdown(f"**{KPITexts.FOOTBALL_FIELD_TITLE}**")

    data = []
    currency = result.financials.currency

    # Signal Intrinsèque (P10 - Mid - P90)
    iv_mid = result.intrinsic_value_per_share
    iv_low = result.quantiles.get("P10", iv_mid * 0.9) if result.quantiles else iv_mid * 0.9
    iv_high = result.quantiles.get("P90", iv_mid * 1.1) if result.quantiles else iv_mid * 1.1

    data.append({
        "method": KPITexts.LABEL_FOOTBALL_FIELD_IV,
        "low": iv_low, "high": iv_high, "mid": iv_mid,
        "color": "#1e293b"
    })

    # Signaux de Marché (Multiples)
    if result.multiples_triangulation:
        rel = result.multiples_triangulation
        multiples = [
            (KPITexts.LABEL_FOOTBALL_FIELD_PE, rel.pe_based_price),
            (KPITexts.LABEL_FOOTBALL_FIELD_EBITDA, rel.ebitda_based_price),
            (KPITexts.LABEL_FOOTBALL_FIELD_REV, rel.rev_based_price)
        ]
        for label, val in multiples:
            if val > 0:
                data.append({"method": label, "low": val * 0.95, "high": val * 1.05, "mid": val, "color": "#94a3b8"})

    if not data:
        st.info(KPITexts.LABEL_MULTIPLES_UNAVAILABLE)
        return

    df = pd.DataFrame(data)

    # Graphique de triangulation
    base = alt.Chart(df).encode(
        y=alt.Y("method:N", title=None, sort=None),
        x=alt.X("low:Q", scale=alt.Scale(zero=False), title=f"{KPITexts.INTRINSIC_PRICE_LABEL} ({currency})")
    )

    bars = base.mark_bar(height=18, cornerRadius=2).encode(
        x="low:Q", x2="high:Q", color=alt.Color("color:N", scale=None)
    )

    ticks = base.mark_tick(color="white", size=18, thickness=2).encode(x="mid:Q")

    price_line = alt.Chart(pd.DataFrame({"x": [result.market_price]})).mark_rule(
        color="#ef4444", strokeWidth=2, strokeDash=[4, 4]
    ).encode(x="x:Q")

    st.altair_chart((bars + ticks + price_line).properties(height=250), use_container_width=True)


# ============================================================================
# 4. SENSIBILITÉ : HEATMAP WACC/G
# ============================================================================

@st.fragment
def display_sensitivity_heatmap(
    base_rate: float,
    base_growth: float,
    calculator_func: Callable,
    currency: str = "EUR",
    is_direct_equity: bool = False
) -> None:
    """Matrice de sensibilité bidimensionnelle (Stress Test)."""
    st.markdown(f"**{ChartTexts.SENS_TITLE}**")

    label_y = KPITexts.LABEL_KE if is_direct_equity else KPITexts.LABEL_WACC

    # Génération de la matrice
    rate_range = np.linspace(base_rate - 0.01, base_rate + 0.01, 5)
    growth_range = np.linspace(base_growth - 0.005, base_growth + 0.005, 5)

    grid = []
    for r in rate_range:
        for g in growth_range:
            if r <= g: continue
            val = calculator_func(r, g)
            grid.append({"rate": r, "growth": g, "val": val})

    if not grid:
        st.warning(UIMessages.CHART_UNAVAILABLE)
        return

    df = pd.DataFrame(grid)

    chart = alt.Chart(df).mark_rect().encode(
        x=alt.X('growth:O', title=KPITexts.LABEL_G, axis=alt.Axis(format='.2%')),
        y=alt.Y('rate:O', title=label_y, axis=alt.Axis(format='.2%')),
        color=alt.Color('val:Q', scale=alt.Scale(scheme='blues'), legend=None),
        tooltip=[
            alt.Tooltip('rate:O', format='.2%', title=label_y),
            alt.Tooltip('growth:O', format='.2%', title=KPITexts.LABEL_G),
            alt.Tooltip('val:Q', format=',.2f', title=KPITexts.LABEL_IV)
        ]
    )

    text = chart.mark_text(baseline='middle').encode(
        text=alt.Text('val:Q', format=',.0f'),
        color=alt.condition(alt.datum.val > df['val'].median(), alt.value('white'), alt.value('black'))
    )

    st.altair_chart((chart + text).properties(height=350), use_container_width=True)


# ============================================================================
# 5. SEGMENTATION : WATERFALL SOTP
# ============================================================================

@st.fragment
def display_sotp_waterfall(result: ValuationResult) -> None:
    """Cascade de valorisation par segments (Sum-of-the-Parts)."""
    if not result.params.sotp.enabled: return

    params = result.params.sotp
    f = result.financials

    # Construction du Bridge SOTP
    labels, values, measures = [], [], []

    # Segments
    for seg in params.segments:
        labels.append(seg.name)
        values.append(seg.enterprise_value)
        measures.append("relative")

    # Décote Holding
    if params.conglomerate_discount > 0:
        labels.append(SOTPTexts.LBL_DISCOUNT)
        values.append(-(sum(values) * params.conglomerate_discount))
        measures.append("relative")

    # Bridge technique
    labels.append(SOTPTexts.LBL_ENTERPRISE_VALUE)
    values.append(0)
    measures.append("total")

    bridge = [
        (KPITexts.LABEL_NET_DEBT, -f.net_debt),
        (KPITexts.LABEL_MINORITIES, -f.minority_interests)
    ]
    for lbl, val in bridge:
        if val != 0:
            labels.append(lbl); values.append(val); measures.append("relative")

    labels.append(KPITexts.EQUITY_VALUE_LABEL)
    values.append(0); measures.append("total")

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        text=[f"{v:,.0f}" if v != 0 else "" for v in values],
        textposition="outside",
        decreasing={"marker": {"color": "#ef4444"}},
        increasing={"marker": {"color": "#10b981"}},
        totals={"marker": {"color": "#1e293b"}}
    ))

    fig.update_layout(
        title=SOTPTexts.DESC_WATERFALL,
        height=450,
        font=dict(family="Inter", size=11),
        margin=dict(t=40, b=20, l=20, r=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True)

@st.fragment
def display_backtest_convergence_chart(backtest_report: Optional[BacktestResult], currency: str) -> None:
    """Convergence historique : Prédit vs Réel."""
    if not backtest_report: return

    data = []
    for p in backtest_report.points:
        data.append({"date": p.valuation_date, "type": BacktestTexts.LBL_HIST_IV, "val": p.intrinsic_value})
        data.append({"date": p.valuation_date, "type": BacktestTexts.LBL_REAL_PRICE, "val": p.market_price})

    df = pd.DataFrame(data)

    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('date:T', title=None, axis=alt.Axis(format='%Y')),
        y=alt.Y('val:Q', scale=alt.Scale(zero=False), title=f"{currency}"),
        color=alt.Color('type:N', title=None, scale=alt.Scale(range=['#10b981', '#ef4444'])),
        tooltip=['date:T', 'type:N', alt.Tooltip('val:Q', format=',.2f')]
    ).properties(height=350).interactive()

    st.altair_chart(chart, use_container_width=True)