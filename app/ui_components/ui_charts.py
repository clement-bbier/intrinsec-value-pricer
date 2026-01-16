"""
app/ui_components/ui_charts.py
VISUALISATIONS — VERSION V4.0 (Hedge Fund Standard)
Rôle : Rendu graphique haute précision incluant le Football Field Chart.
Standards : Altair, i18n, Zero-Depreciation.
"""

from __future__ import annotations

from typing import List, Optional, Callable

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from app.ui_components.ui_kpis import format_smart_number
from app.ui_components.ui_texts import ChartTexts, KPITexts, SOTPTexts
from core.models import ValuationResult


# ============================================================================
# 1. HISTORIQUE DE PRIX
# ============================================================================

def display_price_chart(ticker: str, price_history: Optional[pd.DataFrame]) -> None:
    """Affiche l'historique de prix avec les labels centralisés."""
    if price_history is None or price_history.empty:
        st.info(ChartTexts.PRICE_UNAVAILABLE.format(ticker=ticker))
        return

    df = price_history.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors='coerce')
    df = df.reset_index()

    date_col = next((c for c in df.columns if str(c).lower() in ['date', 'index']), None)
    if not date_col: return

    cols = df.columns.tolist()
    price_col = "Close" if "Close" in cols else ("Adj Close" if "Adj Close" in cols else None)
    if not price_col and len(df.select_dtypes(include=[np.number]).columns) > 0:
        price_col = df.select_dtypes(include=[np.number]).columns[0]

    if not price_col: return

    df = df.rename(columns={date_col: "Date", price_col: "Prix"}).dropna(subset=["Date", "Prix"])

    chart = alt.Chart(df).mark_line(color='#1E88E5', strokeWidth=1.5).encode(
        x=alt.X('Date:T', title=None, axis=alt.Axis(format='%Y-%m')),
        y=alt.Y('Prix:Q', scale=alt.Scale(zero=False), title=None),
        tooltip=[
            alt.Tooltip('Date:T', format=ChartTexts.DATE_FORMAT, title=ChartTexts.TOOLTIP_DATE),
            alt.Tooltip('Prix:Q', format=',.2f', title=ChartTexts.TOOLTIP_PRICE)
        ]
    ).properties(
        height=300,
        title=ChartTexts.PRICE_HISTORY_TITLE.format(ticker=ticker)
    ).interactive()

    st.altair_chart(chart, use_container_width=True)


# ============================================================================
# 2. MONTE CARLO (DISTRIBUTION DES VALEURS)
# ============================================================================

def display_simulation_chart(simulation_results: List[float], market_price: float, currency: str) -> None:
    """Affiche l'histogramme Monte Carlo avec synthèse technique localisée."""
    if not simulation_results:
        st.warning(ChartTexts.SIM_UNAVAILABLE)
        return

    values = np.array([v for v in simulation_results if v is not None and not np.isnan(v)])
    if len(values) == 0: return

    p50 = np.median(values)
    p10 = np.percentile(values, 10)
    p90 = np.percentile(values, 90)

    df_sim = pd.DataFrame({"Valeur": values})

    hist = alt.Chart(df_sim).mark_bar(color="#546E7A", opacity=0.7).encode(
        x=alt.X("Valeur:Q", bin=alt.Bin(maxbins=50), title=ChartTexts.SIM_AXIS_X.format(currency=currency)),
        y=alt.Y("count()", title=ChartTexts.SIM_AXIS_Y)
    )
    rule_p50 = alt.Chart(pd.DataFrame({'x': [p50]})).mark_rule(color="#2E7D32", strokeWidth=3).encode(x='x')
    rule_quantiles = alt.Chart(pd.DataFrame({'x': [p10, p90]})).mark_rule(color="#90A4AE", strokeDash=[4, 4]).encode(x='x')

    layers = [hist, rule_p50, rule_quantiles]
    if market_price > 0:
        layers.append(alt.Chart(pd.DataFrame({'x': [market_price]})).mark_rule(color="#D32F2F", strokeWidth=2, strokeDash=[5, 2]).encode(x='x'))

    st.altair_chart(alt.layer(*layers).properties(height=320), use_container_width=True)

    st.markdown(f"""
    {ChartTexts.SIM_SUMMARY_TITLE.format(count=len(values))}
    * {ChartTexts.SIM_SUMMARY_P50} : {p50:,.2f} {currency}
    * {ChartTexts.SIM_SUMMARY_PRICE} : {market_price:,.2f} {currency}
    * {ChartTexts.SIM_SUMMARY_CI} : {p10:,.2f} à {p90:,.2f} {ChartTexts.SIM_SUMMARY_PROB.format(prob=80)}
    """)


# ============================================================================
# 3. TRIANGULATION : FOOTBALL FIELD CHART (NOUVEAUTÉ SPRINT 4)
# ============================================================================

