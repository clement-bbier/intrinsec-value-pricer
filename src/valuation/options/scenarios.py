"""
src/valuation/options/scenarios.py

SCENARIO ANALYSIS RUNNER
========================
Role: Evaluates discrete deterministic cases (Bear/Base/Bull).
Logic: Iterates through defined scenarios, applying overrides and computing weighted average.
Architecture: Runner Pattern.

Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from src.models.parameters.base_parameter import Parameters
from src.models.company import Company
from src.models.results.options import ScenariosResults, ScenarioOutcome
from src.valuation.strategies.abstract import ValuationStrategy
from src.exceptions import CalculationError

logger = logging.getLogger(__name__)


class ScenariosRunner:
    """
    Executes multiple deterministic valuation runs based on scenario overrides.
    """

    def __init__(self, strategy: ValuationStrategy):
        self.strategy = strategy

    def execute(self, params: Parameters, financials: Company) -> Optional[ScenariosResults]:
        """
        Runs the defined scenarios.
        """
        sc_cfg = params.extensions.scenarios

        if not sc_cfg.enabled or not sc_cfg.cases:
            return None

        outcomes: List[ScenarioOutcome] = []
        weighted_sum = 0.0
        total_prob = 0.0

        # Disable audit for these sub-runs
        self.strategy.glass_box_enabled = False

        for case in sc_cfg.cases:
            try:
                # 1. Prepare Environment
                case_params = params.model_copy(deep=True)

                # 2. Apply Overrides (if defined in the scenario)
                # Growth Override
                if case.growth_override is not None:
                    # Generic application - assumes strategy has projection capability
                    if hasattr(case_params.strategy, 'terminal_value'):
                        case_params.strategy.terminal_value.perpetual_growth_rate = case.growth_override

                # Margin Override (conceptual - requires strategy support)
                # ...

                # 3. Run Strategy
                res = self.strategy.execute(financials, case_params)
                iv = res.intrinsic_value_per_share

                # 4. Collect Result
                prob = case.probability or 0.0
                outcomes.append(ScenarioOutcome(
                    label=case.name,
                    intrinsic_value=iv,
                    upside_pct=0.0,  # Computed later against market price
                    probability=prob
                ))

                weighted_sum += iv * prob
                total_prob += prob

            except (CalculationError, ValueError):
                logger.warning(f"[Scenarios] Failed to calculate case: {case.name}")
                continue

        # Re-enable audit
        self.strategy.glass_box_enabled = True

        if not outcomes:
            return None

        # Normalize expected value if probabilities don't sum to 1
        expected_iv = weighted_sum / total_prob if total_prob > 0 else 0.0

        return ScenariosResults(
            expected_intrinsic_value=expected_iv,
            outcomes=outcomes
        )