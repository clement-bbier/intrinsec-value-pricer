from typing import Any
import streamlit as st
import pandas as pd

from core.models import CompanyFinancials, DCFParameters, ValuationMode
from app.ui_methodology import (
    display_simple_dcf_formula,
    display_fundamental_dcf_formula,
    display_monte_carlo_formula,
)


def format_pct(x: float) -> str:
    """Formate un float en pourcentage (0.05 -> 5.00%)."""
    if x is None: return "N/A"
    return f"{x * 100:.2f} %"


def format_currency(x: float, currency: str) -> str:
    """Formate un montant avec séparateur de milliers et devise."""
    if x is None: return "N/A"
    return f"{x:,.2f} {currency}".replace(",", " ")


def _render_audit_tab_content(financials: CompanyFinancials):
    """
    Contenu de l'onglet 'Audit & Fiabilité' (Le nouveau 3ème onglet).
    """
    score = financials.audit_score

    # Résumé visuel en haut de l'onglet
    if score >= 80:
        st.success(
            f"### 🛡️ Indice de Confiance : Excellent ({score}/100)\nLes données sont complètes, récentes et le modèle est cohérent avec le marché.")
    elif score >= 50:
        st.warning(
            f"### 🛡️ Indice de Confiance : Modéré ({score}/100)\nLe modèle repose sur certaines estimations ou moyennes sectorielles.")
    else:
        st.error(
            f"### 🛡️ Indice de Confiance : Faible ({score}/100)\nAttention : Manque de données critiques ou forte incohérence avec le prix actuel.")

    st.markdown("---")
    st.markdown("#### 📋 Détail des Points de Contrôle")

    # Si pas de détails (cas de fallback), on affiche les warnings classiques
    if not financials.audit_details and financials.warnings:
        for w in financials.warnings:
            st.info(f"ℹ️ {w}")
        return

    # Tri : Pénalités d'abord pour qu'elles soient visibles tout de suite
    details = sorted(financials.audit_details, key=lambda x: x['penalty'])

    for item in details:
        penalty = item['penalty']
        category = item['category']
        reason = item['reason']
        context = item.get('context', '')

        with st.container():
            # Mise en page : Colonne Points | Colonne Explication
            c1, c2 = st.columns([1, 8])

            with c1:
                if penalty < 0:
                    st.error(f"{penalty} pts")
                else:
                    st.success(f"+{penalty} pts")  # Bonus ou Neutre

            with c2:
                st.markdown(f"**[{category}]** {reason}")
                if context:
                    st.caption(f"📝 *Contexte : {context}*")

            st.divider()


