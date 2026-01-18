"""
core/valuation/strategies/dcf_fundamental.py
MÉTHODE : FCFF NORMALIZED — VERSION V10.0 (Architecture Unifiée Sprint 2)
Rôle : Normalisation des flux cycliques et exécution via le Pipeline DCF.
"""

from __future__ import annotations
import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult, TraceHypothesis, ValuationMode
from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.pipelines import DCFCalculationPipeline
from core.computation.growth import SimpleFlowProjector
# Import depuis core.i18n
from core.i18n import RegistryTexts, StrategyInterpretations, StrategyFormulas, CalculationErrors, StrategySources, KPITexts

logger = logging.getLogger(__name__)

class FundamentalFCFFStrategy(ValuationStrategy):
    """FCFF Normalisé. Délègue au pipeline après normalisation des flux."""

    academic_reference = "CFA Institute / Damodaran"
    economic_domain = "Cyclical / Industrial firms"

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFValuationResult:
        # 1. Sélection et validation du flux normalisé
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
            hypotheses=[TraceHypothesis(name="Normalized FCF", value=fcf_base, unit=financials.currency, source=source)]
        )

        # 2. Exécution du Pipeline Unifié
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.FCFF_NORMALIZED,
            glass_box_enabled=self.glass_box_enabled
        )

        result = pipeline.run(base_value=fcf_base, financials=financials, params=params)

        # 3. Finalisation
        self._merge_traces(result)
        return result

    def _select_normalized_fcf(self, financials: CompanyFinancials, params: DCFParameters) -> tuple[float, str]:
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE
        if financials.fcf_fundamental_smoothed is None:
            raise CalculationError(CalculationErrors.MISSING_FCF_NORM)
        return financials.fcf_fundamental_smoothed, StrategySources.YAHOO_FUNDAMENTAL