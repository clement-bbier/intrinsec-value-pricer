"""
src/valuation/strategies/graham_value.py

GRAHAM INTRINSIC VALUE STRATEGY
===============================
Role: Value Investing Engine based on Benjamin Graham's Revised Formula (1974).
Academic Reference: The Intelligent Investor / Security Analysis.
Economic Domain: Defensive / Passive Investors / Mature Firms.
Logic: Calculates Intrinsic Value using normalized EPS and AAA Bond Yields.
Architecture: IValuationRunner implementation.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
"""

from __future__ import annotations

from typing import List

from src.models.parameters.base_parameter import Parameters
from src.models.company import Company
from src.models.glass_box import CalculationStep
from src.models.enums import ValuationMethodology

# Models Results (Nested Architecture)
from src.models.valuation import ValuationResult, ValuationRequest
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedRates, ResolvedCapital
from src.models.results.strategies import GrahamResults
from src.models.results.options import ExtensionBundleResults

# Libraries (DRY Logic)
from src.valuation.library.graham import GrahamLibrary
from src.valuation.strategies.interface import IValuationRunner

# Config & i18n
from src.config.constants import ModelDefaults, MacroDefaults


class GrahamNumberStrategy(IValuationRunner):
    """
    Graham Strategy (Revised 1974 Formula).

    A conservative valuation model that anchors on Normalized Earnings (EPS)
    and adjusts for the current Corporate AAA Bond Yield environment.

    Formula: IV = (EPS * (8.5 + 2*g) * 4.4) / Y
    """

    def __init__(self) -> None:
        self._glass_box: bool = True

    @property
    def glass_box_enabled(self) -> bool:
        return self._glass_box

    @glass_box_enabled.setter
    def glass_box_enabled(self, value: bool) -> None:
        self._glass_box = value

    def execute(self, financials: Company, params: Parameters) -> ValuationResult:
        """
        Executes the Graham valuation sequence.
        """
        steps: List[CalculationStep] = []

        # --- STEP 1: Intrinsic Value Calculation ---
        # Delegate pure math to the Library
        iv_per_share, step_graham = GrahamLibrary.compute_intrinsic_value(params)

        if self._glass_box:
            steps.append(step_graham)

        # --- RESULT RECONSTRUCTION ---
        # We need to extract the inputs used to populate the Audit/Results object.
        # Ideally, we trust the Resolver to have populated params.strategy and params.common.

        s = params.strategy
        r = params.common.rates
        g_param = params.growth

        # 1. Inputs Extraction (for Audit Traceability)
        # Note: We fallback to defaults to ensure safety if params are partial
        eps_used = s.eps_normalized or s.eps_normalized or financials.eps_ttm or 0.0

        # Growth: Graham uses a specific growth estimate or the generic one
        # The Library uses params.growth.fcf_growth_rate, so we mirror that here
        growth_used = s.growth_estimate if s.growth_estimate is not None else (g_param.fcf_growth_rate or ModelDefaults.DEFAULT_GROWTH_RATE)

        # Yield: Critical part of the 1974 formula
        aaa_yield = r.corporate_aaa_yield or MacroDefaults.DEFAULT_CORPORATE_AAA_YIELD

        # 2. Multiplier Calculation (M = 8.5 + 2*g)
        # Computed here for the "Graham Multiplier" audit KPI
        # Formula uses growth as an integer (e.g. 10 for 10%), so we multiply decimal by 100
        graham_multiplier = 8.5 + 2.0 * (growth_used * 100.0)

        # --- OUTPUT PACKAGING ---

        # A. Rates
        # Graham doesn't use WACC. The discount mechanism is the AAA Yield.
        res_rates = ResolvedRates(
            cost_of_equity=aaa_yield, # Proxy for opportunity cost
            cost_of_debt_after_tax=0.0,
            wacc=aaa_yield, # Proxy
            corporate_aaa_yield=aaa_yield
        )

        # B. Capital
        # Graham is an Equity-Per-Share model. We reconstruct Total Equity and Implied EV.
        shares = params.common.capital.shares_outstanding or ModelDefaults.DEFAULT_SHARES_OUTSTANDING
        equity_value_total = iv_per_share * shares

        # Reconstruct EV = Equity + Net Debt
        debt = params.common.capital.total_debt or 0.0
        cash = params.common.capital.cash_and_equivalents or 0.0
        net_debt = debt - cash

        res_capital = ResolvedCapital(
            market_cap=shares * (financials.current_price or 0.0),
            enterprise_value=equity_value_total + net_debt, # Implied EV
            net_debt_resolved=net_debt,
            equity_value_total=equity_value_total
        )

        # C. Common Results
        common_res = CommonResults(
            rates=res_rates,
            capital=res_capital,
            intrinsic_value_per_share=iv_per_share,
            upside_pct=((iv_per_share - (financials.current_price or 0.0)) / (financials.current_price or 1.0)) if financials.current_price else 0.0,
            bridge_trace=steps if self._glass_box else []
        )

        # D. Strategy Specific Results (Graham)
        strategy_res = GrahamResults(
            eps_used=eps_used,
            growth_estimate=growth_used,
            aaa_yield_used=aaa_yield,
            graham_multiplier=graham_multiplier,
            strategy_trace=[] # Main logic is in bridge_trace
        )

        return ValuationResult(
            request=ValuationRequest(
                mode=ValuationMethodology.GRAHAM,
                parameters=params
            ),
            results=Results(
                common=common_res,
                strategy=strategy_res, # Polymorphic slot
                extensions=ExtensionBundleResults()
            )
        )