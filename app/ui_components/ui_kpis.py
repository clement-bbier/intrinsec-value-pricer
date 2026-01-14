"""
app/ui_components/ui_kpis.py
RESTITUTION "GLASS BOX" — VERSION V9.0 (Segmenté & i18n Secured)
Rôle : Affichage haute fidélité des résultats et audit mathématique.
Architecture : Alignée sur la segmentation DCFParameters (Rates, Growth, MC).
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

import numpy as np
import streamlit as st

from core.models import (
    AuditReport,
    CalculationStep,
    CompanyFinancials,
    DCFParameters,
    ValuationResult,
    ValuationMode,
    TerminalValueMethod
)
from app.ui_components.ui_glass_box_registry import get_step_metadata
from app.ui_components.ui_texts import KPITexts, AuditTexts, ExpertTerminalTexts

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. COMPOSANTS ATOMIQUES (UI COMPONENTS)
# ==============================================================================

def atom_kpi_metric(label: str, value: str, help_text: str = "") -> None:
    """Affiche une métrique clé dans le bandeau supérieur."""
    st.metric(label, value, help=help_text)


def atom_calculation_card(
    index: int,
    label: str,
    formula: str,
    substitution: str,
    result: Optional[float],
    unit: str = "",
    interpretation: str = ""
) -> None:
    """Carte d'audit mathématique pour la preuve de calcul."""
    with st.container(border=True):
        st.markdown(f"**{KPITexts.STEP_LABEL.format(index=index)} : {label}**")
        c1, c2, c3 = st.columns([2.5, 4, 1.5])

        with c1:
            st.caption(KPITexts.FORMULA_THEORY)
            if formula and formula != "N/A":
                st.latex(formula)
            else:
                st.markdown(KPITexts.FORMULA_DATA_SOURCE)

        with c2:
            st.caption(KPITexts.APP_NUMERIC)
            if substitution:
                st.code(substitution, language="text")
            else:
                st.markdown("---")

        with c3:
            st.caption(KPITexts.VALUE_UNIT.format(unit=unit))
            if result is None:
                st.markdown("### N/A")
            elif result == 1.0 and "Initialisation" in label:
                st.write(KPITexts.STEP_VALIDATED)
            else:
                st.markdown(f"### {result:,.2f}")

        if interpretation:
            st.caption(f"{KPITexts.NOTE_ANALYSIS} : {interpretation}")


def atom_input_row(label: str, value: str, source: str = "Auto") -> None:
    """Ligne d'affichage d'un input avec sa source."""
    c1, c2, c3 = st.columns([2, 2, 1])
    c1.markdown(f"**{label}**")
    c2.code(value, language=None)
    c3.caption(source)


# ==============================================================================
# 2. NAVIGATION ET AGGREGATION (VALUATION DETAILS)
# ==============================================================================

def display_valuation_details(result: ValuationResult, _provider: Any = None) -> None:
    """Orchestrateur des onglets de détails post-calcul (Accès segmenté MC)."""
    st.divider()

    core_steps = [s for s in result.calculation_trace if not s.step_key.startswith("MC_")]
    mc_steps = [s for s in result.calculation_trace if s.step_key.startswith("MC_")]

    tab_labels = [KPITexts.TAB_INPUTS, KPITexts.TAB_CALC, KPITexts.TAB_AUDIT]

    # Sécurisation de l'accès au segment monte_carlo
    show_mc_tab = (
        result.request is not None
        and result.request.mode.supports_monte_carlo
        and result.params.monte_carlo.enable_monte_carlo
        and mc_steps
    )

    if show_mc_tab:
        tab_labels.append(KPITexts.TAB_MC)

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        _render_inputs_tab(result)

    with tabs[1]:
        for idx, step in enumerate(core_steps, start=1):
            _render_smart_step(idx, step)

    with tabs[2]:
        _render_reliability_report(result.audit_report, result)

    if show_mc_tab:
        with tabs[3]:
            _render_monte_carlo_tab(result, mc_steps)


# ==============================================================================
# 3. ONGLET DONNÉES D'ENTRÉE
# ==============================================================================

