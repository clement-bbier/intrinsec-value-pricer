"""
core/valuation/strategies/rim_banks.py

Méthode : Residual Income Model (RIM)
Version : V1.2 — Pydantic Fix (Arguments nommés stricts)
"""

import logging

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    RIMValuationResult,
    TraceHypothesis
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
    """
    Residual Income Model (Penman).
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

        logger.info(
            "[Strategy] Residual Income Model | ticker=%s",
            financials.ticker
        )

        # ====================================================
        # 1. ANCRAGE COMPTABLE — BOOK VALUE
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
            label="Ancrage comptable initial (Book Value)",
            theoretical_formula="BV₀",
            hypotheses=[
                TraceHypothesis(
                    name="Book value per share",
                    value=bv_per_share,
                    unit=financials.currency,
                    source="Balance sheet"
                )
            ],
            numerical_substitution=f"BV₀ = {bv_per_share:,.2f}",
            result=bv_per_share,
            unit=financials.currency,
            interpretation=(
                "Valeur comptable par action servant d’ancrage "
                "à la valorisation par profits résiduels."
            )
        )

        # ====================================================
        # 2. COÛT DES FONDS PROPRES (Ke)
        # ====================================================

        if params.manual_cost_of_equity is not None:
            ke = params.manual_cost_of_equity
            ke_source = "Manual override"
        else:
            ke = calculate_cost_of_equity_capm(
                params.risk_free_rate,
                financials.beta,
                params.market_risk_premium
            )
            ke_source = "CAPM"

        if ke <= 0:
            raise CalculationError("Cost of Equity invalide.")

        # [CORRECTIF PYDANTIC] Usage d'arguments nommés
        self.add_step(
            label="Coût des fonds propres",
            theoretical_formula="Rf + β × MRP",
            hypotheses=[
                TraceHypothesis(name="Risk-free rate", value=params.risk_free_rate, unit="%"),
                TraceHypothesis(name="Beta", value=financials.beta, unit=""),
                TraceHypothesis(name="Market risk premium", value=params.market_risk_premium, unit="%")
            ],
            numerical_substitution=f"Ke = {ke:.2%} ({ke_source})",
            result=ke,
            unit="%",
            interpretation=(
                "Taux d’actualisation des profits résiduels "
                "supporté par les actionnaires."
            )
        )

        # ====================================================
        # 3. POLITIQUE DE DISTRIBUTION (PAYOUT)
        # ====================================================

        dividend = financials.last_dividend or 0.0
        payout_ratio = 0.50

        if eps_base > 0:
            payout_ratio = max(0.0, min(0.90, dividend / eps_base))

        # [CORRECTIF PYDANTIC] Usage d'arguments nommés
        self.add_step(
            label="Politique de distribution",
            theoretical_formula="Dividend / EPS",
            hypotheses=[
                TraceHypothesis(name="Dividend", value=dividend, unit=financials.currency),
                TraceHypothesis(name="EPS base", value=eps_base, unit=financials.currency)
            ],
            numerical_substitution=(
                f"Payout = {dividend:,.2f} / {eps_base:,.2f}"
            ),
            result=payout_ratio,
            unit="%",
            interpretation=(
                "Part des résultats distribuée aux actionnaires, "
                "utilisée pour la dynamique du clean surplus."
            )
        )

        # ====================================================
        # 4. PROJECTION DES RÉSULTATS
        # ====================================================

        years = params.projection_years
        if years <= 0:
            raise CalculationError("Horizon de projection invalide.")

        projected_eps = []
        current_eps = eps_base

        for _ in range(years):
            current_eps *= (1.0 + params.fcf_growth_rate)
            projected_eps.append(current_eps)

        # [CORRECTIF PYDANTIC] Usage d'arguments nommés
        self.add_step(
            label="Projection des résultats par action",
            theoretical_formula="EPSₜ = EPSₜ₋₁ × (1 + g)",
            hypotheses=[
                TraceHypothesis(name="EPS base", value=eps_base, unit=financials.currency),
                TraceHypothesis(name="Growth rate", value=params.fcf_growth_rate, unit="%")
            ],
            numerical_substitution=f"Projection sur {years} ans",
            result=sum(projected_eps),
            unit=financials.currency,
            interpretation=(
                "Projection des bénéfices nécessaires au calcul "
                "des profits résiduels."
            )
        )

        # ====================================================
        # 5. PROFITS RÉSIDUELS (CLEAN SURPLUS)
        # ====================================================

        residual_incomes, projected_bvs = calculate_rim_vectors(
            current_book_value=bv_per_share,
            cost_of_equity=ke,
            projected_earnings=projected_eps,
            payout_ratio=payout_ratio
        )

        # [CORRECTIF PYDANTIC] Usage d'arguments nommés
        self.add_step(
            label="Calcul des profits résiduels",
            theoretical_formula="RIₜ = EPSₜ − Ke × BVₜ₋₁",
            hypotheses=[
                TraceHypothesis(name="Cost of equity", value=ke, unit="%"),
                TraceHypothesis(name="Payout ratio", value=payout_ratio, unit="%")
            ],
            numerical_substitution="Application du clean surplus",
            result=sum(residual_incomes),
            unit=financials.currency,
            interpretation=(
                "Surprofits générés au-delà de la rémunération "
                "exigée par les actionnaires."
            )
        )

        # ====================================================
        # 6. ACTUALISATION DES PROFITS RÉSIDUELS
        # ====================================================

        discount_factors = calculate_discount_factors(ke, years)
        discounted_ri_sum = calculate_npv(residual_incomes, ke)

        # [CORRECTIF PYDANTIC] Usage d'arguments nommés
        self.add_step(
            label="Valeur actuelle des profits résiduels",
            theoretical_formula="∑ RIₜ / (1+Ke)ᵗ",
            hypotheses=[
                TraceHypothesis(name="Sum Residual Incomes", value=sum(residual_incomes), unit=financials.currency),
                TraceHypothesis(name="Cost of equity", value=ke, unit="%")
            ],
            numerical_substitution=f"NPV(RI, {ke:.2%})",
            result=discounted_ri_sum,
            unit=financials.currency,
            interpretation=(
                "Valeur actuelle des surprofits explicites."
            )
        )

        # ====================================================
        # 7. VALEUR TERMINALE DES PROFITS RÉSIDUELS
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

        # [CORRECTIF PYDANTIC] Usage d'arguments nommés
        self.add_step(
            label="Valeur terminale des profits résiduels",
            theoretical_formula="RIₙ × (1+g)/(Ke−g)",
            hypotheses=[
                TraceHypothesis(name="Terminal RI", value=terminal_ri, unit=financials.currency),
                TraceHypothesis(name="Ke", value=ke, unit="%"),
                TraceHypothesis(name="Perpetual growth", value=params.perpetual_growth_rate, unit="%")
            ],
            numerical_substitution=(
                f"TV × DFₙ = {terminal_value_ri:,.2f} × {discount_factors[-1]:.4f}"
            ),
            result=discounted_terminal_ri,
            unit=financials.currency,
            interpretation=(
                "Valeur de continuation des profits résiduels."
            )
        )

        # ====================================================
        # 8. VALEUR INTRINSÈQUE PAR ACTION
        # ====================================================

        intrinsic_value = (
            bv_per_share
            + discounted_ri_sum
            + discounted_terminal_ri
        )

        # [CORRECTIF PYDANTIC] Usage d'arguments nommés
        self.add_step(
            label="Valeur intrinsèque par action (RIM)",
            theoretical_formula="BV₀ + RI + TV",
            hypotheses=[
                TraceHypothesis(name="Book value", value=bv_per_share, unit=financials.currency),
                TraceHypothesis(name="Discounted RI", value=discounted_ri_sum, unit=financials.currency),
                TraceHypothesis(name="Discounted TV", value=discounted_terminal_ri, unit=financials.currency)
            ],
            numerical_substitution=f"IV = {intrinsic_value:,.2f}",
            result=intrinsic_value,
            unit=financials.currency,
            interpretation=(
                "Valeur fondamentale par action selon le modèle de Penman."
            )
        )

        total_equity_value = (
            intrinsic_value * financials.shares_outstanding
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
            discount_factors=discount_factors,
            sum_discounted_ri=discounted_ri_sum,
            terminal_value_ri=terminal_value_ri,
            discounted_terminal_value=discounted_terminal_ri,
            total_equity_value=total_equity_value,
            calculation_trace=self.calculation_trace
        )