"""
tests/unit/test_strategies_ddm.py

DIVIDEND DISCOUNT MODEL (DDM) STRATEGY TESTS
============================================
Comprehensive test suite for DDM valuation strategy.
Target: ≥90% coverage of src/valuation/strategies/ddm.py
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from src.models.company import Company
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.strategies import DDMParameters
from src.models.parameters.common import CommonParameters, FinancialRatesParameters, CapitalStructureParameters
from src.models.enums import ValuationMethodology, CompanySector
from src.models.glass_box import CalculationStep
from src.valuation.strategies.ddm import DividendDiscountStrategy


class TestDDMStrategy:
    """Test suite for Dividend Discount Model strategy."""

    @pytest.fixture
    def strategy(self):
        """Create a DDM strategy instance."""
        return DividendDiscountStrategy()

    @pytest.fixture
    def basic_company(self):
        """Create a basic company with dividend data."""
        # Create a mock object with the required financial attributes
        company = Mock(spec=Company)
        company.ticker = "AAPL"
        company.name = "Apple Inc."
        company.sector = CompanySector.TECHNOLOGY
        company.current_price = 150.0
        company.currency = "USD"
        company.last_update = datetime.now(timezone.utc)
        company.dividend_share = 3.00
        company.eps_ttm = 6.00
        return company

    @pytest.fixture
    def basic_params(self):
        """Create basic DDM parameters."""
        strategy = DDMParameters(
            dividend_per_share=3.00,
            projection_years=5
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(
                risk_free_rate=0.04,
                market_risk_premium=0.05,
                beta=1.2,
                tax_rate=0.21
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

    @patch('src.valuation.strategies.ddm.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.ddm.DCFLibrary.project_flows_simple')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_terminal_value')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_discounting')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_value_per_share')
    def test_execute_with_valid_inputs(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate, 
        strategy, basic_company, basic_params
    ):
        """Test successful execution with valid inputs."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(
            step_key="KE", label="Cost of Equity", result=0.10,
            theoretical_formula="CAPM", actual_calculation="0.04 + 1.2 × 0.05"
        ))
        mock_project.return_value = ([3150, 3300, 3450, 3600, 3750], CalculationStep(
            step_key="PROJ", label="Projection", result=3750
        ))
        mock_tv.return_value = (50000, CalculationStep(
            step_key="TV", label="Terminal Value", result=50000
        ))
        mock_discount.return_value = (60000, CalculationStep(
            step_key="DISC", label="Discounting", result=60000
        ))
        mock_per_share.return_value = (3.75, CalculationStep(
            step_key="PS", label="Per Share", result=3.75
        ))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Assertions
        assert result is not None
        assert result.request.mode == ValuationMethodology.DDM
        assert result.results.common.intrinsic_value_per_share == 3.75
        assert result.results.common.rates.cost_of_equity == 0.10
        assert len(result.results.common.bridge_trace) > 0
        assert result.results.strategy.projected_dividends == [3150, 3300, 3450, 3600, 3750]
        
        # Verify mocks called
        mock_rate.assert_called_once()
        mock_project.assert_called_once()
        mock_tv.assert_called_once()
        mock_discount.assert_called_once()
        mock_per_share.assert_called_once()

    @patch('src.valuation.strategies.ddm.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.ddm.DCFLibrary.project_flows_manual')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_terminal_value')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_discounting')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_value_per_share')
    def test_execute_with_manual_growth_vector(
        self, mock_per_share, mock_discount, mock_tv, mock_project_manual, mock_rate,
        strategy, basic_company
    ):
        """Test execution with manual growth vector."""
        # Setup params with manual vector
        strategy_params = DDMParameters(
            dividend_per_share=3.00,
            projection_years=3,
            manual_growth_vector=[0.10, 0.08, 0.05]
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=0.04, market_risk_premium=0.05, beta=1.2),
            capital=CapitalStructureParameters(shares_outstanding=16000.0)
        )
        params = Parameters(
            structure=Company(ticker="AAPL", name="Apple Inc."),
            strategy=strategy_params,
            common=common
        )

        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project_manual.return_value = ([3300, 3564, 3742], CalculationStep(
            step_key="PROJ_MANUAL", label="Manual Projection", result=3742
        ))
        mock_tv.return_value = (45000, CalculationStep(step_key="TV", label="TV", result=45000))
        mock_discount.return_value = (50000, CalculationStep(step_key="DISC", label="Disc", result=50000))
        mock_per_share.return_value = (3.12, CalculationStep(step_key="PS", label="PS", result=3.12))

        # Execute
        result = strategy.execute(basic_company, params)

        # Verify manual projection was used
        mock_project_manual.assert_called_once()
        assert result.results.common.intrinsic_value_per_share == 3.12

    @patch('src.valuation.strategies.ddm.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.ddm.DCFLibrary.project_flows_simple')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_terminal_value')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_discounting')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_value_per_share')
    def test_execute_with_missing_dividend(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate,
        strategy, basic_params
    ):
        """Test execution with company missing dividend data."""
        company_no_div = Mock(spec=Company)
        company_no_div.ticker = "TSLA"
        company_no_div.name = "Tesla Inc."
        company_no_div.sector = CompanySector.TECHNOLOGY
        company_no_div.current_price = 200.0
        company_no_div.currency = "USD"
        company_no_div.last_update = datetime.now(timezone.utc)
        company_no_div.dividend_share = None
        company_no_div.eps_ttm = 5.00

        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = ([0, 0, 0, 0, 0], CalculationStep(step_key="PROJ", label="Proj", result=0))
        mock_tv.return_value = (0, CalculationStep(step_key="TV", label="TV", result=0))
        mock_discount.return_value = (0, CalculationStep(step_key="DISC", label="Disc", result=0))
        mock_per_share.return_value = (0, CalculationStep(step_key="PS", label="PS", result=0))

        # Execute
        result = strategy.execute(company_no_div, basic_params)

        # Should handle gracefully with zero dividend
        assert result.results.common.intrinsic_value_per_share == 0

    @patch('src.valuation.strategies.ddm.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.ddm.DCFLibrary.project_flows_simple')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_terminal_value')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_discounting')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_value_per_share')
    def test_execute_uses_user_dividend_override(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test that user-provided dividend overrides company data."""
        # Company has dividend of 3.0, but user overrides to 4.0
        basic_params.strategy.dividend_per_share = 4.00

        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = ([4200, 4400, 4600, 4800, 5000], CalculationStep(
            step_key="PROJ", label="Proj", result=5000
        ))
        mock_tv.return_value = (60000, CalculationStep(step_key="TV", label="TV", result=60000))
        mock_discount.return_value = (70000, CalculationStep(step_key="DISC", label="Disc", result=70000))
        mock_per_share.return_value = (4.37, CalculationStep(step_key="PS", label="PS", result=4.37))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify user override was used (4.0 * 16000 shares = 64000 total dividend mass)
        assert result.results.common.intrinsic_value_per_share == 4.37

    @patch('src.valuation.strategies.ddm.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.ddm.DCFLibrary.project_flows_simple')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_terminal_value')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_discounting')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_value_per_share')
    def test_execute_with_glass_box_disabled(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test execution with glass box disabled."""
        strategy.glass_box_enabled = False

        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = ([3000, 3150, 3300, 3450, 3600], CalculationStep(
            step_key="PROJ", label="Proj", result=3600
        ))
        mock_tv.return_value = (50000, CalculationStep(step_key="TV", label="TV", result=50000))
        mock_discount.return_value = (60000, CalculationStep(step_key="DISC", label="Disc", result=60000))
        mock_per_share.return_value = (3.75, CalculationStep(step_key="PS", label="PS", result=3.75))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Bridge trace should be empty when glass box is disabled
        assert len(result.results.common.bridge_trace) == 0
        assert result.results.common.intrinsic_value_per_share == 3.75

    @patch('src.valuation.strategies.ddm.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.ddm.DCFLibrary.project_flows_simple')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_terminal_value')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_discounting')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_value_per_share')
    @patch('src.valuation.strategies.ddm.calculate_discount_factors')
    def test_payout_ratio_calculation(
        self, mock_disc_factors, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test payout ratio calculation in results."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = ([3000, 3150, 3300, 3450, 3600], CalculationStep(
            step_key="PROJ", label="Proj", result=3600
        ))
        mock_tv.return_value = (50000, CalculationStep(step_key="TV", label="TV", result=50000))
        mock_discount.return_value = (60000, CalculationStep(step_key="DISC", label="Disc", result=60000))
        mock_per_share.return_value = (3.75, CalculationStep(step_key="PS", label="PS", result=3.75))
        mock_disc_factors.return_value = [0.909, 0.826, 0.751, 0.683, 0.621]

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Payout ratio = Dividend / EPS = 3.0 / 6.0 = 0.5
        assert result.results.strategy.payout_ratio_observed == pytest.approx(0.5, rel=0.01)

    @patch('src.valuation.strategies.ddm.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.ddm.DCFLibrary.project_flows_simple')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_terminal_value')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_discounting')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_value_per_share')
    @patch('src.valuation.strategies.ddm.calculate_discount_factors')
    def test_terminal_value_weight_calculation(
        self, mock_disc_factors, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test terminal value weight percentage calculation."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = ([3000, 3150, 3300, 3450, 3600], CalculationStep(
            step_key="PROJ", label="Proj", result=3600
        ))
        mock_tv.return_value = (50000, CalculationStep(step_key="TV", label="TV", result=50000))
        mock_discount.return_value = (60000, CalculationStep(step_key="DISC", label="Disc", result=60000))
        mock_per_share.return_value = (3.75, CalculationStep(step_key="PS", label="PS", result=3.75))
        mock_disc_factors.return_value = [0.909, 0.826, 0.751, 0.683, 0.621]

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # TV weight = PV(TV) / Total Equity Value
        pv_tv = 50000 * 0.621  # 31050
        expected_weight = pv_tv / 60000  # ~0.5175
        assert result.results.strategy.tv_weight_pct == pytest.approx(expected_weight, rel=0.01)

    @patch('src.valuation.strategies.ddm.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.ddm.DCFLibrary.project_flows_simple')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_terminal_value')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_discounting')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_value_per_share')
    def test_upside_percentage_calculation(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test upside percentage calculation."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = ([3000, 3150, 3300, 3450, 3600], CalculationStep(
            step_key="PROJ", label="Proj", result=3600
        ))
        mock_tv.return_value = (50000, CalculationStep(step_key="TV", label="TV", result=50000))
        mock_discount.return_value = (60000, CalculationStep(step_key="DISC", label="Disc", result=60000))
        mock_per_share.return_value = (180.0, CalculationStep(step_key="PS", label="PS", result=180.0))

        # Execute (current price is 150.0)
        result = strategy.execute(basic_company, basic_params)

        # Upside = (180 - 150) / 150 = 0.20 (20%)
        assert result.results.common.upside_pct == pytest.approx(0.20, rel=0.01)

    @patch('src.valuation.strategies.ddm.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.ddm.DCFLibrary.project_flows_simple')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_terminal_value')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_discounting')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_value_per_share')
    def test_capital_structure_reconstruction(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test capital structure values are properly reconstructed."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = ([3000, 3150, 3300, 3450, 3600], CalculationStep(
            step_key="PROJ", label="Proj", result=3600
        ))
        mock_tv.return_value = (50000, CalculationStep(step_key="TV", label="TV", result=50000))
        mock_discount.return_value = (60000, CalculationStep(step_key="DISC", label="Disc", result=60000))
        mock_per_share.return_value = (3.75, CalculationStep(step_key="PS", label="PS", result=3.75))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify capital structure
        assert result.results.common.capital.equity_value_total == 60000
        assert result.results.common.capital.net_debt_resolved == pytest.approx(70000000000, rel=0.01)  # 120B - 50B
        assert result.results.common.capital.enterprise_value == pytest.approx(70000060000, rel=0.01)  # 60000 + 70B
        assert result.results.common.capital.market_cap == pytest.approx(2400000000000, rel=0.01)  # 16B * 150.0

    @patch('src.valuation.strategies.ddm.CommonLibrary.resolve_discount_rate')
    @patch('src.valuation.strategies.ddm.DCFLibrary.project_flows_simple')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_terminal_value')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_discounting')
    @patch('src.valuation.strategies.ddm.DCFLibrary.compute_value_per_share')
    def test_empty_flows_handling(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate,
        strategy, basic_company, basic_params
    ):
        """Test handling of empty projected flows."""
        # Setup mocks with empty flows
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = ([], CalculationStep(step_key="PROJ", label="Proj", result=0))
        mock_tv.return_value = (0, CalculationStep(step_key="TV", label="TV", result=0))
        mock_discount.return_value = (0, CalculationStep(step_key="DISC", label="Disc", result=0))
        mock_per_share.return_value = (0, CalculationStep(step_key="PS", label="PS", result=0))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Should handle empty flows gracefully
        assert result.results.strategy.projected_flows == []
        assert result.results.common.intrinsic_value_per_share == 0