def _render_inputs_tab(result: ValuationResult) -> None:
    """Onglet 1 : Affiche les inputs via les nouveaux segments."""
    f = result.financials
    p = result.params
    mode = result.request.mode if result.request else None

    st.markdown(KPITexts.SECTION_INPUTS_HEADER)
    st.caption(KPITexts.SECTION_INPUTS_CAPTION)

    with st.expander(KPITexts.SEC_A_IDENTITY, expanded=True):
        _render_company_identity(f)

    with st.expander(KPITexts.SEC_B_FINANCIALS, expanded=True):
        _render_financial_data(f)

    with st.expander(KPITexts.SEC_C_MODEL, expanded=True):
        _render_model_parameters(p, mode, result)

    if p.monte_carlo.enable_monte_carlo:
        with st.expander(KPITexts.SEC_D_MC, expanded=True):
            _render_monte_carlo_config(p)


def _render_company_identity(f: CompanyFinancials) -> None:
    """Sous-section : Identité de l'entreprise (Contrat Financier)."""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"**{KPITexts.LABEL_TICKER}**")
        st.code(f.ticker)
    with c2:
        st.markdown(f"**{KPITexts.LABEL_NAME}**")
        st.code(f.name)
    with c3:
        st.markdown(f"**{KPITexts.LABEL_SECTOR}**")
        st.code(f.sector)
    with c4:
        st.markdown(f"**{KPITexts.LABEL_COUNTRY}**")
        st.code(f.country)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.markdown(f"**{KPITexts.LABEL_INDUSTRY}**")
        st.code(f.industry)
    with c6:
        st.markdown(f"**{KPITexts.LABEL_CURRENCY}**")
        st.code(f.currency)
    with c7:
        st.markdown(f"**{KPITexts.LABEL_BETA}**")
        st.code(f"{f.beta:.2f}")
    with c8:
        st.markdown(f"**{KPITexts.LABEL_SHARES}**")
        st.code(f"{f.shares_outstanding:,.0f}")


def _render_financial_data(f: CompanyFinancials) -> None:
    """Sous-section : Données financières clés."""
    st.markdown(KPITexts.SUB_MARKET)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**{KPITexts.LABEL_PRICE}**")
        st.code(f"{f.current_price:,.2f} {f.currency}")
    with c2:
        st.markdown(f"**{KPITexts.LABEL_MCAP}**")
        st.code(f"{f.market_cap:,.0f} {f.currency}")
    with c3:
        st.markdown(f"**{KPITexts.LABEL_BVPS}**")
        bv_display = f"{f.book_value_per_share:,.2f}" if f.book_value_per_share else "N/A"
        st.code(bv_display)

    st.markdown(KPITexts.SUB_CAPITAL)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"**{KPITexts.LABEL_DEBT}**")
        st.code(f"{f.total_debt:,.0f} {f.currency}")
    with c2:
        st.markdown(f"**{KPITexts.LABEL_CASH}**")
        st.code(f"{f.cash_and_equivalents:,.0f} {f.currency}")
    with c3:
        st.markdown(f"**{KPITexts.LABEL_NET_DEBT}**")
        st.code(f"{f.net_debt:,.0f} {f.currency}")
    with c4:
        st.markdown(f"**{KPITexts.LABEL_INTEREST}**")
        st.code(f"{f.interest_expense:,.0f} {f.currency}")

    st.markdown(KPITexts.SUB_PERF)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"**{KPITexts.LABEL_REV}**")
        st.code(f"{f.revenue_ttm:,.0f}" if f.revenue_ttm else "N/A")
    with c2:
        st.markdown(f"**{KPITexts.LABEL_EBIT}**")
        st.code(f"{f.ebit_ttm:,.0f}" if f.ebit_ttm else "N/A")
    with c3:
        st.markdown(f"**{KPITexts.LABEL_NI}**")
        st.code(f"{f.net_income_ttm:,.0f}" if f.net_income_ttm else "N/A")
    with c4:
        st.markdown(f"**{KPITexts.LABEL_EPS}**")
        st.code(f"{f.eps_ttm:,.2f}" if f.eps_ttm else "N/A")

    st.markdown(KPITexts.SUB_CASH)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**{KPITexts.LABEL_FCF_LAST}**")
        st.code(f"{f.fcf_last:,.0f}" if f.fcf_last else "N/A")
    with c2:
        st.markdown(f"**{KPITexts.LABEL_CAPEX}**")
        st.code(f"{f.capex:,.0f}" if f.capex else "N/A")
    with c3:
        st.markdown(f"**{KPITexts.LABEL_DA}**")
        st.code(f"{f.depreciation_and_amortization:,.0f}" if f.depreciation_and_amortization else "N/A")


