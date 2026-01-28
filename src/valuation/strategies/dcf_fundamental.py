"""
src/valuation/strategies/fundamental_fcff.py

FUNDAMENTAL DCF STRATEGY (NORMALIZED)
=====================================
Academic Reference: CFA Institute / Damodaran.
Economic Domain: Cyclical or Industrial firms requiring cash flow smoothing.
Logic: Anchored on normalized/smoothed fundamental flows to reduce volatility.

Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
from typing import Tuple

from src.exceptions import CalculationError
from src.models import (
    CompanyFinancials, DCFParameters, DCFValuationResult,
    TraceHypothesis, ValuationMode
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


class FundamentalFCFFStrategy(ValuationStrategy):
    """
    Normalized FCFF Strategy.

    Uses economic cycle-smoothed flows to value industrial or cyclical
    entities where TTM data may be unrepresentative of long-term earnings.
    """

    academic_reference = "CFA Institute / Damodaran"
    economic_domain = "Cyclical / Industrial firms"

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:
        """
        Executes fundamental valuation using normalized cash flows.
        """
        # 1. SELECT AND VALIDATE NORMALIZED FCF ANCHOR
        fcf_base, source = self._select_normalized_fcf(financials, params)

        if fcf_base <= 0:
            raise CalculationError(CalculationErrors.NEGATIVE_FCF_NORM)

        self.add_step(
            step_key="FCF_NORM_SELECTION",
            label=RegistryTexts.DCF_FCF_NORM_L,
            theoretical_formula=StrategyFormulas.FCF_NORMALIZED,
            result=fcf_base,
            numerical_substitution=KPITexts.SUB_FCF_NORM.format(val=fcf_base, src=source),
            interpretation=StrategyInterpretations.FUND_NORM,
            source=source,
            hypotheses=[
                TraceHypothesis(
                    name=RegistryTexts.FCFF_NORM_L,
                    value=fcf_base,
                    unit=financials.currency,
                    source=source
                )
            ]
        )

        # 2. PIPELINE ORCHESTRATION
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.FCFF_NORMALIZED,
            glass_box_enabled=self.glass_box_enabled
        )

        raw_result = pipeline.run(base_value=fcf_base, financials=financials, params=params)

        # TYPE SAFETY: Resolve generic result into specific DCF container
        if not isinstance(raw_result, DCFValuationResult):
            raise CalculationError(
                DiagnosticTexts.MODEL_LOGIC_MSG.format(
                    model=RegistryTexts.FCFF_NORM_L,
                    issue=type(raw_result).__name__
                )
            )

        result: DCFValuationResult = raw_result

        # 3. FINALIZATION AND INSTITUTIONAL AUDIT
        self._merge_traces(result)
        self.generate_audit_report(result)
        self.verify_output_contract(result)

        return result

    @staticmethod
    def _select_normalized_fcf(
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> Tuple[float, str]:
        """
        Determines the smoothed FCF anchor based on data hierarchy.
        """
        # Priority 1: Expert Manual Override
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        # Priority 2: Calculated smoothed fundamental FCF
        if financials.fcf_fundamental_smoothed is None:
            raise CalculationError(CalculationErrors.MISSING_FCF_NORM)

        return financials.fcf_fundamental_smoothed, StrategySources.YAHOO_FUNDAMENTAL