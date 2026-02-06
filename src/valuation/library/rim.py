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
            base_earnings: float,
            cost_of_equity: float,
            params: Parameters
    ) -> Tuple[List[float], List[float], List[float], CalculationStep]:
        """
        Projects Earnings, Book Values, and Residual Incomes based on Clean Surplus.

        Logic:
          1. Project Earnings (EPS or Net Income) using growth (Constant or Vector).
          2. Derive Book Value (BV) from Retention (1 - Payout).
          3. Calculate RI = Earnings - (BV_prev * Ke).

        Parameters
        ----------
        current_book_value : float
            Starting Book Value (Total or Per Share).
        base_earnings : float
            Starting Earnings (Net Income or EPS) used as anchor.
        cost_of_equity : float
            The discount rate (Ke).
        params : Parameters
            Contains growth assumptions and payout ratio.

        Returns
        -------
        Tuple[List[float], List[float], List[float], CalculationStep]
            (Residual Incomes, Book Values, Projected Earnings, Audit Step).
        """
        g = params.growth
        s = params.strategy

        # 1. Inputs Resolution
        g_rate = g.fcf_growth_rate or ModelDefaults.DEFAULT_GROWTH_RATE
        years = g.projection_years or ModelDefaults.DEFAULT_PROJECTION_YEARS

        # Payout Ratio: Critical for Clean Surplus Relation (BV evolution)
        payout = s.dividend_payout_ratio if s.dividend_payout_ratio is not None else ModelDefaults.DEFAULT_PAYOUT_RATIO

        # 2. Project Earnings Series
        # In RIM, growth is typically applied to Earnings, which then drive BV accumulation.
        projected_earnings = []
        current_earn = base_earnings

        # Check for Manual Growth Vector (Hybrid Mode)
        # We access the strategy-specific field safely
        manual_vector = getattr(s, "manual_growth_vector", None)

        for t in range(1, years + 1):
            if manual_vector and (t - 1) < len(manual_vector):
                current_g = manual_vector[t - 1]
            else:
                current_g = g_rate

            current_earn *= (1.0 + current_g)
            projected_earnings.append(current_earn)

        # 3. Calculate Vectors (RI and BV)
        # Uses the Clean Surplus relation: BV_t = BV_{t-1} + NI_t - Div_t
        residual_incomes, book_values = calculate_rim_vectors(
            current_bv=current_book_value,
            ke=cost_of_equity,
            earnings=projected_earnings,
            payout=payout
        )

        # 4. Trace
        sum_ri = sum(residual_incomes)

        variables = {
            "B_0": VariableInfo(
                symbol="B_0", value=current_book_value,
                source=VariableSource.SYSTEM, description="Current Book Value"
            ),
            "E_0": VariableInfo(
                symbol="E_0", value=base_earnings,
                source=VariableSource.SYSTEM, description="Base Earnings (EPS/NI)"
            ),
            "Ke": VariableInfo(
                symbol="Ke", value=cost_of_equity, formatted_value=f"{cost_of_equity:.2%}",
                source=VariableSource.CALCULATED, description="Cost of Equity"
            ),
            "p": VariableInfo(
                symbol="p", value=payout, formatted_value=f"{payout:.1%}",
                source=VariableSource.MANUAL_OVERRIDE if s.dividend_payout_ratio is not None else VariableSource.DEFAULT,
                description="Payout Ratio"
            )
        }

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

        return residual_incomes, book_values, projected_earnings, step

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
        omega = params.strategy.persistence_factor or ModelDefaults.DEFAULT_PERSISTENCE_FACTOR

        # Safety: Omega cannot equal (1 + Ke)
        denominator = (1.0 + cost_of_equity) - omega
        if abs(denominator) < 1e-6:
            denominator = 0.001

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
            source=StrategySources.CALCULATED,
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