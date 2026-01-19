"""
core/valuation/strategies/dcf_growth.py
MÉTHODE : REVENUE-DRIVEN FCFF — VERSION V10.0 (Architecture Unifiée Sprint 2)
Rôle : Valorisation par revenus avec convergence des marges via Pipeline DCF.
"""

from __future__ import annotations
import logging

from src.exceptions import CalculationError
from src.domain.models import CompanyFinancials, DCFParameters, DCFValuationResult, ValuationMode
from src.valuation.strategies.abstract import ValuationStrategy
from src.valuation.pipelines import DCFCalculationPipeline
from src.computation.growth import MarginConvergenceProjector
# Import depuis core.i18n
from src.i18n import RegistryTexts, StrategyInterpretations, StrategyFormulas, CalculationErrors, KPITexts

logger = logging.getLogger(__name__)

class RevenueBasedStrategy(ValuationStrategy):
    """Revenue-Driven DCF. Injecte le moteur de convergence des marges dans le pipeline."""

    academic_reference = "Damodaran / McKinsey"
    economic_domain = "Growth firms / Revenue-driven"

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFValuationResult:
        # 1. Ancrage revenus
        rev_base = self._select_revenue_base(financials, params)

        # Sécurité financière : Revenus négatifs en mode Auto uniquement
        if params.growth.manual_fcf_base is None and rev_base <= 0:
            raise CalculationError(CalculationErrors.NEGATIVE_FLUX_AUTO.format(model="DCF Growth", val=rev_base))

        self.add_step(
            step_key="GROWTH_REV_BASE",
            label=RegistryTexts.GROWTH_REV_BASE_L,
            theoretical_formula=StrategyFormulas.REVENUE_BASE,
            result=rev_base,
            numerical_substitution=KPITexts.SUB_REV_BASE.format(val=rev_base),
            interpretation=StrategyInterpretations.GROWTH_REV
        )

        # 2. Exécution du Pipeline Unifié (avec le projecteur spécifique Growth)
        pipeline = DCFCalculationPipeline(
            projector=MarginConvergenceProjector(),
            mode=ValuationMode.FCFF_GROWTH,
            glass_box_enabled=self.glass_box_enabled
        )

        result = pipeline.run(base_value=rev_base, financials=financials, params=params)

        # 3. Finalisation
        self._merge_traces(result)
        return result

    def _select_revenue_base(self, financials: CompanyFinancials, params: DCFParameters) -> float:
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base
        if financials.revenue_ttm is None or financials.revenue_ttm <= 0:
            raise CalculationError(CalculationErrors.MISSING_REV)
        return financials.revenue_ttm
