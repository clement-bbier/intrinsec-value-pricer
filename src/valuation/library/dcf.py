"""
src/valuation/library/dcf.py

DCF CALCULATION LIBRARY
=======================
Role: Specialized logic for Discounted Cash Flow models (FCFF, DDM).
Responsibilities:
  - Flow Projection (Explicit Period with Convergence)
  - Terminal Value Calculation (Gordon / Multiple)
  - Discounting (Time Value of Money)
  - Per-Share Value Resolution (Dilution)

Architecture: Stateless Functional Library.
Input: Resolved Parameters plus Computed Rates (WACC/Ke).
Output: Computed values + CalculationSteps.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
"""

from __future__ import annotations

from typing import Tuple, List

from src.models.parameters.base_parameter import Parameters
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.enums import TerminalValueMethod, VariableSource
from src.core.formatting import format_smart_number

# Atomic Math Imports
from src.computation.financial_math import (
    calculate_terminal_value_gordon,
    calculate_terminal_value_exit_multiple,
    calculate_discount_factors,
    calculate_dilution_factor,
    apply_dilution_adjustment
)

# Configuration & i18n
from src.config.constants import ModelDefaults
from src.i18n import (
    RegistryTexts,
    StrategyFormulas,
    StrategyInterpretations,
    SharedTexts,
    StrategySources
)


