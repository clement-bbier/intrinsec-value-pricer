"""
core/valuation/strategies/rim_banks.py

MÉTHODE : RESIDUAL INCOME MODEL (RIM) — VERSION V9.0 (Segmenté & i18n Secured)
Rôle : Valorisation des institutions financières via les profits résiduels (Ohlson).
Architecture : Audit-Grade utilisant les segments Rates & Growth du modèle V9.
"""

from __future__ import annotations

import logging

from src.computation.financial_math import (
    calculate_cost_of_equity_capm,
    calculate_discount_factors,
    calculate_rim_vectors, apply_dilution_adjustment, calculate_dilution_factor,
)
from src.config.constants import ValuationEngineDefaults
from src.exceptions import CalculationError
from src.models import CompanyFinancials, DCFParameters, RIMValuationResult
from src.valuation.strategies.abstract import ValuationStrategy

# Import depuis core.i18n
from src.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    StrategyFormulas,
    CalculationErrors,
    StrategySources,
    KPITexts
)

logger = logging.getLogger(__name__)


class RIMBankingStrategy(ValuationStrategy):
    """
    Residual Income Model (Penman/Ohlson) pour institutions financières.
    Formule : IV = (BV₀ + Σ PV(RI) + PV(TV)) / Dilution_Factor
    """

    academic_reference = "Penman / Ohlson"
    economic_domain = "Banks / Insurance / Financial Services"

    def execute(
            self,
            financials: CompanyFinancials,
            params: DCFParameters
    ) -> RIMValuationResult:
        """Exécute la séquence RIM avec traçabilité Glass Box intégrale."""

        r = params.rates
        g = params.growth

        # 1. Ancrage Valeur Comptable (BV₀)
        bv_per_share, src_bv = self._select_book_value(financials, params)

        self.add_step(
            step_key="RIM_BV_INITIAL",
            label=RegistryTexts.RIM_BV_L,
            theoretical_formula=StrategyFormulas.BV_BASE,
            result=bv_per_share,
            numerical_substitution=KPITexts.SUB_BV_BASE.format(val=bv_per_share, src=src_bv),
            interpretation=RegistryTexts.RIM_BV_D
        )

        # 2. Coût des fonds propres (kₑ)
        ke, sub_ke = self._compute_ke(financials, params)

        self.add_step(
            step_key="RIM_KE_CALC",
            label=RegistryTexts.RIM_KE_L,
            theoretical_formula=StrategyFormulas.CAPM,
            result=ke,
            numerical_substitution=sub_ke,
            interpretation=StrategyInterpretations.WACC.format(wacc=ke)
        )

        # 3. Politique de distribution (Payout)
        eps_base, src_eps = self._select_eps_base(financials, params)
        payout_ratio = self._compute_payout_ratio(financials, eps_base)
        div_per_share = financials.dividends_total_calculated / financials.shares_outstanding if financials.shares_outstanding else 0

        self.add_step(
            step_key="RIM_PAYOUT",
            label=RegistryTexts.RIM_PAYOUT_L,
            theoretical_formula=StrategyFormulas.PAYOUT_RATIO,
            result=payout_ratio,
            numerical_substitution=KPITexts.SUB_PAYOUT.format(div=div_per_share, eps=eps_base, total=payout_ratio),
            interpretation=RegistryTexts.RIM_PAYOUT_D
        )

        # 4. Projection des profits résiduels (RI)
        projected_eps = [eps_base * ((1.0 + (g.fcf_growth_rate or 0.0)) ** t)
                         for t in range(1, g.projection_years + 1)]

        ri_vectors, bv_vectors = calculate_rim_vectors(bv_per_share, ke, projected_eps, payout_ratio)
        factors = calculate_discount_factors(ke, g.projection_years)
        discounted_ri_sum = sum(ri * df for ri, df in zip(ri_vectors, factors))

        self.add_step(
            step_key="RIM_RI_SUM",
            label=RegistryTexts.RIM_RI_L,
            theoretical_formula=StrategyFormulas.RI_SUM,
            result=discounted_ri_sum,
            numerical_substitution=KPITexts.SUB_SUM_RI.format(val=discounted_ri_sum),
            interpretation=RegistryTexts.RIM_RI_D
        )

        # 5. Valeur Terminale (Ohlson ω)
        tv_ri, discounted_tv = self._compute_ohlson_tv(ri_vectors[-1], ke, factors[-1], params)

        # 6. Valeur Intrinsèque Finale et Ajustement Dilution
        base_iv = bv_per_share + discounted_ri_sum + discounted_tv

        dilution_rate = g.annual_dilution_rate
        years = g.projection_years
        dilution_factor = calculate_dilution_factor(dilution_rate, years)
        final_iv = apply_dilution_adjustment(base_iv, dilution_factor)

        if self.glass_box_enabled and dilution_factor > 1.0:
            sub_dilution = f"{base_iv:.2f} / (1 + {dilution_rate:.2%})^{years}"
            self.add_step(
                step_key="SBC_DILUTION_ADJUSTMENT",
                result=final_iv,
                numerical_substitution=sub_dilution,
                label="Ajustement Dilution (SBC)",
                theoretical_formula=r"IV_{diluted} = \frac{IV_{initial}}{(1 + d)^t}",
                interpretation=f"La rémunération en actions (SBC) réduit la part des actionnaires de {(1 - 1 / dilution_factor):.1%}."
            )
        else:
            self.add_step(
                step_key="RIM_FINAL_IV",
                label=RegistryTexts.RIM_IV_L,
                theoretical_formula=StrategyFormulas.RIM_FINAL,
                result=final_iv,
                numerical_substitution=KPITexts.SUB_RIM_FINAL.format(bv=bv_per_share, ri=discounted_ri_sum,
                                                                     tv=discounted_tv),
                interpretation=StrategyInterpretations.IV.format(ticker=financials.ticker)
            )

        # 7. Métriques d'Audit
        audit_metrics = self._compute_rim_audit_metrics(financials, eps_base, bv_per_share, ke)
        shares = g.manual_shares_outstanding if g.manual_shares_outstanding is not None else financials.shares_outstanding

        return RIMValuationResult(
            request=None, financials=financials, params=params, intrinsic_value_per_share=final_iv,
            market_price=financials.current_price, cost_of_equity=ke, current_book_value=bv_per_share,
            projected_residual_incomes=ri_vectors, projected_book_values=bv_vectors,
            discount_factors=factors, sum_discounted_ri=discounted_ri_sum,
            terminal_value_ri=tv_ri, discounted_terminal_value=discounted_tv,
            total_equity_value=final_iv * shares, calculation_trace=self.calculation_trace,
            roe_observed=audit_metrics["roe"], payout_ratio_observed=payout_ratio,
            spread_roe_ke=audit_metrics["roe_ke"], pb_ratio_observed=audit_metrics["pb"]
        )

    # ==========================================================================
    # MÉTHODES PRIVÉES (V9 & i18n Secured)
    # ==========================================================================

    def _select_book_value(self, financials: CompanyFinancials, params: DCFParameters) -> tuple[float, str]:
        """Souveraineté Analyste via segment growth."""
        if params.growth.manual_book_value is not None:
            bv = params.growth.manual_book_value
            if bv <= 0:
                raise CalculationError(CalculationErrors.RIM_NEGATIVE_BV)
            return bv, StrategySources.MANUAL_OVERRIDE
        if financials.book_value_per_share and financials.book_value_per_share > 0:
            return financials.book_value_per_share, StrategySources.YAHOO_TTM_SIMPLE
        raise CalculationError(CalculationErrors.RIM_NEGATIVE_BV)

    def _compute_ke(self, financials: CompanyFinancials, params: DCFParameters) -> tuple[float, str]:
        """Coût des fonds propres via segment rates."""
        r = params.rates
        if r.manual_cost_of_equity is not None:
            return r.manual_cost_of_equity, StrategySources.WACC_MANUAL.format(wacc=r.manual_cost_of_equity)

        rf, mrp = (r.risk_free_rate or 0.04), (r.market_risk_premium or 0.05)
        beta = r.manual_beta if r.manual_beta is not None else financials.beta
        ke = calculate_cost_of_equity_capm(rf, beta, mrp)
        sub = f"{rf:.4f} + {beta:.2f} \times {mrp:.4f}"
        return ke, sub

    def _select_eps_base(self, financials: CompanyFinancials, params: DCFParameters) -> tuple[float, str]:
        """Sélection de l'EPS de départ (Priorité au segment growth.manual_fcf_base)."""
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE
        if financials.eps_ttm and financials.eps_ttm > 0:
            return financials.eps_ttm, StrategySources.YAHOO_TTM_SIMPLE
        raise CalculationError(CalculationErrors.MISSING_EPS_RIM)

    def _compute_payout_ratio(self, financials: CompanyFinancials, eps: float) -> float:
        """Ratio de distribution effectif."""
        if eps <= 0: return 0.0
        div_per_share = financials.dividends_total_calculated / financials.shares_outstanding if financials.shares_outstanding else 0
        return max(0.0, min(ValuationEngineDefaults.RIM_MAX_PAYOUT_RATIO, div_per_share / eps))

    def _compute_ohlson_tv(self, terminal_ri: float, ke: float, last_df: float, params: DCFParameters) -> tuple[float, float]:
        """Valeur terminale RIM utilisant omega (persistance)."""
        omega = params.growth.exit_multiple_value if params.growth.exit_multiple_value is not None else ValuationEngineDefaults.RIM_DEFAULT_OMEGA
        tv_ri = (terminal_ri * omega) / (1 + ke - omega)
        discounted_tv = tv_ri * last_df

        sub_tv_math = f"({terminal_ri:,.2f} \times {omega:.2f}) / (1 + {ke:.4f} - {omega:.2f})"
        self.add_step(
            step_key="RIM_TV_OHLSON",
            label=RegistryTexts.RIM_TV_L,
            theoretical_formula=StrategyFormulas.RIM_PERSISTENCE,
            result=discounted_tv,
            numerical_substitution=KPITexts.SUB_RIM_TV.format(sub_tv=sub_tv_math, factor=last_df),
            interpretation=StrategyInterpretations.RIM_TV
        )
        return tv_ri, discounted_tv

    def _compute_rim_audit_metrics(self, financials, eps, bv, ke) -> dict:
        """Indicateurs pour l'auditeur institutionnel."""
        roe = eps / bv if bv > 0 else 0.0
        return {
            "roe": roe,
            "pb": financials.current_price / bv if bv > 0 else 0.0,
            "roe_ke": roe - ke
        }
