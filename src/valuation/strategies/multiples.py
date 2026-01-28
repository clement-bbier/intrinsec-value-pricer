"""
src/valuation/strategies/multiples.py

MARKET MULTIPLES STRATEGY (RELATIVE VALUATION)
==============================================
Academic Reference: Damodaran (Investment Valuation).
Economic Domain: Sector-based relative valuation.
Invariants: Triangulation of P/E, EV/EBITDA, and EV/Revenue signals.

Role:
-----
Estimates company value by applying median sector multiples to focus on
fundamentals (TTM). Acts as a market-based anchor for DCF results.

Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from typing import Dict

from src.valuation.strategies.abstract import ValuationStrategy
from src.utilities.formatting import format_smart_number
from src.models import (
    CompanyFinancials, DCFParameters, MultiplesValuationResult,
    MultiplesData, TraceHypothesis
)
from src.computation.financial_math import (
    calculate_price_from_pe_multiple,
    calculate_price_from_ev_multiple,
    calculate_triangulated_price
)
# Centralized i18n mapping
from src.i18n import (
    StrategyInterpretations,
    RegistryTexts,
    StrategyFormulas,
    StrategySources,
    KPITexts
)

logger = logging.getLogger(__name__)


class MarketMultiplesStrategy(ValuationStrategy):
    """
    Implements Relative Valuation via peer-group triangulation.

    This strategy calculates three independent price signals based on sector
    multiples and aggregates them into a final intrinsic value.
    """

    def __init__(self, multiples_data: MultiplesData, glass_box_enabled: bool = True):
        super().__init__(glass_box_enabled)
        self.multiples_data = multiples_data

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> MultiplesValuationResult:
        """
        Executes the multiples-based valuation sequence.

        Parameters
        ----------
        financials : CompanyFinancials
            Target company financials (TTM).
        params : DCFParameters
            Global parameters (used for reporting and audit context).

        Returns
        -------
        MultiplesValuationResult
            A result object containing the three signals and the final median/average.
        """
        m = self.multiples_data
        f = financials

        # 1. INDIVIDUAL PRICE SIGNAL COMPUTATION
        # Signal A: Equity-based (P/E)
        price_pe = calculate_price_from_pe_multiple(
            f.net_income_ttm or 0.0,
            m.median_pe,
            f.shares_outstanding
        )

        # Signal B: Enterprise-based (EV/EBITDA)
        # Accounts for Net Debt and minority interests.
        price_ebitda = calculate_price_from_ev_multiple(
            f.ebitda_ttm or 0.0,
            m.median_ev_ebitda,
            f.net_debt,
            f.shares_outstanding,
            f.minority_interests,
            f.pension_provisions
        )

        # Signal C: Enterprise-based (EV/Revenue)
        price_rev = calculate_price_from_ev_multiple(
            f.revenue_ttm or 0.0,
            m.median_ev_rev,
            f.net_debt,
            f.shares_outstanding
        )

        # 2. FINAL TRIANGULATION
        signals = {"P/E": price_pe, "EV/EBITDA": price_ebitda, "EV/Revenue": price_rev}
        final_iv = calculate_triangulated_price(signals)

        # 3. GLASS BOX RECORDING (Audit Trail)
        self._record_steps(f, m, signals, final_iv)

        result = MultiplesValuationResult(
            financials=f,
            params=params,
            intrinsic_value_per_share=final_iv,
            market_price=f.current_price,
            pe_based_price=price_pe,
            ebitda_based_price=price_ebitda,
            rev_based_price=price_rev,
            multiples_data=m,
            calculation_trace=self.calculation_trace
        )

        # Institutional Finalization
        self.generate_audit_report(result)
        self.verify_output_contract(result)
        return result

    def _record_steps(self, f: CompanyFinancials, m: MultiplesData,
                      signals: Dict[str, float], final_iv: float) -> None:
        """
        Records the mathematical steps with institutional traceability.
        """
        # --- P/E STEP ---
        sub_pe = KPITexts.SUB_PE_MULT.format(
            ni=format_smart_number(f.net_income_ttm),
            mult=m.median_pe,
            shares=f"{f.shares_outstanding:,.0f}"
        )

        self.add_step(
            step_key="RELATIVE_PE",
            result=signals["P/E"],
            label=RegistryTexts.PE_LABEL,
            theoretical_formula=StrategyFormulas.PE_MULTIPLE,
            numerical_substitution=sub_pe,
            interpretation=StrategyInterpretations.RELATIVE_PE.format(val=m.median_pe),
            source=StrategySources.YAHOO_TTM_SIMPLE
        )

        # --- EBITDA STEP ---
        sub_ebitda = KPITexts.SUB_EBITDA_MULT.format(
            ebitda=format_smart_number(f.ebitda_ttm),
            mult=m.median_ev_ebitda,
            shares=f"{f.shares_outstanding:,.0f}"
        )

        self.add_step(
            step_key="RELATIVE_EBITDA",
            result=signals["EV/EBITDA"],
            label=RegistryTexts.EBITDA_LABEL,
            theoretical_formula=StrategyFormulas.EV_EBITDA_MULTIPLE,
            numerical_substitution=sub_ebitda,
            interpretation=StrategyInterpretations.RELATIVE_EBITDA.format(val=m.median_ev_ebitda),
            source=StrategySources.YAHOO_TTM_SIMPLE
        )

        # --- TRIANGULATION SYNTHESIS ---
        valid_signals = [s for s in signals.values() if s > 0]
        sub_triangulation = StrategyInterpretations.TRIANGULATION_SUB.format(count=len(valid_signals))

        self.add_step(
            step_key="TRIANGULATION",
            result=final_iv,
            label=RegistryTexts.TRIANG_LABEL,
            theoretical_formula=StrategyFormulas.TRIANGULATION_AVERAGE,
            numerical_substitution=sub_triangulation,
            interpretation=StrategyInterpretations.TRIANGULATION_FINAL,
            source=StrategySources.CALCULATED,
            hypotheses=[
                TraceHypothesis(
                    name=RegistryTexts.PEERS_HYP_LABEL,
                    value=", ".join([p.ticker for p in m.peers]),
                    source=StrategySources.YAHOO_TTM_SIMPLE
                )
            ]
        )