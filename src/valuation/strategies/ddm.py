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

from src.computation.flow_projector import SimpleFlowProjector
from src.exceptions import CalculationError
from src.i18n import (
    CalculationErrors,
    DiagnosticTexts,
    KPITexts,
    RegistryTexts,
    StrategyFormulas,
    StrategyInterpretations,
    StrategySources,
    SharedTexts
)
from src.i18n.fr.ui.expert import DDMTexts as Texts
from src.models import (
    Company,
    Parameters,
    EquityDCFValuationResult,
    ValuationMode
)
from src.valuation.pipelines import DCFCalculationPipeline
from src.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class DividendDiscountStrategy(ValuationStrategy):
    """
    DDM Strategy (Gordon & Shapiro).

    Estimates intrinsic value as the sum of discounted future dividends
    using the Cost of Equity ($K_e$) as the discount rate.

    Attributes
    ----------
    academic_reference : str
        Gordon / Shapiro.
    economic_domain : str
        Dividend-paying Firms / Mature Utilities.
    """

    academic_reference = "Gordon / Shapiro"
    economic_domain = "Dividend-paying Firms / Mature Utilities"

    def execute(
        self,
        financials: Company,
        params: Parameters
    ) -> EquityDCFValuationResult:
        """
        Executes DDM valuation via the Unified Pipeline with type-safe downcasting.

        Parameters
        ----------
        financials : Company
            Target company financial data.
        params : Parameters
            Calculation hypotheses.

        Returns
        -------
        EquityDCFValuationResult
            The intrinsic value result based on dividend streams.
        """
        # 1. RESOLVE DIVIDEND BASE (D_0) - Phase 2 : Traçabilité des variables
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

        # Construction de la variables_map pour exposer le D0 et les actions
        variables = {
            "D_0": self._build_variable_info(
                symbol="D_0",
                value=d0_per_share,
                manual_value=params.growth.manual_dividend_base,
                provider_value=financials.dividend_share,
                description=Texts.INP_DIVIDEND_BASE
            ),
            "Shares": self._build_variable_info(
                symbol="Shares",
                value=financials.shares_outstanding,
                manual_value=params.growth.manual_shares_outstanding,
                provider_value=financials.shares_outstanding,
                description=SharedTexts.INP_SHARES
            )
        }

        self.add_step(
            step_key="DDM_BASE_SELECTION",
            label=RegistryTexts.DDM_BASE_L,
            theoretical_formula=StrategyFormulas.DIVIDEND_BASE,
            result=total_dividend_mass,
            actual_calculation=KPITexts.SUB_DDM_BASE.format(
                d0=d0_per_share,
                shares=financials.shares_outstanding,
                val=total_dividend_mass
            ),
            interpretation=StrategyInterpretations.DDM_LOGIC,
            source=source_div,
            variables_map=variables
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

        # Type Safety Check
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
        financials: Company,
        params: Parameters
    ) -> Tuple[float, str]:
        """
        Resolves the reference dividend per share ($D_0$).

        Returns
        -------
        Tuple[float, str]
            (Dividend per share, Source label)
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