"""
tests/unit/test_strategies_graham_value.py

GRAHAM INTRINSIC VALUE STRATEGY TESTS
=====================================
Comprehensive test suite for Graham Number valuation strategy.
Target: ≥90% coverage of src/valuation/strategies/graham_value.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.models.company import Company
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.strategies import GrahamParameters
from src.models.parameters.common import CommonParameters, FinancialRatesParameters, CapitalStructureParameters
from src.models.enums import ValuationMethodology, CompanySector
from src.models.glass_box import CalculationStep
from src.valuation.strategies.graham_value import GrahamNumberStrategy


class TestGrahamStrategy:
    """Test suite for Graham Intrinsic Value strategy."""

    @pytest.fixture
    def strategy(self):
        """Create a Graham strategy instance."""
        return GrahamNumberStrategy()

    @pytest.fixture
    def basic_company(self):
        """Create a basic company with financial data."""
        company = Mock(spec=Company)
        company.ticker = "AAPL"
        company.name = "Apple Inc."
        company.sector = CompanySector.TECHNOLOGY
        company.current_price = 150.0
        company.currency = "USD"
        company.last_update = datetime.now(timezone.utc)
        company.eps_ttm = 6.00
        return company

    @pytest.fixture
    def basic_params(self):
        """Create basic Graham parameters."""
        strategy = GrahamParameters(
            eps_normalized=6.00,
            growth_estimate=0.10
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(
                risk_free_rate=0.04,
                market_risk_premium=0.05,
                beta=1.2,
                tax_rate=0.21,
                corporate_aaa_yield=0.045
            ),
            capital=CapitalStructureParameters(
                shares_outstanding=16000.0,
                total_debt=120000.0,
                cash_and_equivalents=50000.0
            )
        )
        return Parameters(
            structure=Company(ticker="AAPL", name="Apple Inc."),
            strategy=strategy,
            common=common
        )

    def test_glass_box_property(self, strategy):
        """Test glass_box_enabled property getter/setter."""
        assert strategy.glass_box_enabled is True
        strategy.glass_box_enabled = False
        assert strategy.glass_box_enabled is False
        strategy.glass_box_enabled = True
        assert strategy.glass_box_enabled is True

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_execute_with_valid_inputs(self, mock_graham_calc, strategy, basic_company, basic_params):
        """Test successful execution with valid inputs."""
        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0,
            theoretical_formula="IV = (EPS * (8.5 + 2*g) * 4.4) / Y"
        ))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Assertions
        assert result is not None
        assert result.request.mode == ValuationMethodology.GRAHAM
        assert result.results.common.intrinsic_value_per_share == 180.0
        assert len(result.results.common.bridge_trace) > 0

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_execute_with_glass_box_disabled(self, mock_graham_calc, strategy, basic_company, basic_params):
        """Test execution with glass box disabled."""
        strategy.glass_box_enabled = False

        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0
        ))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Bridge trace should be empty when glass box is disabled
        assert len(result.results.common.bridge_trace) == 0
        assert result.results.common.intrinsic_value_per_share == 180.0

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_graham_multiplier_calculation(self, mock_graham_calc, strategy, basic_company, basic_params):
        """Test Graham multiplier calculation (8.5 + 2*g)."""
        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0
        ))

        # Execute with 10% growth
        result = strategy.execute(basic_company, basic_params)

        # Graham Multiplier = 8.5 + 2 * (0.10 * 100) = 8.5 + 20 = 28.5
        assert result.results.strategy.graham_multiplier == pytest.approx(28.5, rel=0.01)

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_eps_used_from_strategy_params(self, mock_graham_calc, strategy, basic_company, basic_params):
        """Test that EPS from strategy params is used."""
        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0
        ))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify EPS used
        assert result.results.strategy.eps_used == 6.00

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_eps_fallback_to_company_data(self, mock_graham_calc, strategy, basic_company):
        """Test fallback to company EPS when strategy param is None."""
        # Setup params without EPS normalized
        strategy_params = GrahamParameters(
            eps_normalized=None,
            growth_estimate=0.10
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(corporate_aaa_yield=0.045),
            capital=CapitalStructureParameters(shares_outstanding=16000.0)
        )
        params = Parameters(
            structure=Company(ticker="AAPL", name="Apple Inc."),
            strategy=strategy_params,
            common=common
        )

        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0
        ))

        # Execute
        result = strategy.execute(basic_company, params)

        # Should use company EPS (6.00) as fallback
        assert result.results.strategy.eps_used == 6.00

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_growth_estimate_used(self, mock_graham_calc, strategy, basic_company, basic_params):
        """Test that growth estimate is properly used."""
        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0
        ))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify growth estimate
        assert result.results.strategy.growth_estimate == 0.10

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    @patch('src.valuation.strategies.graham_value.ModelDefaults')
    def test_growth_fallback_to_defaults(self, mock_defaults, mock_graham_calc, strategy, basic_company):
        """Test fallback to default growth when not provided."""
        mock_defaults.DEFAULT_GROWTH_RATE = 0.05

        # Setup params without growth estimate
        strategy_params = GrahamParameters(
            eps_normalized=6.00,
            growth_estimate=None
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(corporate_aaa_yield=0.045),
            capital=CapitalStructureParameters(shares_outstanding=16000.0)
        )
        params = Parameters(
            structure=Company(ticker="AAPL", name="Apple Inc."),
            strategy=strategy_params,
            common=common
        )

        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0
        ))

        # Execute
        result = strategy.execute(basic_company, params)

        # Should use default growth
        assert result.results.strategy.growth_estimate == 0.05

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_aaa_yield_used(self, mock_graham_calc, strategy, basic_company, basic_params):
        """Test that AAA yield is properly used."""
        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0
        ))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify AAA yield
        assert result.results.strategy.aaa_yield_used == 0.045

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    @patch('src.valuation.strategies.graham_value.MacroDefaults')
    def test_aaa_yield_fallback_to_defaults(self, mock_macro, mock_graham_calc, strategy, basic_company):
        """Test fallback to default AAA yield when not provided."""
        mock_macro.DEFAULT_CORPORATE_AAA_YIELD = 0.04

        # Setup params without AAA yield
        strategy_params = GrahamParameters(eps_normalized=6.00, growth_estimate=0.10)
        common = CommonParameters(
            rates=FinancialRatesParameters(corporate_aaa_yield=None),
            capital=CapitalStructureParameters(shares_outstanding=16000.0)
        )
        params = Parameters(
            structure=Company(ticker="AAPL", name="Apple Inc."),
            strategy=strategy_params,
            common=common
        )

        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0
        ))

        # Execute
        result = strategy.execute(basic_company, params)

        # Should use default AAA yield
        assert result.results.strategy.aaa_yield_used == 0.04

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_capital_structure_reconstruction(self, mock_graham_calc, strategy, basic_company, basic_params):
        """Test capital structure values are properly reconstructed."""
        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0
        ))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify capital structure
        # Total equity = IV per share * shares = 180 * 16000 = 2,880,000 (normalized to 2.88T)
        assert result.results.common.capital.equity_value_total == pytest.approx(2880000000000, rel=0.01)
        assert result.results.common.capital.net_debt_resolved == pytest.approx(70000000000, rel=0.01)  # 120B - 50B
        # Implied EV = Equity + Net Debt = 2.88T + 70B = 2.95T
        assert result.results.common.capital.enterprise_value == pytest.approx(2950000000000, rel=0.01)
        assert result.results.common.capital.market_cap == pytest.approx(2400000000000, rel=0.01)  # 16B * 150.0

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_upside_calculation(self, mock_graham_calc, strategy, basic_company, basic_params):
        """Test upside percentage calculation."""
        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0
        ))

        # Execute (current price is 150.0)
        result = strategy.execute(basic_company, basic_params)

        # Upside = (180 - 150) / 150 = 0.20 (20%)
        assert result.results.common.upside_pct == pytest.approx(0.20, rel=0.01)

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_rates_reconstruction(self, mock_graham_calc, strategy, basic_company, basic_params):
        """Test rates are properly reconstructed."""
        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0
        ))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # In Graham, Ke is set to AAA yield as proxy
        assert result.results.common.rates.cost_of_equity == 0.045
        assert result.results.common.rates.wacc == 0.045
        assert result.results.common.rates.cost_of_debt_after_tax == 0.0
        assert result.results.common.rates.corporate_aaa_yield == 0.045

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_zero_eps_handling(self, mock_graham_calc, strategy, basic_params):
        """Test handling of zero EPS."""
        basic_params.strategy.eps_normalized = 0.0

        # Setup mock
        mock_graham_calc.return_value = (0.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=0.0
        ))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Should handle zero EPS gracefully - uses the normalized EPS from params
        assert result.results.common.intrinsic_value_per_share == 0.0
        assert result.results.strategy.eps_used == 0.0  # Uses normalized param which is 0

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_negative_growth_handling(self, mock_graham_calc, strategy, basic_company, basic_params):
        """Test handling of negative growth estimate."""
        basic_params.strategy.growth_estimate = -0.05

        # Setup mock - Graham formula can handle negative growth
        mock_graham_calc.return_value = (120.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=120.0
        ))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Graham Multiplier with negative growth = 8.5 + 2*(-5) = 8.5 - 10 = -1.5
        assert result.results.strategy.graham_multiplier == pytest.approx(-1.5, rel=0.01)
        assert result.results.common.intrinsic_value_per_share == 120.0

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_high_growth_handling(self, mock_graham_calc, strategy, basic_company, basic_params):
        """Test handling of high growth estimate."""
        basic_params.strategy.growth_estimate = 0.25  # 25% growth

        # Setup mock
        mock_graham_calc.return_value = (250.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=250.0
        ))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Graham Multiplier = 8.5 + 2 * 25 = 58.5
        assert result.results.strategy.graham_multiplier == pytest.approx(58.5, rel=0.01)
        assert result.results.common.intrinsic_value_per_share == 250.0

    @patch('src.valuation.strategies.graham_value.GrahamLibrary.compute_intrinsic_value')
    def test_missing_company_price_handling(self, mock_graham_calc, strategy, basic_params):
        """Test handling when company has no current price."""
        company_no_price = Mock(spec=Company)
        company_no_price.ticker = "AAPL"
        company_no_price.name = "Apple Inc."
        company_no_price.sector = CompanySector.TECHNOLOGY
        company_no_price.current_price = None
        company_no_price.currency = "USD"
        company_no_price.last_update = datetime.now(timezone.utc)
        company_no_price.eps_ttm = 6.00

        # Setup mock
        mock_graham_calc.return_value = (180.0, CalculationStep(
            step_key="GRAHAM", label="Graham Value", result=180.0
        ))

        # Execute
        result = strategy.execute(company_no_price, basic_params)

        # Upside should be 0 when no current price
        assert result.results.common.upside_pct == 0.0
        assert result.results.common.intrinsic_value_per_share == 180.0
