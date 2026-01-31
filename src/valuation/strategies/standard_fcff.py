"""
src/valuation/strategies/standard_fcff.py

STANDARD FCFF STRATEGY
======================
Academic Reference: Damodaran (Investment Valuation).
Economic Domain: Mature entities with stable, predictable cash flows.
Logic: Two-stage projection followed by terminal value discounting.

Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
from typing import Tuple

from src.exceptions import CalculationError
from src.models import Company, Parameters, DCFValuationResult, ValuationMode
from src.valuation.strategies.abstract import ValuationStrategy
from src.valuation.pipelines import DCFCalculationPipeline
from src.computation.flow_projector import SimpleFlowProjector

# Centralized i18n imports (Strict zero-raw-text policy)
from src.i18n import (
    RegistryTexts,
    StrategyFormulas,
    CalculationErrors,
    StrategySources,
    KPITexts,
    DiagnosticTexts
)

logger = logging.getLogger(__name__)


class StandardFCFFStrategy(ValuationStrategy):
    """
    Standard FCFF (Damodaran).

    Delegates heavy-lifting math to the unified DCF pipeline after anchoring
    on the current TTM Free Cash Flow.
    """

    academic_reference = "Damodaran"
    economic_domain = "Mature firms / Stable cash-flows"

    def execute(
            self,
            financials: Company,
            params: Parameters
    ) -> DCFValuationResult:
        """
        Executes Standard DCF Strategy with strict output contract verification.
        """
        # 1. SELECT BASE FLOW ANCHOR
        fcf_base, source = self._select_base_fcf(financials, params)

        if params.growth.manual_fcf_base is None and fcf_base <= 0:
            raise CalculationError(
                CalculationErrors.NEGATIVE_FLUX_AUTO.format(
                    model=RegistryTexts.FCFF_STANDARD_L,
                    val=fcf_base
                )
            )

        self.add_step(
            step_key="FCF_BASE_SELECTION",
            label=RegistryTexts.DCF_FCF_BASE_L,
            theoretical_formula=StrategyFormulas.FCF_BASE,
            result=fcf_base,
            actual_calculation=KPITexts.SUB_FCF_BASE.format(val=fcf_base, src=source),
            interpretation=RegistryTexts.DCF_FCF_BASE_D,
            source=source
        )

        # 2. PIPELINE EXECUTION
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.FCFF_STANDARD,
            glass_box_enabled=self.glass_box_enabled
        )

        raw_result = pipeline.run(base_value=fcf_base, financials=financials, params=params)

        # TYPE SAFETY: Resolve into DCF container
        if not isinstance(raw_result, DCFValuationResult):
            raise CalculationError(
                DiagnosticTexts.MODEL_LOGIC_MSG.format(
                    model=RegistryTexts.FCFF_STANDARD_L,
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
    def _select_base_fcf(
        financials: Company,
        params: Parameters
    ) -> Tuple[float, str]:
        """
        Identifies the FCF anchor based on sovereignty hierarchy.
        """
        # Priority 1: Expert Manual Override
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        # Priority 2: Deep Fetch TTM FCF
        if financials.fcf_last is not None:
            return financials.fcf_last, StrategySources.YAHOO_TTM

        # Critical failure: No valid flow data
        raise CalculationError(CalculationErrors.MISSING_FCF_STD)