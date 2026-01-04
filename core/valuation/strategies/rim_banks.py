"""
core/valuation/strategies/rim_banks.py
MÉTHODE : RESIDUAL INCOME MODEL (RIM) — VERSION V5.2
Rôle : Correction de l'erreur arithmétique de l'étape 5 et rigueur des flux de surprofits.
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

        self.add_step(step_key="RIM_BV_INITIAL", result=bv_per_share, numerical_substitution=f"BV_0 = {bv_per_share:,.2f}")

        # 2. COÛT DES FONDS PROPRES (ID: RIM_KE_CALC)
        beta_used = params.manual_beta if params.manual_beta is not None else financials.beta
        ke = calculate_cost_of_equity_capm(params.risk_free_rate, beta_used, params.market_risk_premium)
        sub_ke = f"{params.risk_free_rate:.4f} + ({beta_used:.2f} × {params.market_risk_premium:.4f})"

        self.add_step(step_key="RIM_KE_CALC", result=ke, numerical_substitution=sub_ke)

        # 3. DISTRIBUTION (ID: RIM_PAYOUT)
        eps_base = financials.eps_ttm or (financials.net_income_ttm / financials.shares_outstanding if financials.shares_outstanding > 0 else 0)
        if eps_base <= 0: raise CalculationError("EPS positif requis.")

        dividend = financials.last_dividend or 0.0
        payout_ratio = max(0.0, min(0.90, dividend / eps_base))

        self.add_step(step_key="RIM_PAYOUT", result=payout_ratio, numerical_substitution=f"{dividend:,.2f} / {eps_base:,.2f}")

        # 4. PROJECTION BÉNÉFICES (Flux de l'année n pour la TV)
        years = params.projection_years
        projected_eps = [eps_base * ((1.0 + params.fcf_growth_rate) ** (t + 1)) for t in range(years)]

        self.add_step(
            step_key="RIM_EPS_PROJ",
            result=projected_eps[-1], # Audit Fix: on montre le bénéfice terminal
            numerical_substitution=f"{eps_base:,.2f} × (1 + {params.fcf_growth_rate:.3f})^{years}"
        )

        # 5. PROFITS RÉSIDUELS (Preuve par l'année 1)
        residual_incomes, projected_bvs = calculate_rim_vectors(bv_per_share, ke, projected_eps, payout_ratio)
        ri_1 = projected_eps[0] - (ke * bv_per_share)

        self.add_step(
            step_key="RIM_RI_CALC",
            result=ri_1, # Audit Fix: Le résultat doit correspondre à la soustraction affichée
            numerical_substitution=f"{projected_eps[0]:,.2f} - ({ke:.4f} × {bv_per_share:,.2f})"
        )

        # 6. ACTUALISATION DES SURPROFITS (ID: NPV_CALC)
        discount_factors = calculate_discount_factors(ke, years)
        discounted_ri_sum = calculate_npv(residual_incomes, ke)

        self.add_step(
            step_key="NPV_CALC",
            result=discounted_ri_sum,
            numerical_substitution=f"Sum PV(RI_1...RI_{years}) @ ke={ke:.2%}"
        )

        # 7. VALEUR TERMINALE (PV de la TV)
        terminal_ri = residual_incomes[-1]
        if params.terminal_method == TerminalValueMethod.EXIT_MULTIPLE:
            tv_ri = terminal_ri * params.exit_multiple_value
            sub_tv = f"{terminal_ri:,.2f} × {params.exit_multiple_value:.1f}"
        else:
            tv_ri = calculate_terminal_value_gordon(terminal_ri, ke, params.perpetual_growth_rate)
            sub_tv = f"({terminal_ri:,.2f} × {1+params.perpetual_growth_rate:.3f}) / ({ke:.4f} - {params.perpetual_growth_rate:.3f})"

        discounted_tv = tv_ri * discount_factors[-1]
        self.add_step(step_key="TV_GORDON", result=discounted_tv, numerical_substitution=f"{sub_tv} × {discount_factors[-1]:.4f}")

        # 8. VALEUR FINALE (Ancrage + Surprofits + TV)
        intrinsic_value = bv_per_share + discounted_ri_sum + discounted_tv
        shares_to_use = params.manual_shares_outstanding or financials.shares_outstanding

        self.add_step(
            step_key="RIM_FINAL_VALUE",
            result=intrinsic_value,
            numerical_substitution=f"{bv_per_share:,.2f} (BV_0) + {discounted_ri_sum:,.2f} (PV_RI) + {discounted_tv:,.2f} (PV_TV)"
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