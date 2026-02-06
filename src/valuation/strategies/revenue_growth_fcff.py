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

from src.computation.flow_projector import MarginConvergenceProjector
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
from src.i18n.fr.ui.expert import FCFFGrowthTexts as Texts
from src.models import (
    Company,
    Parameters,
    DCFValuationResult,
    ValuationMethodology
)
from src.valuation.pipelines import DCFCalculationPipeline
from src.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class RevenueBasedStrategy(ValuationStrategy):
    """
    Revenue-Driven DCF (Convergence Model).

    Injects the Margin Convergence engine into the calculation pipeline to value
    entities with non-steady-state current profitability by forecasting
    top-line growth and margin expansion.

    Attributes
    ----------
    academic_reference : str
        Damodaran / McKinsey.
    economic_domain : str
        Growth firms / Revenue-driven / Turnarounds.
    """

    academic_reference = "Damodaran / McKinsey"
    economic_domain = "Growth firms / Revenue-driven"

    def execute(
        self,
        financials: Company,
        params: Parameters
    ) -> DCFValuationResult:
        """
        Executes Revenue-driven valuation with margin convergence logic.

        Parameters
        ----------
        financials : Company
            Target company financial data.
        params : Parameters
            Calculation hypotheses.

        Returns
        -------
        DCFValuationResult
            The Enterprise Value result based on revenue and margin trajectories.
        """
        # 1. ANCHOR REVENUE BASE (Phase 2 - Glass Box Provenance)
        rev_base, source_rev = self._select_revenue_base(financials, params)

        # Financial Guard: Prevent negative revenue in Auto mode
        if params.growth.manual_fcf_base is None and rev_base <= 0:
            raise CalculationError(
                CalculationErrors.NEGATIVE_FLUX_AUTO.format(
                    model=RegistryTexts.FCFF_GROWTH_L,
                    val=rev_base
                )
            )

        # Tracé de l'ancrage du Chiffre d'Affaires (Rev_0)
        rev_vars = {
            "Rev_0": self._build_variable_info(
                symbol="Rev_0",
                value=rev_base,
                manual_value=params.growth.manual_fcf_base, # Champ partagé pour l'override d'ancrage
                provider_value=financials.revenue_ttm,
                description=Texts.INP_BASE
            )
        }

        self.add_step(
            step_key="GROWTH_REV_BASE",
            label=RegistryTexts.GROWTH_REV_BASE_L,
            theoretical_formula=StrategyFormulas.REVENUE_BASE,
            result=rev_base,
            actual_calculation=KPITexts.SUB_REV_BASE.format(val=rev_base),
            interpretation=StrategyInterpretations.GROWTH_REV,
            source=source_rev,
            variables_map=rev_vars
        )

        # 2. PIPELINE ORCHESTRATION (Specialized Convergence Projector)
        # On utilise le projecteur de convergence de marges
        pipeline = DCFCalculationPipeline(
            projector=MarginConvergenceProjector(),
            mode=ValuationMethodology.FCFF_GROWTH,
            glass_box_enabled=self.glass_box_enabled
        )

        raw_result = pipeline.run(base_value=rev_base, financials=financials, params=params)

        # TYPE SAFETY: Validation du contrat de sortie
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
        financials: Company,
        params: Parameters
    ) -> Tuple[float, str]:
        """
        Determines the starting Revenue anchor based on hierarchy.

        Returns
        -------
        Tuple[float, str]
            (Revenue value, Source label)
        """
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        if financials.revenue_ttm is None or financials.revenue_ttm <= 0:
            raise CalculationError(CalculationErrors.MISSING_REV)

        return financials.revenue_ttm, StrategySources.YAHOO_TTM_SIMPLE