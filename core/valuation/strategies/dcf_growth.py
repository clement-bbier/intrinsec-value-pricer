"""
core/valuation/strategies/dcf_growth.py
MÉTHODE : REVENUE-DRIVEN FCFF — VERSION V5.2 (Audit-Grade)
Rôle : Valorisation top-down avec preuve de conversion Revenue -> FCF.
"""

import logging
from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials, DCFParameters, DCFValuationResult,
    TraceHypothesis, TerminalValueMethod
)
from core.valuation.strategies.abstract import ValuationStrategy
from core.computation.financial_math import (
    calculate_wacc, calculate_discount_factors,
    calculate_terminal_value_gordon, calculate_npv,
    calculate_equity_value_bridge
)

logger = logging.getLogger(__name__)

class RevenueBasedStrategy(ValuationStrategy):
    """Revenue-Driven DCF avec convergence des marges et audit CFA Ready."""

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFValuationResult:
        logger.info("[Strategy] Revenue-Driven FCFF | ticker=%s", financials.ticker)

        # 1. ANCRAGE REVENUS (ID: GROWTH_REV_BASE)
        rev_base = params.manual_fcf_base if params.manual_fcf_base is not None else financials.revenue_ttm
        if rev_base is None or rev_base <= 0:
            raise CalculationError("Chiffre d'affaires (Revenue) requis.")

        self.add_step(step_key="GROWTH_REV_BASE", result=rev_base, numerical_substitution=f"Rev_0 = {rev_base:,.0f}")

        # 2. CONVERGENCE DES MARGES (ID: GROWTH_MARGIN_CONV)
        curr_margin = (financials.fcf_last / rev_base) if (financials.fcf_last and rev_base > 0) else 0.0
        target_margin = params.target_fcf_margin if params.target_fcf_margin is not None else 0.20

        self.add_step(
            step_key="GROWTH_MARGIN_CONV",
            result=target_margin,
            numerical_substitution=f"{curr_margin:.2%} × Convergence sur {params.projection_years} ans"
        )

        # 3. WACC (Détail CAPM)
        wacc_ctx = calculate_wacc(financials, params)
        wacc = wacc_ctx.wacc
        beta_used = params.manual_beta or financials.beta
        sub_wacc = (
            f"{wacc_ctx.weight_equity:.2f} × [{params.risk_free_rate:.4f} + {beta_used:.2f} × ({params.market_risk_premium:.4f})] + "
            f"{wacc_ctx.weight_debt:.2f} × [{params.cost_of_debt:.4f} × (1 - {params.tax_rate:.2f})]"
        )
        self.add_step(step_key="WACC_CALC", result=wacc, numerical_substitution=sub_wacc)

        # ======================================================================
        # --- CALCUL DES FLUX PROJETÉS (LOGIQUE MÉTIER) ---
        # ======================================================================
        projected_fcfs = []
        curr_rev = rev_base
        for y in range(1, params.projection_years + 1):
            curr_rev *= (1.0 + params.fcf_growth_rate)
            applied_margin = curr_margin + (target_margin - curr_margin) * (y / params.projection_years)
            projected_fcfs.append(curr_rev * applied_margin)

        # 4. CONVERSION REVENU -> FCF (Audit Fix: Preuve de la marge appliquée)
        # On montre comment on obtient le FCF de l'année 1 pour valider la logique
        self.add_step(
            step_key="FCF_PROJ", # On réutilise la clé pour montrer l'année 1 comme preuve
            result=projected_fcfs[0],
            numerical_substitution=f"FCF_1 = (Rev_0 × (1+g)) × Margin_1 = {projected_fcfs[0]:,.0f}"
        )

        # 5. VALEUR TERMINALE (Basée sur FCF_n)
        factors = calculate_discount_factors(wacc, params.projection_years)
        tv = calculate_terminal_value_gordon(projected_fcfs[-1], wacc, params.perpetual_growth_rate)

        # Audit Fix: Prouver la croissance jusqu'à l'année n
        self.add_step(
            step_key="TV_GORDON",
            result=tv,
            numerical_substitution=f"({projected_fcfs[-1]:,.0f} × {1+params.perpetual_growth_rate:.3f}) / ({wacc:.4f} - {params.perpetual_growth_rate:.3f})"
        )

        # 6. ACTUALISATION (Standard CFA : Somme PV Flux + PV TV)
        discounted_sum = calculate_npv(projected_fcfs, wacc)
        pv_tv = tv * factors[-1]
        ev = discounted_sum + pv_tv

        # Etape intermédiaire pour la rigueur temporelle
        self.add_step(
            step_key="NPV_SUM_FLOWS",
            result=discounted_sum,
            numerical_substitution=f"Somme des flux actualisés sur {params.projection_years} ans"
        )

        self.add_step(
            step_key="NPV_CALC",
            result=ev,
            numerical_substitution=f"{discounted_sum:,.0f} (PV Flux) + ({tv:,.0f} × {factors[-1]:.4f}) (PV TV)"
        )

        # 7. BRIDGE & FINAL
        debt = params.manual_total_debt if params.manual_total_debt is not None else financials.total_debt
        cash = params.manual_cash if params.manual_cash is not None else financials.cash_and_equivalents
        shares = params.manual_shares_outstanding if params.manual_shares_outstanding is not None else financials.shares_outstanding

        equity_val = ev - debt + cash
        self.add_step(step_key="EQUITY_BRIDGE", result=equity_val, numerical_substitution=f"{ev:,.0f} - {debt:,.0f} + {cash:,.0f}")

        if shares <= 0: raise CalculationError("Actions invalides.")
        iv_share = equity_val / shares
        self.add_step(step_key="VALUE_PER_SHARE", result=iv_share, numerical_substitution=f"{equity_val:,.0f} / {shares:,.0f}")

        return DCFValuationResult(
            request=None, financials=financials, params=params,
            intrinsic_value_per_share=iv_share, market_price=financials.current_price,
            wacc=wacc, cost_of_equity=wacc_ctx.cost_of_equity,
            cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax,
            projected_fcfs=projected_fcfs, discount_factors=factors,
            sum_discounted_fcf=discounted_sum, terminal_value=tv,
            discounted_terminal_value=pv_tv, enterprise_value=ev,
            equity_value=equity_val, calculation_trace=self.calculation_trace
        )