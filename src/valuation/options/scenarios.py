"""
src/valuation/options/scenarios.py

SCENARIO ANALYSIS RUNNER
========================
Role: Evaluates discrete deterministic cases (Bear/Base/Bull).
Logic: Iterates through defined scenarios, applying overrides and computing weighted average.
Architecture: Runner Pattern.

Standard: SOLID, i18n Secured, NumPy Style.
"""

from __future__ import annotations

import logging

from src.core.exceptions import CalculationError
from src.models.company import Company
from src.models.parameters.base_parameter import Parameters
from src.models.results.options import ScenarioOutcome, ScenariosResults
from src.valuation.strategies.interface import IValuationRunner

logger = logging.getLogger(__name__)


class ScenariosRunner:
    """
    Executes multiple deterministic valuation runs based on scenario overrides.

    This runner clones the base parameters for each defined case, applies
    specific overrides (growth, margins), and computes a probability-weighted
    intrinsic value.

    Attributes
    ----------
    strategy : IValuationRunner
        The underlying valuation engine to be executed for each scenario.
    """

    def __init__(self, strategy: IValuationRunner):
        """
        Initialize the ScenariosRunner.

        Parameters
        ----------
        strategy : IValuationRunner
            The strategy instance (e.g., FCFF, DDM) to run scenarios against.
        """
        self.strategy = strategy

    def execute(self, params: Parameters, financials: Company) -> ScenariosResults | None:
        """
        Execute the scenario analysis.

        Iterates through the scenarios defined in parameters, applies overrides,
        calculates intrinsic values, and aggregates results.

        Parameters
        ----------
        params : Parameters
            The root parameter container containing scenario definitions.
        financials : Company
            The financial dataset used for valuation.

        Returns
        -------
        Optional[ScenariosResults]
            A summary of all scenario outcomes and the expected value,
            or None if disabled.
        """
        sc_cfg = params.extensions.scenarios

        if not sc_cfg.enabled or not sc_cfg.cases:
            return None

        outcomes: list[ScenarioOutcome] = []
        weighted_sum = 0.0
        total_prob = 0.0
        market_price = params.structure.current_price or 1.0

        # Optimization: Temporarily disable step-by-step audit for sub-runs
        original_audit_state = getattr(self.strategy, "glass_box_enabled", True)
        self.strategy.glass_box_enabled = False

        for case in sc_cfg.cases:
            try:
                # 1. Environment Isolation
                case_params = params.model_copy(deep=True)

                # 2. Apply Overrides
                # Growth override: applies to terminal value if applicable
                if case.growth_override is not None:
                    if hasattr(case_params.strategy, "terminal_value"):
                        case_params.strategy.terminal_value.perpetual_growth_rate = case.growth_override
                    # Fallback for strategies without explicit terminal value (e.g. Graham)
                    elif hasattr(case_params.strategy, "growth_estimate"):
                        case_params.strategy.growth_estimate = case.growth_override

                # 3. Strategy Execution
                # Note: results are extracted from the common results block
                valuation_res = self.strategy.execute(financials, case_params)
                iv = valuation_res.results.common.intrinsic_value_per_share
                prob = case.probability or 0.0

                # 4. Results Aggregation
                outcomes.append(
                    ScenarioOutcome(
                        label=case.name, intrinsic_value=iv, upside_pct=(iv / market_price) - 1.0, probability=prob
                    )
                )

                weighted_sum += iv * prob
                total_prob += prob

            except (CalculationError, ValueError, AttributeError) as e:
                logger.warning("[Scenarios] Failed to calculate case '%s': %s", case.name, str(e))
                continue

        # Restore original audit state
        self.strategy.glass_box_enabled = original_audit_state

        if not outcomes:
            return None

        # 5. Probability Normalization
        # Ensures a valid expected value even if weights do not sum to 100%
        expected_iv = weighted_sum / total_prob if total_prob > 0 else 0.0

        return ScenariosResults(expected_intrinsic_value=expected_iv, outcomes=outcomes)
