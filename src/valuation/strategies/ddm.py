"""
src/valuation/strategies/ddm.py

DIVIDEND DISCOUNT MODEL (DDM) STRATEGY RUNNER
=============================================
Role: Direct Equity Valuation based on future dividend streams.
Academic Reference: Gordon & Shapiro.
Economic Domain: Mature, high-payout firms (Utilities, REITs, Banks).
Logic: Discounts projected dividends at Cost of Equity (Ke).
Architecture: IValuationRunner implementation.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
"""

from __future__ import annotations

from typing import List

from src.models.parameters.base_parameter import Parameters
from src.models.company import Company
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.enums import ValuationMethodology, VariableSource

# Models Results
from src.models.valuation import ValuationResult, ValuationRequest
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedRates, ResolvedCapital
from src.models.results.strategies import DDMResults
from src.models.results.options import ExtensionBundleResults

# Libraries
from src.valuation.library.common import CommonLibrary
from src.valuation.library.dcf import DCFLibrary
from src.valuation.strategies.interface import IValuationRunner
from src.computation.financial_math import calculate_discount_factors

# Config & i18n
from src.config.constants import ModelDefaults
from src.i18n import RegistryTexts, StrategySources, StrategyFormulas, StrategyInterpretations, SharedTexts


class DividendDiscountStrategy(IValuationRunner):
    """
    DDM Strategy (Gordon & Shapiro).
    Estimates intrinsic value as the PV of future dividends using Ke.
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
        Executes DDM valuation sequence.
        """
        steps: List[CalculationStep] = []

        # --- STEP 1: Rate Resolution (Ke ONLY) ---
        # DDM uses Cost of Equity as the discount rate.
        ke, step_ke = CommonLibrary.resolve_discount_rate(
            financials=financials,
            params=params,
            use_cost_of_equity_only=True
        )
        if self._glass_box: steps.append(step_ke)

        # --- STEP 2: Dividend Anchor Selection ---
        # We resolve the starting Dividend per Share (D0).
        # Priority: User Input (Strategy) > TTM (Snapshot)
        user_div = params.strategy.dividend_per_share
        d0_per_share = user_div if user_div is not None else (financials.dividend_share or 0.0)

        # We project the TOTAL Dividend Mass to be consistent with the DCF engine
        shares = params.common.capital.shares_outstanding or ModelDefaults.DEFAULT_SHARES_OUTSTANDING
        total_dividend_mass = d0_per_share * shares

        if self._glass_box:
            steps.append(CalculationStep(
                step_key="DDM_ANCHOR",
                label=RegistryTexts.DDM_BASE_L,
                theoretical_formula=StrategyFormulas.DIVIDEND_BASE,
                actual_calculation=f"{d0_per_share:.2f} (D0) × {shares:,.0f} (Shares)",
                result=total_dividend_mass,
                interpretation=StrategyInterpretations.DDM_LOGIC,
                source=StrategySources.MANUAL_OVERRIDE if user_div else StrategySources.YAHOO_TTM_SIMPLE,
                variables_map={
                    "D_0": VariableInfo(
                        symbol="D_0", value=d0_per_share,
                        source=VariableSource.MANUAL_OVERRIDE if user_div else VariableSource.YAHOO_FINANCE,
                        description="Dividend Per Share (Base)"
                    ),
                    "Shares": VariableInfo(
                        symbol="Shares", value=shares,
                        source=VariableSource.SYSTEM, description=SharedTexts.INP_SHARES
                    )
                }
            ))

        # --- STEP 3: Projection ---
        # Checks for manual growth vector
        manual_vector = getattr(params.strategy, "manual_growth_vector", None)

        if manual_vector and len(manual_vector) > 0:
            flows, step_proj = DCFLibrary.project_flows_manual(total_dividend_mass, manual_vector)
        else:
            # Uses standard growth parameters (Linear Fade-Down) applied to Dividends
            flows, step_proj = DCFLibrary.project_flows_simple(total_dividend_mass, params)

        if self._glass_box: steps.append(step_proj)

        # --- STEP 4: Terminal Value ---
        final_flow = flows[-1] if flows else total_dividend_mass
        # TV calculated with Ke (not WACC)
        tv, step_tv = DCFLibrary.compute_terminal_value(final_flow, ke, params)
        if self._glass_box: steps.append(step_tv)

        # --- STEP 5: Discounting ---
        # Discount at Ke. Result is Total Equity Value.
        equity_value_total, step_ev = DCFLibrary.compute_discounting(flows, tv, ke)
        if self._glass_box: steps.append(step_ev)

        # --- STEP 6: Per Share Value ---
        # Simply divide Total Equity by Shares. No Bridge needed for DDM.
        iv_per_share, step_iv = DCFLibrary.compute_value_per_share(equity_value_total, params)
        if self._glass_box: steps.append(step_iv)

        # --- RESULT CONSTRUCTION ---

        # A. Rates
        res_rates = ResolvedRates(
            cost_of_equity=ke,
            cost_of_debt_after_tax=0.0, # Not applicable
            wacc=ke # Proxy for the discount rate used
        )

        # B. Capital (Implied)
        # EV is hypothetical here, we reconstruct it for UI consistency: EV = Equity + Net Debt
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

        # D. Strategy Specific
        discount_factors = calculate_discount_factors(ke, len(flows))
        pv_tv = tv * discount_factors[-1] if discount_factors else 0.0

        # Audit Ratio: Payout Ratio (D0 / EPS)
        eps = financials.eps_ttm or 1.0
        payout = (d0_per_share / eps) if eps > 0 else 0.0

        strategy_res = DDMResults(
            projected_flows=flows,
            discount_factors=discount_factors,
            terminal_value=tv,
            discounted_terminal_value=pv_tv,
            tv_weight_pct=(pv_tv / equity_value_total) if equity_value_total > 0 else 0.0,
            strategy_trace=[],
            # DDM Specifics
            projected_dividends=flows, # Same as flows here
            payout_ratio_observed=payout
        )

        return ValuationResult(
            request=ValuationRequest(
                mode=ValuationMethodology.DDM,
                parameters=params
            ),
            results=Results(
                common=common_res,
                strategy=strategy_res,
                extensions=ExtensionBundleResults()
            )
        )