def display_football_field(result: ValuationResult) -> None:
    """
    Rendu visuel de la triangulation (Football Field).
    Compare le modèle intrinsèque (avec range MC si possible) aux multiples de marché.
    """
    st.subheader(KPITexts.FOOTBALL_FIELD_TITLE)

    data = []
    currency = result.financials.currency

    # 1. Préparation du signal Intrinsèque (avec Range P10-P90 si Monte Carlo)
    iv_p50 = result.intrinsic_value_per_share
    iv_low = iv_p50
    iv_high = iv_p50

    if result.params.monte_carlo.enable_monte_carlo and result.quantiles:
        iv_low = result.quantiles.get("P10", iv_p50)
        iv_high = result.quantiles.get("P90", iv_p50)

    data.append({
        "Method": KPITexts.LABEL_FOOTBALL_FIELD_IV,
        "Low": iv_low, "High": iv_high, "Mid": iv_p50,
        "Color": "#1B5E20" # Vert Institutionnel
    })

    # 2. Ajout des multiples (Signaux Spot)
    if result.multiples_triangulation:
        rel = result.multiples_triangulation
        signals = [
            (KPITexts.LABEL_FOOTBALL_FIELD_PE, rel.pe_based_price),
            (KPITexts.LABEL_FOOTBALL_FIELD_EBITDA, rel.ebitda_based_price),
            (KPITexts.LABEL_FOOTBALL_FIELD_REV, rel.rev_based_price)
        ]

        for label, val in signals:
            if val > 0:
                # Pour les multiples, on simule un range étroit de +/- 5% pour la visibilité
                data.append({
                    "Method": label,
                    "Low": val * 0.95, "High": val * 1.05, "Mid": val,
                    "Color": "#455A64" # Gris Bleu Secteur
                })

    if not data:
        st.info(KPITexts.LABEL_MULTIPLES_UNAVAILABLE)
        return

    df = pd.DataFrame(data)

    # Création du graphique Altair
    base = alt.Chart(df).encode(
        y=alt.Y("Method:N", title=None, sort=None),
        x=alt.X("Low:Q", scale=alt.Scale(zero=False), title=f"Valeur par Action ({currency})")
    )

    # Barres de Range (Intervalle)
    bars = base.mark_bar(height=15).encode(
        x="Low:Q",
        x2="High:Q",
        color=alt.Color("Color:N", scale=None),
        tooltip=[
            alt.Tooltip("Method:N", title="Méthode"),
            alt.Tooltip("Mid:Q", format=",.2f", title="Valeur")
        ]
    )

    # Ticks centraux
    ticks = base.mark_tick(color="white", size=15, thickness=2).encode(x="Mid:Q")

    # Ligne verticale du prix de marché
    price_rule = alt.Chart(pd.DataFrame({"x": [result.market_price]})).mark_rule(
        color="#D32F2F", strokeWidth=2, strokeDash=[4, 4]
    ).encode(x="x:Q")

    price_label = price_rule.mark_text(
        align='left', dx=5, dy=-140, color="#D32F2F", fontWeight='bold'
    ).encode(text=alt.value(f"{KPITexts.LABEL_FOOTBALL_FIELD_PRICE}"))

    final_chart = alt.layer(bars, ticks, price_rule, price_label).properties(height=250)

    st.altair_chart(final_chart, use_container_width=True)


# ============================================================================
# 4. SENSIBILITÉ & CORRÉLATION
# ============================================================================

def display_sensitivity_heatmap(
    base_rate: float,
    base_growth: float,
    calculator_func: Callable,
    currency: str = "EUR",
    is_direct_equity: bool = False
) -> None:
    """Rendu de la matrice de sensibilité avec labels dynamiques (WACC vs Ke)."""
    st.subheader(ChartTexts.SENS_TITLE)

    label_y = "Ke" if is_direct_equity else "WACC"
    title_y = "Coût des Fonds Propres (Ke)" if is_direct_equity else "Coût du Capital (WACC)"
    tooltip_y = "Taux (Ke)" if is_direct_equity else ChartTexts.SENS_TOOLTIP_WACC

    rate_steps = [-0.010, -0.005, 0.0, 0.005, 0.010]
    growth_steps = [-0.005, -0.0025, 0.0, 0.0025, 0.005]
    data = []

    for dr in rate_steps:
        for dg in growth_steps:
            r = base_rate + dr
            g = base_growth + dg
            if r <= g + 0.001: continue
            try:
                val = calculator_func(r, g)
                if val and val > 0:
                    data.append({label_y: r, "Growth": g, "Valeur": round(val, 2)})
            except: continue

    if not data:
        st.warning(ChartTexts.SENS_UNAVAILABLE)
        return

    df = pd.DataFrame(data)

    base = alt.Chart(df).encode(
        x=alt.X('Growth:O', title=ChartTexts.SENS_AXIS_X, axis=alt.Axis(format='.2%')),
        y=alt.Y(f'{label_y}:O', title=title_y, axis=alt.Axis(format='.2%'))
    )

    heatmap = base.mark_rect().encode(
        color=alt.Color('Valeur:Q', scale=alt.Scale(scheme='yellowgreenblue'), legend=None),
        tooltip=[
            alt.Tooltip(label_y, format='.2%', title=tooltip_y),
            alt.Tooltip('Growth', format='.2%', title=ChartTexts.SENS_TOOLTIP_GROWTH),
            alt.Tooltip('Valeur', format=',.2f', title=ChartTexts.SENS_TOOLTIP_VAL.format(currency=currency))
        ]
    )

    text = base.mark_text(baseline='middle').encode(
        text=alt.Text('Valeur:Q', format=',.0f'),
        color=alt.condition(alt.datum.Valeur > df['Valeur'].quantile(0.5), alt.value('white'), alt.value('black'))
    )

    st.altair_chart((heatmap + text).properties(height=350), use_container_width=True)


