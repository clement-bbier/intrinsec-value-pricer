"""
core/valuation/strategies/dcf_standard.py
MÉTHODE : FCFF TWO-STAGE — VERSION V10.0 (Architecture Unifiée Sprint 2)
Rôle : Sélection du flux de départ et exécution via le Pipeline DCF.
"""

from __future__ import annotations
import logging

from src.exceptions import CalculationError
from src.domain.models import CompanyFinancials, DCFParameters, DCFValuationResult, ValuationMode
from src.valuation.strategies.abstract import ValuationStrategy
from src.valuation.pipelines import DCFCalculationPipeline
from src.computation.growth import SimpleFlowProjector
# Import depuis core.i18n
from src.i18n import RegistryTexts, StrategyFormulas, CalculationErrors, StrategySources, KPITexts

logger = logging.getLogger(__name__)

class StandardFCFFStrategy(ValuationStrategy):
    """FCFF Standard (Damodaran). Délègue au pipeline avec un projecteur simple."""

    academic_reference = "Damodaran"
    economic_domain = "Mature firms / Stable cash-flows"

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFValuationResult:
        # 1. Sélection du flux de base
        fcf_base, source = self._select_base_fcf(financials, params)

        # Sécurité financière : Flux négatifs en mode Auto uniquement
        if params.growth.manual_fcf_base is None and fcf_base <= 0:
            raise CalculationError(CalculationErrors.NEGATIVE_FLUX_AUTO.format(model="DCF Standard", val=fcf_base))

        self.add_step(
            step_key="FCF_BASE_SELECTION",
            label=RegistryTexts.DCF_FCF_BASE_L,
            theoretical_formula=StrategyFormulas.FCF_BASE,
            result=fcf_base,
            numerical_substitution=KPITexts.SUB_FCF_BASE.format(val=fcf_base, src=source),
            interpretation=RegistryTexts.DCF_FCF_BASE_D
        )

        # 2. Exécution du Pipeline Unifié
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.FCFF_STANDARD,
            glass_box_enabled=self.glass_box_enabled
        )

        result = pipeline.run(base_value=fcf_base, financials=financials, params=params)

        # 3. Finalisation
        self._merge_traces(result)
        return result

    def _select_base_fcf(self, financials: CompanyFinancials, params: DCFParameters) -> tuple[float, str]:
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE
        if financials.fcf_last is None:
            raise CalculationError(CalculationErrors.MISSING_FCF_STD)
        return financials.fcf_last, StrategySources.YAHOO_TTM
