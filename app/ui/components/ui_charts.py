"""
app/ui/components/ui_charts.py
MOTEUR DE VISUALISATION — TERMINAL DE VALORISATION
==================================================
Rôle : Rendu graphique haute précision (Altair/Plotly).
Note : Version 2026 corrigée (Duplicate IDs & Layout stretch).
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
    KPITexts,
    QuantTexts,
    UIMessages
)
from src.models import ValuationResult, BacktestResult

logger = logging.getLogger(__name__)

# ============================================================================
# 1. ANALYSE TECHNIQUE : HISTORIQUE DE PRIX
# ============================================================================

@st.fragment
def display_price_chart(ticker: str, price_history: Optional[pd.DataFrame]) -> None:
    """Rendu épuré de l'historique de cours (Style Bloomberg)."""
    if price_history is None or price_history.empty:
        st.info(UIMessages.CHART_UNAVAILABLE)
        return

    df = price_history.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors='coerce')
    df = df.reset_index()

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
            alt.Tooltip('date:T', format='%Y-%m-%d', title="Date"),
            alt.Tooltip('price:Q', format=',.2f', title=KPITexts.LABEL_PRICE)
        ]
    ).properties(height=300).interactive()

    st.altair_chart(chart, width='stretch', key=f"price_chart_{ticker}")


# ============================================================================
# 2. ANALYSE QUANTITATIVE : MONTE CARLO (KDE & VAR)
# ============================================================================

