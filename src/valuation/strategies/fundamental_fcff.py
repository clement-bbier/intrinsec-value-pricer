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

from src.computation.flow_projector import SimpleFlowProjector
from src.exceptions import CalculationError
from src.i18n import (
    CalculationErrors,
    DiagnosticTexts,
    KPITexts,
    RegistryTexts,
    StrategyFormulas,
    StrategyInterpretations,
    StrategySources
)
from src.i18n.fr.ui.expert import FCFFNormalizedTexts as Texts
from src.models import (
    Company,
    Parameters,
    DCFValuationResult,
    ValuationMethodology
)
from src.valuation.pipelines import DCFCalculationPipeline
from src.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class FundamentalFCFFStrategy(ValuationStrategy):
    """
    Normalized FCFF Strategy.

    Uses economic cycle-smoothed flows to value industrial or cyclical
    entities where TTM data may be unrepresentative of long-term earnings.

    Attributes
    ----------
    academic_reference : str
        CFA Institute / Damodaran.
    economic_domain : str
        Cyclical / Industrial firms.
    """

    academic_reference = "CFA Institute / Damodaran"
    economic_domain = "Cyclical / Industrial firms"

    def execute(
        self,
        financials: Company,
        params: Parameters
    ) -> DCFValuationResult:
        """
        Executes fundamental valuation using normalized cash flows.

        Parameters
        ----------
        financials : Company
            Target company financial data.
        params : Parameters
            Calculation hypotheses.

        Returns
        -------
        DCFValuationResult
            The Enterprise Value result based on cycle-smoothed flows.
        """
        # 1. SELECT AND VALIDATE NORMALIZED FCF ANCHOR (Phase 2 - Glass Box)
        fcf_base, source = self._select_normalized_fcf(financials, params)

        if fcf_base <= 0:
            raise CalculationError(CalculationErrors.NEGATIVE_FCF_NORM)

        # Construction de la variables_map pour tracer l'origine du lissage
        variables = {
            "FCF_norm": self._build_variable_info(
                symbol="FCF_norm",
                value=fcf_base,
                manual_value=params.growth.manual_fcf_base,
                provider_value=financials.fcf_fundamental_smoothed,
                description=Texts.INP_BASE
            )
        }

        self.add_step(
            step_key="FCF_NORM_SELECTION",
            label=RegistryTexts.DCF_FCF_NORM_L,
            theoretical_formula=StrategyFormulas.FCF_NORMALIZED,
            result=fcf_base,
            actual_calculation=KPITexts.SUB_FCF_NORM.format(val=fcf_base, src=source),
            interpretation=StrategyInterpretations.FUND_NORM,
            source=source,
            variables_map=variables
        )

        # 2. PIPELINE ORCHESTRATION
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMethodology.FCFF_NORMALIZED,
            glass_box_enabled=self.glass_box_enabled
        )

        raw_result = pipeline.run(base_value=fcf_base, financials=financials, params=params)

        # TYPE SAFETY: Validation du contrat spécifique DCF
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
        financials: Company,
        params: Parameters
    ) -> Tuple[float, str]:
        """
        Determines the smoothed FCF anchor based on data hierarchy.

        Returns
        -------
        Tuple[float, str]
            (Smoothed FCF value, Source label)
        """
        # Priority 1: Expert Manual Override
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        # Priority 2: Calculated smoothed fundamental FCF (Yahoo/Analyst logic)
        if financials.fcf_fundamental_smoothed is None:
            raise CalculationError(CalculationErrors.MISSING_FCF_NORM)

        return financials.fcf_fundamental_smoothed, StrategySources.YAHOO_FUNDAMENTAL