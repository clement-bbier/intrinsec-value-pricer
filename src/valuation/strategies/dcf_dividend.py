"""
src/valuation/strategies/ddm.py

DIVIDEND DISCOUNT MODEL (DDM) STRATEGY
======================================
Academic Reference: Gordon & Shapiro.
Economic Domain: Mature, dividend-paying firms (Utilities, Financials).
Logic: Intrinsic value based on the present value of future dividends.

Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
from typing import Tuple

from src.exceptions import CalculationError
from src.models import (
    CompanyFinancials,
    DCFParameters,
    EquityDCFValuationResult,
    ValuationMode
)
from src.valuation.strategies.abstract import ValuationStrategy
from src.valuation.pipelines import DCFCalculationPipeline
from src.computation.growth import SimpleFlowProjector

# Centralized i18n imports
from src.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    StrategyFormulas,
    CalculationErrors,
    StrategySources,
    KPITexts,
    DiagnosticTexts
)

logger = logging.getLogger(__name__)


class DividendDiscountStrategy(ValuationStrategy):
    """
    DDM Strategy (Gordon & Shapiro).

    Estimates intrinsic value as the sum of discounted future dividends
    using the Cost of Equity ($K_e$) as the discount rate.
    """

    academic_reference = "Gordon / Shapiro"
    economic_domain = "Dividend-paying Firms / Mature Utilities"

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> EquityDCFValuationResult:
        """
        Executes DDM valuation via the Unified Pipeline with type-safe downcasting.
        """
        # 1. RESOLVE DIVIDEND BASE (D_0)
        d0_per_share, source_div = self._resolve_dividend_base(financials, params)

        # Safety Check: Block negative or null dividends in Auto mode
        if params.growth.manual_dividend_base is None and d0_per_share <= 0:
            raise CalculationError(
                CalculationErrors.NEGATIVE_FLUX_AUTO.format(
                    model=RegistryTexts.DDM_L,
                    val=d0_per_share
                )
            )

        # Convert to total mass for Pipeline consistency ($Mass = D_0 \times Shares$)
        total_dividend_mass = d0_per_share * financials.shares_outstanding

        self.add_step(
            step_key="DDM_BASE_SELECTION",
            label=RegistryTexts.DDM_BASE_L,
            theoretical_formula=StrategyFormulas.DIVIDEND_BASE,
            result=total_dividend_mass,
            numerical_substitution=KPITexts.SUB_DDM_BASE.format(
                d0=d0_per_share,
                shares=financials.shares_outstanding,
                val=total_dividend_mass
            ),
            interpretation=StrategyInterpretations.DDM_LOGIC,
            source=source_div
        )

        # 2. PIPELINE CONFIGURATION (DIRECT EQUITY MODE)
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.DDM,
            glass_box_enabled=self.glass_box_enabled
        )

        raw_result = pipeline.run(
            base_value=total_dividend_mass,
            financials=financials,
            params=params
        )

        # Type Safety: Ensure the pipeline returned an Equity-specific result
        if not isinstance(raw_result, EquityDCFValuationResult):
            raise CalculationError(
                DiagnosticTexts.MODEL_LOGIC_MSG.format(
                    model=RegistryTexts.DDM_L,
                    issue=type(raw_result).__name__
                )
            )

        result: EquityDCFValuationResult = raw_result

        # 3. FINALIZATION AND AUDIT
        self._merge_traces(result)
        self.generate_audit_report(result)
        self.verify_output_contract(result)

        return result

    @staticmethod
    def _resolve_dividend_base(
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> Tuple[float, str]:
        """
        Resolves the reference dividend per share ($D_0$).
        """
        g = params.growth

        # A. Expert Override
        if g.manual_dividend_base is not None:
            return g.manual_dividend_base, StrategySources.MANUAL_OVERRIDE

        # B. TTM Market Data
        if financials.dividend_share is not None and financials.dividend_share > 0:
            return financials.dividend_share, StrategySources.YAHOO_TTM_SIMPLE

        # C. Default Fallback
        return 0.0, StrategySources.CALCULATED