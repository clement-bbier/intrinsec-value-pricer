"""
core/valuation/strategies/dcf_growth.py

Méthode : Revenue-Driven FCFF (High Growth DCF)
Version : V1 Normative

Références académiques :
- Damodaran, A. – Valuation of Young, Growth and Tech Firms
- CFA Institute – Equity Valuation (Growth Companies)

Principe :
- La valeur est dérivée du chiffre d’affaires
- Les marges convergent vers un niveau soutenable
- La croissance ralentit vers le long terme
"""

import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult
from core.valuation.strategies.abstract import ValuationStrategy
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
    Revenue-Driven FCFF DCF (High Growth / Tech).

    Référence académique :
    - Aswath Damodaran

    Domaine de validité :
    - Entreprises en forte croissance
    - Modèle économique scalable
    - FCF actuels faibles ou négatifs

    Invariants financiers :
    - Convergence des marges vers un niveau réaliste
    - WACC > g_terminal
    - Croissance décroissante à long terme
    """

    academic_reference = "Damodaran"
    economic_domain = "High growth / Tech firms"
    financial_invariants = [
        "margin_convergence",
        "WACC > g_terminal",
        "long_term_growth < GDP_growth"
    ]

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:
        """
        Exécute un DCF Revenue-Driven.

        Étapes :
        1. Projection du chiffre d’affaires
        2. Convergence progressive de la marge FCF
        3. Actualisation et valeur terminale disciplinée
        """

        logger.info(
            "[Strategy] Revenue-Driven FCFF | ticker=%s",
            financials.ticker
        )

        # ====================================================
        # 1. BASE DE REVENUE
        # ====================================================

        revenue_base = financials.revenue_ttm

        if revenue_base is None or revenue_base <= 0:
            raise CalculationError(
                "Revenue TTM requis pour la stratégie Revenue-Driven."
            )

        # ====================================================
        # 2. MARGES (ACTUELLE → CIBLE)
        # ====================================================

        # Marge actuelle implicite (peut être négative)
        current_margin = 0.0
        if financials.fcf_last is not None and revenue_base > 0:
            current_margin = financials.fcf_last / revenue_base

        # Marge cible long terme (discipline imposée)
        target_margin = (
            params.target_fcf_margin
            if params.target_fcf_margin is not None
            else 0.20
        )

        if target_margin <= 0 or target_margin > 0.40:
            raise CalculationError(
                "Marge cible irréaliste pour une valorisation soutenable."
            )

        logger.info(
            "[Growth] Revenue base=%.0f | Margin %.1f%% → %.1f%%",
            revenue_base,
            current_margin * 100,
            target_margin * 100
        )

        # ====================================================
        # 3. PROJECTION DES FCF (REVENUE → MARGE)
        # ====================================================

        projected_fcfs = []
        current_revenue = revenue_base
        revenue_growth = params.fcf_growth_rate

        if revenue_growth <= -1.0:
            raise CalculationError("Taux de croissance du revenu invalide.")

        for year in range(1, params.projection_years + 1):
            # A. Croissance du revenu
            current_revenue *= (1.0 + revenue_growth)

            # B. Convergence progressive de la marge
            progress = year / params.projection_years
            applied_margin = (
                current_margin
                + (target_margin - current_margin) * progress
            )

            # C. FCF implicite
            fcf = current_revenue * applied_margin
            projected_fcfs.append(fcf)

        # ====================================================
        # 4. ACTUALISATION & VALEUR TERMINALE
        # ====================================================

        wacc_ctx = calculate_wacc(financials, params)
        wacc = wacc_ctx.wacc

        discounted_sum = calculate_npv(projected_fcfs, wacc)
        discount_factors = calculate_discount_factors(
            wacc, len(projected_fcfs)
        )

        # Valeur terminale (croissance disciplinée)
        tv = calculate_terminal_value_gordon(
            projected_fcfs[-1],
            wacc,
            params.perpetual_growth_rate
        )
        discounted_tv = tv * discount_factors[-1]

        # ====================================================
        # 5. PASSAGE À LA VALEUR PAR ACTION
        # ====================================================

        enterprise_value = discounted_sum + discounted_tv
        equity_value = calculate_equity_value_bridge(
            enterprise_value,
            financials.total_debt,
            financials.cash_and_equivalents
        )

        if financials.shares_outstanding <= 0:
            raise CalculationError("Nombre d’actions invalide.")

        intrinsic_value = equity_value / financials.shares_outstanding

        # ====================================================
        # 6. CONSTRUCTION DU RÉSULTAT
        # ====================================================

        return DCFValuationResult(
            request=None,  # injecté par le moteur
            financials=financials,
            params=params,
            intrinsic_value_per_share=intrinsic_value,
            market_price=financials.current_price,
            wacc=wacc,
            cost_of_equity=wacc_ctx.cost_of_equity,
            cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax,
            projected_fcfs=projected_fcfs,
            discount_factors=discount_factors,
            sum_discounted_fcf=discounted_sum,
            terminal_value=tv,
            discounted_terminal_value=discounted_tv,
            enterprise_value=enterprise_value,
            equity_value=equity_value
        )