def display_results(
        financials: CompanyFinancials,
        params: DCFParameters,
        result: Any,
        mode: ValuationMode,
) -> None:
    """Composant principal d'affichage des résultats."""

    st.subheader(f"💎 Valorisation Intrinsèque – {financials.ticker}")

    # --- 1. BANDEAU KPI (Haut de page) ---
    # ON PASSE À 5 COLONNES
    col_price, col_iv, col_delta, col_score, col_wacc = st.columns(5)

    market_price = financials.current_price
    intrinsic_value = result.intrinsic_value_per_share
    currency = financials.currency

    delta_abs = intrinsic_value - market_price
    delta_pct = (delta_abs / market_price) * 100 if market_price > 0 else 0.0

    with col_price:
        st.metric("Prix de Marché", format_currency(market_price, currency))

    with col_iv:
        st.metric(
            "Valeur Intrinsèque (Modèle)",
            format_currency(intrinsic_value, currency),
            delta=f"{delta_abs:,.2f} {currency}".replace(",", " "),
        )

    with col_delta:
        label = "Sous-évalué (Opportunité)" if delta_abs > 0 else "Surévalué (Risque)"
        st.metric(
            "Potentiel",
            label,
            delta=f"{delta_pct:.2f}%",
            delta_color="normal" if delta_abs > 0 else "inverse",
        )

    # --- NOUVEAU KPI : SCORE ---
    with col_score:
        score = financials.audit_score
        # Couleur du delta : Vert si > 80, Gris si > 50, Rouge sinon
        # Note: Streamlit gère "normal", "inverse", "off".
        color = "normal" if score >= 80 else ("off" if score >= 50 else "inverse")

        st.metric(
            "🛡️ Score Confiance",
            f"{score:.0f} / 100",
            delta=financials.audit_rating,
            delta_color=color,
            help="Note de fiabilité basée sur la qualité des données (TTM, Analystes) et la cohérence mathématique."
        )

    with col_wacc:
        st.metric(
            "CMPC / WACC",
            format_pct(result.wacc),
            help="Coût Moyen Pondéré du Capital. Représente le risque global."
        )

    st.markdown("---")

    # --- 2. ONGLETS (Détails, Méthodologie, Audit) ---
    # AJOUT DU 3ème ONGLET
    tab1, tab2, tab3 = st.tabs([
        "📋 Détails des Hypothèses",
        "📚 Comprendre le Calcul",
        "🛡️ Audit & Fiabilité"
    ])

    # --- ONGLET 1 : DÉTAILS ---
    with tab1:
        c1, c2, c3 = st.columns(3)

        with c1:
            st.caption("🛡️ Paramètres de Risque (WACC)")
            df_risk = pd.DataFrame({
                "Paramètre": ["Taux sans risque (Rf)", "Prime de risque (MRP)", "Coût de la dette (Rd)",
                              "Taux d'impôt Effectif", "Bêta Action"],
                "Valeur": [
                    format_pct(params.risk_free_rate),
                    format_pct(params.market_risk_premium),
                    format_pct(params.cost_of_debt),
                    format_pct(params.tax_rate),
                    f"{financials.beta:.2f}"
                ]
            })
            st.table(df_risk)

        with c2:
            st.caption("🚀 Hypothèses de Croissance")
            if mode == ValuationMode.FUNDAMENTAL_FCFF:
                fcf_label = "FCFF Normatif (Pondéré 5 ans)"
                fcf_val = financials.fcf_fundamental_smoothed
            else:
                fcf_label = "FCFF TTM (12 derniers mois)"
                fcf_val = financials.fcf_last

            fcf_display = format_currency(fcf_val, currency) if fcf_val is not None else "Donnée Indisponible"

            df_growth = pd.DataFrame({
                "Paramètre": ["Flux de Départ (FCF)", "Croissance Initiale (Phase 1)",
                              "Croissance Perpétuelle (Terminal)"],
                "Valeur": [
                    fcf_display,
                    format_pct(params.fcf_growth_rate),
                    format_pct(params.perpetual_growth_rate)
                ]
            })
            st.table(df_growth)

        with c3:
            st.caption("🏦 Bilan & Structure")

            def to_m(v):
                if v is None: return "N/A"
                return f"{v / 1e6:,.0f} M".replace(",", " ")

            df_bs = pd.DataFrame({
                "Poste": ["Dette Totale", "Cash Disponible", "Nombre d'Actions", "Intérêts Payés (TTM)"],
                "Valeur": [
                    to_m(financials.total_debt),
                    to_m(financials.cash_and_equivalents),
                    to_m(financials.shares_outstanding),
                    to_m(financials.interest_expense)
                ]
            })
            st.table(df_bs)

    # --- ONGLET 2 : MÉTHODOLOGIE ---
    with tab2:
        if mode == ValuationMode.SIMPLE_FCFF:
            display_simple_dcf_formula()
        elif mode == ValuationMode.FUNDAMENTAL_FCFF:
            display_fundamental_dcf_formula()
        elif mode == ValuationMode.MONTE_CARLO:
            display_monte_carlo_formula()

    # --- ONGLET 3 : AUDIT (NOUVEAU) ---
    with tab3:
        _render_audit_tab_content(financials)