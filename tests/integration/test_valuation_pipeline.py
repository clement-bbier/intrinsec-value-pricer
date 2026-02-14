"""
tests/integration/test_valuation_pipeline.py

INTEGRATION TEST: FULL PIPELINE
===============================
Role: Verifies the end-to-end execution of the Orchestrator.
Scope: Hydration -> Strategy -> Results.
"""

from src.models.results.strategies import FCFFStandardResults
from src.models.valuation import ValuationResult
from src.valuation.orchestrator import ValuationOrchestrator


class TestValuationPipeline:

    def test_fcff_standard_execution_success(self, fcff_request_standard, mock_apple_snapshot):
        """
        Scenario: Nominal case for Apple Inc. using Standard FCFF.
        Expected: A populated ValuationResult with positive Intrinsic Value.
        """
        # 1. Initialize Orchestrator
        orchestrator = ValuationOrchestrator()

        # 2. Run Pipeline
        result = orchestrator.run(
            request=fcff_request_standard,
            snapshot=mock_apple_snapshot
        )

        # 3. Assert Envelope Structure
        assert isinstance(result, ValuationResult)
        assert result.request.mode == fcff_request_standard.mode

        # 4. Assert Hydration (Resolver worked?)
        # WACC should be calculated (around 10% given beta 1.2, rf 4%, mrp 5%)
        # Ke = 4 + 1.2*5 = 10%. WACC roughly similar as debt is low.
        wacc = result.results.common.rates.wacc
        assert 0.08 < wacc < 0.12, f"WACC {wacc} seems unrealistic for this dataset"

        # 5. Assert Core Value
        iv = result.results.common.intrinsic_value_per_share
        assert iv > 0, "Intrinsic Value should be positive for profitable Apple mock"

        # Check Upside calculation
        assert result.upside_pct is not None

        # 6. Assert Strategy Specifics
        strat_res = result.results.strategy
        assert isinstance(strat_res, FCFFStandardResults)
        assert len(strat_res.projected_flows) == 5
        assert strat_res.terminal_value > 0