def _render_model_parameters(p: DCFParameters, mode: Optional[ValuationMode], result: ValuationResult) -> None:
    """Sous-section : Paramètres (Segmentés Rates & Growth V9)."""
    r, g = p.rates, p.growth  # Accès aux nouveaux segments

    st.markdown(KPITexts.SUB_RATES)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"**{KPITexts.LABEL_RF}**")
        st.code(f"{r.risk_free_rate:.2%}" if r.risk_free_rate else "N/A")
    with c2:
        st.markdown(f"**{KPITexts.LABEL_MRP}**")
        st.code(f"{r.market_risk_premium:.2%}" if r.market_risk_premium else "N/A")
    with c3:
        st.markdown(f"**{KPITexts.LABEL_KD}**")
        st.code(f"{r.cost_of_debt:.2%}" if r.cost_of_debt else "N/A")
    with c4:
        st.markdown(f"**{KPITexts.LABEL_TAX}**")
        st.code(f"{r.tax_rate:.1%}" if r.tax_rate else "N/A")

    st.markdown(KPITexts.SUB_GROWTH)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**{KPITexts.LABEL_G}**")
        st.code(f"{g.fcf_growth_rate:.2%}" if g.fcf_growth_rate else "N/A")
    with c2:
        st.markdown(f"**{KPITexts.LABEL_GN}**")
        st.code(f"{g.perpetual_growth_rate:.2%}" if g.perpetual_growth_rate else "N/A")
    with c3:
        st.markdown(f"**{KPITexts.LABEL_HORIZON}**")
        st.code(f"{g.projection_years} {KPITexts.UNIT_YEARS}")

    st.markdown(KPITexts.SUB_CALCULATED)
    c1, c2, c3 = st.columns(3)
    wacc = getattr(result, 'wacc', None)
    ke = getattr(result, 'cost_of_equity', None)
    with c1:
        st.markdown(f"**{KPITexts.LABEL_WACC}**")
        st.code(f"{wacc:.2%}" if wacc else "N/A")
    with c2:
        st.markdown(f"**{KPITexts.LABEL_KE}**")
        st.code(f"{ke:.2%}" if ke else "N/A")
    with c3:
        st.markdown(f"**{KPITexts.LABEL_METHOD}**")
        st.code(mode.value if mode else "N/A")

    st.markdown(KPITexts.SUB_TV)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{KPITexts.LABEL_TV_METHOD}**")
        st.code(g.terminal_method.value if g.terminal_method else "N/A")
    with c2:
        if g.terminal_method == TerminalValueMethod.EXIT_MULTIPLE:
            st.markdown(f"**{KPITexts.LABEL_EXIT_M}**")
            st.code(f"{g.exit_multiple_value:.1f}x" if g.exit_multiple_value else "N/A")
        else:
            st.markdown(f"**{KPITexts.LABEL_GN}**")
            st.code(f"{g.perpetual_growth_rate:.2%}" if g.perpetual_growth_rate else "N/A")


def _render_monte_carlo_config(p: DCFParameters) -> None:
    """Sous-section : Configuration MC (Segmentée i18n Secured)."""
    mc = p.monte_carlo  # Accès au segment MC
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"**{KPITexts.LABEL_SIMULATIONS}**")
        st.code(f"{mc.num_simulations:,}")
    with c2:
        st.markdown(f"**{AuditTexts.MC_VOL_BETA}**")
        st.code(f"{mc.beta_volatility:.1%}" if mc.beta_volatility else "Auto")
    with c3:
        st.markdown(f"**{AuditTexts.MC_VOL_G}**")
        st.code(f"{mc.growth_volatility:.1%}" if mc.growth_volatility else "Auto")
    with c4:
        st.markdown(f"**{KPITexts.LABEL_CORRELATION_BG}**")
        st.code(f"{mc.correlation_beta_growth:.2f}")


# ==============================================================================
# 4. ONGLET AUDIT
# ==============================================================================

