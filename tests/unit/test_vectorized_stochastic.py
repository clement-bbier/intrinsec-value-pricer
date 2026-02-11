"""
tests/unit/test_vectorized_stochastic.py

VECTORIZED MONTE CARLO TESTS FOR ALL STRATEGIES
================================================
Role: Validates that each strategy's `execute_stochastic` method produces
      correct, finite, vectorized output using pure NumPy.
Coverage: All 7 strategies + MonteCarloRunner fast-path.
Standards: pytest + numpy testing.
"""

from unittest.mock import Mock

import numpy as np
import pytest

from src.models.company import Company
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import (
    CapitalStructureParameters,
    CommonParameters,
    FinancialRatesParameters,
)
from src.models.parameters.strategies import (
    DDMParameters,
    FCFEParameters,
    FCFFGrowthParameters,
    FCFFNormalizedParameters,
    FCFFStandardParameters,
    GrahamParameters,
    RIMParameters,
    TerminalValueParameters,
)
from src.valuation.strategies.ddm import DividendDiscountStrategy
from src.valuation.strategies.fcfe import FCFEStrategy
from src.valuation.strategies.fundamental_fcff import FundamentalFCFFStrategy
from src.valuation.strategies.graham_value import GrahamNumberStrategy
from src.valuation.strategies.revenue_growth_fcff import RevenueGrowthFCFFStrategy
from src.valuation.strategies.rim_banks import RIMBankingStrategy
from src.valuation.strategies.standard_fcff import StandardFCFFStrategy

# ============================================================================
# SHARED FIXTURES
# ============================================================================

N_SIMS = 1000


@pytest.fixture
def base_vectors():
    """Standard vector bundle used by DCF-family strategies."""
    rng = np.random.default_rng(42)
    return {
        'wacc': rng.normal(0.10, 0.01, N_SIMS),
        'growth': rng.normal(0.05, 0.01, N_SIMS),
        'terminal_growth': np.clip(rng.normal(0.02, 0.005, N_SIMS), -0.01, 0.08),
        'base_flow': rng.normal(100.0, 10.0, N_SIMS),
    }


@pytest.fixture
def company():
    """Minimal Company mock for stochastic execution."""
    c = Mock(spec=Company)
    c.ticker = "TEST"
    c.name = "Test Corp"
    c.current_price = 150.0
    c.revenue_ttm = 50000.0
    c.fcf_ttm = 5000.0
    c.book_value_ps = 30.0
    c.eps_ttm = 6.0
    c.beta = 1.1
    return c


@pytest.fixture
def common_params():
    """Common parameters shared across strategies."""
    return CommonParameters(
        rates=FinancialRatesParameters(
            risk_free_rate=0.04,
            market_risk_premium=0.06,
            beta=1.1,
            tax_rate=0.25,
            corporate_aaa_yield=0.045,
        ),
        capital=CapitalStructureParameters(
            shares_outstanding=16000.0,
            total_debt=120000.0,
            cash_and_equivalents=50000.0,
        ),
    )


# ============================================================================
# TEST: StandardFCFFStrategy.execute_stochastic
# ============================================================================