class DCFLibrary:
    """
    Stateless functional library for DCF-specific calculations.
    """

    @staticmethod
    def project_flows_simple(
        base_flow: float,
        params: Parameters
    ) -> Tuple[List[float], CalculationStep]:
        """
        Projects cash flows using a standard growth rate with linear fade-down.

        Logic:
          - Starts at 'g_start' (Short-term growth).
          - Converges linearly towards 'g_term' (Terminal growth) over the horizon.
          - Uses 'projection_years' horizon.

        Parameters
        ----------
        base_flow : float
            The Year 0 anchor (FCF or Dividend).
        params : Parameters
            Contains growth assumptions.

        Returns
        -------
        Tuple[List[float], CalculationStep]
            The list of projected flows and the audit step.
        """
        g = params.growth

        # 1. Resolve Growth Rates
        g_start = g.fcf_growth_rate or ModelDefaults.DEFAULT_GROWTH_RATE
        g_term = g.perpetual_growth_rate or ModelDefaults.DEFAULT_TERMINAL_GROWTH
        years = g.projection_years or ModelDefaults.DEFAULT_PROJECTION_YEARS

        # 2. Projection Loop (Linear Convergence)
        flows = []
        current_flow = base_flow

        for t in range(1, years + 1):
            # Interpolation factor (0.0 at year 1 -> 1.0 at year N)
            # This ensures we glide smoothly from Short Term G to Terminal G
            if years > 1:
                alpha = (t - 1) / (years - 1)
                current_g = g_start * (1 - alpha) + g_term * alpha
            else:
                current_g = g_start

            current_flow *= (1.0 + current_g)
            flows.append(current_flow)

        # 3. Trace Building
        variables = {
            "FCF_0": VariableInfo(
                symbol="FCF_0", value=base_flow,
                source=VariableSource.SYSTEM,
                description="Base Year Flow"
            ),
            "g_start": VariableInfo(
                symbol="g_start", value=g_start, formatted_value=f"{g_start:.1%}",
                source=VariableSource.MANUAL_OVERRIDE if g.fcf_growth_rate else VariableSource.DEFAULT,
                description="Initial Growth Rate"
            ),
            "g_term": VariableInfo(
                symbol="g_term", value=g_term, formatted_value=f"{g_term:.1%}",
                source=VariableSource.MANUAL_OVERRIDE if g.perpetual_growth_rate else VariableSource.DEFAULT,
                description="Terminal Growth Target"
            ),
            "n": VariableInfo(
                symbol="n", value=float(years),
                source=VariableSource.MANUAL_OVERRIDE if g.projection_years else VariableSource.DEFAULT,
                description=SharedTexts.INP_PROJ_YEARS
            )
        }

        step = CalculationStep(
            step_key="FCF_PROJ",
            label=RegistryTexts.DCF_PROJ_L,
            theoretical_formula=StrategyFormulas.FCF_PROJECTION,
            actual_calculation=f"{format_smart_number(base_flow)} × (Linear Convergence {g_start:.1%} → {g_term:.1%})",
            result=sum(flows), # Indicative result: Sum of undiscounted flows
            interpretation=StrategyInterpretations.PROJ.format(years=years, g=g_start),
            source=StrategySources.YAHOO_TTM_SIMPLE,
            variables_map=variables
        )

        return flows, step

    @staticmethod
    def project_flows_manual(
            base_flow: float,
            growth_vector: List[float]
    ) -> Tuple[List[float], CalculationStep]:
        """
        Projects flows using an explicit year-by-year growth vector provided by an expert.

        Parameters
        ----------
        base_flow : float
            The Year 0 anchor.
        growth_vector : List[float]
            The list of growth rates for each year (e.g. [0.10, 0.08, 0.05]).

        Returns
        -------
        Tuple[List[float], CalculationStep]
            The projected flows and the trace.
        """
        flows = []
        current_flow = base_flow
        years = len(growth_vector)

        # 1. Manual Projection Loop
        for i, g_rate in enumerate(growth_vector):
            current_flow *= (1.0 + g_rate)
            flows.append(current_flow)

        # 2. Trace
        # We display the average growth in the trace summary for readability
        avg_growth = sum(growth_vector) / years if years > 0 else 0.0

        variables = {
            "FCF_0": VariableInfo(
                symbol="FCF_0", value=base_flow,
                source=VariableSource.SYSTEM, description="Base Year Flow"
            ),
            "n": VariableInfo(
                symbol="n", value=float(years),
                source=VariableSource.MANUAL_OVERRIDE, description="Manual Horizon"
            ),
            "g_avg": VariableInfo(
                symbol="g_avg", value=avg_growth, formatted_value=f"{avg_growth:.1%}",
                source=VariableSource.MANUAL_OVERRIDE, description="Average Custom Growth"
            )
        }

        step = CalculationStep(
            step_key="FCF_PROJ_MANUAL",
            label=RegistryTexts.DCF_PROJ_L,
            theoretical_formula=StrategyFormulas.FLOW_PROJECTION,
            actual_calculation=f"Manual Vector Projection ({years} years)",
            result=sum(flows),
            interpretation=f"Projection manuelle experte sur {years} ans (Moyenne: {avg_growth:.1%})",
            source=StrategySources.MANUAL_OVERRIDE,
            variables_map=variables
        )

        return flows, step

    @staticmethod
    def project_flows_revenue_model(
            base_revenue: float,
            current_margin: float,
            target_margin: float,
            params: Parameters
    ) -> Tuple[List[float], List[float], List[float], CalculationStep]:
        """
        Projects FCF based on Revenue Growth and Margin Convergence.

        Logic:
          1. Rev(t) projected via Linear Fade-Down growth (or Manual Vector).
          2. Margin(t) converges linearly from Current -> Target.
          3. FCF(t) = Rev(t) * Margin(t).

        Parameters
        ----------
        base_revenue : float
            The Year 0 Revenue anchor.
        current_margin : float
            The TTM FCF Margin (FCF / Revenue).
        target_margin : float
            The normative target margin at year N.
        params : Parameters
            Contains strategy-specific inputs (revenue_growth_rate, target_fcf_margin).

        Returns
        -------
        Tuple[List[float], List[float], List[float], CalculationStep]
            (FCF Flows, Projected Revenues, Projected Margins, Trace)
        """
        # 1. Setup Parameters
        # params.strategy contains specific overrides for this model
        # Using getattr to safely access strategy-specific fields that exist in FCFFGrowthParameters
        strat_params = params.strategy

        g_start = getattr(strat_params, "revenue_growth_rate", None) or ModelDefaults.DEFAULT_GROWTH_RATE
        g_term = params.growth.perpetual_growth_rate or ModelDefaults.DEFAULT_TERMINAL_GROWTH
        years = params.growth.projection_years or ModelDefaults.DEFAULT_PROJECTION_YEARS

        # Check for Manual Vector (Hybrid Mode)
        manual_vector = getattr(strat_params, "manual_growth_vector", None)

        revenues = []
        margins = []
        fcfs = []

        current_rev = base_revenue

        # 2. Projection Loop
        for t in range(1, years + 1):
            # A. Revenue Growth Logic
            if manual_vector and (t-1) < len(manual_vector):
                current_g = manual_vector[t-1]
            else:
                # Linear Fade Down
                if years > 1:
                    alpha = (t - 1) / (years - 1)
                    current_g = g_start * (1 - alpha) + g_term * alpha
                else:
                    current_g = g_start

            current_rev *= (1.0 + current_g)
            revenues.append(current_rev)

            # B. Margin Convergence Logic
            # Linear interpolation: Margin_0 -> Margin_Target
            if years > 0:
                progress = t / years
                current_m = current_margin * (1 - progress) + target_margin * progress
            else:
                current_m = target_margin

            margins.append(current_m)

            # C. FCF Calculation
            fcfs.append(current_rev * current_m)

        # 3. Trace
        variables = {
            "Rev_0": VariableInfo(
                symbol="Rev_0", value=base_revenue,
                source=VariableSource.SYSTEM, description="Base Revenue"
            ),
            "M_0": VariableInfo(
                symbol="M_0", value=current_margin, formatted_value=f"{current_margin:.1%}",
                source=VariableSource.CALCULATED, description="Current FCF Margin"
            ),
            "M_target": VariableInfo(
                symbol="M_n", value=target_margin, formatted_value=f"{target_margin:.1%}",
                source=VariableSource.MANUAL_OVERRIDE if getattr(strat_params, "target_fcf_margin", None) else VariableSource.DEFAULT,
                description="Target FCF Margin"
            ),
            "g_rev": VariableInfo(
                symbol="g_rev", value=g_start, formatted_value=f"{g_start:.1%}",
                source=VariableSource.MANUAL_OVERRIDE, description="Initial Revenue Growth"
            )
        }

        step = CalculationStep(
            step_key="REV_MARGIN_CONV",
            label=RegistryTexts.GROWTH_MARGIN_L,
            theoretical_formula=StrategyFormulas.GROWTH_MARGIN_CONV,
            actual_calculation=f"Revenue Growth ({g_start:.1%}->{g_term:.1%}) & Margin ({current_margin:.1%}->{target_margin:.1%})",
            result=sum(fcfs),
            interpretation=StrategyInterpretations.GROWTH_MARGIN,
            source=StrategySources.CALCULATED,
            variables_map=variables
        )

        return fcfs, revenues, margins, step

    @staticmethod
    def compute_terminal_value(
        final_flow: float,
        discount_rate: float,
        params: Parameters
    ) -> Tuple[float, CalculationStep]:
        """
        Calculates Terminal Value based on User Selection (Gordon vs Multiple).

        Parameters
        ----------
        final_flow : float
            The projected flow of the last explicit year (Year N).
        discount_rate : float
            The discount rate used (WACC or Ke).
        params : Parameters
            Contains TV method and assumptions.

        Returns
        -------
        Tuple[float, CalculationStep]
            Terminal Value (TV) and the audit step.
        """
        tv_params = params.strategy.terminal_value
        method = tv_params.method or TerminalValueMethod.GORDON_GROWTH

        if method == TerminalValueMethod.GORDON_GROWTH:
            g_perp = tv_params.perpetual_growth_rate or ModelDefaults.DEFAULT_TERMINAL_GROWTH

            # Math: TV = FCF_n * (1+g) / (r - g)
            tv = calculate_terminal_value_gordon(final_flow, discount_rate, g_perp)

            step = CalculationStep(
                step_key="TV_GORDON",
                label=RegistryTexts.DCF_TV_GORDON_L,
                theoretical_formula=StrategyFormulas.GORDON,
                actual_calculation=f"({format_smart_number(final_flow)} × (1 + {g_perp:.1%})) / ({discount_rate:.1%} - {g_perp:.1%})",
                result=tv,
                interpretation=StrategyInterpretations.TV,
                variables_map={
                    "g_perp": VariableInfo(
                        symbol="g", value=g_perp, formatted_value=f"{g_perp:.2%}",
                        source=VariableSource.MANUAL_OVERRIDE if tv_params.perpetual_growth_rate else VariableSource.DEFAULT,
                        description=SharedTexts.INP_PERP_G
                    ),
                    "r": VariableInfo(
                        symbol="r", value=discount_rate, formatted_value=f"{discount_rate:.2%}",
                        source=VariableSource.CALCULATED, description="Discount Rate"
                    )
                }
            )
            return tv, step

        else: # EXIT_MULTIPLE
            multiple = tv_params.exit_multiple or ModelDefaults.DEFAULT_EXIT_MULTIPLE

            # Math: TV = FCF_n * Multiple
            tv = calculate_terminal_value_exit_multiple(final_flow, multiple)

            step = CalculationStep(
                step_key="TV_MULTIPLE",
                label=RegistryTexts.DCF_TV_MULT_L,
                theoretical_formula=StrategyFormulas.TERMINAL_MULTIPLE,
                actual_calculation=f"{format_smart_number(final_flow)} × {multiple:.1f}x",
                result=tv,
                interpretation=StrategyInterpretations.TV,
                variables_map={
                    "M": VariableInfo(
                        symbol="M", value=multiple, formatted_value=f"{multiple:.1f}x",
                        source=VariableSource.MANUAL_OVERRIDE if tv_params.exit_multiple else VariableSource.DEFAULT,
                        description="Exit Multiple"
                    )
                }
            )
            return tv, step

    @staticmethod
    def compute_discounting(
        flows: List[float],
        terminal_value: float,
        discount_rate: float
    ) -> Tuple[float, CalculationStep]:
        """
        Calculates the Enterprise Value (NPV of Flows + PV of TV).

        Parameters
        ----------
        flows : List[float]
            The projected cash flows.
        terminal_value : float
            The terminal value at year N.
        discount_rate : float
            The WACC or Cost of Equity.

        Returns
        -------
        Tuple[float, CalculationStep]
            Total Enterprise Value and the audit step.
        """
        # 1. Discount Factors
        years_count = len(flows)
        factors = calculate_discount_factors(discount_rate, years_count)

        # 2. Sum PV of Flows
        sum_pv_flows = sum(f * d for f, d in zip(flows, factors))

        # 3. PV of Terminal Value
        pv_tv = terminal_value * factors[-1]

        # 4. Total Enterprise Value
        total_ev = sum_pv_flows + pv_tv

        # 5. Trace
        step = CalculationStep(
            step_key="NPV_CALC",
            label=RegistryTexts.DCF_EV_L,
            theoretical_formula=StrategyFormulas.NPV,
            actual_calculation=f"{format_smart_number(sum_pv_flows)} (Flows) + {format_smart_number(pv_tv)} (TV)",
            result=total_ev,
            interpretation=StrategyInterpretations.EV_CONTEXT,
            source=StrategySources.EV_CALC,
            variables_map={
                "r": VariableInfo(
                    symbol="r", value=discount_rate, formatted_value=f"{discount_rate:.2%}",
                    source=VariableSource.CALCULATED, description="Discount Rate"
                ),
                "Σ_PV_Flows": VariableInfo(
                    symbol="ΣPV", value=sum_pv_flows, formatted_value=format_smart_number(sum_pv_flows),
                    source=VariableSource.CALCULATED, description="PV of Explicit Period"
                ),
                "PV_TV": VariableInfo(
                    symbol="PV_TV", value=pv_tv, formatted_value=format_smart_number(pv_tv),
                    source=VariableSource.CALCULATED, description="PV of Terminal Value"
                )
            }
        )

        return total_ev, step

    @staticmethod
    def compute_value_per_share(
        equity_value: float,
        params: Parameters
    ) -> Tuple[float, CalculationStep]:
        """
        Calculates final price per share, applying SBC dilution adjustment if needed.

        Parameters
        ----------
        equity_value : float
            The Total Equity Value.
        params : Parameters
            Contains shares outstanding and dilution parameters.

        Returns
        -------
        Tuple[float, CalculationStep]
            Final price per share and the audit step.
        """
        # 1. Shares Outstanding
        shares = params.common.capital.shares_outstanding or ModelDefaults.DEFAULT_SHARES_OUTSTANDING

        # 2. Base Price
        base_iv = equity_value / shares

        # 3. Dilution Logic
        dilution_rate = params.growth.annual_dilution_rate or 0.0
        years = params.growth.projection_years or ModelDefaults.DEFAULT_PROJECTION_YEARS

        dilution_factor = calculate_dilution_factor(dilution_rate, years)
        final_iv = apply_dilution_adjustment(base_iv, dilution_factor)

        # 4. Trace (Smart logic: show dilution only if active)
        if dilution_factor > 1.0:
            step = CalculationStep(
                step_key="VALUE_PER_SHARE_DILUTED",
                label=RegistryTexts.SBC_L,
                theoretical_formula=StrategyFormulas.SBC_DILUTION,
                actual_calculation=f"{format_smart_number(base_iv)} / (1 + {dilution_rate:.1%})^{years}",
                result=final_iv,
                interpretation=StrategyInterpretations.SBC_DILUTION_INTERP.format(pct=f"{(dilution_factor-1):.1%}"),
                variables_map={
                    "Shares": VariableInfo(
                        symbol="Shares", value=shares, formatted_value=f"{shares:,.0f}",
                        source=VariableSource.SYSTEM, description=SharedTexts.INP_SHARES
                    ),
                    "Dilution": VariableInfo(
                        symbol="δ", value=dilution_rate, formatted_value=f"{dilution_rate:.1%}",
                        source=VariableSource.MANUAL_OVERRIDE, description="Annual SBC Dilution"
                    )
                }
            )
        else:
            step = CalculationStep(
                step_key="VALUE_PER_SHARE",
                label=RegistryTexts.DCF_IV_L,
                theoretical_formula=StrategyFormulas.VALUE_PER_SHARE,
                actual_calculation=f"{format_smart_number(equity_value)} / {shares:,.0f}",
                result=final_iv,
                interpretation="Final Intrinsic Value per share.",
                variables_map={
                    "Equity": VariableInfo(
                        symbol="Eq", value=equity_value, formatted_value=format_smart_number(equity_value),
                        source=VariableSource.CALCULATED
                    ),
                    "Shares": VariableInfo(
                        symbol="Shares", value=shares, formatted_value=f"{shares:,.0f}",
                        source=VariableSource.SYSTEM, description=SharedTexts.INP_SHARES
                    )
                }
            )

        return final_iv, step