def _render_reliability_report(report: Optional[AuditReport], result: ValuationResult) -> None:
    """Rendu analytique dynamique basé sur les piliers d'audit réels."""
    if not report:
        st.info(AuditTexts.NO_REPORT)
        return

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown(AuditTexts.GLOBAL_SCORE.format(score=report.global_score))
    with c2:
        st.metric(AuditTexts.RATING_SCORE, report.rating)
    with c3:
        coverage = (report.audit_coverage or 0.0) * 100
        st.metric(AuditTexts.COVERAGE, f"{coverage:.0f}%")

    st.divider()
    st.markdown(AuditTexts.CHECK_TABLE)

    h1, h2, h3, h4 = st.columns([2.5, 2.5, 3, 1.5])
    h1.caption(AuditTexts.H_INDICATOR)
    h2.caption(AuditTexts.H_RULE)
    h3.caption(AuditTexts.H_EVIDENCE)
    h4.caption(AuditTexts.H_VERDICT)

    if report.pillar_breakdown and report.pillar_breakdown.pillars:
        for _pillar_type, score_obj in report.pillar_breakdown.pillars.items():
            for diag_message in score_obj.diagnostics:
                test_key = _map_message_to_meta_key(diag_message)
                meta = get_step_metadata(test_key) or {"label": "Test Spécifique", "formula": r"\text{N/A}"}
                substitution = _format_numerical_evidence(test_key, result)

                alert_keywords = ["ALERTE", "RISQUE", "DIVERGENCE", "FRAGILE", "HORS", "CRITIQUE", "DÉFICIT"]
                is_alert = any(k in diag_message.upper() for k in alert_keywords)
                status_text = AuditTexts.STATUS_ALERT if is_alert else AuditTexts.STATUS_OK
                color = "red" if is_alert else "green"

                with st.container():
                    r1, r2, r3, r4 = st.columns([2.5, 2.5, 3, 1.5])
                    r1.markdown(f"**{meta['label']}**", help=meta.get('description', ''))
                    r2.latex(meta['formula'])
                    r3.info(substitution)
                    r4.markdown(f":{color}[**{status_text}**]")

    relevant_logs = [log for log in report.logs if "attribute" not in log.message.lower()]
    if relevant_logs:
        st.divider()
        with st.expander(AuditTexts.AUDIT_NOTES_EXPANDER, expanded=report.global_score < 40):
            for log in relevant_logs:
                if log.severity == "CRITICAL": st.error(f"**[{log.category}]** {log.message}")
                elif log.severity == "WARNING": st.warning(f"**[{log.category}]** {log.message}")
                else: st.info(f"**[{log.category}]** {log.message}")


# ==============================================================================
# 5. HELPERS DE MAPPING & EVIDENCE (Accès Segmentés V9)
# ==============================================================================

def _map_message_to_meta_key(message: str) -> str:
    m = message.upper()
    if "BETA" in m or "BÊTA" in m: return "AUDIT_BETA_COHERENCE"
    if "ICR" in m or "SOLVABILITÉ" in m: return "AUDIT_SOLVENCY_ICR"
    if "TRÉSORERIE > CAPITALISATION" in m or "NET-NET" in m: return "AUDIT_CASH_MCAP"
    if "LIQUIDITÉ" in m or "SMALL-CAP" in m: return "AUDIT_LIQUIDITY"
    if "LEVIER" in m: return "AUDIT_LEVERAGE"
    if "CONVERGENCE MACRO" in m or ("G PERPÉTUEL" in m and "RF" in m): return "AUDIT_G_RF_CONVERGENCE"
    if "PLANCHER" in m and "RF" in m: return "AUDIT_RF_FLOOR"
    if "CAPEX" in m or "RÉINVESTISSEMENT" in m: return "AUDIT_CAPEX_DA"
    if "CROISSANCE" in m and ("HORS" in m or "AGRESSIVE" in m): return "AUDIT_GROWTH_LIMIT"
    if "PAYOUT" in m or "DISTRIBUTION" in m: return "AUDIT_PAYOUT_STABILITY"
    if "WACC" in m and ("BAS" in m or "MINIMUM" in m or "PLANCHER" in m): return "AUDIT_WACC_FLOOR"
    if "VALEUR TERMINALE" in m or ("CONCENTRATION" in m and "TV" in m): return "AUDIT_TV_CONCENTRATION"
    if "G >=" in m or "GORDON" in m or ("G" in m and "WACC" in m): return "AUDIT_G_WACC"
    if "SPREAD" in m or ("ROE" in m and "KE" in m): return "AUDIT_ROE_KE_SPREAD"
    if "P/B" in m or "BOOK VALUE" in m: return "AUDIT_PB_RATIO"
    return "AUDIT_UNKNOWN"


