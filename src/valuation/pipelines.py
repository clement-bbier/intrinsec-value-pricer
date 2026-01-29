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
from typing import Any, Dict, List, Optional, Tuple

from src.computation.financial_math import (
    apply_dilution_adjustment,
    calculate_cost_of_equity,
    calculate_dilution_factor,
    calculate_discount_factors,
    calculate_terminal_value_exit_multiple,
    calculate_terminal_value_gordon,
    calculate_wacc,
)
from src.computation.flow_projector import FlowProjector, ProjectionOutput
from src.exceptions import CalculationError, ModelDivergenceError
from src.i18n import (
    CalculationErrors,
    KPITexts,
    RegistryTexts,
    StrategyFormulas,
    StrategyInterpretations,
    StrategySources,
)
from src.models import (
    CalculationStep,
    CompanyFinancials,
    DCFParameters,
    DCFValuationResult,
    EquityDCFValuationResult,
    TerminalValueMethod,
    TraceHypothesis,
    ValuationMode,
    ValuationResult,
    VariableInfo,
    VariableSource,
)
from src.utilities.formatting import format_smart_number

logger = logging.getLogger(__name__)


# ==============================================================================
# HELPER FUNCTIONS FOR VARIABLE PROVENANCE TRACKING
# ==============================================================================

def _build_variable_info(
    symbol: str,
    value: float,
    manual_value: Optional[float],
    provider_value: Optional[float],
    description: str = "",
    default_source: VariableSource = VariableSource.YAHOO_FINANCE,
    format_as_pct: bool = False,
    format_as_currency: bool = False,
    decimals: int = 2
) -> VariableInfo:
    """
    Constructs a VariableInfo object with automatic provenance detection.

    This helper determines the source of a variable based on whether
    a manual override was provided, simplifying Glass Box population.

    Parameters
    ----------
    symbol : str
        Mathematical symbol (e.g., "WACC", "g", "β").
    value : float
        The actual value used in the calculation.
    manual_value : Optional[float]
        The value provided by the user (None if not overridden).
    provider_value : Optional[float]
        The value from the data provider (Yahoo Finance).
    description : str, optional
        Pedagogical description of the variable.
    default_source : VariableSource, optional
        Source to use if no manual override (default: YAHOO_FINANCE).
    format_as_pct : bool, optional
        If True, format value as percentage (default: False).
    format_as_currency : bool, optional
        If True, use smart currency formatting (default: False).
    decimals : int, optional
        Number of decimal places for formatting (default: 2).

    Returns
    -------
    VariableInfo
        Complete variable metadata for Glass Box traceability.

    Examples
    --------
    >>> _build_variable_info(
    ...     symbol="β",
    ...     value=1.2,
    ...     manual_value=1.2,
    ...     provider_value=1.15,
    ...     description="Systematic risk factor",
    ...     default_source=VariableSource.YAHOO_FINANCE
    ... )
    VariableInfo(symbol='β', value=1.2, source=MANUAL_OVERRIDE, is_overridden=True, original_value=1.15)
    """
    # Determine source based on manual override presence
    is_overridden = manual_value is not None

    if is_overridden:
        source = VariableSource.MANUAL_OVERRIDE
        original = provider_value
    elif provider_value is not None:
        source = default_source
        original = None
    else:
        source = VariableSource.DEFAULT
        original = None

    # Format the value for display
    if format_as_pct:
        formatted = f"{value:.{decimals}%}"
    elif format_as_currency:
        formatted = format_smart_number(value)
    else:
        formatted = f"{value:.{decimals}f}"

    return VariableInfo(
        symbol=symbol,
        value=value,
        formatted_value=formatted,
        source=source,
        description=description,
        is_overridden=is_overridden,
        original_value=original
    )


