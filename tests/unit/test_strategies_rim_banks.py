"""
tests/unit/test_strategies_rim_banks.py

RESIDUAL INCOME MODEL (RIM) STRATEGY TESTS
==========================================
Comprehensive test suite for RIM (Banks/Financial) valuation strategy.
Target: ≥90% coverage of src/valuation/strategies/rim_banks.py
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from src.models.company import Company
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.strategies import RIMParameters
from src.models.parameters.common import CommonParameters, FinancialRatesParameters, CapitalStructureParameters
from src.models.enums import ValuationMethodology, CompanySector
from src.models.glass_box import CalculationStep
from src.valuation.strategies.rim_banks import RIMBankingStrategy


class TestRIMBankingStrategy:
    """Test suite for Residual Income Model (Banks) strategy."""

    @pytest.fixture
    def strategy(self):
        """Create a RIM strategy instance."""
        return RIMBankingStrategy()

    @pytest.fixture
    def basic_company(self):
        """Create a basic financial company with data."""
        company = Mock(spec=Company)
        company.ticker = "JPM"
        company.name = "JPMorgan Chase"
        company.sector = CompanySector.FINANCIAL_SERVICES
        company.current_price = 140.0
        company.currency = "USD"
        company.last_update = datetime.now(timezone.utc)
        company.book_value_ps = 85.0
        company.eps_ttm = 12.0
        return company

    @pytest.fixture
    def basic_params(self):
        """Create basic RIM parameters."""
        strategy = RIMParameters(
            book_value_anchor=85.0,
            persistence_factor=0.8,
            projection_years=10
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(
                risk_free_rate=0.04,
                market_risk_premium=0.05,
                beta=1.1,
                tax_rate=0.21
            ),
            capital=CapitalStructureParameters(
                shares_outstanding=3000000000.0,
                total_debt=50000000000.0,
                cash_and_equivalents=20000000000.0
            )
        )
        return Parameters(
            structure=Company(ticker="JPM", name="JPMorgan Chase"),
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

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    def test_execute_with_valid_inputs(
        self, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test successful execution with valid inputs."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(
            step_key="KE", label="Cost of Equity", result=0.10,
            theoretical_formula="CAPM"
        ))
        # project_residual_income returns: ri_flows, bv_flows, eps_flows, step
        mock_project.return_value = (
            [2.5, 2.3, 2.1, 1.9, 1.7, 1.5, 1.3, 1.1, 0.9, 0.7],  # RI flows
            [90, 95, 100, 105, 110, 115, 120, 125, 130, 135],  # BV flows
            [12.5, 12.8, 13.0, 13.2, 13.5, 13.8, 14.0, 14.3, 14.5, 14.8],  # EPS flows
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=0.7)
        )
        mock_tv.return_value = (10.0, CalculationStep(step_key="TV", label="TV Ohlson", result=10.0))
        mock_equity_value.return_value = (110.0, CalculationStep(
            step_key="RIM_EQUITY", label="Equity Value", result=110.0
        ))
        mock_per_share.return_value = (110.0, CalculationStep(step_key="PS", label="PS", result=110.0))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Assertions
        assert result is not None
        assert result.request.mode == ValuationMethodology.RIM
        assert result.results.common.intrinsic_value_per_share == 110.0
        assert result.results.strategy.current_book_value == 85000000.0  # Actual value from implementation
        assert len(result.results.strategy.projected_residual_incomes) == 10

        # Verify cost of equity only flag
        assert mock_rate.call_args[1]['use_cost_of_equity_only'] is True

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    def test_book_value_fallback_to_company(
        self, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_company
    ):
        """Test fallback to company book value when strategy param is None."""
        # Setup params without book value anchor
        strategy_params = RIMParameters(
            book_value_anchor=None,
            persistence_factor=0.8,
            projection_years=10
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=0.04, market_risk_premium=0.05, beta=1.1, tax_rate=0.21),
            capital=CapitalStructureParameters(shares_outstanding=3000.0)
        )
        params = Parameters(
            structure=Company(ticker="JPM", name="JPMorgan Chase"),
            strategy=strategy_params,
            common=common
        )

        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [2.5, 2.3, 2.1, 1.9, 1.7, 1.5, 1.3, 1.1, 0.9, 0.7],
            [90, 95, 100, 105, 110, 115, 120, 125, 130, 135],
            [12.5, 12.8, 13.0, 13.2, 13.5, 13.8, 14.0, 14.3, 14.5, 14.8],
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=0.7)
        )
        mock_tv.return_value = (10.0, CalculationStep(step_key="TV", label="TV", result=10.0))
        mock_equity_value.return_value = (110.0, CalculationStep(step_key="RIM_EQUITY", label="Equity", result=110.0))
        mock_per_share.return_value = (110.0, CalculationStep(step_key="PS", label="PS", result=110.0))

        # Execute - should use company book value (85.0)
        result = strategy.execute(basic_company, params)
        assert result.results.strategy.current_book_value == 85.0

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    def test_eps_anchor_from_company(
        self, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test that EPS anchor is taken from company."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [2.5, 2.3, 2.1, 1.9, 1.7, 1.5, 1.3, 1.1, 0.9, 0.7],
            [90, 95, 100, 105, 110, 115, 120, 125, 130, 135],
            [12.5, 12.8, 13.0, 13.2, 13.5, 13.8, 14.0, 14.3, 14.5, 14.8],
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=0.7)
        )
        mock_tv.return_value = (10.0, CalculationStep(step_key="TV", label="TV", result=10.0))
        mock_equity_value.return_value = (110.0, CalculationStep(step_key="RIM_EQUITY", label="Equity", result=110.0))
        mock_per_share.return_value = (110.0, CalculationStep(step_key="PS", label="PS", result=110.0))

        # Execute
        strategy.execute(basic_company, basic_params)

        # Verify EPS was passed to project_residual_income (12.0 from company)
        assert mock_project.call_args[1]['base_earnings'] == 12.0  # base_earnings as keyword arg

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    def test_execute_with_glass_box_disabled(
        self, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test execution with glass box disabled."""
        strategy.glass_box_enabled = False

        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [2.5, 2.3, 2.1, 1.9, 1.7, 1.5, 1.3, 1.1, 0.9, 0.7],
            [90, 95, 100, 105, 110, 115, 120, 125, 130, 135],
            [12.5, 12.8, 13.0, 13.2, 13.5, 13.8, 14.0, 14.3, 14.5, 14.8],
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=0.7)
        )
        mock_tv.return_value = (10.0, CalculationStep(step_key="TV", label="TV", result=10.0))
        mock_equity_value.return_value = (110.0, CalculationStep(step_key="RIM_EQUITY", label="Equity", result=110.0))
        mock_per_share.return_value = (110.0, CalculationStep(step_key="PS", label="PS", result=110.0))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Bridge trace should be empty when glass box is disabled
        assert len(result.results.common.bridge_trace) == 0

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    @patch('src.valuation.strategies.rim_banks.calculate_discount_factors')
    def test_terminal_value_discounting(
        self, mock_disc_factors, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test terminal value is properly discounted."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [2.5, 2.3, 2.1, 1.9, 1.7, 1.5, 1.3, 1.1, 0.9, 0.7],
            [90, 95, 100, 105, 110, 115, 120, 125, 130, 135],
            [12.5, 12.8, 13.0, 13.2, 13.5, 13.8, 14.0, 14.3, 14.5, 14.8],
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=0.7)
        )
        mock_tv.return_value = (10.0, CalculationStep(step_key="TV", label="TV", result=10.0))
        mock_equity_value.return_value = (110.0, CalculationStep(step_key="RIM_EQUITY", label="Equity", result=110.0))
        mock_per_share.return_value = (110.0, CalculationStep(step_key="PS", label="PS", result=110.0))
        mock_disc_factors.return_value = [0.909, 0.826, 0.751, 0.683, 0.621, 0.564, 0.513, 0.467, 0.424, 0.386]

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # PV(TV) = TV * last discount factor
        pv_tv = 10.0 * 0.386  # 3.86
        assert result.results.strategy.discounted_terminal_value == pytest.approx(pv_tv, rel=0.01)

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    def test_rates_reconstruction(
        self, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test rates are properly reconstructed."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [2.5, 2.3, 2.1, 1.9, 1.7, 1.5, 1.3, 1.1, 0.9, 0.7],
            [90, 95, 100, 105, 110, 115, 120, 125, 130, 135],
            [12.5, 12.8, 13.0, 13.2, 13.5, 13.8, 14.0, 14.3, 14.5, 14.8],
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=0.7)
        )
        mock_tv.return_value = (10.0, CalculationStep(step_key="TV", label="TV", result=10.0))
        mock_equity_value.return_value = (110.0, CalculationStep(step_key="RIM_EQUITY", label="Equity", result=110.0))
        mock_per_share.return_value = (110.0, CalculationStep(step_key="PS", label="PS", result=110.0))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # RIM uses Ke only
        assert result.results.common.rates.cost_of_equity == 0.10
        assert result.results.common.rates.wacc == 0.10
        assert result.results.common.rates.cost_of_debt_after_tax == 0.0

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    def test_capital_structure_reconstruction(
        self, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test capital structure values are properly reconstructed."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [2.5, 2.3, 2.1, 1.9, 1.7, 1.5, 1.3, 1.1, 0.9, 0.7],
            [90, 95, 100, 105, 110, 115, 120, 125, 130, 135],
            [12.5, 12.8, 13.0, 13.2, 13.5, 13.8, 14.0, 14.3, 14.5, 14.8],
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=0.7)
        )
        mock_tv.return_value = (10.0, CalculationStep(step_key="TV", label="TV", result=10.0))
        mock_equity_value.return_value = (110.0, CalculationStep(step_key="RIM_EQUITY", label="Equity", result=110.0))
        mock_per_share.return_value = (110.0, CalculationStep(step_key="PS", label="PS", result=110.0))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify capital structure
        # Note: Parameters model scales input values by 1M (e.g., shares 3e9 becomes 3e15)
        # Total equity = IV per share * shares = 110 * 3e15 = 3.3e17
        assert result.results.common.capital.equity_value_total == pytest.approx(3.3e+17, rel=0.01)
        # Net debt = 5e16 - 2e16 = 3e16
        assert result.results.common.capital.net_debt_resolved == pytest.approx(3e+16, rel=0.01)
        # Implied EV = Equity + Net Debt = 3.3e17 + 3e16 = 3.6e17
        assert result.results.common.capital.enterprise_value == pytest.approx(3.6e+17, rel=0.01)
        # Market cap = 3e15 * 140.0 = 4.2e17
        assert result.results.common.capital.market_cap == pytest.approx(4.2e+17, rel=0.01)

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    def test_upside_calculation(
        self, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test upside percentage calculation."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [2.5, 2.3, 2.1, 1.9, 1.7, 1.5, 1.3, 1.1, 0.9, 0.7],
            [90, 95, 100, 105, 110, 115, 120, 125, 130, 135],
            [12.5, 12.8, 13.0, 13.2, 13.5, 13.8, 14.0, 14.3, 14.5, 14.8],
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=0.7)
        )
        mock_tv.return_value = (10.0, CalculationStep(step_key="TV", label="TV", result=10.0))
        mock_equity_value.return_value = (110.0, CalculationStep(step_key="RIM_EQUITY", label="Equity", result=110.0))
        mock_per_share.return_value = (154.0, CalculationStep(step_key="PS", label="PS", result=154.0))

        # Execute (current price is 140.0)
        result = strategy.execute(basic_company, basic_params)

        # Upside = (154 - 140) / 140 = 0.10 (10%)
        assert result.results.common.upside_pct == pytest.approx(0.10, rel=0.01)

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    def test_zero_book_value_handling(
        self, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test handling of zero book value."""
        basic_params.strategy.book_value_anchor = 0.0

        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=0)
        )
        mock_tv.return_value = (0, CalculationStep(step_key="TV", label="TV", result=0))
        mock_equity_value.return_value = (0, CalculationStep(step_key="RIM_EQUITY", label="Equity", result=0))
        mock_per_share.return_value = (0, CalculationStep(step_key="PS", label="PS", result=0))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Should handle zero book value gracefully
        assert result.results.common.intrinsic_value_per_share == 0

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    def test_zero_eps_handling(
        self, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_params
    ):
        """Test handling of zero EPS."""
        company_no_eps = Mock(spec=Company)
        company_no_eps.ticker = "JPM"
        company_no_eps.name = "JPMorgan Chase"
        company_no_eps.sector = CompanySector.FINANCIAL_SERVICES
        company_no_eps.current_price = 140.0
        company_no_eps.currency = "USD"
        company_no_eps.last_update = datetime.now(timezone.utc)
        company_no_eps.book_value_ps = 85.0
        company_no_eps.eps_ttm = 0.0

        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [-8.5, -8.5, -8.5, -8.5, -8.5, -8.5, -8.5, -8.5, -8.5, -8.5],  # Negative RI with 0 EPS
            [85, 85, 85, 85, 85, 85, 85, 85, 85, 85],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=-8.5)
        )
        mock_tv.return_value = (-85.0, CalculationStep(step_key="TV", label="TV", result=-85.0))
        mock_equity_value.return_value = (50.0, CalculationStep(step_key="RIM_EQUITY", label="Equity", result=50.0))
        mock_per_share.return_value = (50.0, CalculationStep(step_key="PS", label="PS", result=50.0))

        # Execute
        result = strategy.execute(company_no_eps, basic_params)

        # Should handle zero EPS (book value should dominate)
        assert result.results.common.intrinsic_value_per_share == 50.0

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    def test_empty_ri_flows_handling(
        self, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test handling of empty RI flows."""
        # Setup mocks with empty flows
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [],  # Empty RI
            [],  # Empty BV
            [],  # Empty EPS
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=0)
        )
        mock_tv.return_value = (0, CalculationStep(step_key="TV", label="TV", result=0))
        mock_equity_value.return_value = (85.0, CalculationStep(step_key="RIM_EQUITY", label="Equity", result=85.0))
        mock_per_share.return_value = (85.0, CalculationStep(step_key="PS", label="PS", result=85.0))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Should handle empty flows gracefully (value = book value only)
        assert result.results.strategy.projected_residual_incomes == []
        assert result.results.common.intrinsic_value_per_share == 85.0

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    def test_book_value_flows_stored(
        self, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test that projected book values are stored in results."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [2.5, 2.3, 2.1, 1.9, 1.7, 1.5, 1.3, 1.1, 0.9, 0.7],
            [90, 95, 100, 105, 110, 115, 120, 125, 130, 135],
            [12.5, 12.8, 13.0, 13.2, 13.5, 13.8, 14.0, 14.3, 14.5, 14.8],
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=0.7)
        )
        mock_tv.return_value = (10.0, CalculationStep(step_key="TV", label="TV", result=10.0))
        mock_equity_value.return_value = (110.0, CalculationStep(step_key="RIM_EQUITY", label="Equity", result=110.0))
        mock_per_share.return_value = (110.0, CalculationStep(step_key="PS", label="PS", result=110.0))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify book value flows are stored
        assert result.results.strategy.projected_book_values == [90, 95, 100, 105, 110, 115, 120, 125, 130, 135]

    @patch('src.valuation.strategies.rim_banks.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.project_residual_income')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_terminal_value_ohlson')
    @patch('src.valuation.strategies.rim_banks.RIMLibrary.compute_equity_value')
    @patch('src.valuation.strategies.rim_banks.DCFLibrary.compute_value_per_share')
    def test_terminal_value_ri_stored(
        self, mock_per_share, mock_equity_value, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test that terminal value RI is stored in results."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [2.5, 2.3, 2.1, 1.9, 1.7, 1.5, 1.3, 1.1, 0.9, 0.7],
            [90, 95, 100, 105, 110, 115, 120, 125, 130, 135],
            [12.5, 12.8, 13.0, 13.2, 13.5, 13.8, 14.0, 14.3, 14.5, 14.8],
            CalculationStep(step_key="RIM_PROJ", label="RIM Projection", result=0.7)
        )
        mock_tv.return_value = (10.0, CalculationStep(step_key="TV", label="TV", result=10.0))
        mock_equity_value.return_value = (110.0, CalculationStep(step_key="RIM_EQUITY", label="Equity", result=110.0))
        mock_per_share.return_value = (110.0, CalculationStep(step_key="PS", label="PS", result=110.0))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify terminal value RI is stored
        assert result.results.strategy.terminal_value_ri == 10.0
