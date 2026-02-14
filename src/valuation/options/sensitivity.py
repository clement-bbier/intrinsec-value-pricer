from __future__ import annotations

import logging
from typing import Any

import numpy as np

# Centralized imports
from src.config.constants import ModelDefaults
from src.core.exceptions import CalculationError
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.strategies import GrahamParameters
from src.models.results.options import SensitivityResults
from src.valuation.strategies.interface import IValuationRunner

logger = logging.getLogger(__name__)


class SensitivityRunner:
    """Orchestrates the generation of the Sensitivity Matrix."""

    def __init__(self, strategy: IValuationRunner):
        self.strategy = strategy

    def execute(self, base_params: Parameters, financials: Any) -> SensitivityResults | None:
        cfg = base_params.extensions.sensitivity
        if not cfg.enabled:
            return None

        # 1. Define Ranges
        wacc_center = self._get_center_wacc(base_params)
        growth_center = self._get_center_growth(base_params)

        wacc_steps = np.linspace(wacc_center - cfg.wacc_span, wacc_center + cfg.wacc_span, cfg.steps).tolist()

        growth_steps = np.linspace(growth_center - cfg.growth_span, growth_center + cfg.growth_span, cfg.steps).tolist()

        matrix_values: list[list[float]] = []
        work_params = base_params.model_copy(deep=True)

        # 2. Execution Loop
        for g_val in reversed(growth_steps):
            row_values: list[float] = []
            self._apply_growth(work_params, g_val)

            for w_val in wacc_steps:
                self._apply_wacc(work_params, w_val)
                try:
                    self.strategy.glass_box_enabled = False
                    res = self.strategy.execute(financials, work_params)
                    row_values.append(res.results.common.intrinsic_value_per_share)
                except (CalculationError, ValueError, ZeroDivisionError):
                    # Note: Sensitivity analysis explores edge cases (g >= WACC).
                    # Guardrails validate the base case, but sensitivity needs to handle all scenarios.
                    # Return NaN instead of 0.0 to clearly indicate invalid computation (not a $0 valuation).
                    row_values.append(np.nan)

            matrix_values.append(row_values)

        self.strategy.glass_box_enabled = True

        # 3. Packaging
        center_idx = len(wacc_steps) // 2
        return SensitivityResults(
            x_axis_name="WACC / Cost of Equity",
            y_axis_name="Terminal Growth",
            x_values=wacc_steps,
            y_values=list(reversed(growth_steps)),
            values=matrix_values,
            center_value=matrix_values[center_idx][center_idx],
            sensitivity_score=self._compute_volatility_score(matrix_values),
        )

    @staticmethod
    def _get_center_wacc(params: Parameters) -> float:
        r = params.common.rates
        return r.wacc or r.cost_of_equity or ModelDefaults.DEFAULT_WACC

    @staticmethod
    def _get_center_growth(params: Parameters) -> float:
        if hasattr(params.strategy, "terminal_value"):
            return params.strategy.terminal_value.perpetual_growth_rate or ModelDefaults.DEFAULT_TERMINAL_GROWTH
        # Special case: Graham model
        if isinstance(params.strategy, GrahamParameters):
            return params.strategy.growth_estimate or ModelDefaults.DEFAULT_GROWTH_RATE
        return ModelDefaults.DEFAULT_TERMINAL_GROWTH

    @staticmethod
    def _apply_wacc(params: Parameters, value: float) -> None:
        params.common.rates.wacc = value
        params.common.rates.cost_of_equity = value

    @staticmethod
    def _apply_growth(params: Parameters, value: float) -> None:
        if hasattr(params.strategy, "terminal_value"):
            params.strategy.terminal_value.perpetual_growth_rate = value
        elif isinstance(params.strategy, GrahamParameters):
            params.strategy.growth_estimate = value

    @staticmethod
    def _compute_volatility_score(matrix: list[list[float]]) -> float:
        flat = [v for row in matrix for v in row if not np.isnan(v) and v > 0]
        if not flat:
            return 0.0
        return (max(flat) - min(flat)) / (sum(flat) / len(flat))
