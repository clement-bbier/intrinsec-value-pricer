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
    CompanyFinancials,
    Parameters,
    MultiplesValuationResult,
    MultiplesData,
    TraceHypothesis,
    VariableSource
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
    KPITexts,
    SharedTexts
)

logger = logging.getLogger(__name__)


class MarketMultiplesStrategy(ValuationStrategy):
    """
    Implements Relative Valuation via peer-group triangulation.

    This strategy calculates three independent price signals based on sector
    multiples (P/E, EV/EBITDA, EV/Revenue) and aggregates them into a final
    intrinsic value.

    Attributes
    ----------
    multiples_data : MultiplesData
        Container for sector multiples and peer cohort details.
    """

    def __init__(self, multiples_data: MultiplesData, glass_box_enabled: bool = True):
        """
        Initializes the strategy with market data.

        Parameters
        ----------
        multiples_data : MultiplesData
            The sector multiples collected from data providers or manual peer entry.
        glass_box_enabled : bool, default=True
            Whether to record detailed calculation steps for the audit report.
        """
        super().__init__(glass_box_enabled)
        self.multiples_data = multiples_data

    def execute(
        self,
        financials: CompanyFinancials,
        params: Parameters
    ) -> MultiplesValuationResult:
        """
        Executes the multiples-based valuation sequence.

        Parameters
        ----------
        financials : CompanyFinancials
            Target company financials (TTM).
        params : Parameters
            Global parameters (used for reporting and audit context).

        Returns
        -------
        MultiplesValuationResult
            A result object containing the three signals and the final triangulated value.
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
        signals = {
            "P/E": price_pe,
            "EV/EBITDA": price_ebitda,
            "EV/Revenue": price_rev
        }
        final_iv = calculate_triangulated_price(signals)

        # 3. GLASS BOX RECORDING (Audit Trail - Phase 2)
        if self.glass_box_enabled:
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
        Records the mathematical steps with full variable provenance.
        """
        # Common Variables
        shares_val = f.shares_outstanding
        debt_val = f.net_debt

        # --- STEP 1: P/E SIGNAL ---
        pe_vars = {
            "NI": self._build_variable_info(
                "NI", f.net_income_ttm or 0.0, None, f.net_income_ttm,
                "Net Income (TTM)"
            ),
            "P/E": self._build_variable_info(
                "P/E", m.median_pe, None, m.median_pe,
                "Median Sector P/E", default_source=VariableSource.YAHOO_FINANCE
            ),
            "Shares": self._build_variable_info(
                "Shares", shares_val, None, shares_val, SharedTexts.INP_SHARES
            )
        }

        self.add_step(
            step_key="RELATIVE_PE",
            result=signals["P/E"],
            label=RegistryTexts.PE_LABEL,
            theoretical_formula=StrategyFormulas.PRICE_FROM_PE,
            actual_calculation=KPITexts.SUB_PE_MULT.format(
                ni=format_smart_number(f.net_income_ttm),
                mult=m.median_pe,
                shares=f"{shares_val:,.0f}"
            ),
            interpretation=StrategyInterpretations.RELATIVE_PE.format(val=m.median_pe),
            source=StrategySources.YAHOO_TTM_SIMPLE,
            variables_map=pe_vars
        )

        # --- STEP 2: EBITDA SIGNAL ---
        ebitda_vars = {
            "EBITDA": self._build_variable_info(
                "EBITDA", f.ebitda_ttm or 0.0, None, f.ebitda_ttm, "EBITDA (TTM)"
            ),
            "EV/EBITDA": self._build_variable_info(
                "EV/EBITDA", m.median_ev_ebitda, None, m.median_ev_ebitda,
                "Median Sector EV/EBITDA"
            ),
            "NetDebt": self._build_variable_info(
                "NetDebt", debt_val, None, debt_val, "Net Debt position"
            )
        }

        self.add_step(
            step_key="RELATIVE_EBITDA",
            result=signals["EV/EBITDA"],
            label=RegistryTexts.EBITDA_LABEL,
            theoretical_formula=StrategyFormulas.PRICE_FROM_EV_EBITDA,
            actual_calculation=KPITexts.SUB_EBITDA_MULT.format(
                ebitda=format_smart_number(f.ebitda_ttm),
                mult=m.median_ev_ebitda,
                shares=f"{shares_val:,.0f}"
            ),
            interpretation=StrategyInterpretations.RELATIVE_EBITDA.format(val=m.median_ev_ebitda),
            source=StrategySources.YAHOO_TTM_SIMPLE,
            variables_map=ebitda_vars
        )

        # --- STEP 3: TRIANGULATION SYNTHESIS ---
        valid_signals = [s for s in signals.values() if s > 0]

        # Provenance of the peer cohort for audit transparency
        hypotheses = [
            TraceHypothesis(
                name=RegistryTexts.PEERS_HYP_LABEL,
                value=", ".join([p.ticker for p in m.peers]),
                source=StrategySources.YAHOO_TTM_SIMPLE
            )
        ]

        self.add_step(
            step_key="TRIANGULATION",
            result=final_iv,
            label=RegistryTexts.TRIANG_LABEL,
            theoretical_formula=StrategyFormulas.TRIANGULATION_AVERAGE,
            actual_calculation=StrategyInterpretations.TRIANGULATION_SUB.format(
                count=len(valid_signals)
            ),
            interpretation=StrategyInterpretations.TRIANGULATION_FINAL,
            source=StrategySources.CALCULATED,
            hypotheses=hypotheses,
            variables_map={} # The signals themselves are intermediate, usually untracked as variables
        )