"""
core/valuation/strategies/graham_value.py
MÉTHODE : GRAHAM INTRINSIC VALUE — VERSION V6.0 (Audit-Grade)
Rôle : Estimation "Value" (1974 Revised) avec transparence totale sur l'ajustement AAA.
"""

import logging
from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    GrahamValuationResult,
    TraceHypothesis
)
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)

class GrahamNumberStrategy(ValuationStrategy):
    """Estimation 'Value' (Graham 1974 Revised) avec audit mathématique complet."""

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> GrahamValuationResult:
        logger.info("[Strategy] Graham 1974 Revised | ticker=%s", financials.ticker)

        # ======================================================================
        # 1. ANCRAGE CAPACITÉ BÉNÉFICIAIRE (ID: GRAHAM_EPS_BASE)
        # ======================================================================
        eps = financials.eps_ttm
        source_eps = "Yahoo Finance (TTM)"

        if (eps is None or eps <= 0) and financials.net_income_ttm:
            eps = financials.net_income_ttm / financials.shares_outstanding if financials.shares_outstanding > 0 else 0
            source_eps = "Calculated (Net Income / Shares)"

        if params.manual_fcf_base is not None:
            eps = params.manual_fcf_base
            source_eps = "Manual override (Expert)"

        if eps is None or eps <= 0:
            raise CalculationError("EPS strictement positif requis pour le modèle de Graham.")

        self.add_step(
            step_key="GRAHAM_EPS_BASE",
            label="BPA Normalisé (EPS)",
            theoretical_formula=r"EPS",
            result=eps,
            numerical_substitution=f"EPS = {eps:.2f} ({source_eps})",
            interpretation="Bénéfice par action utilisé comme socle de rentabilité."
        )

        # ======================================================================
        # 2. MULTIPLICATEUR DE CROISSANCE (ID: GRAHAM_MULTIPLIER)
        # ======================================================================
        g_display = params.fcf_growth_rate * 100.0
        growth_multiplier = 8.5 + 2.0 * g_display

        self.add_step(
            step_key="GRAHAM_MULTIPLIER",
            label="Multiplicateur de croissance",
            theoretical_formula=r"8.5 + 2g",
            result=growth_multiplier,
            numerical_substitution=f"8.5 + 2 × {g_display:.2f}",
            interpretation="Prime de croissance appliquée selon le barème révisé de Graham."
        )

        # ======================================================================
        # 3. VALEUR INTRINSÈQUE FINALE (ID: GRAHAM_FINAL)
        # ======================================================================
        y_display = params.corporate_aaa_yield * 100.0

        if y_display <= 0:
            raise CalculationError("Le rendement obligataire AAA (Y) doit être > 0.")

        intrinsic_value = (eps * growth_multiplier * 4.4) / y_display

        self.add_step(
            step_key="GRAHAM_FINAL",
            label="Valeur Graham 1974",
            theoretical_formula=r"\frac{EPS \times (8.5 + 2g) \times 4.4}{Y}",
            result=intrinsic_value,
            numerical_substitution=f"({eps:.2f} × {growth_multiplier:.2f} × 4.4) / {y_display:.2f}",
            interpretation="Estimation de la valeur intrinsèque ajustée par le rendement des obligations AAA."
        )

        return GrahamValuationResult(
            request=None, financials=financials, params=params,
            intrinsic_value_per_share=intrinsic_value, market_price=financials.current_price,
            eps_used=eps, growth_rate_used=params.fcf_growth_rate,
            aaa_yield_used=params.corporate_aaa_yield,
            calculation_trace=self.calculation_trace
        )