def _build_variables_map(
    *variable_specs: Tuple[str, float, Optional[float], Optional[float], str, bool]
) -> Dict[str, VariableInfo]:
    """
    Batch constructs a variables_map from multiple variable specifications.

    Provides a concise way to build the provenance dictionary for a
    calculation step with multiple input variables.

    Parameters
    ----------
    *variable_specs : Tuple
        Each tuple contains:
        - symbol (str): Mathematical symbol
        - value (float): Actual value used
        - manual_value (Optional[float]): User override value
        - provider_value (Optional[float]): Provider value
        - description (str): Variable description
        - format_as_pct (bool): Whether to format as percentage

    Returns
    -------
    Dict[str, VariableInfo]
        Complete variables map for CalculationStep.

    Examples
    --------
    >> _build_variables_map(
    ..     ("Rf", 0.04, None, 0.04, "Risk-free rate", True),
    ..     ("β", 1.2, 1.2, 1.15, "Beta", False),
    ..     ("MRP", 0.05, None, 0.05, "Market Risk Premium", True),
    .. )
    """
    result: Dict[str, VariableInfo] = {}

    for spec in variable_specs:
        symbol, value, manual_val, provider_val, desc, is_pct = spec
        result[symbol] = _build_variable_info(
            symbol=symbol,
            value=value,
            manual_value=manual_val,
            provider_value=provider_val,
            description=desc,
            format_as_pct=is_pct
        )

    return result


