import logging
from abc import ABC, abstractmethod
from typing import List

import numpy as np

from core.computation.discounting import (
    calculate_discount_factors,
    calculate_equity_value_bridge,
    calculate_terminal_value,
    calculate_wacc_full_context,
)
from core.computation.growth import project_flows
from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFResult

logger = logging.getLogger(__name__)


class ValuationStrategy(ABC):
    """
    Abstract base class for DCF strategies.

    Contract:
    - execute(financials, params) must return a fully populated DCFResult.
    - _compute_standard_dcf provides the deterministic DCF engine shared by strategies.

    Conventions:
    - Rates are decimals (0.08 = 8%).
    - params.projection_years is an integer horizon in years.
    """

    @abstractmethod
    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
        """Run the valuation strategy and return a complete DCFResult."""
        raise NotImplementedError

    def _compute_standard_dcf(
        self,
        fcf_start: float,
        financials: CompanyFinancials,
        params: DCFParameters,
    ) -> DCFResult:
        """
        Deterministic DCF engine.

        Steps:
        1) WACC computation (full context, supports manual Ke and target weights)
        2) Cash-flow projection (fade-down / high-growth then terminal growth)
        3) Discounting
        4) Terminal value
        5) EV -> Equity bridge
        6) Per-share intrinsic value
        """
        # ---- Input guards (do not change behavior, fail fast on impossible inputs) ----
        try:
            N = int(params.projection_years)
        except Exception as exc:
            raise CalculationError("Invalid projection_years (cannot cast to int).") from exc

        if N <= 0:
            raise CalculationError("Invalid projection_years (<= 0).")

        if fcf_start is None:
            raise CalculationError("Invalid fcf_start (None).")

        try:
            fcf_start_float = float(fcf_start)
        except Exception as exc:
            raise CalculationError("Invalid fcf_start (not a number).") from exc

        # ---- Step 1: WACC ----
        try:
            wacc_context = calculate_wacc_full_context(financials, params)
            wacc = float(wacc_context.wacc)

            # Re-assert key invariant (should already be validated upstream)
            if wacc <= float(params.perpetual_growth_rate):
                raise CalculationError(
                    "Math convergence failure: WACC <= terminal growth "
                    f"(wacc={wacc:.6f}, g_terminal={float(params.perpetual_growth_rate):.6f})."
                )

        except CalculationError:
            raise
        except Exception as exc:
            logger.error("WACC computation failed | ticker=%s | err=%s", financials.ticker, exc)
            raise CalculationError("Critical failure during WACC computation.") from exc

        # ---- Step 2: Projection ----
        projected_fcfs: List[float] = project_flows(
            base_flow=fcf_start_float,
            years=N,
            g_start=float(params.fcf_growth_rate),
            g_term=float(params.perpetual_growth_rate),
            high_growth_years=int(getattr(params, "high_growth_years", 0) or 0),
        )

        if not projected_fcfs or len(projected_fcfs) != N:
            raise CalculationError("Cash-flow projection failure: inconsistent number of projected years.")

        # ---- Step 3: Discounting ----
        factors = calculate_discount_factors(wacc, N)
        if not factors or len(factors) != N:
            raise CalculationError("Discount factor computation failure: inconsistent number of factors.")

        discounted_fcfs = [float(f) * float(d) for f, d in zip(projected_fcfs, factors)]
        sum_discounted = float(np.sum(discounted_fcfs))

        # ---- Step 4: Terminal value ----
        tv = float(calculate_terminal_value(projected_fcfs[-1], wacc, float(params.perpetual_growth_rate)))
        discounted_tv = float(tv * factors[-1])

        # ---- Step 5: EV -> Equity ----
        ev = float(sum_discounted + discounted_tv)

        eq_val = float(
            calculate_equity_value_bridge(
                enterprise_value=ev,
                total_debt=float(financials.total_debt),
                cash=float(financials.cash_and_equivalents),
            )
        )

        # ---- Step 6: Per-share ----
        if float(financials.shares_outstanding) <= 0:
            raise CalculationError("Invalid shares_outstanding (<= 0).")

        iv_share = float(eq_val / float(financials.shares_outstanding))

        # ---- Step 7: Result ----
        return DCFResult(
            wacc=wacc,
            cost_of_equity=float(wacc_context.cost_of_equity),
            after_tax_cost_of_debt=float(wacc_context.cost_of_debt_after_tax),
            projected_fcfs=projected_fcfs,
            discount_factors=factors,
            sum_discounted_fcf=sum_discounted,
            terminal_value=tv,
            discounted_terminal_value=discounted_tv,
            enterprise_value=ev,
            equity_value=eq_val,
            intrinsic_value_per_share=iv_share,
        )
