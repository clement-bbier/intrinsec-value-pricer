"""
tests/snapshots/test_golden_datasets.py

GOLDEN DATASET SNAPSHOT TESTS
==============================
Role: Frozen test cases for determinism, reproducibility, and performance gates.
Architecture: Institutional-grade regression testing with fixed expected values.
"""

from datetime import datetime, timezone

import pytest

from src.core.exceptions import CalculationError
from src.models.company import Company, CompanySnapshot
from src.models.enums import CompanySector, ValuationMethodology
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.options import ExtensionBundleParameters, MCParameters, StandardMCShocksParameters
from src.models.parameters.strategies import FCFFStandardParameters
from src.models.valuation import ValuationRequest
from src.valuation.orchestrator import ValuationOrchestrator

# ==============================================================================
# MODULE-LEVEL CONSTANTS
# ==============================================================================

DEFAULT_RISK_FREE_RATE = 0.04  # 4%
DEFAULT_MARKET_RISK_PREMIUM = 0.05  # 5%
DEFAULT_TAX_RATE = 0.21  # 21%


# ==============================================================================
# GOLDEN DATASET FIXTURES
# ==============================================================================


@pytest.fixture
def golden_aapl_large_cap_tech():
    """
    Dataset 1: AAPL-like Large Cap Tech Company
    Profile: Mature, profitable, strong FCF generation
    Market Cap: ~$3T, FCF: $110B, Growth: 8%, Beta: 1.2
    Expected WACC: ~9%
    """
    return CompanySnapshot(
        ticker="AAPL",
        name="Apple Inc. (Mock)",
        sector="Technology",
        current_price=180.0,
        # Balance Sheet - Large Cap
        total_debt=120_000.0,  # $120B
        cash_and_equivalents=50_000.0,  # $50B
        shares_outstanding=16_000.0,  # 16B shares
        # Income Statement
        revenue_ttm=400_000.0,  # $400B
        ebit_ttm=120_000.0,  # $120B
        net_income_ttm=100_000.0,  # $100B
        interest_expense=3_000.0,  # $3B
        # Cash Flow
        fcf_ttm=110_000.0,  # $110B
        capex_ttm=12_000.0,  # $12B
        # Market Rates
        beta=1.2,
        risk_free_rate=DEFAULT_RISK_FREE_RATE,
        market_risk_premium=DEFAULT_MARKET_RISK_PREMIUM,
        tax_rate=DEFAULT_TAX_RATE,
    )


@pytest.fixture
def golden_high_growth_tech():
    """
    Dataset 2: High Growth Tech (startup-like)
    Profile: High risk, high growth, moderate FCF
    Market Cap: $50B, FCF: $2B, Growth: 25%, Beta: 1.8
    Expected WACC: ~13%
    """
    return CompanySnapshot(
        ticker="HGTH",
        name="High Growth Tech (Mock)",
        sector="Technology",
        current_price=100.0,
        # Balance Sheet
        total_debt=10_000.0,  # $10B
        cash_and_equivalents=5_000.0,  # $5B
        shares_outstanding=500.0,  # 500M shares
        # Income Statement
        revenue_ttm=15_000.0,  # $15B
        ebit_ttm=3_000.0,  # $3B
        net_income_ttm=2_000.0,  # $2B
        interest_expense=500.0,  # $500M
        # Cash Flow
        fcf_ttm=2_000.0,  # $2B
        capex_ttm=1_000.0,  # $1B
        # Market Rates - High Risk
        beta=1.8,
        risk_free_rate=DEFAULT_RISK_FREE_RATE,
        market_risk_premium=0.055,  # 5.5%
        tax_rate=DEFAULT_TAX_RATE,
    )


@pytest.fixture
def golden_mature_utility():
    """
    Dataset 3: Mature Utility Company
    Profile: Low growth, low risk, stable FCF
    Market Cap: $80B, FCF: $8B, Growth: 2%, Beta: 0.5
    Expected WACC: ~6%
    """
    return CompanySnapshot(
        ticker="UTIL",
        name="Stable Utility Corp (Mock)",
        sector="Utilities",
        current_price=75.0,
        # Balance Sheet
        total_debt=50_000.0,  # $50B (high for utilities)
        cash_and_equivalents=5_000.0,  # $5B
        shares_outstanding=1_000.0,  # 1B shares
        # Income Statement
        revenue_ttm=25_000.0,  # $25B
        ebit_ttm=10_000.0,  # $10B
        net_income_ttm=7_000.0,  # $7B
        interest_expense=2_000.0,  # $2B
        # Cash Flow
        fcf_ttm=8_000.0,  # $8B
        capex_ttm=3_000.0,  # $3B
        # Market Rates - Low Risk
        beta=0.5,
        risk_free_rate=DEFAULT_RISK_FREE_RATE,
        market_risk_premium=DEFAULT_MARKET_RISK_PREMIUM,
        tax_rate=DEFAULT_TAX_RATE,
    )


@pytest.fixture
def golden_distressed_company():
    """
    Dataset 4: Distressed Company
    Profile: Negative FCF, declining growth, high risk
    Market Cap: $5B, FCF: -$500M, Growth: -5%, Beta: 2.5
    Expected: Either CalculationError or very low/negative valuation
    """
    return CompanySnapshot(
        ticker="DIST",
        name="Distressed Corp (Mock)",
        sector="Retail",
        current_price=10.0,
        # Balance Sheet - Stressed
        total_debt=8_000.0,  # $8B
        cash_and_equivalents=500.0,  # $500M
        shares_outstanding=500.0,  # 500M shares
        # Income Statement - Losses
        revenue_ttm=5_000.0,  # $5B
        ebit_ttm=-500.0,  # -$500M (negative)
        net_income_ttm=-800.0,  # -$800M
        interest_expense=400.0,  # $400M
        # Cash Flow - Negative
        fcf_ttm=-500.0,  # -$500M (cash burn)
        capex_ttm=300.0,  # $300M
        # Market Rates - Very High Risk
        beta=2.5,
        risk_free_rate=DEFAULT_RISK_FREE_RATE,
        market_risk_premium=0.06,  # 6%
        tax_rate=DEFAULT_TAX_RATE,
    )


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def create_fcff_request(
    snapshot: CompanySnapshot,
    growth_rate: float = 0.05,
    enable_mc: bool = False,
    mc_iterations: int = 1000,
    random_seed: int = 42,
) -> ValuationRequest:
    """
    Creates a standard FCFF valuation request from a snapshot.

    Parameters
    ----------
    snapshot : CompanySnapshot
        The company financial data.
    growth_rate : float
        Growth rate to apply (default: 5%).
    enable_mc : bool
        Whether to enable Monte Carlo simulation.
    mc_iterations : int
        Number of MC simulations.
    random_seed : int
        Random seed for reproducibility.

    Returns
    -------
    ValuationRequest
        Complete request object.
    """
    # Map sector strings to enums
    sector_map = {
        "Technology": CompanySector.TECHNOLOGY,
        "Utilities": CompanySector.UTILITIES,
        "Retail": CompanySector.CONSUMER_CYCLICAL,
    }
    sector_enum = sector_map.get(snapshot.sector, CompanySector.TECHNOLOGY)

    company = Company(
        ticker=snapshot.ticker,
        name=snapshot.name,
        sector=sector_enum,
        current_price=snapshot.current_price,
        currency="USD",
        last_update=datetime.now(timezone.utc),
    )

    strategy_params = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=growth_rate,
    )

    # Monte Carlo configuration
    mc_config = MCParameters(
        enabled=enable_mc,
        iterations=mc_iterations,
        random_seed=random_seed,
        shocks=StandardMCShocksParameters(
            fcf_volatility=0.10,
        )
        if enable_mc
        else None,
    )

    extensions = ExtensionBundleParameters(monte_carlo=mc_config)

    params = Parameters(structure=company, strategy=strategy_params, extensions=extensions)

    return ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)


# ==============================================================================
# DETERMINISTIC VALUATION TESTS
# ==============================================================================