# ==============================================================================
# MAIN PIPELINE CLASS
# ==============================================================================

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

    def __init__(
        self,
        projector: FlowProjector,
        mode: ValuationMode,
        glass_box_enabled: bool = True
    ):
        """
        Initializes the DCF calculation pipeline.

        Parameters
        ----------
        projector : FlowProjector
            The flow projection engine to use.
        mode : ValuationMode
            Valuation mode (FCFF_STANDARD, DDM, FCFE, etc.).
        glass_box_enabled : bool, optional
            Enable Glass Box traceability (default: True).
        """
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
        discount_rate, wacc_ctx = self._resolve_discount_rate(
            financials, params, is_equity_level, wacc_override
        )

        # 2. Cash Flow Projection Phase (FCF_PROJ)
        proj_output = self.projector.project(base_value, financials, params)
        self._add_projection_step(proj_output, financials, params)
        flows = proj_output.flows

        # 3. Terminal Value Calculation (TV_GORDON / TV_MULTIPLE)
        tv, _ = self._compute_terminal_value(flows, discount_rate, params)

        # 4. Discounting and NPV Logic (NPV_CALC)
        factors, sum_pv, pv_tv, final_value = self._compute_npv_logic(
            flows, tv, discount_rate, params
        )

        # 5. Equity Bridge (EQUITY_BRIDGE / EQUITY_DIRECT)
        equity_val, bridge_shares = self._compute_bridge_by_level(
            final_value, financials, params, is_equity_level
        )

        # 6. Final IV per share with SBC Dilution Adjustment (VALUE_PER_SHARE)
        iv_share = self._compute_value_per_share(
            equity_val, bridge_shares, financials, params
        )

        # 7. Audit Metrics Collection
        audit_metrics = self._extract_audit_metrics(financials, pv_tv, final_value)

        # 8. Dispatch final result contract
        if is_equity_level:
            return EquityDCFValuationResult(
                financials=financials,
                params=params,
                intrinsic_value_per_share=iv_share,
                market_price=financials.current_price,
                cost_of_equity=discount_rate,
                projected_equity_flows=flows,
                equity_value=equity_val,
                discounted_terminal_value=pv_tv,
                calculation_trace=self.calculation_trace
            )

        # Securely resolve WACC context attributes
        cost_of_equity = getattr(wacc_ctx, 'cost_of_equity', discount_rate)
        cost_of_debt = getattr(wacc_ctx, 'cost_of_debt_after_tax', 0.0)

        return DCFValuationResult(
            financials=financials,
            params=params,
            intrinsic_value_per_share=iv_share,
            market_price=financials.current_price,
            wacc=discount_rate,
            cost_of_equity=cost_of_equity,
            cost_of_debt_after_tax=cost_of_debt,
            projected_fcfs=flows,
            discount_factors=factors,
            sum_discounted_fcf=sum_pv,
            terminal_value=tv,
            discounted_terminal_value=pv_tv,
            enterprise_value=final_value,
            equity_value=equity_val,
            calculation_trace=self.calculation_trace,
            icr_observed=audit_metrics["icr"],
            capex_to_da_ratio=audit_metrics["capex_ratio"],
            terminal_value_weight=audit_metrics["tv_weight"],
            payout_ratio_observed=audit_metrics["payout"],
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

            # Resolve actual values used
            rf = r.risk_free_rate or 0.04
            beta = r.manual_beta or financials.beta or 1.0
            mrp = r.market_risk_premium or 0.05

            # Build provenance map using helper
            variables = _build_variables_map(
                ("Rf", rf, r.risk_free_rate, 0.04, "Risk-free rate (10Y Treasury)", True),
                ("β", beta, r.manual_beta, financials.beta, "Systematic risk factor (Beta)", False),
                ("MRP", mrp, r.market_risk_premium, 0.05, "Market Risk Premium", True),
            )

            sub = f"{rf:.2%} + {beta:.2f} × {mrp:.2%} = {rate:.2%}"

            self._add_step(
                step_key="KE_CALC",
                result=rate,
                actual_calculation=sub,
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
        variables: Dict[str, VariableInfo] = {
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
                source=(
                    VariableSource.MANUAL_OVERRIDE
                    if params.rates.cost_of_debt
                    else VariableSource.YAHOO_FINANCE
                ),
                description="After-tax Cost of Debt",
                is_overridden=params.rates.cost_of_debt is not None
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

        sub = (
            f"{wacc_ctx.weight_equity:.1%} × {wacc_ctx.cost_of_equity:.2%} + "
            f"{wacc_ctx.weight_debt:.1%} × {wacc_ctx.cost_of_debt_after_tax:.2%}"
        )

        self._add_step(
            step_key="WACC_CALC",
            result=rate,
            actual_calculation=sub,
            label=RegistryTexts.DCF_WACC_L,
            theoretical_formula=StrategyFormulas.WACC,
            source=StrategySources.WACC_CALC,
            interpretation=StrategyInterpretations.WACC_CONTEXT,
            variables=variables
        )

        # Record Hamada adjustment if beta was adjusted for leverage
        if wacc_ctx.beta_adjusted:
            hamada_vars: Dict[str, VariableInfo] = {
                "β_L": VariableInfo(
                    symbol="β_L",
                    value=wacc_ctx.beta_used,
                    formatted_value=f"{wacc_ctx.beta_used:.2f}",
                    source=VariableSource.CALCULATED,
                    description="Levered Beta (Hamada adjusted)"
                )
            }

            self._add_step(
                step_key="BETA_HAMADA_ADJUSTMENT",
                result=wacc_ctx.beta_used,
                actual_calculation=KPITexts.SUB_HAMADA.format(beta=wacc_ctx.beta_used),
                label=StrategyInterpretations.HAMADA_ADJUSTMENT_L,
                theoretical_formula=StrategyFormulas.HAMADA,
                interpretation=StrategyInterpretations.HAMADA_ADJUSTMENT_D,
                variables=hamada_vars
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
                "δ": _build_variable_info(
                    symbol="δ",
                    value=rate,
                    manual_value=params.growth.annual_dilution_rate,
                    provider_value=None,
                    description="Annual SBC dilution rate",
                    default_source=VariableSource.DEFAULT,
                    format_as_pct=True
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
                actual_calculation=sub,
                label=RegistryTexts.SBC_L,
                theoretical_formula=StrategyFormulas.SBC_DILUTION,
                interpretation=StrategyInterpretations.SBC_DILUTION_INTERP.format(
                    pct=f"{(1 - 1 / dilution_factor):.1%}"
                ),
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
                "Shares": _build_variable_info(
                    symbol="Shares",
                    value=shares,
                    manual_value=params.growth.manual_shares_outstanding,
                    provider_value=financials.shares_outstanding,
                    description="Shares outstanding",
                    format_as_pct=False
                )
            }
            # Override formatted_value for shares (no decimals)
            variables["Shares"].formatted_value = f"{shares:,.0f}"

            sub = f"{format_smart_number(equity_val)} / {shares:,.0f}"
            self._add_step(
                step_key="VALUE_PER_SHARE",
                result=final_iv,
                actual_calculation=sub,
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
        actual_calculation: str,
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
        actual_calculation : str
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
            actual_calculation=actual_calculation,
            result=result,
            interpretation=interpretation,
            source=source,
            variables_map=variables or {}
        ))

    def _add_projection_step(
        self,
        output: ProjectionOutput,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> None:
        """
        Specialized trace for the flow projection phase (FCF_PROJ).

        This step was previously a "black box" - now includes full provenance
        for the growth rate and base flow values.

        Parameters
        ----------
        output : ProjectionOutput
            Output from the flow projector containing flows and trace info.
        financials : CompanyFinancials
            Target company financial data.
        params : DCFParameters
            Calculation hypotheses.
        """
        g = params.growth

        # 1. On récupère les variables déjà créées par le FlowProjector (g, g_n, n)
        variables = output.variables

        # 2. On y ajoute juste l'ancrage (FCF_0), qui est connu par le Pipeline
        if "FCF_0" not in variables:
            if g.manual_fcf_base is not None:
                base_flow, base_source = g.manual_fcf_base, VariableSource.MANUAL_OVERRIDE
            else:
                base_flow, base_source = (financials.fcf_last or 0.0), VariableSource.YAHOO_FINANCE

            variables["FCF_0"] = VariableInfo(
                symbol="FCF_0",
                value=base_flow,
                formatted_value=format_smart_number(base_flow),
                source=base_source,
                description="Base year cash flow (Year 0)",
                is_overridden=base_source == VariableSource.MANUAL_OVERRIDE
            )

        # 3. On enregistre l'étape
        self._add_step(
            step_key="FCF_PROJ",
            result=sum(output.flows),
            actual_calculation=output.actual_calculation,
            label=output.method_label,
            theoretical_formula=output.theoretical_formula,
            interpretation=output.interpretation,
            source=StrategySources.YAHOO_TTM,
            variables=variables
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
                "g_n": _build_variable_info(
                    symbol="g_n",
                    value=p_growth,
                    manual_value=g.perpetual_growth_rate,
                    provider_value=None,
                    description="Perpetual growth rate",
                    default_source=VariableSource.DEFAULT,
                    format_as_pct=True
                ),
                "r": VariableInfo(
                    symbol="r",
                    value=discount_rate,
                    formatted_value=f"{discount_rate:.2%}",
                    source=VariableSource.CALCULATED,
                    description="Discount rate (WACC or Ke)"
                )
            }

            sub = (
                f"({format_smart_number(final_flow)} × (1 + {p_growth:.2%})) / "
                f"({discount_rate:.2%} - {p_growth:.2%})"
            )

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
                "Multiple": _build_variable_info(
                    symbol="Multiple",
                    value=exit_m,
                    manual_value=g.exit_multiple_value,
                    provider_value=None,
                    description="Exit multiple (EV/EBITDA or EV/FCF)",
                    default_source=VariableSource.DEFAULT,
                    format_as_pct=False
                )
            }
            # Custom formatting for multiple
            variables["Multiple"].formatted_value = f"{exit_m:.1f}x"

            sub = f"{format_smart_number(final_flow)} × {exit_m:.1f}"

        self._add_step(
            step_key=key,
            result=tv,
            actual_calculation=sub,
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

        label = (
            RegistryTexts.DCF_EV_L
            if not self.mode.is_direct_equity
            else "Total Equity Value"
        )

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
            ),
            "r": VariableInfo(
                symbol="r",
                value=rate,
                formatted_value=f"{rate:.2%}",
                source=VariableSource.CALCULATED,
                description="Discount rate used"
            )
        }

        self._add_step(
            step_key="NPV_CALC",
            result=final_value,
            actual_calculation=f"{format_smart_number(sum_pv)} + {format_smart_number(pv_tv)}",
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
            variables: Dict[str, VariableInfo] = {
                "NPV": VariableInfo(
                    symbol="NPV",
                    value=val,
                    formatted_value=format_smart_number(val),
                    source=VariableSource.CALCULATED,
                    description="Net Present Value of equity flows"
                )
            }

            self._add_step(
                step_key="EQUITY_DIRECT",
                result=val,
                actual_calculation=f"Direct NPV = {format_smart_number(val)}",
                label=RegistryTexts.DCF_BRIDGE_L,
                variables=variables
            )
            return val, shares

        # Full EV to Equity bridge
        g = params.growth
        debt = (
            g.manual_total_debt
            if g.manual_total_debt is not None
            else financials.total_debt
        )
        cash = (
            g.manual_cash
            if g.manual_cash is not None
            else financials.cash_and_equivalents
        )
        min_int = (
            g.manual_minority_interests
            if g.manual_minority_interests is not None
            else financials.minority_interests
        )
        pens = (
            g.manual_pension_provisions
            if g.manual_pension_provisions is not None
            else financials.pension_provisions
        )

        equity_val = val - (debt or 0.0) + (cash or 0.0) - (min_int or 0.0) - (pens or 0.0)

        # Build comprehensive variables map
        variables = {
            "EV": VariableInfo(
                symbol="EV",
                value=val,
                formatted_value=format_smart_number(val),
                source=VariableSource.CALCULATED,
                description="Enterprise Value"
            ),
            "Debt": _build_variable_info(
                symbol="Debt",
                value=debt or 0.0,
                manual_value=g.manual_total_debt,
                provider_value=financials.total_debt,
                description="Total Debt",
                format_as_currency=True
            ),
            "Cash": _build_variable_info(
                symbol="Cash",
                value=cash or 0.0,
                manual_value=g.manual_cash,
                provider_value=financials.cash_and_equivalents,
                description="Cash and Equivalents",
                format_as_currency=True
            ),
            "Minorities": _build_variable_info(
                symbol="Minorities",
                value=min_int or 0.0,
                manual_value=g.manual_minority_interests,
                provider_value=financials.minority_interests,
                description="Minority Interests",
                format_as_currency=True
            ),
            "Pensions": _build_variable_info(
                symbol="Pensions",
                value=pens or 0.0,
                manual_value=g.manual_pension_provisions,
                provider_value=financials.pension_provisions,
                description="Pension Provisions",
                format_as_currency=True
            )
        }

        sub = (
            f"{format_smart_number(val)} - {format_smart_number(debt)} + "
            f"{format_smart_number(cash)} - {format_smart_number(min_int)} - "
            f"{format_smart_number(pens)}"
        )

        self._add_step(
            step_key="EQUITY_BRIDGE",
            result=equity_val,
            actual_calculation=sub,
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
            "capex_ratio": (
                abs(financials.capex / financials.depreciation_and_amortization)
                if financials.depreciation_and_amortization
                else None
            ),
            "tv_weight": pv_tv / ev if ev > 0 else None,
            "payout": (
                financials.dividends_total_calculated / financials.net_income_ttm
                if financials.net_income_ttm
                else None
            ),
            "leverage": financials.total_debt / ebit if ebit != 0 else None
        }