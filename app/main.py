"""
app/main.py

POINT D’ENTRÉE — RAPPORT D’ANALYSTE INTERACTIF
Version : V2.0 — Chapitres 1 → 8 conformes

Rôle :
- Orchestration complète du rapport
- Séparation claire : Inputs → Calcul → Audit → Restitution
- Alignement strict UI ↔ moteur
- UX institutionnelle (lecture top-down, drill-down)

Ce fichier NE contient :
- aucune logique financière
- aucune logique d’audit
- aucune hypothèse métier
"""

from __future__ import annotations

import sys
import logging
from pathlib import Path

import streamlit as st

# ==============================================================================
# 0. SETUP ENVIRONNEMENT
# ==============================================================================

FILE_PATH = Path(__file__).resolve()
ROOT_PATH = FILE_PATH.parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# 1. CONFIG STREAMLIT — SOBRE & INSTITUTIONNEL
# ==============================================================================

st.set_page_config(
    page_title="Intrinsic Value Pricer",
    page_icon="📊",
    layout="wide"
)

# ==============================================================================
# 2. IMPORTS CORE / INFRA
# ==============================================================================

from core.models import (
    ValuationRequest,
    ValuationMode,
    InputSource
)
from core.valuation.engines import run_valuation

from infra.data_providers.yahoo_provider import YahooFinanceProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.auditing.audit_engine import AuditEngine

# ==============================================================================
# 3. IMPORTS UI — RAPPORT D’ANALYSTE
# ==============================================================================

from app.ui_components.ui_inputs_auto import display_auto_inputs
from app.ui_components.ui_inputs_expert import display_expert_request

from app.ui_components.ui_kpis import (
    display_main_kpis,
    display_valuation_details
)

from app.ui_components.ui_charts import (
    display_price_chart,
    display_simulation_chart,
    display_sensitivity_heatmap
)

from app.ui_components.ui_methodology import (
    display_audit_methodology
)

# ==============================================================================
# 4. APPLICATION PRINCIPALE
# ==============================================================================

def main() -> None:
    """
    Orchestration du rapport d’analyste interactif.
    """

    # ------------------------------------------------------------------
    # PAGE DE GARDE
    # ------------------------------------------------------------------
    st.title("Intrinsic Value Pricer")
    st.caption(
        "Rapport d’analyste interactif • "
        "Standards CFA / Damodaran • "
        "Architecture Glass Box • "
        "Audit comme méthode"
    )

    # ------------------------------------------------------------------
    # A. MODE D’UTILISATION (SIDEBAR)
    # ------------------------------------------------------------------
    st.sidebar.header("Mode d’utilisation")

    mode_choice = st.sidebar.radio(
        "Source des données et des hypothèses",
        options=[InputSource.AUTO.value, InputSource.MANUAL.value],
        format_func=lambda x: (
            "AUTO — Hypothèses normatives"
            if x == InputSource.AUTO.value
            else "EXPERT — Hypothèses manuelles"
        )
    )

    input_source = InputSource(mode_choice)

    # ------------------------------------------------------------------
    # B. SAISIE DES INPUTS
    # ------------------------------------------------------------------
    request: ValuationRequest | None = None

    if input_source == InputSource.AUTO:
        request = display_auto_inputs(
            default_ticker="AAPL",
            default_years=5
        )
    else:
        request = display_expert_request(
            default_ticker="AAPL",
            default_years=5
        )

    if request is None:
        st.info("👈 Configurez les paramètres et lancez l’analyse.")
        return

    # ------------------------------------------------------------------
    # C. PIPELINE DE CALCUL (TRANSACTIONNEL)
    # ------------------------------------------------------------------
    try:
        with st.spinner(f"Analyse en cours pour {request.ticker}…"):

            # ----------------------------------------------------------
            # 1. PROVIDERS
            # ----------------------------------------------------------
            macro_provider = YahooMacroProvider()
            data_provider = YahooFinanceProvider(
                macro_provider=macro_provider
            )

            # ----------------------------------------------------------
            # 2. DONNÉES & PARAMÈTRES
            # ----------------------------------------------------------
            if request.input_source == InputSource.AUTO:
                financials, params = (
                    data_provider.get_company_financials_and_parameters(
                        ticker=request.ticker,
                        projection_years=request.projection_years
                    )
                )

                if request.options.get("num_simulations"):
                    params.num_simulations = request.options["num_simulations"]

            else:
                financials = data_provider.get_company_financials(
                    request.ticker
                )
                params = request.manual_params

                if request.manual_beta is not None:
                    financials.beta = request.manual_beta

            # ----------------------------------------------------------
            # 3. MOTEUR DE VALORISATION
            # ----------------------------------------------------------
            result = run_valuation(request, financials, params)

            # ----------------------------------------------------------
            # 4. AUDIT — CHAPITRE 6
            # ----------------------------------------------------------
            result.audit_report = AuditEngine.compute_audit(result)

        # ------------------------------------------------------------------
        # D. RESTITUTION — RAPPORT STRUCTURÉ
        # ------------------------------------------------------------------

        # === PAGE 1 : SYNTHÈSE EXÉCUTIVE ===
        display_main_kpis(result)

        st.markdown("---")

        # === CONTEXTE DE MARCHÉ & INCERTITUDE ===
        st.subheader("Contexte de marché & incertitude")

        c_left, c_right = st.columns([2, 1])

        with c_left:
            try:
                history = data_provider.get_price_history(request.ticker)
                display_price_chart(request.ticker, history)
            except Exception:
                st.warning("Historique de prix indisponible.")

            if result.simulation_results:
                display_simulation_chart(
                    result.simulation_results,
                    result.market_price,
                    result.financials.currency
                )

        with c_right:
            # Sensibilité uniquement si DCF compatible
            if (
                request.mode
                in {
                    ValuationMode.FCFF_TWO_STAGE,
                    ValuationMode.FCFF_NORMALIZED,
                    ValuationMode.FCFF_REVENUE_DRIVEN,
                }
                and hasattr(result, "projected_fcfs")
            ):
                from core.computation.financial_math import (
                    calculate_terminal_value_gordon
                )

                last_fcf = (
                    result.projected_fcfs[-1]
                    if result.projected_fcfs else 0.0
                )

                base_pv = getattr(result, "sum_discounted_fcf", 0.0)
                net_debt = (
                    result.financials.total_debt
                    - result.financials.cash_and_equivalents
                )
                shares = result.financials.shares_outstanding
                years = params.projection_years

                def quick_sensitivity_calc(wacc: float, g: float):
                    if wacc <= g:
                        return None
                    tv = calculate_terminal_value_gordon(last_fcf, wacc, g)
                    tv_disc = tv / ((1 + wacc) ** years)
                    return (base_pv + tv_disc - net_debt) / shares

                display_sensitivity_heatmap(
                    base_wacc=result.wacc,
                    base_growth=params.perpetual_growth_rate,
                    calculator_func=quick_sensitivity_calc,
                    currency=result.financials.currency
                )

        st.markdown("---")

        # === DÉTAIL COMPLET : GLASS BOX & AUDIT ===
        display_valuation_details(result)

        st.markdown("---")

        # === MÉTHODOLOGIE & GOUVERNANCE ===
        display_audit_methodology()

    except Exception as exc:
        logger.error("Erreur critique lors de l’analyse", exc_info=True)
        st.error("❌ Une erreur est survenue lors de l’analyse.")
        st.exception(exc)


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    main()
