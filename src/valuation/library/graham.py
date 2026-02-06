"""
src/valuation/library/graham.py

GRAHAM FORMULA LIBRARY
======================
Role: Implementation of Benjamin Graham's intrinsic value formulas.
Responsibilities:
  - Revised 1974 Formula Calculation
  - Defensive checking of inputs (AAA Yields, Growth caps)

Architecture: Stateless Functional Library.
Input: Resolved Parameters (EPS, Growth, Rates).
Output: Computed values + CalculationSteps.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
"""

from __future__ import annotations

from typing import Tuple

from src.models.parameters.base_parameter import Parameters
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.enums import VariableSource
from src.utilities.formatting import format_smart_number

# Atomic Math Imports
from src.computation.financial_math import calculate_graham_1974_value

# Configuration & i18n
from src.config.constants import MacroDefaults, ModelDefaults
from src.i18n import (
    RegistryTexts,
    StrategyFormulas,
    StrategyInterpretations,
    StrategySources
)


class GrahamLibrary:
    """
    Stateless functional library for Graham Number & Formula calculations.
    """

    @staticmethod
    def compute_intrinsic_value(
            params: Parameters
    ) -> Tuple[float, CalculationStep]:
        """
        Calculates value using the Graham Formula (1974).

        Formula: V = (EPS * (8.5 + 2g) * 4.4) / Y

        Returns
        -------
        Tuple[float, CalculationStep]
            Price per share and the audit step.
        """
        s = params.strategy

        # 1. Resolve Inputs
        eps = s.eps_normalized or s.eps_ttm or 0.0

        # Graham formula expects growth as an integer (e.g., 10 for 10%),
        # but our math function handles the conversion from decimal if needed.
        # Let's check 'financial_math.py': It takes decimal and does (growth_rate * 100).
        g_decimal = params.growth.fcf_growth_rate or ModelDefaults.DEFAULT_GROWTH_RATE

        # Bond Yield (Y)
        # Use corporate AAA yield if provided in macro, else default
        aaa_yield = params.common.rates.corporate_aaa_yield or MacroDefaults.DEFAULT_CORPORATE_AAA_YIELD

        # 2. Calculation
        iv = calculate_graham_1974_value(eps, g_decimal, aaa_yield)

        # 3. Trace
        variables = {
            "EPS": VariableInfo(
                symbol="EPS", value=eps, formatted_value=format_smart_number(eps),
                source=VariableSource.SYSTEM, description="Normalized Earnings Per Share"
            ),
            "g": VariableInfo(
                symbol="g", value=g_decimal, formatted_value=f"{g_decimal:.1%}",
                source=VariableSource.MANUAL_OVERRIDE if params.growth.fcf_growth_rate else VariableSource.DEFAULT,
                description="Expected Growth Rate"
            ),
            "Y": VariableInfo(
                symbol="Y", value=aaa_yield, formatted_value=f"{aaa_yield:.2%}",
                source=VariableSource.SYSTEM, description="AAA Corporate Bond Yield"
            )
        }

        # Pre-format calculation string for clarity
        g_display = g_decimal * 100.0
        y_display = aaa_yield * 100.0

        step = CalculationStep(
            step_key="GRAHAM_FORMULA",
            label=RegistryTexts.GRAHAM_IV_L,
            theoretical_formula=StrategyFormulas.GRAHAM_1974,
            actual_calculation=f"({format_smart_number(eps)} × (8.5 + 2×{g_display:.1f}) × 4.4) / {y_display:.2f}",
            result=iv,
            interpretation=StrategyInterpretations.GRAHAM_INT,
            source=StrategySources.FORMULA,
            variables_map=variables
        )

        return iv, step