"""
src/valuation/options/sensitivity.py

SENSITIVITY ANALYSIS RUNNER (DETERMINISTIC)
===========================================
Role: Executes stress-tests on the Valuation Model by varying key drivers.
Logic: 2D Matrix generation (Heatmap) iterating over WACC (X) and Growth (Y).
Architecture: Visitor Pattern - Runs the strategy multiple times in 'Silent Mode'.

Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
import numpy as np
from typing import List, Any

from src.exceptions import CalculationError, ModelDivergenceError
from src.models.parameters.base_parameter import Parameters
from src.models.results.options import SensitivityResults
from src.valuation.strategies.abstract import ValuationStrategy

# Imports centralisés pour i18n et Config
from src.config.settings import SIMULATION_CONFIG
from src.config.constants import ModelDefaults
from src.i18n import QuantTexts

logger = logging.getLogger(__name__)


class SensitivityRunner:
    """
    Orchestrates the generation of the Sensitivity Matrix.
    """

    def __init__(self, strategy: ValuationStrategy):
        """
        Parameters
        ----------
        strategy : ValuationStrategy
            The instantiated strategy to be stressed (e.g., StandardFCFFStrategy).
            Note: The runner will temporarily mutate the strategy's parameters.
        """
        self.strategy = strategy

    def execute(self, base_params: Parameters, financials: Any) -> SensitivityResults:
        """
        Runs the sensitivity loops.

        Parameters
        ----------
        base_params : Parameters
            The fully resolved parameters from the Main Run.
        financials : Company
            The financial data (immutable).

        Returns
        -------
        SensitivityResults
            The 2D matrix structure ready for UI rendering.
        """
        cfg = base_params.extensions.sensitivity

        # 1. Define Ranges (Axis X & Y)
        wacc_center = self._get_center_wacc(base_params)
        growth_center = self._get_center_growth(base_params)

        # Generate vectors (e.g. [7.5%, 8.0%, 8.5%, 9.0%, 9.5%])
        # We use linspace to get equidistant steps around the center
        wacc_steps = np.linspace(
            wacc_center - cfg.wacc_span,
            wacc_center + cfg.wacc_span,
            cfg.steps
        ).tolist()

        growth_steps = np.linspace(
            growth_center - cfg.growth_span,
            growth_center + cfg.growth_span,
            cfg.steps
        ).tolist()

        # 2. Execution Loop (The Matrix)
        matrix_values: List[List[float]] = []

        # We clone params once to avoid polluting the main object
        # Note: In a high-perf context, we might modify in place and rollback,
        # but deepcopy is safer for correctness.
        work_params = base_params.model_copy(deep=True)

        # Suppress Logs during the loop (Context Manager required in QuantLogger)
        # with QuantLogger.silent_mode():  <-- To implement later
        for g_val in reversed(growth_steps):  # Y-Axis usually goes Top-Down visually
            row_values: List[float] = []

            # Apply Y-Axis Mutation
            self._apply_growth(work_params, g_val)

            for w_val in wacc_steps:
                # Apply X-Axis Mutation
                self._apply_wacc(work_params, w_val)

                try:
                    # Run Strategy (Silent Mode implied by architecture if we disable glass_box)
                    self.strategy.glass_box_enabled = False
                    res = self.strategy.execute(financials, work_params)
                    row_values.append(res.intrinsic_value_per_share)

                except (CalculationError, ModelDivergenceError, ValueError, ZeroDivisionError):
                    # If calculation fails (divergence, negative flows, math error), put 0.0
                    row_values.append(0.0)

            matrix_values.append(row_values)

        # Restore Glass Box for future use if instance is shared
        self.strategy.glass_box_enabled = True

        # 3. Packaging Results
        # Center value is re-calculated or taken from the main run?
        # Ideally, it's the value at the center indices.
        center_idx = len(wacc_steps) // 2
        # Since we reversed Y loop, the center Y index is also reversed
        center_val = matrix_values[center_idx][center_idx]

        return SensitivityResults(
            x_axis_name=QuantTexts.AXIS_WACC,
            y_axis_name=QuantTexts.AXIS_GROWTH,
            x_values=wacc_steps,
            y_values=list(reversed(growth_steps)),  # Match the visual row order
            values=matrix_values,
            center_value=center_val,
            sensitivity_score=self._compute_volatility_score(matrix_values)
        )

    @staticmethod
    def _get_center_wacc(params: Parameters) -> float:
        """Extracts the effective Discount Rate from parameters."""
        # Note: This implies the strategy has populated the Common Rates properly
        # For Equity models (FCFE), this should be Cost of Equity.
        # We assume the main run has already harmonized this in params.common.rates
        r = params.common.rates
        if r.manual_cost_of_equity: return r.manual_cost_of_equity
        # Fallback logic needs to match what the engine calculated.
        # Ideally, we should pass the 'calculated wacc' from the main result,
        # but params is the input.
        # Simplification: We look at the override or the inputs.
        return r.wacc_override or SIMULATION_CONFIG.default_wacc_fallback

    @staticmethod
    def _get_center_growth(params: Parameters) -> float:
        """Extracts the effective Terminal Growth from parameters."""
        return params.strategy.terminal_value.perpetual_growth_rate or ModelDefaults.DEFAULT_TERMINAL_GROWTH

    @staticmethod
    def _apply_wacc(params: Parameters, value: float) -> None:
        """Mutates the WACC/Ke in the parameters object."""
        # We force the override to ensure the strategy uses exactly this value
        # regardless of its internal CAPM calculation.
        params.common.rates.wacc_override = value
        params.common.rates.manual_cost_of_equity = value  # For Equity models

    @staticmethod
    def _apply_growth(params: Parameters, value: float) -> None:
        """Mutates the Growth in the parameters object."""
        params.strategy.terminal_value.perpetual_growth_rate = value

    @staticmethod
    def _compute_volatility_score(matrix: List[List[float]]) -> float:
        """Calculates a simple spread metric: (Max - Min) / Mean."""
        flat = [v for row in matrix for v in row if v > 0]
        if not flat: return 0.0
        return (max(flat) - min(flat)) / (sum(flat) / len(flat))