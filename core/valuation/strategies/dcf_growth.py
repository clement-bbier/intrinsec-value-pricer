"""
core/valuation/strategies/dcf_growth.py
MÉTHODE : REVENUE-DRIVEN FCFF — VERSION V6.0 (Audit-Grade)
Rôle : Valorisation par revenus avec convergence des marges et preuve mathématique.
Audit-Grade : Alignement intégral sur le registre Glass Box et substitution numérique.
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
    """Revenue-Driven DCF avec convergence linéaire des marges et audit complet."""

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFValuationResult:
        logger.info("[Strategy] Revenue-Driven FCFF | ticker=%s", financials.ticker)

        # ======================================================================
        # 1. ANCRAGE REVENUS (ID: GROWTH_REV_BASE)
        # ======================================================================
        rev_base = params.manual_fcf_base if params.manual_fcf_base is not None else financials.revenue_ttm
        if rev_base is None or rev_base <= 0:
            raise CalculationError("Chiffre d'affaires (Revenue) requis pour ce modèle.")

        self.add_step(
            step_key="GROWTH_REV_BASE",
            label="Ancrage des Revenus (Rev_0)",
            theoretical_formula=r"Rev_0",
            result=rev_base,
            numerical_substitution=f"Rev_0 = {rev_base:,.0f}",
            interpretation="Point de départ du modèle basé sur le chiffre d'affaires TTM."
        )

        # ======================================================================
        # 2. CONVERGENCE DES MARGES (ID: GROWTH_MARGIN_CONV)
        # ======================================================================
        curr_margin = (financials.fcf_last / rev_base) if (financials.fcf_last and rev_base > 0) else 0.0
        target_margin = params.target_fcf_margin if params.target_fcf_margin is not None else 0.20

        self.add_step(
            step_key="GROWTH_MARGIN_CONV",
            label="Convergence des Marges",
            theoretical_formula=r"Margin_t \to Margin_{target}",
            result=target_margin,
            numerical_substitution=f"{curr_margin:.2%} \\to {target_margin:.2%} (sur {params.projection_years} ans)",
            interpretation="Modélisation de l'amélioration opérationnelle vers une marge FCF normative."
        )

        # ======================================================================
        # 3. COÛT DU CAPITAL (ID: WACC_CALC)
        # ======================================================================
        wacc_ctx = calculate_wacc(financials, params)
        wacc = wacc_ctx.wacc
        beta_used = params.manual_beta if params.manual_beta is not None else financials.beta

        # Alignement miroir avec la formule théorique du registre
        sub_wacc = (
            f"{wacc_ctx.weight_equity:.2f} × [{params.risk_free_rate:.4f} + {beta_used:.2f} × ({params.market_risk_premium:.4f})] + "
            f"{wacc_ctx.weight_debt:.2f} × [{params.cost_of_debt:.4f} × (1 - {params.tax_rate:.2f})]"
        )

        self.add_step(
            step_key="WACC_CALC",
            label="Calcul du WACC",
            theoretical_formula=r"WACC = w_e \cdot [R_f + \beta \cdot (ERP)] + w_d \cdot [K_d \cdot (1 - \tau)]",
            result=wacc,
            numerical_substitution=sub_wacc,
            interpretation="Taux d'actualisation cible pour l'entreprise."
        )

        # ======================================================================
        # --- CALCUL DES FLUX PROJETÉS (LOGIQUE MÉTIER) ---
        # ======================================================================
        projected_fcfs = []
        curr_rev = rev_base
        for y in range(1, params.projection_years + 1):
            curr_rev *= (1.0 + params.fcf_growth_rate)
            # Convergence linéaire de la marge vers la cible
            applied_margin = curr_margin + (target_margin - curr_margin) * (y / params.projection_years)
            projected_fcfs.append(curr_rev * applied_margin)

        # ======================================================================
        # 4. VALEUR TERMINALE (ID: TV_GORDON)
        # ======================================================================
        # GARDE-FOU AUDIT : g doit être < WACC pour éviter une valeur infinie
        if params.perpetual_growth_rate >= wacc:
             raise CalculationError(
                f"Divergence financière : g ({params.perpetual_growth_rate:.2%}) "
                f"est supérieur ou égal au WACC ({wacc:.2%})."
            )

        factors = calculate_discount_factors(wacc, params.projection_years)
        tv = calculate_terminal_value_gordon(projected_fcfs[-1], wacc, params.perpetual_growth_rate)
        discounted_tv = tv * factors[-1]

        # Preuve arithmétique de Gordon
        sub_tv = (
            f"({projected_fcfs[-1]:,.0f} × {1 + params.perpetual_growth_rate:.3f}) / "
            f"({wacc:.4f} - {params.perpetual_growth_rate:.3f})"
        )

        self.add_step(
            step_key="TV_GORDON",
            label="Valeur Terminale (Gordon)",
            theoretical_formula=r"TV = \frac{FCF_n \cdot (1 + g)}{WACC - g}",
            result=tv,
            numerical_substitution=sub_tv,
            interpretation="Valeur de l'entreprise à l'infini basée sur la dernière marge convergée."
        )

        # ======================================================================
        # 5. VALEUR ACTUELLE NETTE (ID: NPV_CALC)
        # ======================================================================
        discounted_sum = calculate_npv(projected_fcfs, wacc)
        ev = discounted_sum + discounted_tv

        # Preuve de la somme actualisée + TV actualisée
        self.add_step(
            step_key="NPV_CALC",
            label="Valeur d'Entreprise (Enterprise Value)",
            theoretical_formula=r"EV = \sum \frac{FCF_t}{(1+r)^t} + \frac{TV}{(1+r)^n}",
            result=ev,
            numerical_substitution=f"{discounted_sum:,.0f} + ({tv:,.0f} × {factors[-1]:.4f})",
            interpretation="Somme actualisée des flux et de la valeur terminale."
        )

        # ======================================================================
        # 6. EQUITY BRIDGE (ID: EQUITY_BRIDGE)
        # ======================================================================
        debt = params.manual_total_debt if params.manual_total_debt is not None else financials.total_debt
        cash = params.manual_cash if params.manual_cash is not None else financials.cash_and_equivalents
        shares = params.manual_shares_outstanding if params.manual_shares_outstanding is not None else financials.shares_outstanding

        # Ajout des termes manquants pour la parité avec abstract.py
        minorities = params.manual_minority_interests if params.manual_minority_interests is not None else financials.minority_interests
        pensions = params.manual_pension_provisions if params.manual_pension_provisions is not None else financials.pension_provisions

        equity_val = ev - debt + cash - minorities - pensions

        self.add_step(
            step_key="EQUITY_BRIDGE",
            label="Valeur des Fonds Propres (Equity Value)",
            theoretical_formula=r"Equity = EV - Debt + Cash - Minorities - Provisions",
            result=equity_val,
            numerical_substitution=f"{ev:,.0f} - {debt:,.0f} + {cash:,.0f} - {minorities:,.0f} - {pensions:,.0f}",
            interpretation="Ajustement de la structure financière incluant Minoritaires et Provisions pour une parité totale entre modèles."
        )

        # ======================================================================
        # 7. VALEUR PAR ACTION (ID: VALUE_PER_SHARE)
        # ======================================================================
        if shares <= 0: raise CalculationError("Nombre d'actions invalide.")
        intrinsic_value = equity_val / shares

        self.add_step(
            step_key="VALUE_PER_SHARE",
            label="Valeur Intrinsèque par Action",
            theoretical_formula=r"Price = \frac{Equity\_Value}{Shares\_Outstanding}",
            result=intrinsic_value,
            numerical_substitution=f"{equity_val:,.0f} / {shares:,.0f}",
            interpretation="Estimation finale du prix théorique par titre."
        )

        return DCFValuationResult(
            request=None, financials=financials, params=params,
            intrinsic_value_per_share=intrinsic_value, market_price=financials.current_price,
            wacc=wacc, cost_of_equity=wacc_ctx.cost_of_equity,
            cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax,
            projected_fcfs=projected_fcfs, discount_factors=factors,
            sum_discounted_fcf=discounted_sum, terminal_value=tv,
            discounted_terminal_value=discounted_tv, enterprise_value=ev,
            equity_value=equity_val, calculation_trace=self.calculation_trace
        )