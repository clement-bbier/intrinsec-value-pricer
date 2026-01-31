"""
src/valuation/strategies/graham_value.py

GRAHAM INTRINSIC VALUE STRATEGY
===============================
Academic Reference: Benjamin Graham (1974 Revised Formula).
Economic Domain: Value Investing / Defensive / Mature Firms.
Invariants: Capped growth multiplier normalized by AAA Corporate Yield.

Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
from typing import Tuple, Dict, Optional

from src.exceptions import CalculationError
from src.models import Company, Parameters, GrahamValuationResult
from src.valuation.strategies.abstract import ValuationStrategy

# i18n Centralized Mapping
from src.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    StrategyFormulas,
    CalculationErrors,
    StrategySources,
    KPITexts, SharedTexts
)

logger = logging.getLogger(__name__)


class GrahamNumberStrategy(ValuationStrategy):
    """
    Value estimation based on Benjamin Graham's revised 1974 formula.

    Theoretical Formula:
    $$IV = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}$$
    """

    academic_reference = "Benjamin Graham (1974)"
    economic_domain = "Value Investing / Defensive"

    def execute(
        self,
        financials: Company,
        params: Parameters
    ) -> GrahamValuationResult:
        """
        Executes the Graham valuation sequence.
        """
        r = params.rates
        g = params.growth

        # 1. EPS BASE SELECTION
        eps, source_eps = self._select_eps(financials, params)

        self.add_step(
            step_key="GRAHAM_EPS_BASE",
            label=RegistryTexts.GRAHAM_EPS_L,
            theoretical_formula=StrategyFormulas.EPS_BASE,
            result=eps,
            actual_calculation=KPITexts.SUB_EPS_GRAHAM.format(val=eps, src=source_eps),
            interpretation=StrategyInterpretations.GRAHAM_EPS,
            source=source_eps
        )

        # 2. GROWTH MULTIPLIER (M = 8.5 + 2g)
        growth_rate = g.fcf_growth_rate or 0.0
        growth_multiplier = self._compute_growth_multiplier(growth_rate)

        self.add_step(
            step_key="GRAHAM_MULTIPLIER",
            label=RegistryTexts.GRAHAM_MULT_L,
            theoretical_formula=StrategyFormulas.GRAHAM_MULTIPLIER,
            result=growth_multiplier,
            actual_calculation=KPITexts.SUB_GRAHAM_MULT.format(g=growth_rate * 100.0),
            interpretation=StrategyInterpretations.GRAHAM_MULT,
            source=StrategySources.ANALYST_OVERRIDE
        )

        # 3. FINAL INTRINSIC VALUE (AAA YIELD ADJUSTMENT)
        aaa_yield = r.corporate_aaa_yield or 0.044
        self._validate_aaa_yield(aaa_yield)
        intrinsic_value = self._compute_intrinsic_value(eps, growth_multiplier, aaa_yield)

        # On mappe les composants de la formule de Graham
        graham_vars = {
            "EPS": self._build_variable_info("EPS", eps, params.growth.manual_fcf_base, financials.eps_ttm,
                                             SharedTexts.INP_EPS_NORM),
            "g": self._build_variable_info("g", growth_rate, params.growth.fcf_growth_rate, None,
                                           SharedTexts.INP_GROWTH_G, format_as_pct=True),
            "Y": self._build_variable_info("Y", aaa_yield, r.corporate_aaa_yield, 0.044, SharedTexts.INP_YIELD_AAA,
                                           format_as_pct=True)
        }

        self.add_step(
            step_key="GRAHAM_FINAL",
            label=RegistryTexts.GRAHAM_IV_L,
            theoretical_formula=StrategyFormulas.GRAHAM_VALUE,
            result=intrinsic_value,
            actual_calculation=f"({eps:.2f} * {growth_multiplier:.2f} * 4.4) / ({aaa_yield * 100:.2f})",
            interpretation=StrategyInterpretations.GRAHAM_IV,
            source=StrategySources.CALCULATED,
            variables_map=graham_vars
        )

        # 4. RESULT GENERATION & AUDIT PILLARS
        audit_metrics = self._compute_graham_audit_metrics(financials, eps)

        result = GrahamValuationResult(
            request=None,
            financials=financials,
            params=params,
            intrinsic_value_per_share=intrinsic_value,
            market_price=financials.current_price,
            eps_used=eps,
            growth_rate_used=growth_rate,
            aaa_yield_used=aaa_yield,
            calculation_trace=self.calculation_trace,
            pe_observed=audit_metrics["pe"],
            graham_multiplier=growth_multiplier,
            payout_ratio_observed=audit_metrics["payout"]
        )

        self.generate_audit_report(result)
        self.verify_output_contract(result)
        return result

    @staticmethod
    def _select_eps(financials: Company, params: Parameters) -> Tuple[float, str]:
        """Selects the reference EPS based on sovereignty hierarchy."""
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        if financials.eps_ttm is not None and financials.eps_ttm > 0:
            return financials.eps_ttm, StrategySources.YAHOO_TTM_SIMPLE

        if financials.net_income_ttm and financials.shares_outstanding > 0:
            eps_calc = financials.net_income_ttm / financials.shares_outstanding
            if eps_calc > 0:
                return eps_calc, StrategySources.CALCULATED_NI

        raise CalculationError(CalculationErrors.MISSING_EPS_GRAHAM)

    @staticmethod
    def _compute_growth_multiplier(growth_rate: float) -> float:
        """Computes Graham's growth multiplier."""
        return 8.5 + 2.0 * (growth_rate * 100.0)

    @staticmethod
    def _validate_aaa_yield(aaa_yield: float) -> None:
        """Ensures AAA yield is strictly positive to prevent division by zero."""
        if aaa_yield is None or aaa_yield <= 0:
            raise CalculationError(CalculationErrors.INVALID_AAA)

    @staticmethod
    def _compute_intrinsic_value(eps: float, multiplier: float, aaa_yield: float) -> float:
        """Applies Graham's 1974 final formula."""
        return (eps * multiplier * 4.4) / (aaa_yield * 100.0)

    @staticmethod
    def _compute_graham_audit_metrics(financials: Company, eps: float) -> Dict[str, Optional[float]]:
        """Prepares audit metrics for Pillar 3 (Reliability)."""
        pe = financials.current_price / eps if eps > 0 else None
        payout = None
        if financials.net_income_ttm and financials.net_income_ttm > 0:
            payout = financials.dividends_total_calculated / financials.net_income_ttm
        return {"pe": pe, "payout": payout}