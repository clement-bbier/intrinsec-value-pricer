"""
core/valuation/strategies/dcf_standard.py

Méthode : FCFF Two-Stage Discounted Cash Flow
Version : V1.1 — Chapitre 4 conforme (Glass Box)

Références académiques :
- Damodaran, A. – Investment Valuation
- CFA Institute – Equity Valuation
"""

import logging

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    DCFValuationResult,
    TraceHypothesis
)
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class StandardFCFFStrategy(ValuationStrategy):
    """
    FCFF Two-Stage Discounted Cash Flow (Standard).
    """

    academic_reference = "Damodaran"
    economic_domain = "Mature firms / Stable cash-flows"
    financial_invariants = [
        "WACC > g_terminal",
        "projection_years > 0",
        "shares_outstanding > 0"
    ]

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:

        logger.info(
            "[Strategy] FCFF Two-Stage | ticker=%s",
            financials.ticker
        )

        # ====================================================
        # 1. SÉLECTION DU FCF DE BASE (GLASS BOX)
        # ====================================================

        if params.manual_fcf_base is not None:
            fcf_base = params.manual_fcf_base
            source = "Manual override"
        else:
            fcf_base = financials.fcf_last
            source = "Last reported FCF (TTM)"

        if fcf_base is None:
            raise CalculationError(
                "FCF de base indisponible (fcf_last manquant)."
            )

        # --- Trace Glass Box ---
        self.add_step(
            label="Sélection du flux de trésorerie de base",
            theoretical_formula="FCF₀",
            hypotheses=[
                TraceHypothesis(
                    name="FCF base",
                    value=fcf_base,
                    unit=financials.currency,
                    source=source
                )
            ],
            numerical_substitution=f"FCF₀ = {fcf_base:,.2f}",
            result=fcf_base,
            unit=financials.currency,
            interpretation=(
                "Flux de trésorerie libre utilisé comme point de départ "
                "des projections explicites."
            )
        )

        # ====================================================
        # 2. EXÉCUTION DU DCF DÉTERMINISTE
        # ====================================================

        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )
