"""
tests/integration/test_full_flow.py

INTEGRATION TEST: FULL LIFECYCLE
================================
Role: Validates the complete cycle from input resolution through calculation
to result structure, ensuring all V2 paths are correct.
"""

import pytest

from src.config.constants import MacroDefaults, ModelDefaults
from src.models.company import Company, CompanySnapshot
from src.models.enums import ValuationMethodology
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import CommonParameters
from src.models.parameters.strategies import (
    FCFFStandardParameters,
    GrahamParameters,
)
from src.models.results.strategies import FCFFStandardResults
from src.models.valuation import ValuationRequest, ValuationResult
from src.valuation.orchestrator import ValuationOrchestrator
from src.valuation.resolvers.base_resolver import Resolver


@pytest.fixture
def complete_snapshot():
    """A comprehensive snapshot for integration testing."""
    return CompanySnapshot(
        ticker="INTG",
        name="Integration Corp",
        sector="Technology",
        industry="Software",
        country="US",
        currency="EUR",
        current_price=200.0,
        total_debt=100_000.0,
        cash_and_equivalents=30_000.0,
        shares_outstanding=5_000.0,
        revenue_ttm=500_000.0,
        ebit_ttm=100_000.0,
        net_income_ttm=75_000.0,
        interest_expense=5_000.0,
        fcf_ttm=80_000.0,
        capex_ttm=15_000.0,
        beta=1.1,
        risk_free_rate=0.04,
        market_risk_premium=0.055,
        tax_rate=0.25,
    )


class TestFullResolutionCycle:
    """Tests the complete resolution -> calculation -> result cycle."""

    def test_resolution_produces_no_none_values(self, complete_snapshot):
        """All critical fields should be resolved (no None) after full resolution."""
        params = Parameters(
            structure=Company(ticker="INTG"),
            strategy=FCFFStandardParameters(projection_years=7),
        )
        resolver = Resolver()
        resolved = resolver.resolve(params, complete_snapshot)

        # Identity — Company defaults persist unless explicitly overridden
        assert resolved.structure.name is not None
        assert resolved.structure.currency is not None
        assert resolved.structure.current_price == 200.0

        # Rates (critical — None would crash calculations)
        rates = resolved.common.rates
        assert rates.risk_free_rate is not None
        assert rates.market_risk_premium is not None
        assert rates.beta is not None
        assert rates.tax_rate is not None
        assert rates.cost_of_debt is not None

        # Capital (critical — None would crash equity bridge)
        cap = resolved.common.capital
        assert cap.total_debt is not None
        assert cap.shares_outstanding is not None
        assert cap.shares_outstanding > 0

        # Strategy
        assert resolved.strategy.fcf_anchor is not None
        assert resolved.strategy.projection_years == 7

    def test_full_pipeline_fcff_standard(self, complete_snapshot):
        """End-to-end: FCFF Standard from ghost parameters to final result."""
        request = ValuationRequest(
            mode=ValuationMethodology.FCFF_STANDARD,
            parameters=Parameters(
                structure=Company(ticker="INTG", current_price=100.0),
                strategy=FCFFStandardParameters(
                    projection_years=5,
                    growth_rate_p1=0.08,
                ),
            ),
        )

        orchestrator = ValuationOrchestrator()
        result = orchestrator.run(request, complete_snapshot)

        # 1. Result structure
        assert isinstance(result, ValuationResult)
        assert result.request.mode == ValuationMethodology.FCFF_STANDARD

        # 2. Common results
        assert result.results.common.intrinsic_value_per_share > 0
        assert result.results.common.rates.wacc > 0
        assert result.results.common.capital.enterprise_value > 0

        # 3. Strategy results
        strat = result.results.strategy
        assert isinstance(strat, FCFFStandardResults)
        assert strat.terminal_value > 0

        # 4. V2 path: request.parameters should be properly hydrated
        # current_price is resolved from identity (100.0 provided) since it's truthy
        assert result.request.parameters.structure.current_price > 0
        assert result.request.parameters.structure.currency is not None

        # 5. Upside should be calculable
        assert result.upside_pct is not None

    def test_full_pipeline_graham(self, complete_snapshot):
        """End-to-end: Graham from ghost parameters to final result."""
        request = ValuationRequest(
            mode=ValuationMethodology.GRAHAM,
            parameters=Parameters(
                structure=Company(ticker="INTG", current_price=0.0),
                strategy=GrahamParameters(),
            ),
        )

        orchestrator = ValuationOrchestrator()
        result = orchestrator.run(request, complete_snapshot)

        assert isinstance(result, ValuationResult)
        assert result.results.common.intrinsic_value_per_share >= 0

    def test_result_v2_path_correctness(self, complete_snapshot):
        """Verify all V2 data paths used by pillar views are accessible."""
        request = ValuationRequest(
            mode=ValuationMethodology.FCFF_STANDARD,
            parameters=Parameters(
                structure=Company(ticker="INTG"),
                strategy=FCFFStandardParameters(projection_years=5),
            ),
        )

        orchestrator = ValuationOrchestrator()
        result = orchestrator.run(request, complete_snapshot)

        # Paths used by orchestrator.py
        assert result.results.common.intrinsic_value_per_share is not None
        assert result.request.parameters.structure.current_price is not None
        assert result.request.parameters.structure.currency is not None

        # Paths used by extension checks
        ext_params = result.request.parameters.extensions
        assert ext_params.monte_carlo is not None
        assert ext_params.sensitivity is not None
        assert ext_params.scenarios is not None
        assert ext_params.backtest is not None
        assert ext_params.sotp is not None
        assert ext_params.peers is not None

        # Results extensions
        ext_results = result.results.extensions
        assert ext_results is not None