def _format_numerical_evidence(key: str, res: ValuationResult) -> str:
    """Extrait les preuves numériques via les nouveaux segments."""
    f = res.financials
    r, g = res.params.rates, res.params.growth

    try:
        if key == "AUDIT_BETA_COHERENCE": return f"Beta extrait : {f.beta:.2f}"
        if key == "AUDIT_SOLVENCY_ICR":
            val = getattr(res, 'icr_observed', None)
            return f"EBIT / Intérêts : {val:.2f}x" if val is not None else "Donnée N/A"
        if key == "AUDIT_CASH_MCAP":
            ratio = (f.cash_and_equivalents / f.market_cap) if f.market_cap else 0
            return f"Cash/MCap : {ratio:.1%}"
        if key == "AUDIT_LIQUIDITY": return f"MCap : {f.market_cap:,.0f} {f.currency}"
        if key == "AUDIT_LEVERAGE":
            val = getattr(res, 'leverage_observed', None)
            return f"Dette/EBIT : {val:.2f}x" if val is not None else "N/A"
        if key == "AUDIT_G_RF_CONVERGENCE":
            gn, rf = (g.perpetual_growth_rate or 0.0), (r.risk_free_rate or 0.0)
            return f"g:{gn:.1%} vs Rf:{rf:.1%}"
        if key == "AUDIT_RF_FLOOR":
            return f"Rf : {(r.risk_free_rate or 0.0):.2%}"
        if key == "AUDIT_CAPEX_DA":
            val = getattr(res, 'capex_to_da_ratio', None)
            return f"Ratio CapEx/D&A : {val:.1%}" if val is not None else "Donnée N/A"
        if key == "AUDIT_GROWTH_LIMIT":
            return f"Taux g : {(g.fcf_growth_rate or 0.0):.1%}"
        if key == "AUDIT_PAYOUT_STABILITY":
            val = getattr(res, 'payout_ratio_observed', None)
            return f"Payout Ratio : {val:.1%}" if val is not None else "Donnée N/A"
        if key == "AUDIT_WACC_FLOOR":
            return f"WACC Calculé : {getattr(res, 'wacc', 0):.2%}"
        if key == "AUDIT_TV_CONCENTRATION":
            val = getattr(res, 'terminal_value_weight', None)
            return f"Poids TV : {val:.1%}" if val is not None else "N/A"
        if key == "AUDIT_G_WACC":
            w, gn = getattr(res, 'wacc', 0) or 0, (g.perpetual_growth_rate or 0)
            return f"g:{gn:.1%} vs WACC:{w:.1%}"
        if key == "AUDIT_ROE_KE_SPREAD":
            val = getattr(res, 'spread_roe_ke', None)
            return f"Spread ROE-Ke : {val:.2%}" if val is not None else "N/A"
        if key == "AUDIT_PB_RATIO":
            val = getattr(res, 'pb_ratio_observed', None)
            return f"P/B Observé : {val:.2f}x" if val is not None else "N/A"
    except Exception as e:
        logger.error("Erreur extraction preuve pour %s: %s", key, e)
        return AuditTexts.EVIDENCE_ERROR
    return AuditTexts.EVIDENCE_OK


# ==============================================================================
# 6. ONGLET MONTE CARLO (Accès Segmentés V9)
# ==============================================================================

