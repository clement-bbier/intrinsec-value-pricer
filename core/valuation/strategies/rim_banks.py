"""
core/valuation/strategies/rim_banks.py

Méthode : Residual Income Model (RIM)
Version : V1 Normative

Références académiques :
- Penman, S. – Financial Statement Analysis and Security Valuation
- CFA Institute – Equity Valuation (Financial Institutions)

Principe :
- La valeur = Book Value actuelle + valeur actualisée des profits résiduels
- Adaptée aux banques / assurances (bilan central)
"""

import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, RIMValuationResult
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
    """
    Residual Income Model (Penman).

    Référence académique :
    - Stephen Penman

    Domaine de validité :
    - Banques
    - Assurances
    - Institutions financières réglementées

    Invariants financiers :
    - Book Value > 0
    - Cost of Equity > 0
    - Clean Surplus respecté
    """

    academic_reference = "Penman"
    economic_domain = "Banks / Insurance / Financial Institutions"
    financial_invariants = [
        "book_value > 0",
        "cost_of_equity > 0",
        "clean_surplus_relationship"
    ]

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> RIMValuationResult:
        """
        Exécute une valorisation par Residual Income Model.

        Étapes :
        - Ancrage sur la Book Value
        - Projection des Earnings
        - Calcul des profits résiduels
        - Actualisation et valeur terminale
        """

        logger.info(
            "[Strategy] Residual Income Model | ticker=%s",
            financials.ticker
        )

        # ====================================================
        # 1. DONNÉES DE BASE (ANCRAGE COMPTABLE)
        # ====================================================

        bv_per_share = financials.book_value_per_share
        eps_base = financials.eps_ttm

        if bv_per_share is None or bv_per_share <= 0:
            raise CalculationError(
                "Book Value par action requise et strictement positive."
            )

        if eps_base is None:
            if financials.net_income_ttm and financials.shares_outstanding > 0:
                eps_base = (
                    financials.net_income_ttm
                    / financials.shares_outstanding
                )
            else:
                raise CalculationError(
                    "EPS requis pour le Residual Income Model."
                )

        self.add_step(
            "Book Value Initiale",
            "BV_0",
            f"{bv_per_share:,.2f}",
            bv_per_share,
            financials.currency,
            "Ancrage comptable de départ."
        )

        # ====================================================
        # 2. COÛT DES FONDS PROPRES (Ke)
        # ====================================================

        if params.manual_cost_of_equity is not None:
            ke = params.manual_cost_of_equity
            ke_source = "Manual Override"
        else:
            ke = calculate_cost_of_equity_capm(
                params.risk_free_rate,
                financials.beta,
                params.market_risk_premium
            )
            ke_source = "CAPM"

        if ke <= 0:
            raise CalculationError("Cost of Equity invalide.")

        self.add_step(
            "Coût des Fonds Propres (Ke)",
            "Rf + β × MRP",
            f"{ke:.2%}",
            ke,
            "%",
            f"Méthode : {ke_source}"
        )

        # ====================================================
        # 3. POLITIQUE DE DISTRIBUTION (PAYOUT)
        # ====================================================

        dividend = financials.last_dividend or 0.0
        payout_ratio = 0.50  # défaut conservateur

        if eps_base > 0:
            payout_ratio = max(
                0.0,
                min(0.90, dividend / eps_base)
            )

        # ====================================================
        # 4. PROJECTION DES EARNINGS
        # ====================================================

        years = params.projection_years
        if years <= 0:
            raise CalculationError("Horizon de projection invalide.")

        projected_eps = []
        current_eps = eps_base

        for _ in range(years):
            current_eps *= (1.0 + params.fcf_growth_rate)
            projected_eps.append(current_eps)

        # ====================================================
        # 5. PROFITS RÉSIDUELS (CLEAN SURPLUS)
        # ====================================================

        residual_incomes, projected_bvs = calculate_rim_vectors(
            current_book_value=bv_per_share,
            cost_of_equity=ke,
            projected_earnings=projected_eps,
            payout_ratio=payout_ratio
        )

        # ====================================================
        # 6. ACTUALISATION
        # ====================================================

        discount_factors = calculate_discount_factors(ke, years)
        discounted_ri_sum = calculate_npv(residual_incomes, ke)

        self.add_step(
            f"Somme des Profits Résiduels ({years} ans)",
            "∑ RI_t / (1+Ke)^t",
            f"{discounted_ri_sum:,.2f}",
            discounted_ri_sum,
            financials.currency,
            "Valeur actuelle des surprofits."
        )

        # ====================================================
        # 7. VALEUR TERMINALE
        # ====================================================

        terminal_ri = residual_incomes[-1]
        terminal_value_ri = calculate_terminal_value_gordon(
            terminal_ri,
            ke,
            params.perpetual_growth_rate
        )
        discounted_terminal_ri = (
            terminal_value_ri * discount_factors[-1]
        )

        self.add_step(
            "Valeur Terminale (RI)",
            "RI_n × (1+g)/(Ke−g)",
            f"{terminal_value_ri:,.2f}",
            discounted_terminal_ri,
            financials.currency,
            "Valeur terminale des profits résiduels."
        )

        # ====================================================
        # 8. VALEUR INTRINSÈQUE
        # ====================================================

        intrinsic_value = (
            bv_per_share
            + discounted_ri_sum
            + discounted_terminal_ri
        )

        self.add_step(
            "Valeur Intrinsèque (RIM)",
            "BV_0 + RI + TV",
            f"{intrinsic_value:,.2f}",
            intrinsic_value,
            financials.currency,
            "Valeur fondamentale par action."
        )

        total_equity_value = (
            intrinsic_value * financials.shares_outstanding
        )

        # ====================================================
        # 9. RÉSULTAT FINAL
        # ====================================================

        return RIMValuationResult(
            request=None,  # injecté par le moteur
            financials=financials,
            params=params,
            intrinsic_value_per_share=intrinsic_value,
            market_price=financials.current_price,
            cost_of_equity=ke,
            current_book_value=bv_per_share,
            projected_residual_incomes=residual_incomes,
            projected_book_values=projected_bvs,
            discount_factors=discount_factors,
            sum_discounted_ri=discounted_ri_sum,
            terminal_value_ri=terminal_value_ri,
            discounted_terminal_value=discounted_terminal_ri,
            total_equity_value=total_equity_value,
            calculation_trace=self.trace
        )
