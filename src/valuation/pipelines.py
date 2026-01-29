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
    TerminalValueMethod, TraceHypothesis, ValuationMode,
    VariableInfo, VariableSource
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
        """
        Determines the discount rate and records trace steps with full provenance.

        Parameters
        ----------
        financials : CompanyFinancials
            Target company financial data.
        params : DCFParameters
            Calculation hypotheses.
        is_equity : bool
            True for direct equity models (DDM, FCFE, RIM).
        override : float, optional
            Manual WACC override.

        Returns
        -------
        Tuple[float, Any]
            (discount_rate, wacc_context or None for equity models)
        """
        if is_equity:
            rate = calculate_cost_of_equity(financials, params)
            r = params.rates
            rf = r.risk_free_rate or 0.04
            beta = r.manual_beta or financials.beta or 1.0
            mrp = r.market_risk_premium or 0.05

            # Build variables map for Glass Box with full provenance
            variables: Dict[str, VariableInfo] = {
                "Rf": VariableInfo(
                    symbol="Rf",
                    value=rf,
                    formatted_value=f"{rf:.2%}",
                    source=VariableSource.MANUAL_OVERRIDE if r.risk_free_rate else VariableSource.DEFAULT,
                    description="Risk-free rate (10Y Treasury)",
                    is_overridden=r.risk_free_rate is not None
                ),
                "β": VariableInfo(
                    symbol="β",
                    value=beta,
                    formatted_value=f"{beta:.2f}",
                    source=VariableSource.MANUAL_OVERRIDE if r.manual_beta else VariableSource.YAHOO_FINANCE,
                    description="Systematic risk factor (Beta)",
                    is_overridden=r.manual_beta is not None,
                    original_value=financials.beta if r.manual_beta else None
                ),
                "MRP": VariableInfo(
                    symbol="MRP",
                    value=mrp,
                    formatted_value=f"{mrp:.2%}",
                    source=VariableSource.MANUAL_OVERRIDE if r.market_risk_premium else VariableSource.MACRO_PROVIDER,
                    description="Market Risk Premium",
                    is_overridden=r.market_risk_premium is not None
                )
            }

            sub = f"{rf:.2%} + {beta:.2f} × {mrp:.2%} = {rate:.2%}"

            self._add_step(
                step_key="KE_CALC",
                result=rate,
                numerical_substitution=sub,
                label=RegistryTexts.DCF_KE_L,
                theoretical_formula=StrategyFormulas.CAPM,
                interpretation=StrategyInterpretations.KE_CONTEXT,
                source=StrategySources.CAPM_CALC,
                variables=variables
            )
            return rate, None

        # WACC calculation for Entity approach
        wacc_ctx = calculate_wacc(financials, params)
        rate = override if override is not None else wacc_ctx.wacc

        # Build comprehensive variables map for WACC
        variables = {
            "We": VariableInfo(
                symbol="We",
                value=wacc_ctx.weight_equity,
                formatted_value=f"{wacc_ctx.weight_equity:.1%}",
                source=VariableSource.CALCULATED,
                description="Equity weight in capital structure"
            ),
            "Ke": VariableInfo(
                symbol="Ke",
                value=wacc_ctx.cost_of_equity,
                formatted_value=f"{wacc_ctx.cost_of_equity:.2%}",
                source=VariableSource.CALCULATED,
                description="Cost of Equity (CAPM)"
            ),
            "Wd": VariableInfo(
                symbol="Wd",
                value=wacc_ctx.weight_debt,
                formatted_value=f"{wacc_ctx.weight_debt:.1%}",
                source=VariableSource.CALCULATED,
                description="Debt weight in capital structure"
            ),
            "Kd": VariableInfo(
                symbol="Kd",
                value=wacc_ctx.cost_of_debt_after_tax,
                formatted_value=f"{wacc_ctx.cost_of_debt_after_tax:.2%}",
                source=VariableSource.YAHOO_FINANCE if not params.rates.cost_of_debt else VariableSource.MANUAL_OVERRIDE,
                description="After-tax Cost of Debt"
            )
        }

        # Mark WACC as overridden if user provided manual value
        if override is not None:
            variables["WACC"] = VariableInfo(
                symbol="WACC",
                value=rate,
                formatted_value=f"{rate:.2%}",
                source=VariableSource.MANUAL_OVERRIDE,
                description="User-overridden WACC",
                is_overridden=True,
                original_value=wacc_ctx.wacc
            )

        sub = f"{wacc_ctx.weight_equity:.1%} × {wacc_ctx.cost_of_equity:.2%} + {wacc_ctx.weight_debt:.1%} × {wacc_ctx.cost_of_debt_after_tax:.2%}"

        self._add_step(
            step_key="WACC_CALC",
            result=rate,
            numerical_substitution=sub,
            label=RegistryTexts.DCF_WACC_L,
            theoretical_formula=StrategyFormulas.WACC,
            source=StrategySources.WACC_CALC,
            interpretation=StrategyInterpretations.WACC_CONTEXT,
            variables=variables
        )

        # Record Hamada adjustment if beta was adjusted for leverage
        if wacc_ctx.beta_adjusted:
            self._add_step(
                step_key="BETA_HAMADA_ADJUSTMENT",
                result=wacc_ctx.beta_used,
                numerical_substitution=KPITexts.SUB_HAMADA.format(beta=wacc_ctx.beta_used),
                label=StrategyInterpretations.HAMADA_ADJUSTMENT_L,
                theoretical_formula=StrategyFormulas.HAMADA,
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
        """
        Calculates IV per share by integrating the SBC dilution adjustment.

        Parameters
        ----------
        equity_val : float
            Total equity value.
        shares : float
            Number of shares outstanding.
        financials : CompanyFinancials
            Target company financial data.
        params : DCFParameters
            Calculation hypotheses.

        Returns
        -------
        float
            Intrinsic value per share after dilution adjustment.

        Raises
        ------
        CalculationError
            If shares outstanding is zero or negative.
        """
        if shares <= 0:
            raise CalculationError(CalculationErrors.INVALID_SHARES)

        base_iv = equity_val / shares
        rate = params.growth.annual_dilution_rate or 0.0
        years = params.growth.projection_years
        dilution_factor = calculate_dilution_factor(rate, years)
        final_iv = apply_dilution_adjustment(base_iv, dilution_factor)

        # Record SBC dilution step if applicable
        if self.glass_box_enabled and dilution_factor > 1.0:
            variables: Dict[str, VariableInfo] = {
                "IV_base": VariableInfo(
                    symbol="IV_base",
                    value=base_iv,
                    formatted_value=format_smart_number(base_iv),
                    source=VariableSource.CALCULATED,
                    description="Base intrinsic value per share before dilution"
                ),
                "δ": VariableInfo(
                    symbol="δ",
                    value=rate,
                    formatted_value=f"{rate:.2%}",
                    source=VariableSource.MANUAL_OVERRIDE if params.growth.annual_dilution_rate else VariableSource.DEFAULT,
                    description="Annual SBC dilution rate"
                ),
                "n": VariableInfo(
                    symbol="n",
                    value=float(years),
                    formatted_value=str(years),
                    source=VariableSource.CALCULATED,
                    description="Projection years"
                )
            }

            sub = f"{base_iv:.2f} / (1 + {rate:.2%})^{years}"
            self._add_step(
                step_key="SBC_DILUTION_ADJUSTMENT",
                result=final_iv,
                numerical_substitution=sub,
                label="Dilution Adjustment (SBC)",
                theoretical_formula=StrategyFormulas.SBC_DILUTION,
                interpretation=StrategyInterpretations.SBC_DILUTION_INTERP.format(pct=f"{(1 - 1/dilution_factor):.1%}"),
                variables=variables
            )
        else:
            # Standard value per share calculation
            variables = {
                "Equity": VariableInfo(
                    symbol="Equity",
                    value=equity_val,
                    formatted_value=format_smart_number(equity_val),
                    source=VariableSource.CALCULATED,
                    description="Total equity value"
                ),
                "Shares": VariableInfo(
                    symbol="Shares",
                    value=shares,
                    formatted_value=f"{shares:,.0f}",
                    source=VariableSource.YAHOO_FINANCE if not params.growth.manual_shares_outstanding else VariableSource.MANUAL_OVERRIDE,
                    description="Shares outstanding"
                )
            }

            sub = f"{format_smart_number(equity_val)} / {shares:,.0f}"
            self._add_step(
                step_key="VALUE_PER_SHARE",
                result=final_iv,
                numerical_substitution=sub,
                label=RegistryTexts.DCF_IV_L,
                theoretical_formula=StrategyFormulas.VALUE_PER_SHARE,
                interpretation=StrategyInterpretations.IV.format(ticker=financials.ticker),
                variables=variables
            )

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
            hypotheses: Optional[List[TraceHypothesis]] = None,
            variables: Optional[Dict[str, VariableInfo]] = None
    ) -> None:
        """
        Records a step in the Glass Box calculation trace.

        This method creates a complete audit trail for each calculation step,
        including variable provenance for full transparency (ST-2.1 compliance).

        Parameters
        ----------
        step_key : str
            Unique identifier for the step (e.g., "WACC_CALC", "TV_GORDON").
            Must correspond to an entry in the Glass Box registry.
        result : float
            Numerical result of the calculation step.
        numerical_substitution : str
            Numerical application string showing actual values substituted.
            Example: "0.75 × 8.5% + 0.25 × 4.2% × (1 - 25%)"
        label : str, optional
            Display label for the step (defaults to step_key if empty).
        theoretical_formula : str, optional
            LaTeX formula from StrategyFormulas module.
        interpretation : str, optional
            Pedagogical interpretation from StrategyInterpretations module.
        source : str, optional
            Data source description from StrategySources module.
        hypotheses : Optional[List[TraceHypothesis]], optional
            Associated hypotheses for legacy audit compatibility.
        variables : Optional[Dict[str, VariableInfo]], optional
            Variable provenance map for drill-down transparency.
            Each key is the variable symbol, value is VariableInfo with:
            - symbol: Mathematical notation (e.g., "WACC", "g", "β")
            - value: Numerical value used
            - formatted_value: Display string (e.g., "8.5%", "150.5 M€")
            - source: VariableSource enum (YAHOO_FINANCE, MANUAL_OVERRIDE, etc.)
            - is_overridden: True if user overrode automatic value
            - original_value: Original auto value if overridden

        Notes
        -----
        This method does nothing if glass_box_enabled is False.
        Steps are automatically numbered sequentially starting from 1.

        Financial Impact
        ----------------
        Each CalculationStep is a critical audit checkpoint.
        Complete transparency allows validation of all assumptions used.
        """
        if not self.glass_box_enabled:
            return

        self.calculation_trace.append(CalculationStep(
            step_id=len(self.calculation_trace) + 1,
            step_key=step_key,
            label=label or step_key,
            theoretical_formula=theoretical_formula,
            hypotheses=hypotheses or [],
            numerical_substitution=numerical_substitution,
            actual_calculation=numerical_substitution,  # ST-2.1: Alias for new field
            result=result,
            interpretation=interpretation,
            source=source,
            variables_map=variables or {}
        ))

    def _add_projection_step(self, output: ProjectionOutput) -> None:
        """
        Specialized trace for the flow projection phase (FCF_PROJ).

        Parameters
        ----------
        output : ProjectionOutput
            Output from the flow projector containing flows and trace info.
        """
        self._add_step(
            step_key="FCF_PROJ",
            result=sum(output.flows),
            numerical_substitution=output.numerical_substitution,
            label=output.method_label,
            theoretical_formula=output.theoretical_formula,
            interpretation=output.interpretation,
            source=StrategySources.YAHOO_TTM
        )

    def _compute_terminal_value(
            self,
            flows: List[float],
            discount_rate: float,
            params: DCFParameters
    ) -> Tuple[float, str]:
        """
        Calculates terminal value via Gordon Growth or Exit Multiple.

        Parameters
        ----------
        flows : List[float]
            Projected cash flows.
        discount_rate : float
            WACC or Cost of Equity.
        params : DCFParameters
            Calculation hypotheses.

        Returns
        -------
        Tuple[float, str]
            (terminal_value, step_key used)

        Raises
        ------
        ModelDivergenceError
            If perpetual growth rate exceeds discount rate (Gordon model).
        """
        g = params.growth
        final_flow = flows[-1]

        if g.terminal_method == TerminalValueMethod.GORDON_GROWTH:
            p_growth = g.perpetual_growth_rate or 0.0

            # Mathematical stability check
            if p_growth >= discount_rate:
                raise ModelDivergenceError(p_growth, discount_rate)

            tv = calculate_terminal_value_gordon(final_flow, discount_rate, p_growth)
            key = "TV_GORDON"
            label = RegistryTexts.DCF_TV_GORDON_L
            formula = StrategyFormulas.GORDON

            # Build variables map
            variables: Dict[str, VariableInfo] = {
                "FCF_n": VariableInfo(
                    symbol="FCF_n",
                    value=final_flow,
                    formatted_value=format_smart_number(final_flow),
                    source=VariableSource.CALCULATED,
                    description="Final year cash flow"
                ),
                "g_n": VariableInfo(
                    symbol="g_n",
                    value=p_growth,
                    formatted_value=f"{p_growth:.2%}",
                    source=VariableSource.MANUAL_OVERRIDE if g.perpetual_growth_rate else VariableSource.DEFAULT,
                    description="Perpetual growth rate"
                ),
                "r": VariableInfo(
                    symbol="r",
                    value=discount_rate,
                    formatted_value=f"{discount_rate:.2%}",
                    source=VariableSource.CALCULATED,
                    description="Discount rate (WACC or Ke)"
                )
            }

            sub = f"({format_smart_number(final_flow)} × (1 + {p_growth:.2%})) / ({discount_rate:.2%} - {p_growth:.2%})"

        else:
            exit_m = g.exit_multiple_value or 12.0
            tv = calculate_terminal_value_exit_multiple(final_flow, exit_m)
            key = "TV_MULTIPLE"
            label = RegistryTexts.DCF_TV_MULT_L
            formula = StrategyFormulas.TERMINAL_MULTIPLE

            # Build variables map
            variables = {
                "FCF_n": VariableInfo(
                    symbol="FCF_n",
                    value=final_flow,
                    formatted_value=format_smart_number(final_flow),
                    source=VariableSource.CALCULATED,
                    description="Final year cash flow"
                ),
                "Multiple": VariableInfo(
                    symbol="Multiple",
                    value=exit_m,
                    formatted_value=f"{exit_m:.1f}x",
                    source=VariableSource.MANUAL_OVERRIDE if g.exit_multiple_value else VariableSource.DEFAULT,
                    description="Exit multiple (EV/EBITDA or EV/FCF)"
                )
            }

            sub = f"{format_smart_number(final_flow)} × {exit_m:.1f}"

        self._add_step(
            step_key=key,
            result=tv,
            numerical_substitution=sub,
            label=label,
            theoretical_formula=formula,
            interpretation=StrategyInterpretations.TV,
            variables=variables
        )

        return tv, key

    def _compute_npv_logic(
            self,
            flows: List[float],
            tv: float,
            rate: float,
            params: DCFParameters
    ) -> Tuple[List[float], float, float, float]:
        """
        Calculates NPV of flows and Terminal Value.

        Parameters
        ----------
        flows : List[float]
            Projected cash flows.
        tv : float
            Terminal value.
        rate : float
            Discount rate.
        params : DCFParameters
            Calculation hypotheses.

        Returns
        -------
        Tuple[List[float], float, float, float]
            (discount_factors, sum_pv_flows, pv_terminal_value, enterprise_value)
        """
        factors = calculate_discount_factors(rate, params.growth.projection_years)
        sum_pv = sum(f * d for f, d in zip(flows, factors))
        pv_tv = tv * factors[-1]
        final_value = sum_pv + pv_tv

        label = RegistryTexts.DCF_EV_L if not self.mode.is_direct_equity else "Total Equity Value"

        # Build variables map
        variables: Dict[str, VariableInfo] = {
            "ΣPV_FCF": VariableInfo(
                symbol="ΣPV_FCF",
                value=sum_pv,
                formatted_value=format_smart_number(sum_pv),
                source=VariableSource.CALCULATED,
                description="Sum of discounted cash flows"
            ),
            "PV_TV": VariableInfo(
                symbol="PV_TV",
                value=pv_tv,
                formatted_value=format_smart_number(pv_tv),
                source=VariableSource.CALCULATED,
                description="Present value of terminal value"
            )
        }

        self._add_step(
            step_key="NPV_CALC",
            result=final_value,
            numerical_substitution=f"{format_smart_number(sum_pv)} + {format_smart_number(pv_tv)}",
            label=label,
            theoretical_formula=StrategyFormulas.NPV,
            source=StrategySources.EV_CALC,
            interpretation=StrategyInterpretations.EV_CONTEXT,
            variables=variables
        )

        return factors, sum_pv, pv_tv, final_value

    def _compute_bridge_by_level(
            self,
            val: float,
            financials: CompanyFinancials,
            params: DCFParameters,
            is_equity: bool
    ) -> Tuple[float, float]:
        """
        Toggles between EV-Bridge calculation or direct Equity pass-through.

        Parameters
        ----------
        val : float
            Enterprise value or equity value.
        financials : CompanyFinancials
            Target company financial data.
        params : DCFParameters
            Calculation hypotheses.
        is_equity : bool
            True for direct equity models.

        Returns
        -------
        Tuple[float, float]
            (equity_value, shares_outstanding)
        """
        shares = params.growth.manual_shares_outstanding or financials.shares_outstanding

        if is_equity:
            self._add_step(
                step_key="EQUITY_DIRECT",
                result=val,
                numerical_substitution=f"Direct NPV = {format_smart_number(val)}",
                label=RegistryTexts.DCF_BRIDGE_L
            )
            return val, shares

        # Full EV to Equity bridge
        g = params.growth
        debt = g.manual_total_debt if g.manual_total_debt is not None else financials.total_debt
        cash = g.manual_cash if g.manual_cash is not None else financials.cash_and_equivalents
        min_int = g.manual_minority_interests if g.manual_minority_interests is not None else financials.minority_interests
        pens = g.manual_pension_provisions if g.manual_pension_provisions is not None else financials.pension_provisions

        equity_val = val - (debt or 0.0) + (cash or 0.0) - (min_int or 0.0) - (pens or 0.0)

        # Build variables map
        variables: Dict[str, VariableInfo] = {
            "EV": VariableInfo(
                symbol="EV",
                value=val,
                formatted_value=format_smart_number(val),
                source=VariableSource.CALCULATED,
                description="Enterprise Value"
            ),
            "Debt": VariableInfo(
                symbol="Debt",
                value=debt or 0.0,
                formatted_value=format_smart_number(debt or 0.0),
                source=VariableSource.MANUAL_OVERRIDE if g.manual_total_debt is not None else VariableSource.YAHOO_FINANCE,
                description="Total Debt",
                is_overridden=g.manual_total_debt is not None,
                original_value=financials.total_debt if g.manual_total_debt is not None else None
            ),
            "Cash": VariableInfo(
                symbol="Cash",
                value=cash or 0.0,
                formatted_value=format_smart_number(cash or 0.0),
                source=VariableSource.MANUAL_OVERRIDE if g.manual_cash is not None else VariableSource.YAHOO_FINANCE,
                description="Cash and Equivalents",
                is_overridden=g.manual_cash is not None,
                original_value=financials.cash_and_equivalents if g.manual_cash is not None else None
            )
        }

        sub = f"{format_smart_number(val)} - {format_smart_number(debt)} + {format_smart_number(cash)}..."

        self._add_step(
            step_key="EQUITY_BRIDGE",
            result=equity_val,
            numerical_substitution=sub,
            label=RegistryTexts.DCF_BRIDGE_L,
            theoretical_formula=StrategyFormulas.EQUITY_BRIDGE,
            interpretation=StrategyInterpretations.BRIDGE,
            source=StrategySources.YAHOO_TTM_SIMPLE,
            variables=variables
        )

        return equity_val, shares

    @staticmethod
    def _extract_audit_metrics(
            financials: CompanyFinancials,
            pv_tv: float,
            ev: float
    ) -> Dict[str, Optional[float]]:
        """
        Extracts key ratios for Pillar 3 reliability assessment.

        Parameters
        ----------
        financials : CompanyFinancials
            Target company financial data.
        pv_tv : float
            Present value of terminal value.
        ev : float
            Enterprise value.

        Returns
        -------
        Dict[str, Optional[float]]
            Audit metrics dictionary.
        """
        ebit = financials.ebit_ttm or 0.0
        interest = financials.interest_expense or 0.0

        return {
            "icr": ebit / interest if interest > 0 else 0.0,
            "capex_ratio": abs(
                financials.capex / financials.depreciation_and_amortization
            ) if financials.depreciation_and_amortization else None,
            "tv_weight": pv_tv / ev if ev > 0 else None,
            "payout": financials.dividends_total_calculated / financials.net_income_ttm if financials.net_income_ttm else None,
            "leverage": financials.total_debt / ebit if ebit != 0 else None
        }