def _render_monte_carlo_tab(result: ValuationResult, mc_steps: List[CalculationStep]) -> None:
    """Rendu probabiliste (Pilotage intégral par ui_texts)."""
    from app.ui_components.ui_charts import display_simulation_chart, display_correlation_heatmap

    if result.simulation_results is None or len(result.simulation_results) == 0:
        st.warning(AuditTexts.MC_FAILED)
        return

    f, sims = result.financials, np.array(result.simulation_results)
    prob_overvalued = (sims < result.market_price).mean() if result.market_price else 0.0
    q = result.quantiles or {}

    # Raccourcis segmentés
    mc, g = result.params.monte_carlo, result.params.growth

    st.markdown(AuditTexts.MC_TITLE)
    c1, c2, c3 = st.columns(3)
    c1.metric(AuditTexts.MC_DOWNSIDE, f"{prob_overvalued:.1%}")
    c2.metric(AuditTexts.MC_MEDIAN, f"{q.get('P50', 0.0):,.2f}")
    c3.metric(AuditTexts.MC_TAIL_RISK, f"{q.get('P10', 0.0):,.2f}")

    display_simulation_chart(result.simulation_results, result.market_price, f.currency)
    st.divider()

    col_sens, col_stress = st.columns([1.5, 2.5])
    with col_sens:
        st.markdown(AuditTexts.MC_SENS_RHO)
        if result.rho_sensitivity:
            st.table([{"Scénario": k, "IV (P50)": f"{v:,.2f}"} for k, v in result.rho_sensitivity.items()])
        else: st.caption(AuditTexts.MC_NO_DATA)

    with col_stress:
        st.markdown(AuditTexts.MC_STRESS_TITLE)
        if result.stress_test_value is not None:
            st.warning(AuditTexts.MC_FLOOR_VAL.format(val=result.stress_test_value, curr=f.currency))
            st.caption(AuditTexts.MC_STRESS_DESC)

    with st.expander(AuditTexts.MC_AUDIT_HYP, expanded=False):
        col_mat, col_inf = st.columns([1.2, 2.8])
        with col_mat: display_correlation_heatmap(rho=mc.correlation_beta_growth)
        with col_inf:
            st.caption(f"{AuditTexts.MC_VOL_BETA} : {(mc.beta_volatility or 0.0):.1%}")
            st.caption(f"{AuditTexts.MC_VOL_G} : {(mc.growth_volatility or 0.0):.1%}")

            # Affichage réactif via segment growth
            if g.terminal_method == TerminalValueMethod.GORDON_GROWTH:
                st.caption(f"{ExpertTerminalTexts.MC_VOL_GN} : {(mc.terminal_growth_volatility or 0.0):.1%}")
            elif result.request and result.request.mode == ValuationMode.RESIDUAL_INCOME_MODEL:
                st.caption(f"{ExpertTerminalTexts.MC_VOL_OMEGA} : {(mc.terminal_growth_volatility or 0.0):.1%}")

            st.info(AuditTexts.MC_CORREL_INFO)

    with st.expander(AuditTexts.MC_AUDIT_STOCH, expanded=False):
        for idx, step in enumerate(mc_steps, start=1): _render_smart_step(idx, step)


# ==============================================================================
# 7. RÉSUMÉ EXÉCUTIF (i18n Secured)
# ==============================================================================

def render_executive_summary(result: ValuationResult) -> None:
    """Synthèse décisionnelle (Utilise KPITexts.LABEL_IV)."""
    f = result.financials
    st.subheader(KPITexts.EXEC_TITLE.format(name=f.name, ticker=f.ticker))

    iv = result.intrinsic_value_per_share
    iv_display = f"{iv:,.2f} {f.currency}" if iv is not None else "N/A"
    price_display = f"{result.market_price:,.2f} {f.currency}" if result.market_price is not None else "N/A"

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1: atom_kpi_metric(KPITexts.LABEL_PRICE, price_display)
        with c2: atom_kpi_metric(KPITexts.LABEL_IV, iv_display)
        with c3: atom_kpi_metric(KPITexts.EXEC_CONFIDENCE, result.audit_report.rating if result.audit_report else "N/A")


def _render_smart_step(index: int, step: CalculationStep) -> None:
    """Lookup dynamique dans STEP_METADATA."""
    meta = get_step_metadata(step.step_key)
    atom_calculation_card(
        index=index,
        label=meta.get("label", step.label),
        formula=meta.get("formula", step.theoretical_formula),
        substitution=step.numerical_substitution,
        result=step.result,
        unit=meta.get("unit", ""),
        interpretation=step.interpretation
    )