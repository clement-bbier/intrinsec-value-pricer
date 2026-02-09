"""
src/valuation/strategies/standard_fcff.py

STANDARD FCFF STRATEGY RUNNER
=============================
Role: Core DCF Engine using Free Cash Flow to Firm.
Logic: Projects FCF, calculates Terminal Value, Discounts to PV, Bridges to Equity.
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
from src.models.results.strategies import FCFFStandardResults
from src.models.results.options import ExtensionBundleResults

# Libraries (DRY Logic)
from src.valuation.library.common import CommonLibrary
from src.valuation.library.dcf import DCFLibrary
from src.valuation.strategies.interface import IValuationRunner
from src.computation.financial_math import calculate_discount_factors

# Config
from src.config.constants import ModelDefaults


class StandardFCFFStrategy(IValuationRunner):
    """
    The workhorse of valuation: Discounted Free Cash Flow to Firm.
    Supports both 'Simple Fade-Down' (Auto) and 'Explicit Vector' (Expert) modes.
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
        Executes the DCF Standard sequence.
        """
        steps: List[CalculationStep] = []

        # --- STEP 1: WACC & Rates ---
        # Delegate to CommonLibrary (Single Responsibility)
        wacc, step_wacc = CommonLibrary.resolve_discount_rate(
            financials=financials,
            params=params,
            use_cost_of_equity_only=False
        )
        if self._glass_box: steps.append(step_wacc)

        # --- STEP 2: FCF Projection ---
        # StrategyResolver has already prioritized User Input > Normalized > TTM
        # We assume fcf_anchor is populated (fallback to 0.0 handled by Pydantic/Defaults)
        fcf_base = params.strategy.fcf_anchor or ModelDefaults.DEFAULT_FCF_TTM

        # Expert Override Logic (Vector vs Scalar)
        # We rely on the Model definition to carry the manual vector if present
        manual_vector = getattr(params.strategy, "manual_growth_vector", None)

        if manual_vector and len(manual_vector) > 0:
            # EXPERT MODE: Use explicit vector via Library
            flows, step_proj = DCFLibrary.project_flows_manual(fcf_base, manual_vector)
        else:
            # AUTO MODE: Use linear fade-down via Library
            flows, step_proj = DCFLibrary.project_flows_simple(fcf_base, params)

        if self._glass_box: steps.append(step_proj)

        # --- STEP 3: Terminal Value ---
        # Uses the last projected flow (Year N)
        final_flow = flows[-1] if flows else fcf_base
        tv, step_tv = DCFLibrary.compute_terminal_value(final_flow, wacc, params)
        if self._glass_box: steps.append(step_tv)

        # --- STEP 4: Discounting (Enterprise Value) ---
        ev, step_ev = DCFLibrary.compute_discounting(flows, tv, wacc)
        if self._glass_box: steps.append(step_ev)

        # --- STEP 5: Equity Bridge ---
        equity_value, step_bridge = CommonLibrary.compute_equity_bridge(ev, params)
        if self._glass_box: steps.append(step_bridge)

        # --- STEP 6: Per Share & Synthesis ---
        iv_per_share, step_iv = DCFLibrary.compute_value_per_share(equity_value, params)
        if self._glass_box: steps.append(step_iv)

        # --- RESULT CONSTRUCTION (The Nested Packaging) ---

        # A. Resolved Rates Object (Reconstruction for Result View)
        # We extract effective rates from the WACC calculation result or fallback to params
        r = params.common.rates

        # Defensive access to trace variables if available, else standard fallback
        trace_ke = step_wacc.get_variable("Ke")
        trace_kd = step_wacc.get_variable("Kd(1-t)")

        val_ke = trace_ke.value if (self._glass_box and trace_ke) else (r.cost_of_equity or 0.0)
        val_kd = trace_kd.value if (self._glass_box and trace_kd) else (ModelDefaults.DEFAULT_COST_OF_DEBT * (1 - (r.tax_rate or 0.25)))

        res_rates = ResolvedRates(
            cost_of_equity=val_ke,
            cost_of_debt_after_tax=val_kd,
            wacc=wacc
        )

        # B. Resolved Capital Object
        shares = params.common.capital.shares_outstanding or ModelDefaults.DEFAULT_SHARES_OUTSTANDING
        price = financials.current_price or 0.0
        market_cap = shares * price

        debt = params.common.capital.total_debt or 0.0
        cash = params.common.capital.cash_and_equivalents or 0.0

        res_capital = ResolvedCapital(
            market_cap=market_cap,
            enterprise_value=ev,
            net_debt_resolved=debt - cash,
            equity_value_total=equity_value
        )

        # C. Common Results
        upside = (iv_per_share - price) / price if price > 0 else 0.0

        common_res = CommonResults(
            rates=res_rates,
            capital=res_capital,
            intrinsic_value_per_share=iv_per_share,
            upside_pct=upside,
            bridge_trace=steps if self._glass_box else []
        )

        # D. Strategy Specific Results (FCFF Standard)
        # We need discount factors for the UI chart (re-calculated here as they are deterministic)
        discount_factors = calculate_discount_factors(wacc, len(flows))

        # PV of TV for weighting
        pv_tv = tv * discount_factors[-1] if discount_factors else 0.0
        tv_weight = pv_tv / ev if ev > 0 else 0.0

        strategy_res = FCFFStandardResults(
            projected_flows=flows,
            discount_factors=discount_factors,
            terminal_value=tv,
            discounted_terminal_value=pv_tv,
            tv_weight_pct=tv_weight,
            strategy_trace=[] # Main trace is in CommonResults to keep UI unified
        )

        # E. Final Assembly
        return ValuationResult(
            request=ValuationRequest(
                mode=ValuationMethodology.FCFF_STANDARD,
                parameters=params
            ),
            results=Results(
                common=common_res,
                strategy=strategy_res,
                extensions=ExtensionBundleResults() # Empty by default
            )
        )