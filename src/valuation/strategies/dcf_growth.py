"""
src/valuation/strategies/revenue_growth.py

REVENUE-DRIVEN GROWTH STRATEGY
==============================
Academic Reference: Damodaran / McKinsey.
Economic Domain: High-growth firms / Start-ups / Turnarounds.
Logic: Margin convergence with linear fade-down toward a target normative state.

Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
from typing import Tuple

from src.exceptions import CalculationError
from src.models import CompanyFinancials, DCFParameters, DCFValuationResult, ValuationMode
from src.valuation.strategies.abstract import ValuationStrategy
from src.valuation.pipelines import DCFCalculationPipeline
from src.computation.growth import MarginConvergenceProjector

# Centralized i18n imports
from src.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    StrategyFormulas,
    CalculationErrors,
    KPITexts,
    StrategySources,
    DiagnosticTexts
)

logger = logging.getLogger(__name__)


class RevenueBasedStrategy(ValuationStrategy):
    """
    Revenue-Driven DCF (Convergence Model).

    Injects the Margin Convergence engine into the calculation pipeline to value
    entities with non-steady-state current profitability.
    """

    academic_reference = "Damodaran / McKinsey"
    economic_domain = "Growth firms / Revenue-driven"

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:
        """
        Executes Revenue-driven valuation with margin convergence logic.
        """
        # 1. ANCHOR REVENUE BASE
        rev_base, source_rev = self._select_revenue_base(financials, params)

        # Financial Guard: Prevent negative revenue in Auto mode
        if params.growth.manual_fcf_base is None and rev_base <= 0:
            raise CalculationError(
                CalculationErrors.NEGATIVE_FLUX_AUTO.format(
                    model=RegistryTexts.FCFF_GROWTH_L,
                    val=rev_base
                )
            )

        self.add_step(
            step_key="GROWTH_REV_BASE",
            label=RegistryTexts.GROWTH_REV_BASE_L,
            theoretical_formula=StrategyFormulas.REVENUE_BASE,
            result=rev_base,
            numerical_substitution=KPITexts.SUB_REV_BASE.format(val=rev_base),
            interpretation=StrategyInterpretations.GROWTH_REV,
            source=source_rev
        )

        # 2. PIPELINE ORCHESTRATION (Specialized Convergence Projector)
        pipeline = DCFCalculationPipeline(
            projector=MarginConvergenceProjector(),
            mode=ValuationMode.FCFF_GROWTH,
            glass_box_enabled=self.glass_box_enabled
        )

        raw_result = pipeline.run(base_value=rev_base, financials=financials, params=params)

        # TYPE SAFETY: Explicit cast for IDE resolution
        if not isinstance(raw_result, DCFValuationResult):
            raise CalculationError(
                DiagnosticTexts.MODEL_LOGIC_MSG.format(
                    model=RegistryTexts.FCFF_GROWTH_L,
                    issue=type(raw_result).__name__
                )
            )

        result: DCFValuationResult = raw_result

        # 3. FINALIZATION AND AUDIT
        self._merge_traces(result)
        self.generate_audit_report(result)
        self.verify_output_contract(result)

        return result

    @staticmethod
    def _select_revenue_base(
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> Tuple[float, str]:
        """
        Determines the starting Revenue anchor.
        """
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        if financials.revenue_ttm is None or financials.revenue_ttm <= 0:
            raise CalculationError(CalculationErrors.MISSING_REV)

        return financials.revenue_ttm, StrategySources.YAHOO_TTM_SIMPLE