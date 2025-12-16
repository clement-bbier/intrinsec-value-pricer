import logging
from typing import List

from core.models import (
    CompanyFinancials,
    DCFParameters,
    RIMValuationResult,
    TerminalValueMethod
)
from core.valuation.strategies.abstract import ValuationStrategy
from core.exceptions import CalculationError
from core.computation.financial_math import (
    calculate_cost_of_equity_capm,
    calculate_discount_factors,
    calculate_npv,
    calculate_rim_vectors,
    calculate_terminal_value_gordon,
    calculate_terminal_value_exit_multiple
)

logger = logging.getLogger(__name__)


class RIMBankingStrategy(ValuationStrategy):
    """
    STRATÉGIE 5 : RESIDUAL INCOME MODEL (RIM).
    Standard pour les banques.
    V = Book_Value + Somme(Residual_Income / (1+Ke)^t)
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> RIMValuationResult:
        logger.info("[Strategy] Executing RIMBankingStrategy | ticker=%s", financials.ticker)

        # 1. Validation des Inputs Critiques
        bv_per_share = financials.book_value_per_share
        eps_base = financials.eps_ttm

        if bv_per_share is None or bv_per_share <= 0:
            raise CalculationError("Donnée manquante : 'Book Value Per Share' est requis pour le modèle RIM.")

        if eps_base is None or eps_base == 0:
            if financials.net_income_ttm and financials.shares_outstanding:
                eps_base = financials.net_income_ttm / financials.shares_outstanding
            else:
                raise CalculationError("Donnée manquante : 'EPS' requis pour projeter le RI.")

        # Trace
        self.add_step(
            "Ancrage Comptable (Book Value)",
            "BV_{0}",
            f"{bv_per_share:.2f}",
            bv_per_share,
            financials.currency,
            "Valeur comptable des fonds propres."
        )

        # 2. Coût des Fonds Propres (Ke)
        if params.manual_cost_of_equity:
            ke = params.manual_cost_of_equity
        else:
            ke = calculate_cost_of_equity_capm(
                params.risk_free_rate,
                financials.beta,
                params.market_risk_premium
            )

        self.add_step(
            "Coût des Capitaux Propres (Ke)",
            "R_f + \\beta \\times MRP",
            f"{ke:.1%}",
            ke,
            "%",
            "Rentabilité exigée."
        )

        # 3. Payout Ratio (Hypothèse simplifiée pour Clean Surplus)
        div_base = financials.last_dividend or 0.0
        payout_ratio = 0.50  # Défaut
        if eps_base > 0:
            payout_ratio = max(0.0, min(0.90, div_base / eps_base))

        # 4. Projections (EPS -> RI -> BV)
        years = params.projection_years
        projected_eps = []
        current_eps = eps_base

        for i in range(1, years + 1):
            current_eps *= (1.0 + params.fcf_growth_rate)
            projected_eps.append(current_eps)

        residual_incomes, projected_bvs = calculate_rim_vectors(
            current_book_value=bv_per_share,
            cost_of_equity=ke,
            projected_earnings=projected_eps,
            payout_ratio=payout_ratio
        )

        # 5. Actualisation
        factors = calculate_discount_factors(ke, years)
        sum_discounted_ri = calculate_npv(residual_incomes, ke)

        self.add_step(
            f"Somme des RI Actualisés ({years} ans)",
            "\\sum RI_t / (1+Ke)^t",
            f"{sum_discounted_ri:,.2f}",
            sum_discounted_ri,
            financials.currency,
            "Surprofits économiques futurs."
        )

        # 6. Valeur Terminale
        final_ri = residual_incomes[-1]
        tv_ri = calculate_terminal_value_gordon(final_ri, ke, params.perpetual_growth_rate)
        discounted_tv_ri = tv_ri * factors[-1]

        self.add_step(
            "Valeur Terminale RI",
            "RI_n * (1+g) / (Ke-g)",
            f"{tv_ri:,.2f} (Actu: {discounted_tv_ri:,.2f})",
            discounted_tv_ri,
            financials.currency,
            "Croissance perpétuelle du profit économique."
        )

        # 7. Total
        intrinsic_value = bv_per_share + sum_discounted_ri + discounted_tv_ri
        total_equity = intrinsic_value * financials.shares_outstanding

        self.add_step(
            "Valeur Intrinsèque (RIM)",
            "BV_0 + \\sum RI + TV",
            f"{intrinsic_value:,.2f}",
            intrinsic_value,
            financials.currency,
            "Valeur Juste."
        )

        return RIMValuationResult(
            request=None,
            financials=financials,
            params=params,
            intrinsic_value_per_share=intrinsic_value,
            market_price=financials.current_price,
            cost_of_equity=ke,
            current_book_value=bv_per_share,
            projected_residual_incomes=residual_incomes,
            projected_book_values=projected_bvs,
            discount_factors=factors,
            sum_discounted_ri=sum_discounted_ri,
            terminal_value_ri=tv_ri,
            discounted_terminal_value=discounted_tv_ri,
            total_equity_value=total_equity,
            calculation_trace=self.trace
        )