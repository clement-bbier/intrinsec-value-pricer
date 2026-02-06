"""
src/valuation/library/rim.py

RESIDUAL INCOME MODEL (RIM) LIBRARY
===================================
Role: Specialized logic for Excess Return models (Banks, Insurance).
Responsibilities:
  - Book Value & RI Projection (Clean Surplus Relation)
  - Terminal Value Calculation (Ohlson with Persistence)
  - Discounting (Ke based) & Anchoring to Current Book Value

Architecture: Stateless Functional Library.
Input: Resolved Parameters + Cost of Equity (Ke).
Output: Computed values + CalculationSteps.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
"""

from __future__ import annotations

from typing import Tuple, List

from src.models.parameters.base_parameter import Parameters
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.enums import VariableSource
from src.utilities.formatting import format_smart_number

# Atomic Math Imports
from src.computation.financial_math import (
    calculate_rim_vectors,
    calculate_discount_factors
)

# Configuration & i18n
from src.config.constants import ModelDefaults
from src.i18n import (
    RegistryTexts,
    StrategyFormulas,
    StrategyInterpretations,
    StrategySources
)


class RIMLibrary:
    """
    Stateless functional library for Residual Income calculations.
    """

    @staticmethod
    def project_residual_income(
            current_book_value: float,
            cost_of_equity: float,
            params: Parameters
    ) -> Tuple[List[float], List[float], List[float], CalculationStep]:
        """
        Projects Net Income, Book Values, and Residual Incomes based on Clean Surplus.

        Logic:
          1. Project Net Income (NI) using growth.
          2. Derive Book Value (BV) from Retention (1 - Payout).
          3. Calculate RI = NI - (BV_prev * Ke).

        Returns
        -------
        Tuple[List[float], List[float], List[float], CalculationStep]
            (Residual Incomes, Book Values, Net Incomes, Audit Step).
        """
        g = params.growth
        s = params.strategy

        # 1. Inputs
        # Note: Ideally, we project NI based on ROE, but for simplicity/consistency with DCF,
        # we often project NI directly using growth rate starting from NI_0.
        ni_base = s.net_income_ttm or 0.0
        g_rate = g.fcf_growth_rate or ModelDefaults.DEFAULT_GROWTH_RATE
        years = g.projection_years or ModelDefaults.DEFAULT_PROJECTION_YEARS
        payout = s.dividend_payout_ratio if s.dividend_payout_ratio is not None else 0.0

        # 2. Project Net Income Series (Simple Growth)
        # TODO: Could be refactored to use a shared 'project_series' utility if strictly DRY
        projected_ni = []
        current_ni = ni_base
        for _ in range(years):
            current_ni *= (1.0 + g_rate)
            projected_ni.append(current_ni)

        # 3. Calculate Vectors (RI and BV)
        residual_incomes, book_values = calculate_rim_vectors(
            current_bv=current_book_value,
            ke=cost_of_equity,
            earnings=projected_ni,
            payout=payout
        )

        # 4. Trace
        variables = {
            "B_0": VariableInfo(
                symbol="B_0", value=current_book_value,
                source=VariableSource.SYSTEM, description="Current Book Value (Equity)"
            ),
            "Ke": VariableInfo(
                symbol="Ke", value=cost_of_equity, formatted_value=f"{cost_of_equity:.2%}",
                source=VariableSource.CALCULATED, description="Cost of Equity"
            ),
            "Payout": VariableInfo(
                symbol="p", value=payout, formatted_value=f"{payout:.1%}",
                source=VariableSource.MANUAL_OVERRIDE if s.dividend_payout_ratio is not None else VariableSource.DEFAULT,
                description="Dividend Payout Ratio"
            )
        }

        # Sum of RI for indicative display
        sum_ri = sum(residual_incomes)

        step = CalculationStep(
            step_key="RIM_PROJ",
            label=RegistryTexts.RIM_RI_L,
            theoretical_formula=StrategyFormulas.RIM_RI,
            actual_calculation=f"Sum(RI) over {years} years = {format_smart_number(sum_ri)}",
            result=sum_ri,
            interpretation=StrategyInterpretations.RIM_PROJ.format(years=years),
            source=StrategySources.CALCULATED,
            variables_map=variables
        )

        return residual_incomes, book_values, projected_ni, step

    @staticmethod
    def compute_terminal_value_ohlson(
            final_ri: float,
            cost_of_equity: float,
            params: Parameters
    ) -> Tuple[float, CalculationStep]:
        """
        Calculates Terminal Value using the Ohlson Model with Persistence Factor (omega).

        Formula: TV = (RI_n * ω) / (1 + Ke - ω)

        Parameters
        ----------
        final_ri : float
            Residual Income in the last explicit year.
        cost_of_equity : float
            Cost of Equity (Ke).
        params : Parameters
            Contains persistence factor (omega).

        Returns
        -------
        Tuple[float, CalculationStep]
            Terminal Value and audit step.
        """
        # Resolve Omega (Persistence)
        # Default 0.60 implies abnormal returns fade but persist somewhat
        omega = params.strategy.persistence_factor
        if omega is None:
            omega = ModelDefaults.DEFAULT_PERSISTENCE_FACTOR

        # Safety: Omega cannot equal (1 + Ke) to avoid division by zero
        # In reality, Omega is usually [0, 1].
        denominator = (1.0 + cost_of_equity) - omega
        if denominator == 0:
            denominator = 0.001  # Safety clamp

        tv = (final_ri * omega) / denominator

        variables = {
            "RI_n": VariableInfo(
                symbol="RI_n", value=final_ri, formatted_value=format_smart_number(final_ri),
                source=VariableSource.CALCULATED, description="Final Year Residual Income"
            ),
            "ω": VariableInfo(
                symbol="ω", value=omega, formatted_value=f"{omega:.2f}",
                source=VariableSource.MANUAL_OVERRIDE if params.strategy.persistence_factor else VariableSource.DEFAULT,
                description="Ohlson Persistence Factor"
            ),
            "Ke": VariableInfo(
                symbol="Ke", value=cost_of_equity, formatted_value=f"{cost_of_equity:.2%}",
                source=VariableSource.CALCULATED, description="Cost of Equity"
            )
        }

        step = CalculationStep(
            step_key="TV_OHLSON",
            label=RegistryTexts.RIM_TV_L,
            theoretical_formula=StrategyFormulas.RIM_TV,
            actual_calculation=f"({format_smart_number(final_ri)} × {omega:.2f}) / (1 + {cost_of_equity:.1%} - {omega:.2f})",
            result=tv,
            interpretation=StrategyInterpretations.RIM_PERSISTENCE.format(val=omega),
            variables_map=variables
        )

        return tv, step

    @staticmethod
    def compute_equity_value(
            current_book_value: float,
            residual_incomes: List[float],
            terminal_value: float,
            cost_of_equity: float
    ) -> Tuple[float, CalculationStep]:
        """
        Aggregates components to find Total Equity Value.

        Formula: V = B_0 + Sum(PV(RI)) + PV(TV)
        """
        # 1. Discount Factors
        factors = calculate_discount_factors(cost_of_equity, len(residual_incomes))

        # 2. PV of RIs
        pv_ri = sum(ri * df for ri, df in zip(residual_incomes, factors))

        # 3. PV of TV
        pv_tv = terminal_value * factors[-1]

        # 4. Total Value
        total_equity = current_book_value + pv_ri + pv_tv

        variables = {
            "B_0": VariableInfo(
                symbol="B_0", value=current_book_value, formatted_value=format_smart_number(current_book_value),
                source=VariableSource.SYSTEM
            ),
            "ΣPV_RI": VariableInfo(
                symbol="ΣPV_RI", value=pv_ri, formatted_value=format_smart_number(pv_ri),
                source=VariableSource.CALCULATED, description="PV of Explicit Residual Incomes"
            ),
            "PV_TV": VariableInfo(
                symbol="PV_TV", value=pv_tv, formatted_value=format_smart_number(pv_tv),
                source=VariableSource.CALCULATED, description="PV of Terminal Value"
            )
        }

        step = CalculationStep(
            step_key="RIM_AGGREGATION",
            label=RegistryTexts.RIM_IV_L,
            theoretical_formula=StrategyFormulas.RIM_GLOBAL,
            actual_calculation=f"{format_smart_number(current_book_value)} + {format_smart_number(pv_ri)} + {format_smart_number(pv_tv)}",
            result=total_equity,
            interpretation=StrategyInterpretations.RIM_FINAL,
            source=StrategySources.CALCULATED,
            variables_map=variables
        )

        return total_equity, step