@st.fragment
def display_simulation_chart(ticker: str, simulation_results: List[float], market_price: float, currency: str) -> None:
    """Distribution stochastique avec visualisation de la VaR et des quantiles."""
    if not simulation_results:
        st.warning(QuantTexts.MC_FAILED)
        return

    values = np.array([v for v in simulation_results if v is not None and not np.isnan(v)])
    if values.size == 0: return

    p50, p10, p90 = np.median(values), np.percentile(values, 10), np.percentile(values, 90)
    df_sim = pd.DataFrame({"value": values})

    # Histogramme de densité
    hist = alt.Chart(df_sim).mark_bar(color="#94a3b8", opacity=0.6).encode(
        x=alt.X("value:Q", bin=alt.Bin(maxbins=50), title=f"Valeur par action ({currency})"),
        y=alt.Y("count()", title=None)
    )

    # Lignes d'ancrage
    rule_p50 = alt.Chart(pd.DataFrame({'x': [p50]})).mark_rule(color="#1e293b", strokeWidth=2).encode(x='x')
    rule_ci = alt.Chart(pd.DataFrame({'x': [p10, p90]})).mark_rule(color="#ef4444", strokeDash=[4, 4]).encode(x='x')
    price_marker = alt.Chart(pd.DataFrame({'x': [market_price]})).mark_rule(color="#3b82f6", strokeWidth=2).encode(x='x')

    st.altair_chart(alt.layer(hist, rule_p50, rule_ci, price_marker).properties(height=320),
                    width='stretch', key=f"mc_dist_{ticker}")

    # Synthèse probabiliste
    st.markdown(f"""
    <div style="font-size: 0.85rem; color: #64748b; padding: 10px; border-left: 3px solid #1e293b; background: #f8fafc; border-radius: 4px; margin-top: 10px;">
        {len(values):,} itérations | 
        {QuantTexts.MC_MEDIAN} : <b>{p50:,.2f} {currency}</b> | 
        Intervalle de confiance 80% : {p10:,.2f} — {p90:,.2f}
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# 3. STRATÉGIE : FOOTBALL FIELD (TRIANGULATION)
# ============================================================================

@st.fragment
def display_football_field(result: ValuationResult) -> None:
    """Triangulation visuelle entre modèles intrinsèques et relatifs."""
    data = []
    ticker = result.ticker
    currency = result.financials.currency
    iv_mid = result.intrinsic_value_per_share

    iv_low = result.quantiles.get("P10", iv_mid * 0.9) if result.quantiles else iv_mid * 0.9
    iv_high = result.quantiles.get("P90", iv_mid * 1.1) if result.quantiles else iv_mid * 1.1

    data.append({
        "method": "Valeur intrinsèque",
        "low": iv_low, "high": iv_high, "mid": iv_mid, "color": "#1e293b"
    })

    if result.multiples_triangulation:
        rel = result.multiples_triangulation
        multiples = [
            (KPITexts.LABEL_FOOTBALL_FIELD_PE, rel.pe_based_price),
            (KPITexts.LABEL_FOOTBALL_FIELD_EBITDA, rel.ebitda_based_price),
            (KPITexts.LABEL_FOOTBALL_FIELD_REV, rel.rev_based_price)
        ]
        for label, val in multiples:
            if val > 0:
                data.append({"method": label, "low": val * 0.9, "high": val * 1.1, "mid": val, "color": "#94a3b8"})

    if not data: return

    df = pd.DataFrame(data)
    base = alt.Chart(df).encode(
        y=alt.Y("method:N", title=None, sort=None),
        x=alt.X("low:Q", scale=alt.Scale(zero=False), title=f"Prix estimé ({currency})")
    )

    bars = base.mark_bar(height=18, cornerRadius=2).encode(
        x="low:Q", x2="high:Q", color=alt.Color("color:N", scale=None)
    )
    ticks = base.mark_tick(color="white", size=18, thickness=2).encode(x="mid:Q")
    price_line = alt.Chart(pd.DataFrame({"x": [result.market_price]})).mark_rule(
        color="#ef4444", strokeWidth=2, strokeDash=[4, 4]
    ).encode(x="x:Q")

    st.altair_chart((bars + ticks + price_line).properties(height=250),
                    width='stretch', key=f"football_{ticker}")


# ============================================================================
# 4. SENSIBILITÉ : HEATMAP WACC/G
# ============================================================================

@st.fragment
def display_sensitivity_heatmap(
    ticker: str,
    base_rate: float,
    base_growth: float,
    calculator_func: Callable,
    currency: str = "EUR",
    is_direct_equity: bool = False
) -> None:
    """Matrice de sensibilité bidimensionnelle (Stress Test)."""
    label_y = KPITexts.LABEL_KE if is_direct_equity else KPITexts.LABEL_WACC

    rate_range = np.linspace(base_rate - 0.01, base_rate + 0.01, 5)
    growth_range = np.linspace(base_growth - 0.005, base_growth + 0.005, 5)

    grid = []
    for r in rate_range:
        for g in growth_range:
            if r <= g: continue
            val = calculator_func(r, g)
            grid.append({"rate": r, "growth": g, "val": val})

    if not grid: return
    df = pd.DataFrame(grid)
    median_val = float(df['val'].median())

    base = alt.Chart(df).encode(
        x=alt.X('growth:O', title="Croissance perpétuelle (g)", axis=alt.Axis(format='.2%')),
        y=alt.Y('rate:O', title=label_y, axis=alt.Axis(format='.2%'))
    )

    rects = base.mark_rect().encode(
        color=alt.Color('val:Q', scale=alt.Scale(scheme='blues'), legend=None),
        tooltip=[
            alt.Tooltip('rate:O', format='.2%', title=label_y),
            alt.Tooltip('growth:O', format='.2%', title="Croissance (g)"),
            alt.Tooltip('val:Q', format=',.2f', title=f"IV ({currency})")
        ]
    )

    text = base.mark_text(baseline='middle').encode(
        text=alt.Text('val:Q', format=',.0f'),
        color=alt.condition(f"datum.val > {median_val}", alt.value('white'), alt.value('black'))
    )

    st.altair_chart((rects + text).properties(height=350),
                    width='stretch', key=f"sens_heat_{ticker}")


# ============================================================================
# 5. SEGMENTATION & BACKTESTING : WATERFALL & CONVERGENCE
# ============================================================================

@st.fragment
def display_sotp_waterfall(result: ValuationResult) -> None:
    """Cascade de valorisation par segments avec bridge de dette."""
    if not result.params.sotp or not result.params.sotp.enabled:
        return

    params, f = result.params.sotp, result.financials
    labels, values, measures = [], [], []

    for seg in params.segments:
        labels.append(seg.name); values.append(seg.enterprise_value); measures.append("relative")

    if params.conglomerate_discount > 0:
        labels.append("Décote holding")
        values.append(-(sum(values) * params.conglomerate_discount))
        measures.append("relative")

    labels.append("Valeur d'entreprise")
    values.append(0); measures.append("total")

    bridge = [("Dette nette", -f.net_debt), ("Intérêts minoritaires", -f.minority_interests)]
    for lbl, val in bridge:
        if val != 0:
            labels.append(lbl); values.append(val); measures.append("relative")

    labels.append("Valeur des fonds propres")
    values.append(0); measures.append("total")

    fig = go.Figure(go.Waterfall(
        orientation="v", measure=measures, x=labels, y=values,
        text=[f"{v:,.0f}" if v != 0 else "" for v in values],
        textposition="outside",
        decreasing={"marker": {"color": "#ef4444"}}, # Rouge soft
        increasing={"marker": {"color": "#10b981"}}, # Vert soft
        totals={"marker": {"color": "#1e293b"}}
    ))

    fig.update_layout(
        height=450, font=dict(family="Inter", size=11),
        margin=dict(t=40, b=20, l=20, r=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, width='stretch', key=f"waterfall_sotp_{result.ticker}")

@st.fragment
def display_backtest_convergence_chart(ticker: str, backtest_report: Optional[BacktestResult], currency: str) -> None:
    """Graphique de convergence historique (Prédit vs Réel)."""
    if not backtest_report or not backtest_report.points:
        st.info("Données historiques insuffisantes pour le backtesting.")
        return

    data = []
    for p in backtest_report.points:
        data.append({"date": p.valuation_date, "type": "IV historique", "val": p.intrinsic_value})
        data.append({"date": p.valuation_date, "type": "Prix réel", "val": p.market_price})

    df = pd.DataFrame(data)
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('date:T', title=None, axis=alt.Axis(format='%Y')),
        y=alt.Y('val:Q', scale=alt.Scale(zero=False), title=currency),
        color=alt.Color('type:N', title=None, scale=alt.Scale(range=['#10b981', '#ef4444'])),
        tooltip=['date:T', 'type:N', alt.Tooltip('val:Q', format=',.2f')]
    ).properties(height=350).interactive()

    st.altair_chart(chart, width='stretch', key=f"backtest_chart_{ticker}")