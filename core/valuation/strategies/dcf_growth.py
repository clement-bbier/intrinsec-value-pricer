"""
core/valuation/strategies/dcf_growth.py

Méthode : Revenue-Driven FCFF (High Growth DCF)
Version : V3.1 — Souveraineté Analyste Intégrale (Full Override)
"""

import logging

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    DCFValuationResult,
    TraceHypothesis
)
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

        logger.info(
            "[Strategy] Revenue-Driven FCFF | ticker=%s",
            financials.ticker
        )

        # ====================================================
        # 1. BASE DE REVENUE (GLASS BOX) — PRIORITÉ MANUELLE
        # ====================================================

        if params.manual_fcf_base is not None:
            revenue_base = params.manual_fcf_base
            revenue_source = "Analyst Override"
        else:
            revenue_base = financials.revenue_ttm
            revenue_source = "Financial statements"

        if revenue_base is None or revenue_base <= 0:
            raise CalculationError(
                "Revenue TTM requis pour la stratégie Revenue-Driven."
            )

        self.add_step(
            label="Sélection du chiffre d’affaires de base",
            theoretical_formula="Revenue₀ (TTM)",
            hypotheses=[
                TraceHypothesis(
                    name="Revenue TTM",
                    value=revenue_base,
                    unit=financials.currency,
                    source=revenue_source
                )
            ],
            numerical_substitution=f"Revenue₀ = {revenue_base:,.2f}",
            result=revenue_base,
            unit=financials.currency,
            interpretation=(
                "Chiffre d’affaires utilisé comme base de projection "
                "dans le modèle Revenue-Driven."
            )
        )

        # ====================================================
        # 2. MARGE ACTUELLE (GLASS BOX)
        # ====================================================

        if financials.fcf_last is not None and revenue_base > 0:
            current_margin = financials.fcf_last / revenue_base
        else:
            current_margin = 0.0

        self.add_step(
            label="Marge FCF actuelle",
            theoretical_formula="FCF / Revenue",
            hypotheses=[
                TraceHypothesis(
                    name="FCF last",
                    value=financials.fcf_last,
                    unit=financials.currency
                ),
                TraceHypothesis(
                    name="Revenue TTM",
                    value=revenue_base,
                    unit=financials.currency
                )
            ],
            numerical_substitution=(
                f"{financials.fcf_last or 0:,.2f} / {revenue_base:,.2f}"
            ),
            result=current_margin,
            unit="%",
            interpretation=(
                "Marge actuelle implicite, pouvant être faible ou négative "
                "pour une entreprise en forte croissance."
            )
        )

        # ====================================================
        # 3. MARGE CIBLE LONG TERME (GLASS BOX)
        # ====================================================

        target_margin = (
            params.target_fcf_margin
            if params.target_fcf_margin is not None
            else 0.20
        )

        if target_margin <= 0 or target_margin > 0.40:
            raise CalculationError(
                "Marge cible irréaliste pour une valorisation soutenable."
            )

        self.add_step(
            label="Marge FCF cible long terme",
            theoretical_formula="FCF_margin_target",
            hypotheses=[
                TraceHypothesis(
                    name="Target margin",
                    value=target_margin,
                    unit="%",
                    source="User input / Damodaran benchmarks"
                )
            ],
            numerical_substitution=f"Margin_target = {target_margin:.2%}",
            result=target_margin,
            unit="%",
            interpretation=(
                "Marge FCF soutenable à long terme, "
                "cohérente avec la maturité du modèle économique."
            )
        )

        # ====================================================
        # 4. PROJECTION DES FCF (REVENUE → MARGE)
        # ====================================================

        projected_fcfs = []
        current_revenue = revenue_base
        revenue_growth = params.fcf_growth_rate

        if revenue_growth <= -1.0:
            raise CalculationError("Taux de croissance du revenu invalide.")

        for year in range(1, params.projection_years + 1):
            current_revenue *= (1.0 + revenue_growth)

            progress = year / params.projection_years
            applied_margin = (
                current_margin
                + (target_margin - current_margin) * progress
            )

            fcf = current_revenue * applied_margin
            projected_fcfs.append(fcf)

        self.add_step(
            label="Projection des flux de trésorerie libres",
            theoretical_formula="Revenueₜ × Marginₜ",
            hypotheses=[
                TraceHypothesis(
                    name="Revenue growth rate",
                    value=revenue_growth,
                    unit="%"
                ),
                TraceHypothesis(
                    name="Margin convergence",
                    value=f"{current_margin:.2%} → {target_margin:.2%}",
                    unit="%"
                )
            ],
            numerical_substitution=(
                "FCFₜ = Revenueₜ × Marginₜ "
                "(convergence linéaire sur l’horizon)"
            ),
            result=sum(projected_fcfs),
            unit=financials.currency,
            interpretation=(
                "Transformation du chiffre d’affaires projeté en flux "
                "de trésorerie libres via une convergence progressive des marges."
            )
        )

        # ====================================================
        # 5. ACTUALISATION & VALEUR TERMINALE
        # ====================================================

        wacc_ctx = calculate_wacc(financials, params)
        wacc = wacc_ctx.wacc

        # Souveraineté : On trace le Beta réellement utilisé (Expert vs Marché)
        beta_used = params.manual_beta if params.manual_beta is not None else financials.beta

        discounted_sum = calculate_npv(projected_fcfs, wacc)
        discount_factors = calculate_discount_factors(
            wacc, len(projected_fcfs)
        )

        g_perp = params.perpetual_growth_rate
        if wacc <= g_perp:
            g_perp = wacc - 0.005 # Sécurité

        tv = calculate_terminal_value_gordon(
            projected_fcfs[-1],
            wacc,
            g_perp
        )
        discounted_tv = tv * discount_factors[-1]

        self.add_step(
            label="Valeur terminale actualisée",
            theoretical_formula="FCFₙ × (1+g) / (WACC − g)",
            hypotheses=[
                TraceHypothesis(name="Final FCF", value=projected_fcfs[-1], unit=financials.currency),
                TraceHypothesis(name="Beta used", value=beta_used, unit="", source="Manual" if params.manual_beta else "Market"),
                TraceHypothesis(name="WACC", value=wacc, unit="%"),
                TraceHypothesis(name="Perpetual growth", value=g_perp, unit="%")
            ],
            numerical_substitution=(
                f"TV × DFₙ = {tv:,.2f} × {discount_factors[-1]:.4f}"
            ),
            result=discounted_tv,
            unit=financials.currency,
            interpretation="Valeur de continuation disciplinée basée sur le taux d'actualisation souverain."
        )

        # ====================================================
        # 6. PASSAGE À LA VALEUR PAR ACTION (SOVERAINETÉ BRIDGE)
        # ====================================================

        enterprise_value = discounted_sum + discounted_tv

        # Détermination des leviers bilanciels prioritaires
        debt_to_use = params.manual_total_debt if params.manual_total_debt is not None else financials.total_debt
        cash_to_use = params.manual_cash if params.manual_cash is not None else financials.cash_and_equivalents
        shares_to_use = params.manual_shares_outstanding if params.manual_shares_outstanding is not None else financials.shares_outstanding

        bridge = calculate_equity_value_bridge(
            enterprise_value,
            debt_to_use,
            cash_to_use
        )

        if isinstance(bridge, dict):
            equity_value = bridge["equity_value"]
        else:
            equity_value = bridge

        if shares_to_use <= 0:
            raise CalculationError("Nombre d’actions invalide.")

        intrinsic_value = equity_value / shares_to_use

        self.add_step(
            label="Valeur intrinsèque par action",
            theoretical_formula="Equity / Shares outstanding",
            hypotheses=[
                TraceHypothesis(name="Equity value", value=equity_value, unit=financials.currency),
                TraceHypothesis(
                    name="Shares outstanding",
                    value=shares_to_use,
                    unit="#",
                    source="Manual Override" if params.manual_shares_outstanding else "Market"
                )
            ],
            numerical_substitution=(
                f"{equity_value:,.2f} / {shares_to_use:,.0f}"
            ),
            result=intrinsic_value,
            unit=financials.currency,
            interpretation="Valeur intrinsèque finale estimée sur la base de la structure de capital choisie."
        )

        return DCFValuationResult(
            request=None,
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
            equity_value=equity_value,
            calculation_trace=self.calculation_trace
        )