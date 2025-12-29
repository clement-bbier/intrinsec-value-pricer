"""
core/valuation/strategies/rim_banks.py

Méthode : Residual Income Model (RIM)
Version : V3.1 — Souveraineté Analyste Intégrale & Cohérence Glass Box
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
    Valorise l'entreprise par sa valeur comptable actuelle augmentée de la
    valeur actuelle de ses profits résiduels futurs.
    """

    academic_reference = "Penman (2001) / Ohlson Model"
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
        # 1. ANCRAGE COMPTABLE — BOOK VALUE (SOVERAINETÉ)
        # ====================================================

        # Priorité à la surcharge manuelle si définie par l'expert
        if params.manual_book_value is not None:
            bv_per_share = params.manual_book_value
            bv_source = "Expert Override"
        else:
            bv_per_share = financials.book_value_per_share
            bv_source = "Balance sheet (Yahoo)"

        eps_base = financials.eps_ttm

        if bv_per_share is None or bv_per_share <= 0:
            raise CalculationError(
                "Book Value par action requise et strictement positive pour le RIM."
            )

        if eps_base is None:
            if financials.net_income_ttm and financials.shares_outstanding > 0:
                eps_base = financials.net_income_ttm / financials.shares_outstanding
            else:
                raise CalculationError(
                    "Bénéfice par action (EPS) requis pour projeter les profits résiduels."
                )

        self.add_step(
            label="Ancrage comptable initial (Book Value)",
            theoretical_formula="BV₀",
            hypotheses=[
                TraceHypothesis(
                    name="Book value per share",
                    value=bv_per_share,
                    unit=financials.currency,
                    source=bv_source
                )
            ],
            numerical_substitution=f"BV₀ = {bv_per_share:,.2f}",
            result=bv_per_share,
            unit=financials.currency,
            interpretation=(
                "Valeur nette comptable servant d’ancrage à la valorisation "
                "avant prise en compte de la création de valeur future."
            )
        )

        # ====================================================
        # 2. COÛT DES FONDS PROPRES (Ke) (SOVERAINETÉ)
        # ====================================================

        if params.manual_cost_of_equity is not None:
            ke = params.manual_cost_of_equity
            ke_source = "Expert Ke Override"
            beta_used = 0.0 # Non utilisé pour le calcul final
        else:
            # Gestion cohérente du Beta (Expert > Market)
            beta_used = params.manual_beta if params.manual_beta is not None else financials.beta
            ke = calculate_cost_of_equity_capm(
                params.risk_free_rate,
                beta_used,
                params.market_risk_premium
            )
            ke_source = "Manual Beta" if params.manual_beta is not None else "CAPM (Yahoo Beta)"

        if ke <= 0:
            raise CalculationError("Cost of Equity invalide (doit être > 0).")

        self.add_step(
            label="Coût des fonds propres (Ke)",
            theoretical_formula="Rf + β × MRP",
            hypotheses=[
                TraceHypothesis(name="Risk-free rate", value=params.risk_free_rate, unit="%"),
                TraceHypothesis(name="Beta used", value=beta_used, unit="", source=ke_source),
                TraceHypothesis(name="Market risk premium", value=params.market_risk_premium, unit="%")
            ],
            numerical_substitution=f"Ke = {ke:.2%}",
            result=ke,
            unit="%",
            interpretation=(
                "Taux d’actualisation exigé par les actionnaires pour "
                "le niveau de risque systématique estimé."
            )
        )

        # ====================================================
        # 3. POLITIQUE DE DISTRIBUTION (PAYOUT)
        # ====================================================

        dividend = financials.last_dividend or 0.0
        payout_ratio = 0.50 # Default si EPS négatif ou nul

        if eps_base > 0:
            payout_ratio = max(0.0, min(0.90, dividend / eps_base))

        self.add_step(
            label="Politique de distribution",
            theoretical_formula="Dividend / EPS",
            hypotheses=[
                TraceHypothesis(name="Dividend", value=dividend, unit=financials.currency),
                TraceHypothesis(name="EPS base", value=eps_base, unit=financials.currency)
            ],
            numerical_substitution=f"Payout = {dividend:,.2f} / {eps_base:,.2f}",
            result=payout_ratio,
            unit="%",
            interpretation=(
                "Part des bénéfices distribuée, influençant la "
                "recapitalisation interne de la Book Value."
            )
        )

        # ====================================================
        # 4. PROJECTION DES RÉSULTATS
        # ====================================================

        years = params.projection_years
        projected_eps = []
        current_eps = eps_base

        for _ in range(years):
            current_eps *= (1.0 + params.fcf_growth_rate)
            projected_eps.append(current_eps)

        self.add_step(
            label="Projection des bénéfices par action",
            theoretical_formula="EPSₜ = EPSₜ₋₁ × (1 + g)",
            hypotheses=[
                TraceHypothesis(name="EPS base", value=eps_base, unit=financials.currency),
                TraceHypothesis(name="Growth rate (g)", value=params.fcf_growth_rate, unit="%")
            ],
            numerical_substitution=f"Projection sur {years} ans",
            result=sum(projected_eps),
            unit=financials.currency,
            interpretation="Trajectoire de rentabilité estimée pour la période explicite."
        )

        # ====================================================
        # 5. PROFITS RÉSIDUELS (CLEAN SURPLUS RELATIONSHIP)
        # ====================================================

        residual_incomes, projected_bvs = calculate_rim_vectors(
            current_book_value=bv_per_share,
            cost_of_equity=ke,
            projected_earnings=projected_eps,
            payout_ratio=payout_ratio
        )

        self.add_step(
            label="Calcul des profits résiduels",
            theoretical_formula="RIₜ = EPSₜ − (Ke × BVₜ₋₁)",
            hypotheses=[
                TraceHypothesis(name="Cost of equity", value=ke, unit="%"),
                TraceHypothesis(name="Payout ratio", value=payout_ratio, unit="%")
            ],
            numerical_substitution="Application itérative de la richesse créée",
            result=sum(residual_incomes),
            unit=financials.currency,
            interpretation=(
                "Surprofits générés par l'entreprise au-delà du coût "
                "d'opportunité de ses fonds propres."
            )
        )

        # ====================================================
        # 6. ACTUALISATION DES PROFITS RÉSIDUELS
        # ====================================================

        discount_factors = calculate_discount_factors(ke, years)
        discounted_ri_sum = calculate_npv(residual_incomes, ke)

        self.add_step(
            label="Valeur actuelle des profits résiduels",
            theoretical_formula="∑ RIₜ / (1+Ke)ᵗ",
            hypotheses=[
                TraceHypothesis(name="Sum Residual Incomes", value=sum(residual_incomes), unit=financials.currency),
                TraceHypothesis(name="Ke", value=ke, unit="%")
            ],
            numerical_substitution=f"NPV(RI, {ke:.2%})",
            result=discounted_ri_sum,
            unit=financials.currency,
            interpretation="Contribution des surprofits explicites à la valeur intrinsèque."
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
        discounted_terminal_ri = terminal_value_ri * discount_factors[-1]

        self.add_step(
            label="Valeur terminale des profits résiduels",
            theoretical_formula="RIₙ × (1+g)/(Ke−g)",
            hypotheses=[
                TraceHypothesis(name="Terminal RI", value=terminal_ri, unit=financials.currency),
                TraceHypothesis(name="Perpetual growth", value=params.perpetual_growth_rate, unit="%")
            ],
            numerical_substitution=f"TV × DFₙ = {terminal_value_ri:,.2f} × {discount_factors[-1]:.4f}",
            result=discounted_terminal_ri,
            unit=financials.currency,
            interpretation="Estimation de la création de valeur résiduelle à perpétuité."
        )

        # ====================================================
        # 8. VALEUR INTRINSÈQUE FINALE (SOUVERAINETÉ BRIDGE)
        # ====================================================

        intrinsic_value = (
            bv_per_share
            + discounted_ri_sum
            + discounted_terminal_ri
        )

        # Priorité au nombre d'actions manuel pour le prix par action
        shares_to_use = (
            params.manual_shares_outstanding
            if params.manual_shares_outstanding is not None
            else financials.shares_outstanding
        )

        if shares_to_use <= 0:
            raise CalculationError("Nombre d'actions nul ou invalide.")

        total_equity_value = intrinsic_value * shares_to_use

        self.add_step(
            label="Valeur intrinsèque par action (RIM)",
            theoretical_formula="BV₀ + PV(RI) + PV(TV_RI)",
            hypotheses=[
                TraceHypothesis(name="Initial Book Value", value=bv_per_share, unit=financials.currency),
                TraceHypothesis(name="Shares used", value=shares_to_use, unit="#", source="Manual" if params.manual_shares_outstanding else "Yahoo")
            ],
            numerical_substitution=f"IV = {intrinsic_value:,.2f}",
            result=intrinsic_value,
            unit=financials.currency,
            interpretation="Valeur fondamentale estimée par action selon le modèle de Penman."
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