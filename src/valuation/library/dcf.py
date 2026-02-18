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

# Atomic Math Imports
from src.computation.financial_math import (
    apply_dilution_adjustment,
    calculate_dilution_factor,
    calculate_discount_factors,
    calculate_fcf_tax_adjustment_factor,
    calculate_terminal_value_exit_multiple,
    calculate_terminal_value_gordon,
    calculate_wacc_for_terminal_value,
    normalize_terminal_flow_for_stable_state,
)

# Configuration & i18n
from src.config.constants import MacroDefaults, ModelDefaults
from src.core.formatting import format_smart_number
from src.i18n import RegistryTexts, SharedTexts, StrategyFormulas, StrategyInterpretations, StrategySources
from src.models.company import Company
from src.models.enums import TerminalValueMethod, VariableSource
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.parameters.base_parameter import Parameters


class DCFLibrary:
    """
    Stateless functional library for DCF-specific calculations.
    """

    @staticmethod
    def project_flows_simple(base_flow: float, params: Parameters) -> tuple[list[float], CalculationStep]:
        """
        Projects cash flows using a standard growth rate with linear fade-down.
        """
        # --- FIX: Access Strategy Parameters (Polymorphic) ---
        strat = params.strategy

        # Safe access to growth attributes depending on the model (FCFF vs FCFE)
        # We look for 'growth_rate_p1' (Standard DCF) or 'growth_rate' (FCFE/DDM)
        g_start = (
            getattr(strat, "growth_rate_p1", getattr(strat, "growth_rate", None)) or ModelDefaults.DEFAULT_GROWTH_RATE
        )

        # Access Terminal Value params
        tv_params = strat.terminal_value
        g_term = tv_params.perpetual_growth_rate or ModelDefaults.DEFAULT_TERMINAL_GROWTH

        # Access Projection Years
        years = getattr(strat, "projection_years", None) or ModelDefaults.DEFAULT_PROJECTION_YEARS

        # 2. Projection Loop (Linear Convergence)
        flows = []
        current_flow = base_flow

        for t in range(1, years + 1):
            if years > 1:
                alpha = (t - 1) / (years - 1)
                current_g = g_start * (1 - alpha) + g_term * alpha
            else:
                current_g = g_start

            current_flow *= 1.0 + current_g
            flows.append(current_flow)

        # 3. Trace Building
        variables = {
            "FCF_0": VariableInfo(
                symbol="FCF_0", value=base_flow, source=VariableSource.SYSTEM, description="Base Year Flow"
            ),
            "g_start": VariableInfo(
                symbol="g_start",
                value=g_start,
                formatted_value=f"{g_start:.1%}",
                source=VariableSource.MANUAL_OVERRIDE,
                description="Initial Growth Rate",
            ),
            "g_term": VariableInfo(
                symbol="g_term",
                value=g_term,
                formatted_value=f"{g_term:.1%}",
                source=VariableSource.MANUAL_OVERRIDE,
                description="Terminal Growth Target",
            ),
            "n": VariableInfo(
                symbol="n",
                value=float(years),
                source=VariableSource.MANUAL_OVERRIDE,
                description=SharedTexts.INP_PROJ_YEARS,
            ),
        }

        step = CalculationStep(
            step_key="FCF_PROJ",
            label=RegistryTexts.DCF_PROJ_L,
            theoretical_formula=StrategyFormulas.FCF_PROJECTION,
            actual_calculation=f"{format_smart_number(base_flow)} × (Linear Convergence {g_start:.1%} → {g_term:.1%})",
            result=sum(flows),
            interpretation=StrategyInterpretations.PROJ.format(years=years, g=g_start),
            source=StrategySources.YAHOO_TTM_SIMPLE,
            variables_map=variables,
        )

        return flows, step

    @staticmethod
    def project_flows_manual(base_flow: float, growth_vector: list[float]) -> tuple[list[float], CalculationStep]:
        """
        Projects flows using an explicit year-by-year growth vector.
        """
        flows = []
        current_flow = base_flow
        years = len(growth_vector)

        for _, g_rate in enumerate(growth_vector):
            current_flow *= 1.0 + g_rate
            flows.append(current_flow)

        avg_growth = sum(growth_vector) / years if years > 0 else 0.0

        variables = {
            "FCF_0": VariableInfo(
                symbol="FCF_0",
                value=base_flow,
                source=VariableSource.SYSTEM,
                description="Base Year Flow",
            ),
            "g_avg": VariableInfo(
                symbol="g_avg",
                value=avg_growth,
                formatted_value=f"{avg_growth:.1%}",
                source=VariableSource.MANUAL_OVERRIDE,
                description="Average Custom Growth",
            ),
        }

        step = CalculationStep(
            step_key="FCF_PROJ_MANUAL",
            label=RegistryTexts.DCF_PROJ_L,
            theoretical_formula=StrategyFormulas.FLOW_PROJECTION,
            actual_calculation=f"Manual Vector Projection ({years} years)",
            result=sum(flows),
            interpretation=f"Projection manuelle experte sur {years} ans (Moyenne: {avg_growth:.1%})",
            source=StrategySources.MANUAL_OVERRIDE,
            variables_map=variables,
        )

        return flows, step

    @staticmethod
    def project_flows_revenue_model(
        base_revenue: float, current_margin: float, target_margin: float, params: Parameters
    ) -> tuple[list[float], list[float], list[float], CalculationStep]:
        """
        Projects FCF based on Revenue Growth and Margin Convergence.
        """
        # Access Strategy Parameters (Specifically FCFFGrowthParameters)
        strat = params.strategy

        # Safety Fallbacks
        g_start = getattr(strat, "revenue_growth_rate", None) or ModelDefaults.DEFAULT_GROWTH_RATE
        tv_params = getattr(strat, "terminal_value", None)
        g_term = tv_params.perpetual_growth_rate if tv_params else ModelDefaults.DEFAULT_TERMINAL_GROWTH
        years = getattr(strat, "projection_years", None) or ModelDefaults.DEFAULT_PROJECTION_YEARS
        manual_vector = getattr(strat, "manual_growth_vector", None)

        revenues = []
        margins = []
        fcfs = []

        current_rev = base_revenue

        for t in range(1, years + 1):
            # A. Revenue Growth Logic
            if manual_vector and (t - 1) < len(manual_vector):
                current_g = manual_vector[t - 1]
            else:
                if years > 1:
                    alpha = (t - 1) / (years - 1)
                    current_g = g_start * (1 - alpha) + g_term * alpha
                else:
                    current_g = g_start

            current_rev *= 1.0 + current_g
            revenues.append(current_rev)

            # B. Margin Convergence
            if years > 0:
                progress = t / years
                current_m = current_margin * (1 - progress) + target_margin * progress
            else:
                current_m = target_margin

            margins.append(current_m)
            fcfs.append(current_rev * current_m)

        variables = {
            "Rev_0": VariableInfo(
                symbol="Rev_0",
                value=base_revenue,
                source=VariableSource.SYSTEM,
                description="Base Revenue",
            ),
            "M_target": VariableInfo(
                symbol="M_n",
                value=target_margin,
                formatted_value=f"{target_margin:.1%}",
                source=VariableSource.MANUAL_OVERRIDE,
                description="Target FCF Margin",
            ),
            "g_rev": VariableInfo(
                symbol="g_rev",
                value=g_start,
                formatted_value=f"{g_start:.1%}",
                source=VariableSource.MANUAL_OVERRIDE,
                description="Initial Revenue Growth",
            ),
        }

        step = CalculationStep(
            step_key="REV_MARGIN_CONV",
            label=RegistryTexts.GROWTH_MARGIN_L,
            theoretical_formula=StrategyFormulas.GROWTH_MARGIN_CONV,
            actual_calculation=f"Revenue Growth & Margin Convergence ({current_margin:.1%} -> {target_margin:.1%})",
            result=sum(fcfs),
            interpretation=StrategyInterpretations.GROWTH_MARGIN,
            source=StrategySources.CALCULATED,
            variables_map=variables,
        )

        return fcfs, revenues, margins, step

    @staticmethod
    def compute_terminal_value(
        final_flow: float, discount_rate: float, params: Parameters, financials: Company
    ) -> tuple[float, CalculationStep, list]:
        """
        Calculates Terminal Value based on Strategy selection.

        Combines:
        1. Tax Convergence (Agent #34): Adjusts WACC and FCF for marginal tax rate
        2. Golden Rule: Adjusts FCF for sustainable reinvestment based on ROIC

        Parameters
        ----------
        final_flow : float
            The last projected cash flow from the explicit period.
        discount_rate : float
            The discount rate for the explicit period (WACC or Ke).
        params : Parameters
            User-defined or automated parameters.
        financials : Company
            Financial snapshots. Used to recalculate WACC with marginal tax rate for TV
            when applicable (FCFF strategies). Required for all strategies for consistency.

        Returns
        -------
        tuple[float, CalculationStep, list]
            Terminal value, calculation step for audit trail, and list of diagnostic events.

        Notes
        -----
        If marginal_tax_rate is provided in params and financials is available,
        the terminal value will be calculated using a WACC that applies the
        marginal tax rate instead of the effective tax rate. This reflects that
        temporary tax benefits are not perpetual.

        For equity-based strategies (DDM, FCFE), the financials parameter is still
        required but marginal tax adjustments don't apply.

        Diagnostics are generated for:
        - Beta adjustment skipped due to 5% threshold
        - Operating margin fallback when EBIT/Revenue data unavailable
        """
        tv_params = params.strategy.terminal_value
        method = tv_params.method or TerminalValueMethod.GORDON_GROWTH

        if method == TerminalValueMethod.GORDON_GROWTH:
            g_perp = tv_params.perpetual_growth_rate or ModelDefaults.DEFAULT_TERMINAL_GROWTH
            roic_stable = tv_params.roic_stable  # Can be None for Golden Rule

            # Step 1: Tax Convergence - Use marginal tax rate for terminal value WACC if available
            tv_discount_rate = discount_rate
            tax_adjustment_factor = 1.0
            tv_diagnostics = []  # Collect diagnostics from TV calculation
            marginal_tax_rate = getattr(params.common.rates, 'marginal_tax_rate', None)

            if marginal_tax_rate is not None and financials is not None:
                # Recalculate WACC using marginal tax rate for terminal value
                wacc_tv_breakdown = calculate_wacc_for_terminal_value(financials, params)
                tv_discount_rate = wacc_tv_breakdown.wacc

                # Collect WACC diagnostics (e.g., beta adjustment skipped)
                if hasattr(wacc_tv_breakdown, 'diagnostics') and wacc_tv_breakdown.diagnostics:
                    tv_diagnostics.extend(wacc_tv_breakdown.diagnostics)

                # Calculate tax adjustment factor for FCF
                # This adjusts FCF_n to reflect the marginal tax rate in perpetuity
                # Pass financials to use real operating margin
                effective_tax_rate = params.common.rates.tax_rate or MacroDefaults.DEFAULT_TAX_RATE
                if effective_tax_rate != marginal_tax_rate:
                    # Request diagnostics to detect fallback usage
                    tax_adjustment_factor, fcf_diagnostics = calculate_fcf_tax_adjustment_factor(
                        effective_tax_rate=effective_tax_rate,
                        marginal_tax_rate=marginal_tax_rate,
                        financials=financials,  # Pass financials for real margin calculation
                        return_diagnostics=True
                    )
                    # Collect FCF adjustment diagnostics (e.g., margin fallback used)
                    if fcf_diagnostics:
                        tv_diagnostics.extend(fcf_diagnostics)

            # Step 2: Golden Rule - Normalize terminal flow for sustainable reinvestment
            adjusted_flow, reinvestment_rate = normalize_terminal_flow_for_stable_state(
                final_flow, g_perp, roic_stable
            )

            # Step 3: Calculate terminal value using adjusted flow with tax factor
            tv = calculate_terminal_value_gordon(adjusted_flow, tv_discount_rate, g_perp, tax_adjustment_factor)

            # Build variables map
            variables_map = {
                "g_perp": VariableInfo(
                    symbol="g",
                    value=g_perp,
                    formatted_value=f"{g_perp:.2%}",
                    source=VariableSource.MANUAL_OVERRIDE,
                    description=SharedTexts.INP_PERP_G,
                ),
                "r": VariableInfo(
                    symbol="r",
                    value=tv_discount_rate,
                    formatted_value=f"{tv_discount_rate:.2%}",
                    source=VariableSource.CALCULATED,
                    description="Discount Rate",
                ),
            }

            # Add Golden Rule details if adjustment was applied
            if reinvestment_rate > 0:
                variables_map["FCF_unadjusted"] = VariableInfo(
                    symbol="FCF_n",
                    value=final_flow,
                    formatted_value=format_smart_number(final_flow),
                    source=VariableSource.CALCULATED,
                    description=SharedTexts.LABEL_FCF_BEFORE_ADJUSTMENT,
                )
                variables_map["reinvestment_rate"] = VariableInfo(
                    symbol="reinv",
                    value=reinvestment_rate,
                    formatted_value=f"{reinvestment_rate:.2%}",
                    source=VariableSource.CALCULATED,
                    description=SharedTexts.LABEL_REINVESTMENT_RATE,
                )
                variables_map["ROIC_stable"] = VariableInfo(
                    symbol="ROIC",
                    value=roic_stable,
                    formatted_value=f"{roic_stable:.2%}" if roic_stable else "N/A",
                    source=VariableSource.MANUAL_OVERRIDE,
                    description=SharedTexts.LABEL_ROIC_STABLE,
                )
                variables_map["FCF_adjusted"] = VariableInfo(
                    symbol="FCF_adj",
                    value=adjusted_flow,
                    formatted_value=format_smart_number(adjusted_flow),
                    source=VariableSource.CALCULATED,
                    description=SharedTexts.LABEL_FCF_AFTER_ADJUSTMENT,
                )

            # Build calculation string to show all adjustments
            calculation_note = f"({format_smart_number(final_flow)}"
            
            if reinvestment_rate > 0:
                calculation_note += f" × (1 - {reinvestment_rate:.2%})"
            
            calculation_note += f" × (1 + {g_perp:.1%}))"
            
            if tax_adjustment_factor != 1.0:
                calculation_note += f" × {tax_adjustment_factor:.4f}"
            
            calculation_note += f" / ({tv_discount_rate:.1%} - {g_perp:.1%})"

            step = CalculationStep(
                step_key="TV_GORDON",
                label=RegistryTexts.DCF_TV_GORDON_L,
                theoretical_formula=StrategyFormulas.GORDON,
                actual_calculation=calculation_note,
                result=tv,
                interpretation=StrategyInterpretations.TV,
                variables_map=variables_map,
            )
            return tv, step, tv_diagnostics

        else:  # EXIT_MULTIPLE
            multiple = tv_params.exit_multiple or ModelDefaults.DEFAULT_EXIT_MULTIPLE
            tv = calculate_terminal_value_exit_multiple(final_flow, multiple)

            step = CalculationStep(
                step_key="TV_MULTIPLE",
                label=RegistryTexts.DCF_TV_MULT_L,
                theoretical_formula=StrategyFormulas.TERMINAL_MULTIPLE,
                actual_calculation=f"{format_smart_number(final_flow)} × {multiple:.1f}x",
                result=tv,
                interpretation=StrategyInterpretations.TV,
                variables_map={
                    "multiple": VariableInfo(
                        symbol="M",
                        value=multiple,
                        formatted_value=f"{multiple:.1f}x",
                        source=VariableSource.MANUAL_OVERRIDE,
                        description="Exit Multiple",
                    )
                },
            )
            return tv, step, []  # No diagnostics for exit multiple method
                variables_map={
                    "M": VariableInfo(
                        symbol="M",
                        value=multiple,
                        formatted_value=f"{multiple:.1f}x",
                        source=VariableSource.MANUAL_OVERRIDE,
                        description="Exit Multiple",
                    )
                },
            )
            return tv, step

    @staticmethod
    def compute_discounting(
        flows: list[float], terminal_value: float, discount_rate: float
    ) -> tuple[float, CalculationStep]:
        """Calculates the Enterprise Value (NPV of Flows + PV of TV)."""
        years_count = len(flows)
        factors = calculate_discount_factors(discount_rate, years_count)
        sum_pv_flows = sum(f * d for f, d in zip(flows, factors))
        pv_tv = terminal_value * factors[-1]
        total_ev = sum_pv_flows + pv_tv

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
                    symbol="r",
                    value=discount_rate,
                    formatted_value=f"{discount_rate:.2%}",
                    source=VariableSource.CALCULATED,
                    description="Discount Rate",
                ),
                "ΣPV": VariableInfo(
                    symbol="ΣPV",
                    value=sum_pv_flows,
                    source=VariableSource.CALCULATED,
                    description="PV of Explicit Period",
                ),
                "PV_TV": VariableInfo(
                    symbol="PV_TV",
                    value=pv_tv,
                    source=VariableSource.CALCULATED,
                    description="PV of Terminal Value",
                ),
            },
        )
        return total_ev, step

    @staticmethod
    def compute_value_per_share(equity_value: float, params: Parameters) -> tuple[float, CalculationStep]:
        """Calculates final price per share, applying SBC dilution adjustment."""
        # Fix: Capital structure comes from common.capital
        shares = params.common.capital.shares_outstanding or ModelDefaults.DEFAULT_SHARES_OUTSTANDING
        base_iv = equity_value / shares

        # Fix: Dilution rate is stored in common.capital (from Model Batch)
        dilution_rate = params.common.capital.annual_dilution_rate or 0.0
        # Fix: Years come from strategy
        years = getattr(params.strategy, "projection_years", ModelDefaults.DEFAULT_PROJECTION_YEARS)

        dilution_factor = calculate_dilution_factor(dilution_rate, years)
        final_iv = apply_dilution_adjustment(base_iv, dilution_factor)

        if dilution_factor > 1.0:
            step = CalculationStep(
                step_key="VALUE_PER_SHARE_DILUTED",
                label=RegistryTexts.SBC_L,
                theoretical_formula=StrategyFormulas.SBC_DILUTION,
                actual_calculation=f"{format_smart_number(base_iv)} / (1 + {dilution_rate:.1%})^{years}",
                result=final_iv,
                interpretation=StrategyInterpretations.SBC_DILUTION_INTERP.format(pct=f"{(dilution_factor - 1):.1%}"),
                variables_map={
                    "Shares": VariableInfo(
                        symbol="Shares",
                        value=shares,
                        formatted_value=f"{shares:,.0f}",
                        source=VariableSource.SYSTEM,
                        description=SharedTexts.INP_SHARES,
                    ),
                    "Dilution": VariableInfo(
                        symbol="δ",
                        value=dilution_rate,
                        formatted_value=f"{dilution_rate:.1%}",
                        source=VariableSource.MANUAL_OVERRIDE,
                        description="Annual SBC Dilution",
                    ),
                },
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
                        symbol="Eq",
                        value=equity_value,
                        source=VariableSource.CALCULATED,
                    ),
                    "Shares": VariableInfo(
                        symbol="Shares",
                        value=shares,
                        formatted_value=f"{shares:,.0f}",
                        source=VariableSource.SYSTEM,
                    ),
                },
            )

        return final_iv, step
