"""
src/valuation/pipelines.py

UNIFIED CALCULATION PIPELINE (DRY ARCHITECTURE)
==============================================
Role: Universal engine for discounted flow models (FCFF, FCFE, DDM).
Architecture: Firm-Level (EV) vs Equity-Level (IV) bifurcated orchestration.
Standards: Systematic SBC dilution adjustment and Glass Box traceability.

Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
from typing import List, Optional, Tuple, Dict, Any

from src.models import (
    CalculationStep, CompanyFinancials, DCFParameters,
    ValuationResult, DCFValuationResult, EquityDCFValuationResult,
    TerminalValueMethod, TraceHypothesis, ValuationMode
)
from src.computation.financial_math import (
    calculate_discount_factors,
    calculate_terminal_value_exit_multiple,
    calculate_terminal_value_gordon,
    calculate_wacc,
    calculate_cost_of_equity,
    calculate_dilution_factor,
    apply_dilution_adjustment
)
from src.computation.growth import FlowProjector, ProjectionOutput
from src.exceptions import CalculationError, ModelDivergenceError
from src.i18n import (
    RegistryTexts, StrategyInterpretations, StrategyFormulas,
    CalculationErrors, KPITexts, StrategySources
)
from src.utilities.formatting import format_smart_number

logger = logging.getLogger(__name__)


class DCFCalculationPipeline:
    """
    Universal execution engine for flow-based valuations.

    Attributes
    ----------
    projector : FlowProjector
        The flow projection engine (Simple, Convergence, etc.).
    mode : ValuationMode
        Valuation mode determining the logical branch (Entity vs Equity).
    glass_box_enabled : bool
        Enables or disables detailed mathematical trace generation.
    """

    def __init__(self, projector: FlowProjector, mode: ValuationMode, glass_box_enabled: bool = True):
        self.projector = projector
        self.mode = mode
        self.glass_box_enabled = glass_box_enabled
        self.calculation_trace: List[CalculationStep] = []

    def run(
            self,
            base_value: float,
            financials: CompanyFinancials,
            params: DCFParameters,
            wacc_override: Optional[float] = None
    ) -> ValuationResult:
        """
        Executes the full valuation chain.

        Parameters
        ----------
        base_value : float
            Anchor flow value (FCF, Dividend, or Revenue).
        financials : CompanyFinancials
            Target company financial data.
        params : DCFParameters
            Calculation hypotheses (rates, growth, dilution).
        wacc_override : float, optional
            Forces the use of a specific WACC if provided.

        Returns
        -------
        ValuationResult
            Enriched result (DCF or Equity) including the Glass Box trace.
        """
        # 1. Determine Discount Rate (r)
        is_equity_level = self.mode.is_direct_equity
        discount_rate, wacc_ctx = self._resolve_discount_rate(financials, params, is_equity_level, wacc_override)

        # 2. Cash Flow Projection Phase (FCF_PROJ)
        proj_output = self.projector.project(base_value, financials, params)
        self._add_projection_step(proj_output)
        flows = proj_output.flows

        # 3. Terminal Value Calculation (TV_GORDON / TV_MULTIPLE)
        tv, _ = self._compute_terminal_value(flows, discount_rate, params)

        # 4. Discounting and NPV Logic (NPV_CALC)
        factors, sum_pv, pv_tv, final_value = self._compute_npv_logic(flows, tv, discount_rate, params)

        # 5. Equity Bridge (EQUITY_BRIDGE / EQUITY_DIRECT)
        equity_val, bridge_shares = self._compute_bridge_by_level(final_value, financials, params, is_equity_level)

        # 6. Final IV per share with SBC Dilution Adjustment (VALUE_PER_SHARE)
        iv_share = self._compute_value_per_share(equity_val, bridge_shares, financials, params)

        # 7. Audit Metrics Collection
        audit_metrics = self._extract_audit_metrics(financials, pv_tv, final_value)

        # 8. Dispatch final result contract
        if is_equity_level:
            return EquityDCFValuationResult(
                financials=financials, params=params, intrinsic_value_per_share=iv_share,
                market_price=financials.current_price, cost_of_equity=discount_rate,
                projected_equity_flows=flows, equity_value=equity_val,
                discounted_terminal_value=pv_tv, calculation_trace=self.calculation_trace
            )

        # Securely resolve WACC context attributes
        cost_of_equity = getattr(wacc_ctx, 'cost_of_equity', discount_rate)
        cost_of_debt = getattr(wacc_ctx, 'cost_of_debt_after_tax', 0.0)

        return DCFValuationResult(
            financials=financials, params=params, intrinsic_value_per_share=iv_share,
            market_price=financials.current_price, wacc=discount_rate,
            cost_of_equity=cost_of_equity,
            cost_of_debt_after_tax=cost_of_debt,
            projected_fcfs=flows, discount_factors=factors, sum_discounted_fcf=sum_pv,
            terminal_value=tv, discounted_terminal_value=pv_tv, enterprise_value=final_value,
            equity_value=equity_val, calculation_trace=self.calculation_trace,
            icr_observed=audit_metrics["icr"], capex_to_da_ratio=audit_metrics["capex_ratio"],
            terminal_value_weight=audit_metrics["tv_weight"], payout_ratio_observed=audit_metrics["payout"],
            leverage_observed=audit_metrics["leverage"]
        )

    # ==========================================================================
    # ATOMIC CALCULATION METHODS (SOLID Principles)
    # ==========================================================================

    def _resolve_discount_rate(
            self,
            financials: CompanyFinancials,
            params: DCFParameters,
            is_equity: bool,
            override: Optional[float]
    ) -> Tuple[float, Any]:
        """Determines the discount rate and records trace steps."""
        if is_equity:
            rate = calculate_cost_of_equity(financials, params)
            r = params.rates
            rf, beta, mrp = (r.risk_free_rate or 0.04), (r.manual_beta or financials.beta or 1.0), (r.market_risk_premium or 0.05)
            sub = StrategySources.MANUAL_OVERRIDE.format(wacc=rate) if r.manual_cost_of_equity else f"{rf:.1%} + {beta:.2f} × {mrp:.1%}"
            self._add_step("KE_CALC", rate, sub, label=RegistryTexts.DCF_KE_L, theoretical_formula=StrategyFormulas.CAPM)
            return rate, None

        wacc_ctx = calculate_wacc(financials, params)
        rate = override if override is not None else wacc_ctx.wacc
        sub = StrategySources.MANUAL_OVERRIDE.format(wacc=rate) if override else \
              f"{wacc_ctx.weight_equity:.1%} × {wacc_ctx.cost_of_equity:.1%} + {wacc_ctx.weight_debt:.1%} × {wacc_ctx.cost_of_debt_after_tax:.1%}"

        self._add_step(
            "WACC_CALC", rate, sub,
            label=RegistryTexts.DCF_WACC_L,
            theoretical_formula=StrategyFormulas.WACC,
            source=StrategySources.WACC_CALC,
            interpretation=StrategyInterpretations.WACC_CONTEXT
        )

        if wacc_ctx.beta_adjusted:
            self._add_step(
                "BETA_HAMADA_ADJUSTMENT", wacc_ctx.beta_used, KPITexts.SUB_HAMADA.format(beta=wacc_ctx.beta_used),
                label=StrategyInterpretations.HAMADA_ADJUSTMENT_L, theoretical_formula=StrategyFormulas.HAMADA,
                interpretation=StrategyInterpretations.HAMADA_ADJUSTMENT_D
            )
        return rate, wacc_ctx

    def _compute_value_per_share(
            self,
            equity_val: float,
            shares: float,
            financials: CompanyFinancials,
            params: DCFParameters
    ) -> float:
        """Calculates IV per share by integrating the SBC dilution adjustment."""
        if shares <= 0:
            raise CalculationError(CalculationErrors.INVALID_SHARES)

        base_iv = equity_val / shares
        rate, years = params.growth.annual_dilution_rate, params.growth.projection_years
        dilution_factor = calculate_dilution_factor(rate, years)
        final_iv = apply_dilution_adjustment(base_iv, dilution_factor)

        if self.glass_box_enabled and dilution_factor > 1.0:
            sub = f"{base_iv:.2f} / (1 + {rate:.2%})^{years}"
            self._add_step(
                "SBC_DILUTION_ADJUSTMENT", final_iv, sub, label="Dilution Adjustment (SBC)",
                theoretical_formula=StrategyFormulas.SBC_DILUTION,
                interpretation=StrategyInterpretations.SBC_DILUTION_INTERP.format(pct=f"{(1 - 1/dilution_factor):.1%}")
            )
        else:
            sub = f"{format_smart_number(equity_val)} / {shares:,.0f}"
            self._add_step("VALUE_PER_SHARE", final_iv, sub, label=RegistryTexts.DCF_IV_L,
                           theoretical_formula=StrategyFormulas.VALUE_PER_SHARE,
                           interpretation=StrategyInterpretations.IV.format(ticker=financials.ticker))
        return final_iv

    # ==========================================================================
    # TRACE HELPERS AND MAPPING
    # ==========================================================================

    def _add_step(
            self,
            step_key: str,
            result: float,
            numerical_substitution: str,
            label: str = "",
            theoretical_formula: str = "",
            interpretation: str = "",
            source: str = "",
            hypotheses: Optional[List[TraceHypothesis]] = None
    ) -> None:
        """Records a step in the Glass Box calculation trace."""
        if not self.glass_box_enabled:
            return

        self.calculation_trace.append(CalculationStep(
            step_id=len(self.calculation_trace) + 1,
            step_key=step_key,
            label=label or step_key,
            theoretical_formula=theoretical_formula,
            hypotheses=hypotheses or [],
            numerical_substitution=numerical_substitution,
            result=result,
            interpretation=interpretation,
            source=source
        ))

    def _add_projection_step(self, output: ProjectionOutput) -> None:
        """Specialized trace for the flow projection phase (FCF_PROJ)."""
        self._add_step("FCF_PROJ", sum(output.flows), output.numerical_substitution,
                       label=output.method_label, theoretical_formula=output.theoretical_formula,
                       interpretation=output.interpretation, source=StrategySources.YAHOO_TTM)

    def _compute_terminal_value(self, flows: List[float], discount_rate: float, params: DCFParameters) -> Tuple[float, str]:
        """Handles TV via Gordon Growth or Exit Multiple."""
        g = params.growth
        if g.terminal_method == TerminalValueMethod.GORDON_GROWTH:
            p_growth = g.perpetual_growth_rate or 0.0
            if p_growth >= discount_rate:
                raise ModelDivergenceError(p_growth, discount_rate)
            tv = calculate_terminal_value_gordon(flows[-1], discount_rate, p_growth)
            key, label, formula = "TV_GORDON", RegistryTexts.DCF_TV_GORDON_L, StrategyFormulas.GORDON
            sub = f"({format_smart_number(flows[-1])} × (1 + {p_growth:.1%})) / ({discount_rate:.1%} - {p_growth:.1%})"
        else:
            exit_m = g.exit_multiple_value or 12.0
            tv = calculate_terminal_value_exit_multiple(flows[-1], exit_m)
            key, label, formula = "TV_MULTIPLE", RegistryTexts.DCF_TV_MULT_L, StrategyFormulas.TERMINAL_MULTIPLE
            sub = f"{format_smart_number(flows[-1])} × {exit_m:.1f}"

        self._add_step(key, tv, sub, label, theoretical_formula=formula, interpretation=StrategyInterpretations.TV)
        return tv, key

    def _compute_npv_logic(self, flows: List[float], tv: float, rate: float, params: DCFParameters) -> Tuple:
        """Calculates NPV of flows and Terminal Value (NPV_CALC)."""
        factors = calculate_discount_factors(rate, params.growth.projection_years)
        sum_pv, pv_tv = sum(f * d for f, d in zip(flows, factors)), (tv * factors[-1])
        final_value = sum_pv + pv_tv
        label = RegistryTexts.DCF_EV_L if not self.mode.is_direct_equity else "Total Equity Value"

        self._add_step(
            "NPV_CALC", final_value, f"{format_smart_number(sum_pv)} + {format_smart_number(pv_tv)}",
            label=label, theoretical_formula=StrategyFormulas.NPV,
            source=StrategySources.EV_CALC,
            interpretation=StrategyInterpretations.EV_CONTEXT
        )
        return factors, sum_pv, pv_tv, final_value

    def _compute_bridge_by_level(
            self,
            val: float,
            financials: CompanyFinancials,
            params: DCFParameters,
            is_equity: bool
    ) -> Tuple[float, float]:
        """Toggles between EV-Bridge calculation or direct Equity pass-through."""
        shares = params.growth.manual_shares_outstanding or financials.shares_outstanding
        if is_equity:
            self._add_step("EQUITY_DIRECT", val, f"Direct NPV = {format_smart_number(val)}",
                           label=RegistryTexts.DCF_BRIDGE_L)
            return val, shares

        g = params.growth
        debt, cash = (g.manual_total_debt or financials.total_debt), (g.manual_cash or financials.cash_and_equivalents)
        min_int, pens = (g.manual_minority_interests or financials.minority_interests), (g.manual_pension_provisions or financials.pension_provisions)
        equity_val = val - (debt or 0.0) + (cash or 0.0) - (min_int or 0.0) - (pens or 0.0)
        sub = f"{format_smart_number(val)} - {format_smart_number(debt)} + {format_smart_number(cash)}..."

        self._add_step("EQUITY_BRIDGE", equity_val, sub, label=RegistryTexts.DCF_BRIDGE_L,
                       theoretical_formula=StrategyFormulas.EQUITY_BRIDGE,
                       interpretation=StrategyInterpretations.BRIDGE,
                       source=StrategySources.YAHOO_TTM_SIMPLE)
        return equity_val, shares

    @staticmethod
    def _extract_audit_metrics(financials: CompanyFinancials, pv_tv: float, ev: float) -> Dict[str, Optional[float]]:
        """Extracts key ratios for Pillar 3 reliability assessment."""
        ebit = financials.ebit_ttm or 0.0
        interest = financials.interest_expense or 0.0

        return {
            "icr": ebit / interest if interest > 0 else 0.0,
            "capex_ratio": abs(
                financials.capex / financials.depreciation_and_amortization) if financials.depreciation_and_amortization else None,
            "tv_weight": pv_tv / ev if ev > 0 else None,
            "payout": financials.dividends_total_calculated / financials.net_income_ttm if financials.net_income_ttm else None,
            "leverage": financials.total_debt / ebit if ebit != 0 else None
        }