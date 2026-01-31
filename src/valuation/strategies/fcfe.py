"""
src/valuation/strategies/fcfe.py

FREE CASH FLOW TO EQUITY (FCFE) STRATEGY
========================================
Academic Reference: Damodaran (Investment Valuation).
Economic Domain: Leveraged firms / Financial Services.
Logic: Direct Equity valuation via a Clean Walk of shareholder flows.

Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from typing import Tuple, Dict

from src.computation.financial_math import calculate_fcfe_reconstruction
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
from src.i18n.fr.ui.expert import FCFETexts as Texts
from src.models import (
    Company,
    Parameters,
    EquityDCFValuationResult,
    ValuationMode
)
from src.valuation.pipelines import DCFCalculationPipeline
from src.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class FCFEStrategy(ValuationStrategy):
    """
    FCFE Strategy (Direct Equity).

    Reconstructs the cash flow available to shareholders ($FCFE$) after
    operating expenses, reinvestment, and net debt servicing.

    Attributes
    ----------
    academic_reference : str
        Damodaran.
    economic_domain : str
        Equity Valuation / Leveraged Firms.
    """

    academic_reference = "Damodaran"
    economic_domain = "Equity Valuation / Leveraged Firms"

    def execute(
        self,
        financials: Company,
        params: Parameters
    ) -> EquityDCFValuationResult:
        """
        Executes FCFE valuation via the Unified Pipeline with logical walk tracking.

        Parameters
        ----------
        financials : Company
            Target company financial data.
        params : Parameters
            Calculation hypotheses.

        Returns
        -------
        EquityDCFValuationResult
            The intrinsic value result for shareholders.
        """
        # 1. SHAREHOLDER FLOW RECONSTRUCTION (Phase 2 - Glass Box Map)
        ni, adj, nb, fcfe_base, sources_map = self._resolve_fcfe_components(financials, params)

        # Financial Guard: Block negative FCFE in Auto mode
        if params.growth.manual_fcf_base is None and fcfe_base <= 0:
            raise CalculationError(
                CalculationErrors.NEGATIVE_FLUX_AUTO.format(
                    model=RegistryTexts.FCFE_L,
                    val=fcfe_base
                )
            )

        variables = {
            "NI": self._build_variable_info(
                "NI", ni, None, financials.net_income_ttm, "Net Income (TTM)"
            ),
            "Adj": self._build_variable_info(
                "Adj", adj, None, adj, "Non-cash Adjustments & CapEx delta"
            ),
            "NB": self._build_variable_info(
                "NB", nb, params.growth.manual_net_borrowing, financials.net_borrowing_ttm,
                Texts.INP_NET_BORROWING
            )
        }

        self.add_step(
            step_key="FCFE_BASE_SELECTION",
            label=RegistryTexts.FCFE_BASE_L,
            theoretical_formula=StrategyFormulas.FCFE_RECONSTRUCTION,
            result=fcfe_base,
            actual_calculation=KPITexts.SUB_FCFE_WALK.format(
                ni=ni, adj=adj, nb=nb, total=fcfe_base
            ),
            interpretation=StrategyInterpretations.FCFE_LOGIC,
            source=sources_map["total"],
            variables_map=variables
        )

        # 2. PIPELINE EXECUTION (DIRECT EQUITY MODE)
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.FCFE,
            glass_box_enabled=self.glass_box_enabled
        )

        raw_result = pipeline.run(
            base_value=fcfe_base,
            financials=financials,
            params=params
        )

        if not isinstance(raw_result, EquityDCFValuationResult):
            raise CalculationError(
                DiagnosticTexts.MODEL_LOGIC_MSG.format(
                    model=RegistryTexts.FCFE_L,
                    issue=type(raw_result).__name__
                )
            )

        result: EquityDCFValuationResult = raw_result

        # 3. FINALIZATION
        self._merge_traces(result)
        self.generate_audit_report(result)
        self.verify_output_contract(result)

        return result

    @staticmethod
    def _resolve_fcfe_components(
        financials: Company,
        params: Parameters
    ) -> Tuple[float, float, float, float, Dict[str, str]]:
        """
        Resolves FCFE components for a transparent walk.

        Returns
        -------
        Tuple[float, float, float, float, Dict[str, str]]
            (Net Income, Adjustments, Net Borrowing, Total FCFE, Sources Map)
        """
        g = params.growth
        sources = {"total": StrategySources.YAHOO_TTM_SIMPLE}

        # Case A: Direct Analyst Override (La source devient orange Manual)
        if g.manual_fcf_base is not None:
            sources["total"] = StrategySources.MANUAL_OVERRIDE
            return 0.0, 0.0, 0.0, g.manual_fcf_base, sources

        # Case B: Standard Reconstruction Walk
        ni = financials.net_income_ttm or 0.0
        nb = (
            g.manual_net_borrowing
            if g.manual_net_borrowing is not None
            else (financials.net_borrowing_ttm or 0.0)
        )

        # Adjustments: FCF (Operating) - Net Income
        adj = (financials.fcf_last - ni) if financials.fcf_last is not None else 0.0

        fcfe_calculated = calculate_fcfe_reconstruction(ni=ni, adjustments=adj, net_borrowing=nb)

        if fcfe_calculated <= 0:
            logger.warning("[FCFE] Negative reconstructed flow for %s", financials.ticker)

        return ni, adj, nb, fcfe_calculated, sources