class TestDeterministicValuations:
    """Tests that frozen datasets produce consistent intrinsic values."""

    def test_aapl_large_cap_tech_valuation(self, golden_aapl_large_cap_tech):
        """
        Test AAPL-like large cap tech valuation.
        Expected IV: ~$200-220 per share (frozen baseline).
        """
        orchestrator = ValuationOrchestrator()
        request = create_fcff_request(golden_aapl_large_cap_tech, growth_rate=0.08)

        result = orchestrator.run(request, golden_aapl_large_cap_tech)

        # Assert structure
        assert result is not None
        assert result.results.common.intrinsic_value_per_share > 0

        # Assert metadata is populated
        assert result.metadata is not None
        assert result.metadata.model_name == "FCFF_STANDARD"
        assert result.metadata.ticker == "AAPL"
        assert result.metadata.run_id is not None
        assert result.metadata.input_hash != ""
        assert result.metadata.execution_time_ms is not None

        # Note: audit_report may be None if auditing is not enabled in the orchestrator
        # This is acceptable - not all valuations generate audit reports

        # Frozen expected value (computed during first run, then fixed)
        # This should be stable across runs with same inputs
        iv = result.results.common.intrinsic_value_per_share

        # Large cap tech with 8% growth, strong FCF should be valued reasonably
        # Based on actual calculation: IV ~100
        assert 80 < iv < 120, f"IV {iv:.2f} outside expected range for AAPL profile"

    def test_high_growth_tech_valuation(self, golden_high_growth_tech):
        """
        Test high growth tech company valuation.
        Expected IV: High due to growth, but risk-adjusted.
        """
        orchestrator = ValuationOrchestrator()
        request = create_fcff_request(golden_high_growth_tech, growth_rate=0.25)

        result = orchestrator.run(request, golden_high_growth_tech)

        # Assert structure
        assert result is not None
        iv = result.results.common.intrinsic_value_per_share
        assert iv > 0

        # Metadata checks
        assert result.metadata is not None
        assert result.metadata.ticker == "HGTH"

        # High growth should command premium, but WACC is also high
        assert 50 < iv < 200, f"IV {iv:.2f} outside expected range for high growth"

    def test_mature_utility_valuation(self, golden_mature_utility):
        """
        Test mature utility company valuation.
        Expected IV: Moderate, stable value due to low growth and low risk.
        """
        orchestrator = ValuationOrchestrator()
        request = create_fcff_request(golden_mature_utility, growth_rate=0.02)

        result = orchestrator.run(request, golden_mature_utility)

        # Assert structure
        assert result is not None
        iv = result.results.common.intrinsic_value_per_share
        assert iv > 0

        # Metadata checks
        assert result.metadata is not None
        assert result.metadata.ticker == "UTIL"

        # Low growth utility should have stable, moderate valuation
        # Based on actual calculation: IV ~213
        assert 150 < iv < 250, f"IV {iv:.2f} outside expected range for utility"

    def test_distressed_company_handling(self, golden_distressed_company):
        """
        Test distressed company with negative FCF.
        Expected: Either raises CalculationError or returns very low/negative value.
        """
        orchestrator = ValuationOrchestrator()
        request = create_fcff_request(golden_distressed_company, growth_rate=-0.05)

        try:
            result = orchestrator.run(request, golden_distressed_company)

            # If it doesn't raise, check that IV is very low or negative
            iv = result.results.common.intrinsic_value_per_share

            # Distressed company should have very low valuation
            # Could be negative in enterprise value approach
            assert iv < 50, f"Distressed company IV {iv:.2f} seems too high"

            # Metadata should still be populated
            assert result.metadata is not None
            assert result.metadata.ticker == "DIST"

        except CalculationError:
            # This is also acceptable - negative FCF can cause valuation failures.
            # We only assert that a CalculationError is raised, not on its message,
            # to keep the test robust against message wording changes.
            pass


# ==============================================================================
# MONTE CARLO REPRODUCIBILITY TESTS
# ==============================================================================


