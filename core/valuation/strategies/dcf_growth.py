"""
core/valuation/strategies/dcf_growth.py
MÉTHODE : REVENUE-DRIVEN FCFF — VERSION V9.0 (Segmenté & i18n Secured)
Rôle : Valorisation par revenus avec convergence des marges et preuve mathématique.
Architecture : Audit-Grade avec alignement intégral sur le registre Glass Box.
"""

from __future__ import annotations

import logging
from typing import List

from core.computation.financial_math import (
    calculate_discount_factors,
    calculate_npv,
    calculate_terminal_value_gordon,
    calculate_wacc,
)
from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult
from core.valuation.strategies.abstract import ValuationStrategy

# Import des constantes de texte pour i18n
from app.ui_components.ui_texts import (
    RegistryTexts,
    StrategyInterpretations,
    CalculationErrors,
    StrategySources,
    KPITexts,
    DiagnosticTexts
)

logger = logging.getLogger(__name__)


class RevenueBasedStrategy(ValuationStrategy):
    """
    Revenue-Driven DCF avec convergence linéaire des marges.
    Adapté aux entreprises en croissance où les revenus sont plus fiables que les FCF.
    """

    academic_reference = "Damodaran / McKinsey"
    economic_domain = "Growth firms / Revenue-driven"

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:
        """Exécute la stratégie Revenue-Driven avec convergence des marges via segments V9."""
        logger.info("[Strategy] Revenue-Driven FCFF | ticker=%s", financials.ticker)

        # Raccourcis vers les segments
        r = params.rates
        g = params.growth

        # =====================================================================
        # 1. ANCRAGE REVENUS
        # =====================================================================
        rev_base = self._select_revenue_base(financials, params)

        # CORRECTION i18n : Utilisation de SUB_REV_BASE
        self.add_step(
            step_key="GROWTH_REV_BASE",
            label=RegistryTexts.GROWTH_REV_BASE_L,
            theoretical_formula=r"Rev_0",
            result=rev_base,
            numerical_substitution=KPITexts.SUB_REV_BASE.format(val=rev_base),
            interpretation=StrategyInterpretations.GROWTH_REV
        )

        # =====================================================================
        # 2. CONVERGENCE DES MARGES
        # =====================================================================
        curr_margin, target_margin = self._compute_margins(financials, params, rev_base)

        # CORRECTION i18n : Utilisation de SUB_MARGIN_CONV
        self.add_step(
            step_key="GROWTH_MARGIN_CONV",
            label=RegistryTexts.GROWTH_MARGIN_L,
            theoretical_formula=r"Margin_t \to Margin_{target}",
            result=target_margin,
            numerical_substitution=KPITexts.SUB_MARGIN_CONV.format(
                curr=curr_margin,
                target=target_margin,
                years=g.projection_years
            ),
            interpretation=StrategyInterpretations.GROWTH_MARGIN
        )

        # =====================================================================
        # 3. COÛT DU CAPITAL
        # =====================================================================
        wacc, wacc_ctx = self._compute_growth_wacc(financials, params)

        # =====================================================================
        # 4. PROJECTION DES FLUX
        # =====================================================================
        projected_fcfs = self._project_fcfs(
            rev_base, curr_margin, target_margin, params
        )

        # =====================================================================
        # 5. VALEUR TERMINALE
        # =====================================================================
        p_growth = g.perpetual_growth_rate or 0.0
        self._validate_gordon_convergence(p_growth, wacc)

        factors = calculate_discount_factors(wacc, g.projection_years)
        tv = calculate_terminal_value_gordon(
            projected_fcfs[-1], wacc, p_growth
        )
        discounted_tv = tv * factors[-1]

        self.add_step(
            step_key="TV_GORDON",
            label=RegistryTexts.DCF_TV_GORDON_L,
            theoretical_formula=r"TV = \frac{FCF_n \cdot (1 + g)}{WACC - g}",
            result=tv,
            numerical_substitution=(
                f"({projected_fcfs[-1]:,.0f} × {1 + p_growth:.3f}) / "
                f"({wacc:.4f} - {p_growth:.4f})"
            ),
            interpretation=StrategyInterpretations.GROWTH_TV
        )

        # =====================================================================
        # 6. VALEUR D'ENTREPRISE (NPV)
        # =====================================================================
        discounted_sum = calculate_npv(projected_fcfs, wacc)
        ev = discounted_sum + discounted_tv

        self.add_step(
            step_key="NPV_CALC",
            label=RegistryTexts.DCF_EV_L,
            theoretical_formula=r"EV = \sum \frac{FCF_t}{(1+r)^t} + \frac{TV}{(1+r)^n}",
            result=ev,
            numerical_substitution=f"{discounted_sum:,.0f} + ({tv:,.0f} × {factors[-1]:.4f})",
            interpretation=StrategyInterpretations.GROWTH_EV
        )

        # =====================================================================
        # 7. EQUITY BRIDGE
        # =====================================================================
        equity_val, bridge = self._compute_growth_equity_bridge(ev, financials, params)

        self.add_step(
            step_key="EQUITY_BRIDGE",
            label=RegistryTexts.DCF_BRIDGE_L,
            theoretical_formula=r"Equity = EV - Debt + Cash - Minorities - Provisions",
            result=equity_val,
            numerical_substitution=(
                f"{ev:,.0f} - {bridge['debt']:,.0f} + {bridge['cash']:,.0f} - "
                f"{bridge['minorities']:,.0f} - {bridge['pensions']:,.0f}"
            ),
            interpretation=StrategyInterpretations.BRIDGE
        )

        # =====================================================================
        # 8. VALEUR PAR ACTION
        # =====================================================================
        intrinsic_value = self._compute_growth_value_per_share(equity_val, bridge["shares"])

        self.add_step(
            step_key="VALUE_PER_SHARE",
            label=RegistryTexts.DCF_IV_L,
            theoretical_formula=r"IV = \frac{Equity\_Value}{Shares\_Outstanding}",
            result=intrinsic_value,
            numerical_substitution=f"{equity_val:,.0f} / {bridge['shares']:,.0f}",
            interpretation=StrategyInterpretations.GROWTH_IV
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
            discount_factors=factors,
            sum_discounted_fcf=discounted_sum,
            terminal_value=tv,
            discounted_terminal_value=discounted_tv,
            enterprise_value=ev,
            equity_value=equity_val,
            calculation_trace=self.calculation_trace
        )

    # ==========================================================================
    # MÉTHODES PRIVÉES (Adaptées à la segmentation V9.0 & i18n)
    # ==========================================================================

    def _select_revenue_base(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> float:
        """Sélectionne le revenu de base via le segment growth."""
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base

        if financials.revenue_ttm is None or financials.revenue_ttm <= 0:
            raise CalculationError(CalculationErrors.MISSING_REV)

        return financials.revenue_ttm

    def _compute_margins(
        self,
        financials: CompanyFinancials,
        params: DCFParameters,
        rev_base: float
    ) -> tuple[float, float]:
        """Calcule les marges courante et cible via le segment growth."""
        curr_margin = 0.0
        if financials.fcf_last and rev_base > 0:
            curr_margin = financials.fcf_last / rev_base

        # Par défaut 20% si non saisi
        target_margin = params.growth.target_fcf_margin if params.growth.target_fcf_margin is not None else 0.20

        return curr_margin, target_margin

    def _compute_growth_wacc(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> tuple:
        """Calcule le WACC avec traçabilité via le segment rates."""
        wacc_ctx = calculate_wacc(financials, params)
        wacc = wacc_ctx.wacc

        r = params.rates
        beta_used = r.manual_beta if r.manual_beta is not None else financials.beta

        # Substitution utilisant les segments rates
        sub_wacc = (
            f"{wacc_ctx.weight_equity:.2f} × [{r.risk_free_rate or 0:.4f} + "
            f"{beta_used:.2f} × ({r.market_risk_premium or 0:.4f})] + "
            f"{wacc_ctx.weight_debt:.2f} × [{r.cost_of_debt or 0:.4f} × "
            f"(1 - {r.tax_rate or 0:.2f})]"
        )

        self.add_step(
            step_key="WACC_CALC",
            label=RegistryTexts.DCF_WACC_L,
            theoretical_formula=r"WACC = w_e \cdot [R_f + \beta \cdot (ERP)] + w_d \cdot [K_d \cdot (1 - \tau)]",
            result=wacc,
            numerical_substitution=sub_wacc,
            interpretation=StrategyInterpretations.WACC.format(wacc=wacc)
        )

        return wacc, wacc_ctx

    def _project_fcfs(
        self,
        rev_base: float,
        curr_margin: float,
        target_margin: float,
        params: DCFParameters
    ) -> List[float]:
        """Projette les FCF avec convergence linéaire des marges via le segment growth."""
        projected_fcfs = []
        curr_rev = rev_base
        g = params.growth

        for y in range(1, g.projection_years + 1):
            curr_rev *= (1.0 + (g.fcf_growth_rate or 0.0))
            applied_margin = curr_margin + (target_margin - curr_margin) * (y / g.projection_years)
            projected_fcfs.append(curr_rev * applied_margin)

        return projected_fcfs

    def _validate_gordon_convergence(self, perpetual_growth: float, wacc: float) -> None:
        """Valide la convergence du modèle de Gordon via DiagnosticTexts."""
        if perpetual_growth >= wacc:
            raise CalculationError(
                DiagnosticTexts.MODEL_G_DIV_MSG.format(g=perpetual_growth, wacc=wacc)
            )

    def _compute_growth_equity_bridge(
        self,
        ev: float,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> tuple[float, dict]:
        """Calcule le passage EV → Equity Value via le segment growth."""
        g = params.growth

        debt = g.manual_total_debt if g.manual_total_debt is not None else financials.total_debt
        cash = g.manual_cash if g.manual_cash is not None else financials.cash_and_equivalents
        shares = g.manual_shares_outstanding if g.manual_shares_outstanding is not None else financials.shares_outstanding
        minorities = g.manual_minority_interests if g.manual_minority_interests is not None else financials.minority_interests
        pensions = g.manual_pension_provisions if g.manual_pension_provisions is not None else financials.pension_provisions

        equity_val = ev - debt + cash - minorities - pensions

        bridge = {
            "debt": debt,
            "cash": cash,
            "shares": shares,
            "minorities": minorities,
            "pensions": pensions
        }

        return equity_val, bridge

    def _compute_growth_value_per_share(self, equity_val: float, shares: float) -> float:
        """Calcule la valeur intrinsèque par action."""
        if shares <= 0:
            raise CalculationError(CalculationErrors.INVALID_SHARES_SIMPLE)

        return equity_val / shares