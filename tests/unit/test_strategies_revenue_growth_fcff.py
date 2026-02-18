"""
tests/unit/test_strategies_revenue_growth_fcff.py

REVENUE GROWTH FCFF STRATEGY TESTS
==================================
Comprehensive test suite for Revenue Growth FCFF valuation strategy.
Target: ≥90% coverage of src/valuation/strategies/revenue_growth_fcff.py
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from src.models.company import Company
from src.models.enums import CompanySector, ValuationMethodology
from src.models.glass_box import CalculationStep
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import CapitalStructureParameters, CommonParameters, FinancialRatesParameters
from src.models.parameters.strategies import FCFFGrowthParameters
from src.valuation.strategies.revenue_growth_fcff import RevenueGrowthFCFFStrategy


class TestRevenueGrowthFCFFStrategy:
    """Test suite for Revenue Growth FCFF strategy."""

    @pytest.fixture
    def strategy(self):
        """Create a Revenue Growth FCFF strategy instance."""
        return RevenueGrowthFCFFStrategy()

    @pytest.fixture
    def basic_company(self):
        """Create a basic company with financial data."""
        company = Mock(spec=Company)
        company.ticker = "TSLA"
        company.name = "Tesla Inc."
        company.sector = CompanySector.TECHNOLOGY
        company.current_price = 200.0
        company.currency = "USD"
        company.last_update = datetime.now(timezone.utc)
        company.revenue_ttm = 80000.0
        company.fcf_ttm = 8000.0
        return company

    @pytest.fixture
    def basic_params(self):
        """Create basic Revenue Growth FCFF parameters."""
        strategy = FCFFGrowthParameters(
            revenue_ttm=80000.0, revenue_growth_rate=20.0, target_fcf_margin=15.0, projection_years=5
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=4.0, market_risk_premium=6.0, beta=1.5, tax_rate=21.0),
            capital=CapitalStructureParameters(
                shares_outstanding=3000.0, total_debt=15000.0, cash_and_equivalents=5000.0
            ),
        )
        return Parameters(structure=Company(ticker="TSLA", name="Tesla Inc."), strategy=strategy, common=common)

    def test_glass_box_property(self, strategy):
        """Test glass_box_enabled property getter/setter."""
        assert strategy.glass_box_enabled is True
        strategy.glass_box_enabled = False
        assert strategy.glass_box_enabled is False
        strategy.glass_box_enabled = True
        assert strategy.glass_box_enabled is True

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    def test_execute_with_valid_inputs(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test successful execution with valid inputs."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(
            side_effect=lambda key: (
                Mock(value=0.13) if key == "Ke" else Mock(value=0.06) if key == "Kd(1-t)" else Mock(value=0.0)
            )
        )

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        # project_flows_revenue_model returns: flows, revenues, margins, step
        mock_project_rev.return_value = (
            [9600, 11520, 13440, 14400, 15000],  # FCF flows
            [96000, 115200, 134400, 144000, 150000],  # Revenues
            [0.10, 0.10, 0.10, 0.10, 0.10],  # Margins
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Assertions
        assert result is not None
        assert result.request.mode == ValuationMethodology.FCFF_GROWTH
        assert result.results.common.intrinsic_value_per_share == 46.67
        assert result.results.strategy.projected_revenues == [96000, 115200, 134400, 144000, 150000]
        assert result.results.strategy.projected_margins == [0.10, 0.10, 0.10, 0.10, 0.10]

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    def test_revenue_fallback_to_company_data(
        self, mock_per_share, mock_bridge, mock_discount, mock_tv, mock_project_rev, mock_rate, strategy, basic_company
    ):
        """Test fallback to company revenue when strategy param is None."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10))

        # Setup params without revenue_ttm
        strategy_params = FCFFGrowthParameters(
            revenue_ttm=None, revenue_growth_rate=20.0, target_fcf_margin=15.0, projection_years=5
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=4.0, market_risk_premium=6.0, beta=1.5, tax_rate=21.0),
            capital=CapitalStructureParameters(
                shares_outstanding=3000.0, total_debt=15000.0, cash_and_equivalents=5000.0
            ),
        )
        params = Parameters(
            structure=Company(ticker="TSLA", name="Tesla Inc."), strategy=strategy_params, common=common
        )

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [9600, 11520, 13440, 14400, 15000],
            [96000, 115200, 134400, 144000, 150000],
            [0.10, 0.10, 0.10, 0.10, 0.10],
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))

        # Execute - should use company revenue (80000)
        result = strategy.execute(basic_company, params)
        assert result.results.common.intrinsic_value_per_share == 46.67

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    def test_current_margin_calculation(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test current margin calculation from FCF and Revenue."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10))

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [9600, 11520, 13440, 14400, 15000],
            [96000, 115200, 134400, 144000, 150000],
            [0.10, 0.10, 0.10, 0.10, 0.10],
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))

        # Execute
        strategy.execute(basic_company, basic_params)

        # Current margin = FCF / Revenue = 8000 / 80000 = 0.10 (10%)
        # This is passed to project_flows_revenue_model
        assert mock_project_rev.called

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    @patch("src.valuation.strategies.revenue_growth_fcff.ModelDefaults")
    def test_target_margin_fallback_to_defaults(
        self,
        mock_defaults,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
    ):
        """Test fallback to default target margin when not provided."""
        mock_defaults.DEFAULT_FCF_MARGIN_TARGET = 0.12
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10))

        # Setup params without target margin
        strategy_params = FCFFGrowthParameters(
            revenue_ttm=80000.0, revenue_growth_rate=20.0, target_fcf_margin=None, projection_years=5
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=4.0, market_risk_premium=6.0, beta=1.5, tax_rate=21.0),
            capital=CapitalStructureParameters(shares_outstanding=3000.0),
        )
        params = Parameters(
            structure=Company(ticker="TSLA", name="Tesla Inc."), strategy=strategy_params, common=common
        )

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [9600, 11520, 13440, 14400, 15000],
            [96000, 115200, 134400, 144000, 150000],
            [0.10, 0.11, 0.12, 0.12, 0.12],
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))

        # Execute
        result = strategy.execute(basic_company, params)
        assert result is not None

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    def test_execute_with_glass_box_disabled(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test execution with glass box disabled."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10))

        strategy.glass_box_enabled = False

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [9600, 11520, 13440, 14400, 15000],
            [96000, 115200, 134400, 144000, 150000],
            [0.10, 0.10, 0.10, 0.10, 0.10],
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Bridge trace should be empty when glass box is disabled
        assert len(result.results.common.bridge_trace) == 0

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    @patch("src.valuation.strategies.revenue_growth_fcff.calculate_discount_factors")
    def test_terminal_value_weight_calculation(
        self,
        mock_disc_factors,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test terminal value weight percentage calculation."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10))

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [9600, 11520, 13440, 14400, 15000],
            [96000, 115200, 134400, 144000, 150000],
            [0.10, 0.10, 0.10, 0.10, 0.10],
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))
        mock_disc_factors.return_value = [0.909, 0.826, 0.751, 0.683, 0.621]

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # TV weight = PV(TV) / EV
        pv_tv = 200000 * 0.621  # 124200
        expected_weight = pv_tv / 150000  # ~0.828
        assert result.results.strategy.tv_weight_pct == pytest.approx(expected_weight, rel=0.01)

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    def test_target_margin_reached_stored(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test that target margin reached is stored in results."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10))

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [9600, 11520, 13440, 14400, 15000],
            [96000, 115200, 134400, 144000, 150000],
            [0.10, 0.12, 0.14, 0.15, 0.15],  # Converging to 0.15
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify target margin reached (last margin value)
        assert result.results.strategy.target_margin_reached == 0.15

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    def test_capital_structure_reconstruction(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test capital structure values are properly reconstructed."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10))

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [9600, 11520, 13440, 14400, 15000],
            [96000, 115200, 134400, 144000, 150000],
            [0.10, 0.10, 0.10, 0.10, 0.10],
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify capital structure
        # Note: Parameters are automatically scaled by 1e6 (scale="million")
        # shares_outstanding=3000 -> 3000000000, total_debt=15000 -> 15000000000, cash=5000 -> 5000000000
        assert result.results.common.capital.enterprise_value == 150000
        assert result.results.common.capital.equity_value_total == 140000
        assert result.results.common.capital.net_debt_resolved == 10000000000.0  # 15000000000 - 5000000000
        assert result.results.common.capital.market_cap == 600000000000.0  # 3000000000 * 200.0

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    def test_zero_revenue_handling(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test handling of zero revenue."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.0))

        basic_params.strategy.revenue_ttm = 0.0

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=0),
        )
        mock_tv.return_value = (0, CalculationStep(step_key="TV", label="TV", result=0))
        mock_discount.return_value = (0, CalculationStep(step_key="DISC", label="Disc", result=0))
        mock_bridge.return_value = (0, CalculationStep(step_key="BRIDGE", label="Bridge", result=0))
        mock_per_share.return_value = (0, CalculationStep(step_key="PS", label="PS", result=0))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Should handle zero revenue gracefully
        assert result.results.common.intrinsic_value_per_share == 0

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    def test_empty_margins_handling(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test handling when margins list is empty."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10))

        # Setup mocks with empty margins
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [9600, 11520, 13440, 14400, 15000],
            [96000, 115200, 134400, 144000, 150000],
            [],  # Empty margins list
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Should use target margin from params as fallback
        assert result.results.strategy.target_margin_reached == 0.15

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    def test_wcr_ratio_passed_to_projection(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
    ):
        """Test that wcr_ratio is passed to project_flows_revenue_model."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10))

        # Setup params with wcr_ratio
        strategy_params = FCFFGrowthParameters(
            revenue_ttm=80000.0,
            revenue_growth_rate=20.0,
            target_fcf_margin=15.0,
            projection_years=5,
            wcr_to_revenue_ratio=5.0,
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=4.0, market_risk_premium=6.0, beta=1.5, tax_rate=21.0),
            capital=CapitalStructureParameters(shares_outstanding=3000.0),
        )
        params = Parameters(
            structure=Company(ticker="TSLA", name="Tesla Inc."), strategy=strategy_params, common=common
        )

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [9000, 10500, 12000, 13000, 13500],  # FCF with WCR adjustment
            [96000, 115200, 134400, 144000, 150000],
            [0.10, 0.10, 0.10, 0.10, 0.10],
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))

        # Execute
        result = strategy.execute(basic_company, params)

        # Verify wcr_ratio was passed to project_flows_revenue_model
        assert mock_project_rev.called
        call_kwargs = mock_project_rev.call_args.kwargs
        assert "wcr_ratio" in call_kwargs
        assert call_kwargs["wcr_ratio"] == 0.05  # 5% normalized to 0.05

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    def test_wcr_ratio_none_fallback(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
    ):
        """Test that wcr_ratio=None is passed correctly (no WCR adjustment)."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10))

        # Setup params without wcr_ratio
        strategy_params = FCFFGrowthParameters(
            revenue_ttm=80000.0,
            revenue_growth_rate=20.0,
            target_fcf_margin=15.0,
            projection_years=5,
            wcr_to_revenue_ratio=None,
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=4.0, market_risk_premium=6.0, beta=1.5, tax_rate=21.0),
            capital=CapitalStructureParameters(shares_outstanding=3000.0),
        )
        params = Parameters(
            structure=Company(ticker="TSLA", name="Tesla Inc."), strategy=strategy_params, common=common
        )

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [9600, 11520, 13440, 14400, 15000],  # FCF without WCR adjustment
            [96000, 115200, 134400, 144000, 150000],
            [0.10, 0.10, 0.10, 0.10, 0.10],
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))

        # Execute
        result = strategy.execute(basic_company, params)

        # Verify wcr_ratio was passed as None
        assert mock_project_rev.called
        call_kwargs = mock_project_rev.call_args.kwargs
        assert "wcr_ratio" in call_kwargs
        assert call_kwargs["wcr_ratio"] is None

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    def test_historical_wcr_ratio_fallback(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
    ):
        """Test that historical WCR ratio is used as fallback when user doesn't provide one."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10))

        # Setup params without wcr_ratio (None)
        strategy_params = FCFFGrowthParameters(
            revenue_ttm=80000.0,
            revenue_growth_rate=20.0,
            target_fcf_margin=15.0,
            projection_years=5,
            wcr_to_revenue_ratio=None,  # User didn't provide
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=4.0, market_risk_premium=6.0, beta=1.5, tax_rate=21.0),
            capital=CapitalStructureParameters(shares_outstanding=3000.0),
        )
        params = Parameters(
            structure=Company(ticker="TSLA", name="Tesla Inc."), strategy=strategy_params, common=common
        )

        # Mock company with historical WCR ratio
        basic_company.historical_wcr_ratio = 0.08  # 8% historical ratio

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [8800, 10560, 12320, 13200, 13800],  # FCF with WCR adjustment
            [96000, 115200, 134400, 144000, 150000],
            [0.10, 0.10, 0.10, 0.10, 0.10],
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))

        # Execute
        result = strategy.execute(basic_company, params)

        # Verify historical wcr_ratio was used
        assert mock_project_rev.called
        call_kwargs = mock_project_rev.call_args.kwargs
        assert "wcr_ratio" in call_kwargs
        assert call_kwargs["wcr_ratio"] == 0.08  # Historical ratio was used

        # Verify result is successful
        assert result is not None
        assert result.results is not None

    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.project_flows_revenue_model")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.revenue_growth_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.revenue_growth_fcff.DCFLibrary.compute_value_per_share")
    def test_user_wcr_overrides_historical(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_rev,
        mock_rate,
        strategy,
        basic_company,
    ):
        """Test that user-provided WCR ratio takes precedence over historical."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10))

        # Setup params with wcr_ratio (user provided)
        strategy_params = FCFFGrowthParameters(
            revenue_ttm=80000.0,
            revenue_growth_rate=20.0,
            target_fcf_margin=15.0,
            projection_years=5,
            wcr_to_revenue_ratio=5.0,  # User provided 5%
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=4.0, market_risk_premium=6.0, beta=1.5, tax_rate=21.0),
            capital=CapitalStructureParameters(shares_outstanding=3000.0),
        )
        params = Parameters(
            structure=Company(ticker="TSLA", name="Tesla Inc."), strategy=strategy_params, common=common
        )

        # Mock company with historical WCR ratio (should be ignored)
        basic_company.historical_wcr_ratio = 0.08  # 8% historical ratio

        # Setup mocks
        mock_rate.return_value = (0.10, mock_wacc_step)
        mock_project_rev.return_value = (
            [9000, 10500, 12000, 13000, 13500],
            [96000, 115200, 134400, 144000, 150000],
            [0.10, 0.10, 0.10, 0.10, 0.10],
            CalculationStep(step_key="PROJ_REV", label="Revenue Projection", result=15000),
        )
        mock_tv.return_value = (200000, CalculationStep(step_key="TV", label="TV", result=200000))
        mock_discount.return_value = (150000, CalculationStep(step_key="DISC", label="Disc", result=150000))
        mock_bridge.return_value = (140000, CalculationStep(step_key="BRIDGE", label="Bridge", result=140000))
        mock_per_share.return_value = (46.67, CalculationStep(step_key="PS", label="PS", result=46.67))

        # Execute
        result = strategy.execute(basic_company, params)

        # Verify user-provided wcr_ratio was used (not historical)
        assert mock_project_rev.called
        call_kwargs = mock_project_rev.call_args.kwargs
        assert "wcr_ratio" in call_kwargs
        assert call_kwargs["wcr_ratio"] == 0.05  # User's 5% was used, not historical 8%