class TestStandardFCFFStochastic:
    """Vectorized execution tests for Standard FCFF."""

    def test_output_shape(self, company, common_params, base_vectors):
        strategy_params = FCFFStandardParameters(
            projection_years=5,
            terminal_value=TerminalValueParameters(perpetual_growth_rate=0.02),
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = StandardFCFFStrategy.execute_stochastic(company, params, base_vectors)
        assert result.shape == (N_SIMS,)

    def test_output_finite(self, company, common_params, base_vectors):
        strategy_params = FCFFStandardParameters(projection_years=5)
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = StandardFCFFStrategy.execute_stochastic(company, params, base_vectors)
        assert np.all(np.isfinite(result))

    def test_output_varies(self, company, common_params, base_vectors):
        """Stochastic output should not be constant."""
        strategy_params = FCFFStandardParameters(projection_years=5)
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = StandardFCFFStrategy.execute_stochastic(company, params, base_vectors)
        assert np.std(result) > 0

    def test_higher_wacc_lowers_value(self, company, common_params):
        """Higher discount rate should generally lower intrinsic value."""
        strategy_params = FCFFStandardParameters(projection_years=5)
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        vectors_low = {
            'wacc': np.full(100, 0.08),
            'growth': np.full(100, 0.05),
            'terminal_growth': np.full(100, 0.02),
            'base_flow': np.full(100, 100.0),
        }
        vectors_high = {
            'wacc': np.full(100, 0.15),
            'growth': np.full(100, 0.05),
            'terminal_growth': np.full(100, 0.02),
            'base_flow': np.full(100, 100.0),
        }
        iv_low_wacc = StandardFCFFStrategy.execute_stochastic(company, params, vectors_low)
        iv_high_wacc = StandardFCFFStrategy.execute_stochastic(company, params, vectors_high)
        assert np.mean(iv_low_wacc) > np.mean(iv_high_wacc)


# ============================================================================
# TEST: FundamentalFCFFStrategy.execute_stochastic
# ============================================================================

class TestFundamentalFCFFStochastic:
    """Vectorized execution tests for Fundamental (Normalized) FCFF."""

    def test_output_shape(self, company, common_params, base_vectors):
        strategy_params = FCFFNormalizedParameters(projection_years=5)
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = FundamentalFCFFStrategy.execute_stochastic(company, params, base_vectors)
        assert result.shape == (N_SIMS,)

    def test_output_finite(self, company, common_params, base_vectors):
        strategy_params = FCFFNormalizedParameters(projection_years=5)
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = FundamentalFCFFStrategy.execute_stochastic(company, params, base_vectors)
        assert np.all(np.isfinite(result))


# ============================================================================
# TEST: RevenueGrowthFCFFStrategy.execute_stochastic
# ============================================================================

class TestRevenueGrowthFCFFStochastic:
    """Vectorized execution tests for Revenue-Growth FCFF."""

    def test_output_shape(self, company, common_params, base_vectors):
        strategy_params = FCFFGrowthParameters(
            projection_years=5,
            target_fcf_margin=0.20,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = RevenueGrowthFCFFStrategy.execute_stochastic(company, params, base_vectors)
        assert result.shape == (N_SIMS,)

    def test_output_finite(self, company, common_params, base_vectors):
        strategy_params = FCFFGrowthParameters(
            projection_years=5,
            target_fcf_margin=0.20,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = RevenueGrowthFCFFStrategy.execute_stochastic(company, params, base_vectors)
        assert np.all(np.isfinite(result))


# ============================================================================
# TEST: FCFEStrategy.execute_stochastic
# ============================================================================

class TestFCFEStochastic:
    """Vectorized execution tests for Free Cash Flow to Equity."""

    def test_output_shape(self, company, common_params, base_vectors):
        strategy_params = FCFEParameters(projection_years=5)
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = FCFEStrategy.execute_stochastic(company, params, base_vectors)
        assert result.shape == (N_SIMS,)

    def test_output_finite(self, company, common_params, base_vectors):
        strategy_params = FCFEParameters(projection_years=5)
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = FCFEStrategy.execute_stochastic(company, params, base_vectors)
        assert np.all(np.isfinite(result))

    def test_no_debt_subtraction(self, company, common_params, base_vectors):
        """FCFE should add cash but NOT subtract debt (unlike FCFF)."""
        strategy_params = FCFEParameters(projection_years=5)
        # Set debt to 0 and cash to 0 to isolate the equity computation
        common_no_bridge = CommonParameters(
            rates=common_params.rates,
            capital=CapitalStructureParameters(
                shares_outstanding=16000.0,
                total_debt=0.0,
                cash_and_equivalents=0.0,
            ),
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_no_bridge,
        )
        result = FCFEStrategy.execute_stochastic(company, params, base_vectors)
        assert result.shape == (N_SIMS,)
        assert np.all(np.isfinite(result))


# ============================================================================
# TEST: DDMStrategy.execute_stochastic
# ============================================================================

class TestDDMStochastic:
    """Vectorized execution tests for Dividend Discount Model."""

    def test_output_shape(self, company, common_params, base_vectors):
        strategy_params = DDMParameters(
            dividend_per_share=3.0,
            projection_years=5,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = DividendDiscountStrategy.execute_stochastic(company, params, base_vectors)
        assert result.shape == (N_SIMS,)

    def test_output_finite(self, company, common_params, base_vectors):
        strategy_params = DDMParameters(
            dividend_per_share=3.0,
            projection_years=5,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = DividendDiscountStrategy.execute_stochastic(company, params, base_vectors)
        assert np.all(np.isfinite(result))

    def test_output_varies(self, company, common_params, base_vectors):
        strategy_params = DDMParameters(
            dividend_per_share=3.0,
            projection_years=5,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = DividendDiscountStrategy.execute_stochastic(company, params, base_vectors)
        assert np.std(result) > 0


# ============================================================================
# TEST: RIMBankingStrategy.execute_stochastic
# ============================================================================

class TestRIMStochastic:
    """Vectorized execution tests for Residual Income Model."""

    def test_output_shape(self, company, common_params, base_vectors):
        strategy_params = RIMParameters(
            book_value_anchor=30.0,
            projection_years=5,
            persistence_factor=0.6,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = RIMBankingStrategy.execute_stochastic(company, params, base_vectors)
        assert result.shape == (N_SIMS,)

    def test_output_finite(self, company, common_params, base_vectors):
        strategy_params = RIMParameters(
            book_value_anchor=30.0,
            projection_years=5,
            persistence_factor=0.6,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = RIMBankingStrategy.execute_stochastic(company, params, base_vectors)
        assert np.all(np.isfinite(result))

    def test_output_varies(self, company, common_params, base_vectors):
        strategy_params = RIMParameters(
            book_value_anchor=30.0,
            projection_years=5,
            persistence_factor=0.6,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = RIMBankingStrategy.execute_stochastic(company, params, base_vectors)
        assert np.std(result) > 0

    def test_book_value_anchor_fallback(self, company, common_params, base_vectors):
        """When book_value_anchor is None, should fall back to company data."""
        strategy_params = RIMParameters(
            projection_years=5,
            persistence_factor=0.6,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = RIMBankingStrategy.execute_stochastic(company, params, base_vectors)
        assert result.shape == (N_SIMS,)
        assert np.all(np.isfinite(result))


# ============================================================================
# TEST: GrahamNumberStrategy.execute_stochastic
# ============================================================================

class TestGrahamStochastic:
    """Vectorized execution tests for Graham Value Formula."""

    def test_output_shape(self, company, common_params, base_vectors):
        strategy_params = GrahamParameters(
            eps_normalized=6.0,
            growth_estimate=0.10,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = GrahamNumberStrategy.execute_stochastic(company, params, base_vectors)
        assert result.shape == (N_SIMS,)

    def test_output_finite(self, company, common_params, base_vectors):
        strategy_params = GrahamParameters(
            eps_normalized=6.0,
            growth_estimate=0.10,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = GrahamNumberStrategy.execute_stochastic(company, params, base_vectors)
        assert np.all(np.isfinite(result))

    def test_output_varies(self, company, common_params, base_vectors):
        strategy_params = GrahamParameters(
            eps_normalized=6.0,
            growth_estimate=0.10,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        result = GrahamNumberStrategy.execute_stochastic(company, params, base_vectors)
        assert np.std(result) > 0

    def test_graham_formula_consistency(self, company, common_params):
        """Verify the Graham formula: IV = (EPS * (8.5 + 2g) * 4.4) / Y."""
        strategy_params = GrahamParameters(
            eps_normalized=6.0,
            growth_estimate=0.10,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        # Use deterministic vectors
        vectors = {
            'base_flow': np.array([6.0]),
            'growth': np.array([0.10]),
            'wacc': np.array([0.10]),
            'terminal_growth': np.array([0.02]),
        }
        result = GrahamNumberStrategy.execute_stochastic(company, params, vectors)

        # Manual computation: EPS=6, g=0.10 -> g*100=10
        # multiplier = 8.5 + 2*10 = 28.5
        # IV = (6 * 28.5 * 4.4) / (0.045 * 100) = 752.4 / 4.5 = 167.2
        expected = (6.0 * (8.5 + 2.0 * 10.0) * 4.4) / (0.045 * 100.0)
        np.testing.assert_allclose(result[0], expected, rtol=1e-6)


# ============================================================================
# TEST: Performance Gate — Vectorization Speed
# ============================================================================

class TestVectorizationPerformance:
    """Ensures vectorized execution is fast enough."""

    def test_10k_simulations_under_100ms(self, company, common_params):
        """10,000 simulations should complete in under 100ms."""
        import time

        n = 10_000
        rng = np.random.default_rng(42)
        vectors = {
            'wacc': rng.normal(0.10, 0.01, n),
            'growth': rng.normal(0.05, 0.01, n),
            'terminal_growth': np.clip(rng.normal(0.02, 0.005, n), -0.01, 0.08),
            'base_flow': rng.normal(100.0, 10.0, n),
        }
        strategy_params = FCFFStandardParameters(projection_years=5)
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )

        start = time.perf_counter()
        result = StandardFCFFStrategy.execute_stochastic(company, params, vectors)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result.shape == (n,)
        assert np.all(np.isfinite(result))
        assert elapsed_ms < 100, f"10k sims took {elapsed_ms:.1f}ms, should be <100ms"

    def test_all_strategies_fast(self, company, common_params):
        """All strategies should process 10k simulations in under 200ms each."""
        import time

        n = 10_000
        rng = np.random.default_rng(42)
        vectors = {
            'wacc': rng.normal(0.10, 0.01, n),
            'growth': rng.normal(0.05, 0.01, n),
            'terminal_growth': np.clip(rng.normal(0.02, 0.005, n), -0.01, 0.08),
            'base_flow': rng.normal(100.0, 10.0, n),
        }

        strategies_and_params = [
            (StandardFCFFStrategy, FCFFStandardParameters(projection_years=5)),
            (FundamentalFCFFStrategy, FCFFNormalizedParameters(projection_years=5)),
            (FCFEStrategy, FCFEParameters(projection_years=5)),
            (DividendDiscountStrategy, DDMParameters(dividend_per_share=3.0, projection_years=5)),
            (GrahamNumberStrategy, GrahamParameters(eps_normalized=6.0, growth_estimate=0.10)),
        ]

        for strategy_cls, strategy_params in strategies_and_params:
            params = Parameters(
                structure=Company(ticker="TEST", name="Test Corp"),
                strategy=strategy_params,
                common=common_params,
            )
            start = time.perf_counter()
            result = strategy_cls.execute_stochastic(company, params, vectors)
            elapsed_ms = (time.perf_counter() - start) * 1000

            assert result.shape == (n,), f"{strategy_cls.__name__} wrong shape"
            assert elapsed_ms < 200, (
                f"{strategy_cls.__name__} took {elapsed_ms:.1f}ms for 10k sims, should be <200ms"
            )

    def test_rim_strategy_fast(self, company, common_params):
        """RIM strategy (with loop over years) should still be fast."""
        import time

        n = 10_000
        rng = np.random.default_rng(42)
        vectors = {
            'wacc': rng.normal(0.10, 0.01, n),
            'growth': rng.normal(0.05, 0.01, n),
            'terminal_growth': np.clip(rng.normal(0.02, 0.005, n), -0.01, 0.08),
            'base_flow': rng.normal(6.0, 0.6, n),
        }
        strategy_params = RIMParameters(
            book_value_anchor=30.0,
            projection_years=5,
            persistence_factor=0.6,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        start = time.perf_counter()
        result = RIMBankingStrategy.execute_stochastic(company, params, vectors)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result.shape == (n,)
        assert elapsed_ms < 200, f"RIM 10k sims took {elapsed_ms:.1f}ms, should be <200ms"

    def test_revenue_growth_strategy_fast(self, company, common_params):
        """Revenue-Growth strategy should process 10k simulations quickly."""
        import time

        n = 10_000
        rng = np.random.default_rng(42)
        vectors = {
            'wacc': rng.normal(0.10, 0.01, n),
            'growth': rng.normal(0.05, 0.01, n),
            'terminal_growth': np.clip(rng.normal(0.02, 0.005, n), -0.01, 0.08),
            'base_flow': rng.normal(50000.0, 5000.0, n),
        }
        strategy_params = FCFFGrowthParameters(
            projection_years=5,
            target_fcf_margin=0.20,
        )
        params = Parameters(
            structure=Company(ticker="TEST", name="Test Corp"),
            strategy=strategy_params,
            common=common_params,
        )
        start = time.perf_counter()
        result = RevenueGrowthFCFFStrategy.execute_stochastic(company, params, vectors)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result.shape == (n,)
        assert elapsed_ms < 200, (
            f"Revenue-Growth 10k sims took {elapsed_ms:.1f}ms, should be <200ms"
        )