def display_correlation_heatmap(rho: float = -0.30) -> None:
    """Rendu de la matrice de corrélation."""
    corr_data = pd.DataFrame([
        {"X": "Beta (β)", "Y": "Beta (β)", "Val": 1.0},
        {"X": "Growth (g)", "Y": "Growth (g)", "Val": 1.0},
        {"X": "Beta (β)", "Y": "Growth (g)", "Val": rho},
        {"X": "Growth (g)", "Y": "Beta (β)", "Val": rho},
    ])

    base = alt.Chart(corr_data).encode(
        x=alt.X('X:N', title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Y:N', title=None)
    )

    heatmap = base.mark_rect().encode(
        color=alt.Color('Val:Q', scale=alt.Scale(scheme='redblue', domain=[-1, 1]), legend=None),
        tooltip=['X', 'Y', 'Val']
    )

    text = base.mark_text().encode(
        text=alt.Text('Val:Q', format='.2f'),
        color=alt.condition((alt.datum.Val > 0.5) | (alt.datum.Val < -0.5), alt.value('white'), alt.value('black'))
    )

    st.altair_chart((heatmap + text).properties(height=180), use_container_width=True)
    st.caption(ChartTexts.CORREL_CAPTION)


# ============================================================================
# 5. SOMME DES PARTIES (WATERFALL SOTP) — SPRINT 6 (ST 4.1)
# ============================================================================

def display_sotp_waterfall(result: ValuationResult) -> None:
    """
    Rendu Plotly d'une cascade de valorisation Sum-of-the-Parts (ST 4.1).
    Visualise la décomposition sans aucune chaîne de caractères en dur.
    """
    if not result.params.sotp.enabled or not result.params.sotp.segments:
        return

    params = result.params.sotp
    f = result.financials

    # 1. Préparation des données de la cascade
    labels = []
    values = []
    measures = []

    # A. Ajout de chaque segment (Données relatives)
    raw_ev_sum = 0
    for seg in params.segments:
        labels.append(seg.name)
        values.append(seg.enterprise_value)
        measures.append("relative")
        raw_ev_sum += seg.enterprise_value

    # B. Décote de conglomérat (Si applicable)
    discount_val = - (raw_ev_sum * params.conglomerate_discount)
    if discount_val != 0:
        labels.append(SOTPTexts.LBL_DISCOUNT)
        values.append(discount_val)
        measures.append("relative")

    # C. Sous-total : Valeur d'Entreprise (Somme des parties après décote)
    labels.append(SOTPTexts.LBL_ENTERPRISE_VALUE)
    values.append(0)
    measures.append("total")

    # D. Pont vers la Valeur Actionnariale (Equity Bridge)
    # Utilisation des labels standardisés de KPITexts
    bridge_data = [
        (KPITexts.LABEL_DEBT, -f.total_debt),
        (KPITexts.LABEL_CASH, f.cash_and_equivalents),
        (KPITexts.LABEL_MINORITIES, -f.minority_interests),
        (KPITexts.LABEL_PENSIONS, -f.pension_provisions)
    ]

    for lbl, val in bridge_data:
        if val != 0:
            labels.append(lbl)
            values.append(val)
            measures.append("relative")

    # E. Résultat Final : Valeur des Capitaux Propres (Total final)
    labels.append(SOTPTexts.LBL_EQUITY_VALUE)
    values.append(0)
    measures.append("total")

    # 2. Création du graphique Plotly
    fig = go.Figure(go.Waterfall(
        name="SOTP",
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#2E7D32"}},
        decreasing={"marker": {"color": "#C62828"}},
        totals={"marker": {"color": "#1565C0"}},
        textposition="outside",
        # Formatage dynamique sans f-string hardcodée pour le symbole
        text=[f"{v:,.0f}" if v != 0 else "" for v in values],
    ))

    fig.update_layout(
        title=SOTPTexts.DESC_WATERFALL,
        showlegend=False,
        height=500,
        margin=dict(t=50, b=20, l=20, r=20),
        yaxis=dict(title=f"{KPITexts.VALUE_UNIT.format(unit=f.currency)}")
    )

    st.plotly_chart(fig, use_container_width=True)