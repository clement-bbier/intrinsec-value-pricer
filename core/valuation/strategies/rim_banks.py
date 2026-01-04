"""
core/valuation/strategies/rim_banks.py
MÉTHODE : RESIDUAL INCOME MODEL (RIM) — VERSION V5.1
Architecture : Registry-Driven (Alignement Numérique Intégral).
"""

import logging
from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    RIMValuationResult,
    TraceHypothesis,
    TerminalValueMethod
)
from core.valuation.strategies.abstract import ValuationStrategy
from core.computation.financial_math import (
    calculate_cost_of_equity_capm,
    calculate_terminal_value_gordon,
    calculate_discount_factors,
    calculate_npv,
    calculate_rim_vectors
)

logger = logging.getLogger(__name__)

class RIMBankingStrategy(ValuationStrategy):
    """Residual Income Model (Penman/Ohlson) pour institutions financières."""

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> RIMValuationResult:
        logger.info("[Strategy] Residual Income Model | ticker=%s", financials.ticker)

        # 1. ANCRAGE COMPTABLE (ID: RIM_BV_INITIAL)
        bv_per_share = params.manual_book_value if params.manual_book_value is not None else financials.book_value_per_share

        if bv_per_share is None or bv_per_share <= 0:
            raise CalculationError("Book Value par action requise et > 0.")

        self.add_step(
            step_key="RIM_BV_INITIAL",
            result=bv_per_share,
            numerical_substitution=f"BV_0 = {bv_per_share:,.2f}"
        )

        # 2. COÛT DES FONDS PROPRES (ID: RIM_KE_CALC)
        # Alignement : Rf + beta * MRP
        beta_used = params.manual_beta if params.manual_beta is not None else financials.beta
        if params.manual_cost_of_equity is not None:
            ke = params.manual_cost_of_equity
            sub_ke = f"k_e = {ke:.4f} (Surcharge Analyste)"
        else:
            ke = calculate_cost_of_equity_capm(params.risk_free_rate, beta_used, params.market_risk_premium)
            sub_ke = f"{params.risk_free_rate:.4f} + ({beta_used:.2f} \\times {params.market_risk_premium:.4f})"

        self.add_step(step_key="RIM_KE_CALC", result=ke, numerical_substitution=sub_ke)

        # 3. DISTRIBUTION (ID: RIM_PAYOUT)
        # Alignement : Div / EPS
        eps_base = financials.eps_ttm or (financials.net_income_ttm / financials.shares_outstanding if financials.shares_outstanding > 0 else 0)
        if eps_base <= 0: raise CalculationError("EPS requis pour projeter les profits résiduels.")

        dividend = financials.last_dividend or 0.0
        payout_ratio = max(0.0, min(0.90, dividend / eps_base))

        self.add_step(
            step_key="RIM_PAYOUT",
            result=payout_ratio,
            numerical_substitution=f"{dividend:,.2f} / {eps_base:,.2f}"
        )

        # 4. PROJECTION BÉNÉFICES (ID: RIM_EPS_PROJ)
        # Alignement : EPS_t = EPS_{t-1} * (1+g)
        years = params.projection_years
        projected_eps = [eps_base * ((1.0 + params.fcf_growth_rate) ** (t + 1)) for t in range(years)]

        self.add_step(
            step_key="RIM_EPS_PROJ",
            result=projected_eps[-1],
            numerical_substitution=f"{eps_base:,.2f} \\times (1 + {params.fcf_growth_rate:.3f})^{years}"
        )

        # 5. PROFITS RÉSIDUELS (ID: RIM_RI_CALC)
        # Alignement : NI_t - (ke * BV_{t-1})
        residual_incomes, projected_bvs = calculate_rim_vectors(bv_per_share, ke, projected_eps, payout_ratio)
        # On montre le calcul du premier RI pour la preuve
        sub_ri = f"{projected_eps[0]:,.2f} - ({ke:.4f} \\times {bv_per_share:,.2f})"

        self.add_step(
            step_key="RIM_RI_CALC",
            result=sum(residual_incomes),
            numerical_substitution=sub_ri
        )

        # 6. ACTUALISATION (ID: NPV_CALC)
        discount_factors = calculate_discount_factors(ke, years)
        discounted_ri_sum = calculate_npv(residual_incomes, ke)

        self.add_step(
            step_key="NPV_CALC",
            result=discounted_ri_sum,
            numerical_substitution=f"NPV(Residual Incomes, r={ke:.4f})"
        )

        # 7. VALEUR TERMINALE (ID: TV_GORDON / TV_MULTIPLE)
        terminal_ri = residual_incomes[-1]
        if params.terminal_method == TerminalValueMethod.EXIT_MULTIPLE:
            tv_ri = terminal_ri * params.exit_multiple_value
            key_tv, sub_tv = "TV_MULTIPLE", f"{terminal_ri:,.2f} \\times {params.exit_multiple_value:.1f}"
        else:
            tv_ri = calculate_terminal_value_gordon(terminal_ri, ke, params.perpetual_growth_rate)
            key_tv = "TV_GORDON"
            sub_tv = f"({terminal_ri:,.2f} \\times {1+params.perpetual_growth_rate:.3f}) / ({ke:.4f} - {params.perpetual_growth_rate:.3f})"

        discounted_tv = tv_ri * discount_factors[-1]
        self.add_step(step_key=key_tv, result=discounted_tv, numerical_substitution=f"{sub_tv} \\times {discount_factors[-1]:.4f}")

        # 8. VALEUR FINALE (ID: RIM_FINAL_VALUE)
        # Alignement : BV_0 + Sum PV(RI)
        intrinsic_value = bv_per_share + discounted_ri_sum + discounted_tv
        shares_to_use = params.manual_shares_outstanding or financials.shares_outstanding

        self.add_step(
            step_key="RIM_FINAL_VALUE",
            result=intrinsic_value,
            numerical_substitution=f"{bv_per_share:,.2f} + {discounted_ri_sum:,.2f} + {discounted_tv:,.2f}"
        )

        return RIMValuationResult(
            request=None, financials=financials, params=params,
            intrinsic_value_per_share=intrinsic_value, market_price=financials.current_price,
            cost_of_equity=ke, current_book_value=bv_per_share,
            projected_residual_incomes=residual_incomes, projected_book_values=projected_bvs,
            discount_factors=discount_factors, sum_discounted_ri=discounted_ri_sum,
            terminal_value_ri=tv_ri, discounted_terminal_value=discounted_tv,
            total_equity_value=intrinsic_value * shares_to_use, calculation_trace=self.calculation_trace
        )