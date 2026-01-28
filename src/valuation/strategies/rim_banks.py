"""
src/valuation/strategies/rim_banks.py

RESIDUAL INCOME MODEL (RIM) STRATEGY
====================================
Academic Reference: Penman / Ohlson.
Economic Domain: Financial Institutions (Banks, Insurance).
Invariants: Book Value anchor plus Present Value of Residual Incomes (RI).

Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
from typing import Tuple, Dict, Optional

from src.computation.financial_math import (
    calculate_cost_of_equity_capm,
    calculate_discount_factors,
    calculate_rim_vectors,
    apply_dilution_adjustment,
    calculate_dilution_factor,
)
from src.config.constants import ValuationEngineDefaults
from src.exceptions import CalculationError
from src.models import CompanyFinancials, DCFParameters, RIMValuationResult
from src.valuation.strategies.abstract import ValuationStrategy

# Centralized i18n
from src.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    StrategyFormulas,
    CalculationErrors,
    StrategySources,
    KPITexts
)

logger = logging.getLogger(__name__)


def _compute_ohlson_tv(terminal_ri: float, ke: float, last_df: float,
                       params: DCFParameters) -> Tuple[float, float]:
    omega = params.growth.exit_multiple_value or ValuationEngineDefaults.RIM_DEFAULT_OMEGA
    tv_ri = (terminal_ri * omega) / (1 + ke - omega)
    discounted_tv = tv_ri * last_df
    return tv_ri, discounted_tv


class RIMBankingStrategy(ValuationStrategy):
    r"""
    Residual Income Model specialized for the Financial Sector.

    Formula:
    $$IV = BV_0 + \sum_{t=1}^{n} \frac{RI_t}{(1+k_e)^t} + \frac{RI_{terminal}}{(1+k_e-\omega)(1+k_e)^n}$$
    """

    academic_reference = "Penman / Ohlson"
    economic_domain = "Banks / Insurance / Financial Services"

    def execute(
            self,
            financials: CompanyFinancials,
            params: DCFParameters
    ) -> RIMValuationResult:
        """
        Executes the comprehensive RIM sequence.
        """
        g = params.growth

        # 1. BOOK VALUE ANCHOR (BV₀)
        bv_per_share, src_bv = self._select_book_value(financials, params)

        self.add_step(
            step_key="RIM_BV_INITIAL",
            label=RegistryTexts.RIM_BV_L,
            theoretical_formula=StrategyFormulas.BV_BASE,
            result=bv_per_share,
            numerical_substitution=KPITexts.SUB_BV_BASE.format(val=bv_per_share, src=src_bv),
            interpretation=RegistryTexts.RIM_BV_D,
            source=src_bv
        )

        # 2. COST OF EQUITY (kₑ)
        ke, sub_ke = self._compute_ke(financials, params)

        self.add_step(
            step_key="RIM_KE_CALC",
            label=RegistryTexts.RIM_KE_L,
            theoretical_formula=StrategyFormulas.CAPM,
            result=ke,
            numerical_substitution=sub_ke,
            interpretation=StrategyInterpretations.WACC_CONTEXT,
            source=StrategySources.WACC_CALC
        )

        # 3. DISTRIBUTION POLICY & EPS BASE
        eps_base, src_eps = self._select_eps_base(financials, params)
        payout_ratio = self._compute_payout_ratio(financials, eps_base)

        # 4. RESIDUAL INCOME PROJECTION
        # RI = EPS - (Ke * BV_prev)
        projected_eps = [
            eps_base * ((1.0 + (g.fcf_growth_rate or 0.0)) ** t)
            for t in range(1, g.projection_years + 1)
        ]

        ri_vectors, bv_vectors = calculate_rim_vectors(bv_per_share, ke, projected_eps, payout_ratio)
        factors = calculate_discount_factors(ke, g.projection_years)
        discounted_ri_sum = sum(ri * df for ri, df in zip(ri_vectors, factors))

        # 5. TERMINAL VALUE (Ohlson Persistence Factor ω)
        tv_ri, discounted_tv = _compute_ohlson_tv(ri_vectors[-1], ke, factors[-1], params)

        # 6. DILUTION & FINAL IV
        base_iv = bv_per_share + discounted_ri_sum + discounted_tv
        dilution_factor = calculate_dilution_factor(g.annual_dilution_rate, g.projection_years)
        final_iv = apply_dilution_adjustment(base_iv, dilution_factor)

        # 7. AUDIT & OUTPUT CONTRACT
        audit_metrics = self._compute_rim_audit_metrics(financials, eps_base, bv_per_share, ke)
        shares = g.manual_shares_outstanding or financials.shares_outstanding

        result = RIMValuationResult(
            financials=financials, params=params, intrinsic_value_per_share=final_iv,
            market_price=financials.current_price, cost_of_equity=ke, current_book_value=bv_per_share,
            projected_residual_incomes=ri_vectors, projected_book_values=bv_vectors,
            discount_factors=factors, sum_discounted_ri=discounted_ri_sum,
            terminal_value_ri=tv_ri, discounted_terminal_value=discounted_tv,
            total_equity_value=final_iv * shares, calculation_trace=self.calculation_trace,
            roe_observed=audit_metrics["roe"], payout_ratio_observed=payout_ratio,
            spread_roe_ke=audit_metrics["roe_ke"], pb_ratio_observed=audit_metrics["pb"]
        )

        self.generate_audit_report(result)
        self.verify_output_contract(result)
        return result

    @staticmethod
    def _select_book_value(financials: CompanyFinancials, params: DCFParameters) -> Tuple[float, str]:
        if params.growth.manual_book_value is not None:
            return params.growth.manual_book_value, StrategySources.MANUAL_OVERRIDE
        if financials.book_value_per_share and financials.book_value_per_share > 0:
            return financials.book_value_per_share, StrategySources.YAHOO_TTM_SIMPLE
        raise CalculationError(CalculationErrors.RIM_NEGATIVE_BV)

    @staticmethod
    def _compute_ke(financials: CompanyFinancials, params: DCFParameters) -> Tuple[float, str]:
        r = params.rates
        if r.manual_cost_of_equity is not None:
            return r.manual_cost_of_equity, StrategySources.WACC_MANUAL.format(wacc=r.manual_cost_of_equity)
        rf, mrp = (r.risk_free_rate or 0.04), (r.market_risk_premium or 0.05)
        beta = r.manual_beta if r.manual_beta is not None else (financials.beta or 1.0)
        ke = calculate_cost_of_equity_capm(rf, beta, mrp)
        return ke, KPITexts.SUB_CAPM_MATH.format(rf=rf, beta=beta, mrp=mrp)

    @staticmethod
    def _select_eps_base(financials: CompanyFinancials, params: DCFParameters) -> Tuple[float, str]:
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE
        if financials.eps_ttm and financials.eps_ttm > 0:
            return financials.eps_ttm, StrategySources.YAHOO_TTM_SIMPLE
        raise CalculationError(CalculationErrors.MISSING_EPS_RIM)

    @staticmethod
    def _compute_payout_ratio(financials: CompanyFinancials, eps: float) -> float:
        if eps <= 0: return 0.0
        div_ps = (financials.dividends_total_calculated / financials.shares_outstanding) if financials.shares_outstanding else 0
        return max(0.0, min(ValuationEngineDefaults.RIM_MAX_PAYOUT_RATIO, div_ps / eps))

    @staticmethod
    def _compute_rim_audit_metrics(financials: CompanyFinancials, eps: float,
                                   bv: float, ke: float) -> Dict[str, Optional[float]]:
        roe = eps / bv if bv > 0 else 0.0
        return {"roe": roe, "pb": financials.current_price / bv if bv > 0 else 0.0, "roe_ke": roe - ke}