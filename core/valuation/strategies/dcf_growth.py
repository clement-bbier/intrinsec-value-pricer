import logging
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult
from core.valuation.strategies.abstract import ValuationStrategy
from core.exceptions import CalculationError
from core.computation.financial_math import (
    calculate_wacc,
    calculate_discount_factors,
    calculate_terminal_value_gordon,
    calculate_npv,
    calculate_equity_value_bridge
)

logger = logging.getLogger(__name__)


class RevenueBasedStrategy(ValuationStrategy):
    """
    STRATÉGIE 4 : DCF "TECH / GROWTH" (REVENUE DRIVEN).
    Projeté à partir du Revenu et d'une convergence de Marge FCF.
    Ne peut pas utiliser _run_dcf_math car la logique de projection est différente.
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFValuationResult:
        logger.info(
            "[Strategy] Executing RevenueBasedStrategy | ticker=%s | years=%s",
            financials.ticker,
            params.projection_years
        )

        # 1. Détermination de la Base Revenu
        revenue_base = financials.revenue_ttm
        source_rev = "ttm"

        if params.manual_fcf_base is not None and params.manual_fcf_base > 0:
            # En mode Growth, l'override agit sur le Revenu de départ
            revenue_base = params.manual_fcf_base
            source_rev = "manual_override"

        if revenue_base is None or revenue_base <= 0:
            msg = "Donnée manquante : Chiffre d'Affaires (Revenue TTM) requis pour la stratégie Growth."
            raise CalculationError(msg)

        # 2. Détermination des Marges
        current_margin = 0.0
        if financials.fcf_last is not None and revenue_base > 0:
            current_margin = financials.fcf_last / revenue_base

        target_margin = params.target_fcf_margin if params.target_fcf_margin is not None else 0.25

        logger.info(
            "[Growth] Rev=%s (%s) | Margin: %.1f%% -> %.1f%%",
            f"{revenue_base:,.0f}", source_rev, current_margin * 100, target_margin * 100
        )

        # 3. Projection des Flux Spécifiques (Revenue -> Margin -> FCF)
        projected_fcfs = []
        current_revenue = revenue_base
        growth_rate = params.fcf_growth_rate  # Utilisé comme Revenue Growth ici

        for i in range(1, params.projection_years + 1):
            # A. Croissance Revenu
            current_revenue *= (1.0 + growth_rate)

            # B. Convergence Marge (Interpolation Linéaire)
            progress = i / params.projection_years
            applicable_margin = current_margin + (target_margin - current_margin) * progress

            # C. FCF Implicite
            fcf_implied = current_revenue * applicable_margin
            projected_fcfs.append(fcf_implied)

        # 4. Calcul Financier (Utilisation du nouveau moteur centralisé)

        # A. Calcul du WACC
        wacc_ctx = calculate_wacc(financials, params)
        wacc = wacc_ctx.wacc

        # B. Actualisation
        factors = calculate_discount_factors(wacc, len(projected_fcfs))
        sum_discounted = calculate_npv(projected_fcfs, wacc)

        # C. Valeur Terminale
        tv = calculate_terminal_value_gordon(
            final_flow=projected_fcfs[-1],
            rate=wacc,
            g_perp=params.perpetual_growth_rate
        )
        discounted_tv = tv * factors[-1]

        # D. Equity Value
        ev = sum_discounted + discounted_tv
        eq_val = calculate_equity_value_bridge(
            ev, financials.total_debt, financials.cash_and_equivalents
        )

        # E. Per Share
        iv_share = 0.0
        if financials.shares_outstanding > 0:
            iv_share = eq_val / financials.shares_outstanding

        # 5. Retour Résultat Typé (Standard DCF Result)
        return DCFValuationResult(
            request=None,  # Sera injecté par le workflow
            financials=financials,
            params=params,
            intrinsic_value_per_share=iv_share,
            market_price=financials.current_price,
            wacc=wacc,
            cost_of_equity=wacc_ctx.cost_of_equity,
            cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax,
            projected_fcfs=projected_fcfs,
            discount_factors=factors,
            sum_discounted_fcf=sum_discounted,
            terminal_value=tv,
            discounted_terminal_value=discounted_tv,
            enterprise_value=ev,
            equity_value=eq_val
        )