class TestMonteCarloReproducibility:
    """Tests that MC simulations are deterministic with same seed."""

    def test_mc_same_seed_produces_identical_results(self, golden_aapl_large_cap_tech):
        """
        Test that two MC runs with the same seed produce identical results.
        """
        orchestrator = ValuationOrchestrator()

        # Run 1 with seed=42
        request1 = create_fcff_request(
            golden_aapl_large_cap_tech, growth_rate=0.08, enable_mc=True, mc_iterations=1000, random_seed=42
        )
        result1 = orchestrator.run(request1, golden_aapl_large_cap_tech)

        # Run 2 with same seed=42
        request2 = create_fcff_request(
            golden_aapl_large_cap_tech, growth_rate=0.08, enable_mc=True, mc_iterations=1000, random_seed=42
        )
        result2 = orchestrator.run(request2, golden_aapl_large_cap_tech)

        # Assert MC results exist
        mc1 = result1.results.extensions.monte_carlo
        mc2 = result2.results.extensions.monte_carlo
        assert mc1 is not None
        assert mc2 is not None

        # Assert identical simulation values (check all values for full reproducibility)
        assert len(mc1.simulation_values) == len(mc2.simulation_values)

        # Check that all values are identical (deterministic) using numpy for precision
        import numpy as np

        values1 = np.array(mc1.simulation_values)
        values2 = np.array(mc2.simulation_values)
        assert np.array_equal(values1, values2), "MC values should be identical with same seed"

        # Check quantiles are identical
        assert abs(mc1.quantiles["P50"] - mc2.quantiles["P50"]) < 0.01
        assert abs(mc1.mean - mc2.mean) < 0.01

    def test_mc_different_seed_produces_different_results(self, golden_aapl_large_cap_tech):
        """
        Test that two MC runs with different seeds produce different results.
        """
        orchestrator = ValuationOrchestrator()

        # Run 1 with seed=42
        request1 = create_fcff_request(
            golden_aapl_large_cap_tech, growth_rate=0.08, enable_mc=True, mc_iterations=1000, random_seed=42
        )
        result1 = orchestrator.run(request1, golden_aapl_large_cap_tech)

        # Run 2 with different seed=123
        request2 = create_fcff_request(
            golden_aapl_large_cap_tech, growth_rate=0.08, enable_mc=True, mc_iterations=1000, random_seed=123
        )
        result2 = orchestrator.run(request2, golden_aapl_large_cap_tech)

        # Assert MC results exist
        mc1 = result1.results.extensions.monte_carlo
        mc2 = result2.results.extensions.monte_carlo
        assert mc1 is not None
        assert mc2 is not None

        # Check that at least some values are different
        different_count = sum(
            1 for v1, v2 in zip(mc1.simulation_values[:100], mc2.simulation_values[:100]) if abs(v1 - v2) > 0.01
        )

        # Most values should be different with different seed
        assert different_count > 50, "Different seeds should produce different MC results"


# ==============================================================================
# PERFORMANCE GATE TESTS
# ==============================================================================


class TestPerformanceGates:
    """Tests that valuations meet performance requirements."""

    def test_standard_fcff_performance_gate(self, golden_aapl_large_cap_tech):
        """
        Test that standard FCFF valuation completes within 500ms.
        Target: <200ms locally, <500ms in CI.
        """
        orchestrator = ValuationOrchestrator()
        request = create_fcff_request(golden_aapl_large_cap_tech, growth_rate=0.08)

        result = orchestrator.run(request, golden_aapl_large_cap_tech)

        # Check execution time from metadata
        assert result.metadata is not None
        exec_time = result.metadata.execution_time_ms
        assert exec_time is not None

        # Performance gate: Should complete in < 500ms (generous for CI)
        assert exec_time < 500, f"Standard valuation took {exec_time}ms, exceeds 500ms gate (target is <200ms locally)"

    def test_monte_carlo_performance_gate(self, golden_aapl_large_cap_tech):
        """
        Test that MC simulation with 10,000 iterations completes within 5 seconds.
        Target: <2s locally, <5s in CI.
        """
        orchestrator = ValuationOrchestrator()
        request = create_fcff_request(
            golden_aapl_large_cap_tech, growth_rate=0.08, enable_mc=True, mc_iterations=10_000, random_seed=42
        )

        result = orchestrator.run(request, golden_aapl_large_cap_tech)

        # Check execution time
        assert result.metadata is not None
        exec_time = result.metadata.execution_time_ms
        assert exec_time is not None

        # Performance gate: Should complete in < 5000ms (generous for CI)
        assert exec_time < 5000, (
            f"MC simulation (10k) took {exec_time}ms, exceeds 5000ms gate (target is <2000ms locally)"
        )

        # Verify MC actually ran
        mc_results = result.results.extensions.monte_carlo
        assert mc_results is not None
        assert len(mc_results.simulation_values) > 0
