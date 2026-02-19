"""
tests/unit/test_strategies_fundamental_fcff.py

FUNDAMENTAL FCFF (NORMALIZED) STRATEGY TESTS
============================================
Comprehensive test suite for Fundamental FCFF (Normalized) valuation strategy.
Target: ≥90% coverage of src/valuation/strategies/fundamental_fcff.py
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from src.models.company import Company
from src.models.enums import CompanySector, ValuationMethodology
from src.models.glass_box import CalculationStep
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import CapitalStructureParameters, CommonParameters, FinancialRatesParameters
from src.models.parameters.strategies import FCFFNormalizedParameters
from src.valuation.strategies.fundamental_fcff import FundamentalFCFFStrategy


class TestFundamentalFCFFStrategy:
    """Test suite for Fundamental FCFF (Normalized) strategy."""

    @pytest.fixture
    def strategy(self):
        """Create a Fundamental FCFF strategy instance."""
        return FundamentalFCFFStrategy()

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
        company.fcf_ttm = 100000.0
        company.ebit_ttm = 110000.0
        return company

    @pytest.fixture
    def basic_params(self):
        """Create basic Fundamental FCFF parameters."""
        strategy = FCFFNormalizedParameters(fcf_norm=95000.0, projection_years=5, roic=15.0, reinvestment_rate=30.0)
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=0.04, market_risk_premium=0.05, beta=1.2, tax_rate=0.21),
            capital=CapitalStructureParameters(
                shares_outstanding=16000.0, total_debt=120000.0, cash_and_equivalents=50000.0
            ),
        )
        return Parameters(structure=Company(ticker="AAPL", name="Apple Inc."), strategy=strategy, common=common)

    def test_glass_box_property(self, strategy):
        """Test glass_box_enabled property getter/setter."""
        assert strategy.glass_box_enabled is True
        strategy.glass_box_enabled = False
        assert strategy.glass_box_enabled is False
        strategy.glass_box_enabled = True
        assert strategy.glass_box_enabled is True

    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_value_per_share")
    def test_execute_with_valid_inputs(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test successful execution with valid inputs."""
        # Create mock step with get_variable method
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(
            side_effect=lambda key: (
                Mock(value=0.10) if key == "Ke" else Mock(value=0.05) if key == "Kd(1-t)" else Mock(value=0.0)
            )
        )

        # Setup mocks
        mock_rate.return_value = (0.08, mock_wacc_step)
        mock_project.return_value = (
            [98800, 102752, 106862, 111136, 115582],
            CalculationStep(step_key="PROJ", label="Projection", result=115582),
        )
        mock_tv.return_value = (1800000, CalculationStep(step_key="TV", label="Terminal Value", result=1800000), [])
        mock_discount.return_value = (1500000, CalculationStep(step_key="DISC", label="Discounting", result=1500000))
        mock_bridge.return_value = (1430000, CalculationStep(step_key="BRIDGE", label="Equity Bridge", result=1430000))
        mock_per_share.return_value = (89.375, CalculationStep(step_key="PS", label="Per Share", result=89.375))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Assertions
        assert result is not None
        assert result.request.mode == ValuationMethodology.FCFF_NORMALIZED
        assert result.results.common.intrinsic_value_per_share == 89.375
        assert result.results.common.rates.wacc == 0.08
        assert len(result.results.common.bridge_trace) > 0

        # Verify WACC was used (not cost of equity only)
        assert mock_rate.call_args[1]["use_cost_of_equity_only"] is False

    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.project_flows_manual")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_value_per_share")
    def test_execute_with_manual_growth_vector(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project_manual,
        mock_rate,
        strategy,
        basic_company,
    ):
        """Test execution with manual growth vector."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(
            side_effect=lambda key: Mock(value=0.10) if key == "Ke" else Mock(value=0.05)
        )

        # Setup params with manual vector
        strategy_params = FCFFNormalizedParameters(
            fcf_norm=95000.0, projection_years=3, manual_growth_vector=[0.10, 0.08, 0.05]
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=0.04, market_risk_premium=0.05, beta=1.2, tax_rate=0.21),
            capital=CapitalStructureParameters(
                shares_outstanding=16000.0, total_debt=120000.0, cash_and_equivalents=50000.0
            ),
        )
        params = Parameters(
            structure=Company(ticker="AAPL", name="Apple Inc."), strategy=strategy_params, common=common
        )

        # Setup mocks
        mock_rate.return_value = (0.08, mock_wacc_step)
        mock_project_manual.return_value = (
            [104500, 112860, 118503],
            CalculationStep(step_key="PROJ_MANUAL", label="Manual Projection", result=118503),
        )
        mock_tv.return_value = (1700000, CalculationStep(step_key="TV", label="TV", result=1700000), [])
        mock_discount.return_value = (1450000, CalculationStep(step_key="DISC", label="Disc", result=1450000))
        mock_bridge.return_value = (1380000, CalculationStep(step_key="BRIDGE", label="Bridge", result=1380000))
        mock_per_share.return_value = (86.25, CalculationStep(step_key="PS", label="PS", result=86.25))

        # Execute
        result = strategy.execute(basic_company, params)

        # Verify manual projection was used
        mock_project_manual.assert_called_once()
        assert result.results.common.intrinsic_value_per_share == 86.25

    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_value_per_share")
    def test_execute_with_zero_normalized_fcf(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test execution with zero normalized FCF."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.0))

        basic_params.strategy.fcf_norm = 0.0

        # Setup mocks
        mock_rate.return_value = (0.08, mock_wacc_step)
        mock_project.return_value = ([0, 0, 0, 0, 0], CalculationStep(step_key="PROJ", label="Proj", result=0))
        mock_tv.return_value = (0, CalculationStep(step_key="TV", label="TV", result=0), [])
        mock_discount.return_value = (0, CalculationStep(step_key="DISC", label="Disc", result=0))
        mock_bridge.return_value = (0, CalculationStep(step_key="BRIDGE", label="Bridge", result=0))
        mock_per_share.return_value = (0, CalculationStep(step_key="PS", label="PS", result=0))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Should handle zero anchor gracefully
        assert result.results.common.intrinsic_value_per_share == 0

    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_value_per_share")
    def test_execute_with_glass_box_disabled(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test execution with glass box disabled."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10 if key == "Ke" else 0.05))

        strategy.glass_box_enabled = False

        # Setup mocks
        mock_rate.return_value = (0.08, mock_wacc_step)
        mock_project.return_value = (
            [98800, 102752, 106862, 111136, 115582],
            CalculationStep(step_key="PROJ", label="Proj", result=115582),
        )
        mock_tv.return_value = (1800000, CalculationStep(step_key="TV", label="TV", result=1800000), [])
        mock_discount.return_value = (1500000, CalculationStep(step_key="DISC", label="Disc", result=1500000))
        mock_bridge.return_value = (1430000, CalculationStep(step_key="BRIDGE", label="Bridge", result=1430000))
        mock_per_share.return_value = (89.375, CalculationStep(step_key="PS", label="PS", result=89.375))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Bridge trace should be empty when glass box is disabled
        assert len(result.results.common.bridge_trace) == 0
        assert result.results.common.intrinsic_value_per_share == 89.375

    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_value_per_share")
    @patch("src.valuation.strategies.fundamental_fcff.calculate_discount_factors")
    def test_terminal_value_weight_calculation(
        self,
        mock_disc_factors,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test terminal value weight percentage calculation."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10 if key == "Ke" else 0.05))

        # Setup mocks
        mock_rate.return_value = (0.08, mock_wacc_step)
        mock_project.return_value = (
            [98800, 102752, 106862, 111136, 115582],
            CalculationStep(step_key="PROJ", label="Proj", result=115582),
        )
        mock_tv.return_value = (1800000, CalculationStep(step_key="TV", label="TV", result=1800000), [])
        mock_discount.return_value = (1500000, CalculationStep(step_key="DISC", label="Disc", result=1500000))
        mock_bridge.return_value = (1430000, CalculationStep(step_key="BRIDGE", label="Bridge", result=1430000))
        mock_per_share.return_value = (89.375, CalculationStep(step_key="PS", label="PS", result=89.375))
        mock_disc_factors.return_value = [0.926, 0.857, 0.794, 0.735, 0.681]

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # TV weight = PV(TV) / EV
        pv_tv = 1800000 * 0.681  # 1225800
        expected_weight = pv_tv / 1500000  # ~0.817
        assert result.results.strategy.tv_weight_pct == pytest.approx(expected_weight, rel=0.01)

    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_value_per_share")
    def test_rates_reconstruction(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test rates are properly reconstructed from calculation steps."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(
            side_effect=lambda key: (
                Mock(value=0.10) if key == "Ke" else Mock(value=0.05) if key == "Kd(1-t)" else Mock(value=0.0)
            )
        )

        # Setup mocks
        mock_rate.return_value = (0.08, mock_wacc_step)
        mock_project.return_value = (
            [98800, 102752, 106862, 111136, 115582],
            CalculationStep(step_key="PROJ", label="Proj", result=115582),
        )
        mock_tv.return_value = (1800000, CalculationStep(step_key="TV", label="TV", result=1800000), [])
        mock_discount.return_value = (1500000, CalculationStep(step_key="DISC", label="Disc", result=1500000))
        mock_bridge.return_value = (1430000, CalculationStep(step_key="BRIDGE", label="Bridge", result=1430000))
        mock_per_share.return_value = (89.375, CalculationStep(step_key="PS", label="PS", result=89.375))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify rates are properly extracted
        assert result.results.common.rates.wacc == 0.08
        assert result.results.common.rates.cost_of_equity == 0.10
        assert result.results.common.rates.cost_of_debt_after_tax == 0.05

    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_value_per_share")
    def test_capital_structure_reconstruction(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test capital structure values are properly reconstructed."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10 if key == "Ke" else 0.05))

        # Setup mocks
        mock_rate.return_value = (0.08, mock_wacc_step)
        mock_project.return_value = (
            [98800, 102752, 106862, 111136, 115582],
            CalculationStep(step_key="PROJ", label="Proj", result=115582),
        )
        mock_tv.return_value = (1800000, CalculationStep(step_key="TV", label="TV", result=1800000), [])
        mock_discount.return_value = (1500000, CalculationStep(step_key="DISC", label="Disc", result=1500000))
        mock_bridge.return_value = (1430000, CalculationStep(step_key="BRIDGE", label="Bridge", result=1430000))
        mock_per_share.return_value = (89.375, CalculationStep(step_key="PS", label="PS", result=89.375))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify capital structure
        # Note: Parameters are automatically scaled by 1e6 (scale="million")
        # total_debt=120000 -> 120000000000, cash=50000 -> 50000000000, shares=16000 -> 16000000000
        assert result.results.common.capital.enterprise_value == 1500000
        assert result.results.common.capital.equity_value_total == 1430000
        assert result.results.common.capital.net_debt_resolved == 70000000000.0  # 120000000000 - 50000000000
        assert result.results.common.capital.market_cap == 2400000000000.0  # 16000000000 * 150.0

    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_value_per_share")
    def test_normalized_fcf_stored_in_results(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test that normalized FCF is stored in strategy results."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10 if key == "Ke" else 0.05))

        # Setup mocks
        mock_rate.return_value = (0.08, mock_wacc_step)
        mock_project.return_value = (
            [98800, 102752, 106862, 111136, 115582],
            CalculationStep(step_key="PROJ", label="Proj", result=115582),
        )
        mock_tv.return_value = (1800000, CalculationStep(step_key="TV", label="TV", result=1800000), [])
        mock_discount.return_value = (1500000, CalculationStep(step_key="DISC", label="Disc", result=1500000))
        mock_bridge.return_value = (1430000, CalculationStep(step_key="BRIDGE", label="Bridge", result=1430000))
        mock_per_share.return_value = (89.375, CalculationStep(step_key="PS", label="PS", result=89.375))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Verify normalized FCF is stored
        # Note: Parameters are automatically scaled by 1e6 (scale="million")
        # fcf_norm=95000 -> 95000000000
        assert result.results.strategy.normalized_fcf_used == 95000000000.0

    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_value_per_share")
    def test_empty_flows_handling(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test handling of empty projected flows."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.0))

        # Setup mocks with empty flows
        mock_rate.return_value = (0.08, mock_wacc_step)
        mock_project.return_value = ([], CalculationStep(step_key="PROJ", label="Proj", result=0))
        mock_tv.return_value = (0, CalculationStep(step_key="TV", label="TV", result=0), [])
        mock_discount.return_value = (0, CalculationStep(step_key="DISC", label="Disc", result=0))
        mock_bridge.return_value = (0, CalculationStep(step_key="BRIDGE", label="Bridge", result=0))
        mock_per_share.return_value = (0, CalculationStep(step_key="PS", label="PS", result=0))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Should handle empty flows gracefully
        assert result.results.strategy.projected_flows == []
        assert result.results.common.intrinsic_value_per_share == 0

    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_value_per_share")
    def test_growth_calculated_from_roic_and_reinvestment_rate(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project,
        mock_rate,
        strategy,
        basic_company,
    ):
        """Test that growth is calculated from ROIC × Reinvestment Rate (Damodaran)."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10 if key == "Ke" else 0.05))

        # Setup params with ROIC and Reinvestment Rate (no manual growth)
        # roic=15.0 becomes 0.15 after scaling, reinvestment_rate=30.0 becomes 0.30
        strategy_params = FCFFNormalizedParameters(
            fcf_norm=95000.0, projection_years=5, roic=15.0, reinvestment_rate=30.0
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=0.04, market_risk_premium=0.05, beta=1.2, tax_rate=0.21),
            capital=CapitalStructureParameters(
                shares_outstanding=16000.0, total_debt=120000.0, cash_and_equivalents=50000.0
            ),
        )
        params = Parameters(
            structure=Company(ticker="AAPL", name="Apple Inc."), strategy=strategy_params, common=common
        )

        # Setup mocks
        mock_rate.return_value = (0.08, mock_wacc_step)
        mock_project.return_value = (
            [98800, 102752, 106862, 111136, 115582],
            CalculationStep(step_key="PROJ", label="Projection", result=115582),
        )
        mock_tv.return_value = (1800000, CalculationStep(step_key="TV", label="TV", result=1800000), [])
        mock_discount.return_value = (1500000, CalculationStep(step_key="DISC", label="Disc", result=1500000))
        mock_bridge.return_value = (1430000, CalculationStep(step_key="BRIDGE", label="Bridge", result=1430000))
        mock_per_share.return_value = (89.375, CalculationStep(step_key="PS", label="PS", result=89.375))

        # Execute
        result = strategy.execute(basic_company, params)

        # Verify growth was computed: g = 0.15 × 0.30 = 0.045
        assert result is not None
        assert result.results.common.intrinsic_value_per_share == 89.375

        # Verify that growth_rate was dynamically set based on ROIC × RR
        # This is the key test: the strategy modifies params.strategy.growth_rate internally
        assert params.strategy.growth_rate == pytest.approx(0.045, rel=0.01)

    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_value_per_share")
    def test_growth_consistency_check_with_manual_override(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project,
        mock_rate,
        strategy,
        basic_company,
    ):
        """Test consistency check when user provides both ROIC/RR and manual growth."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10 if key == "Ke" else 0.05))

        # Setup params with ROIC, Reinvestment Rate AND manual growth (inconsistent)
        # g_derived = 0.15 × 0.30 = 0.045, but user overrides with 0.06
        # roic=15.0 becomes 0.15, reinvestment_rate=30.0 becomes 0.30, growth_rate=6.0 becomes 0.06
        strategy_params = FCFFNormalizedParameters(
            fcf_norm=95000.0, projection_years=5, roic=15.0, reinvestment_rate=30.0, growth_rate=6.0
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=0.04, market_risk_premium=0.05, beta=1.2, tax_rate=0.21),
            capital=CapitalStructureParameters(
                shares_outstanding=16000.0, total_debt=120000.0, cash_and_equivalents=50000.0
            ),
        )
        params = Parameters(
            structure=Company(ticker="AAPL", name="Apple Inc."), strategy=strategy_params, common=common
        )

        # Setup mocks
        mock_rate.return_value = (0.08, mock_wacc_step)
        mock_project.return_value = (
            [98800, 102752, 106862, 111136, 115582],
            CalculationStep(step_key="PROJ", label="Projection", result=115582),
        )
        mock_tv.return_value = (1800000, CalculationStep(step_key="TV", label="TV", result=1800000), [])
        mock_discount.return_value = (1500000, CalculationStep(step_key="DISC", label="Disc", result=1500000))
        mock_bridge.return_value = (1430000, CalculationStep(step_key="BRIDGE", label="Bridge", result=1430000))
        mock_per_share.return_value = (89.375, CalculationStep(step_key="PS", label="PS", result=89.375))

        # Execute
        result = strategy.execute(basic_company, params)

        # Manual override should take precedence
        assert result is not None
        # The growth_rate should still be 0.06 (manual override)
        assert params.strategy.growth_rate == 0.06

    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fundamental_fcff.CommonLibrary.compute_equity_bridge")
    @patch("src.valuation.strategies.fundamental_fcff.DCFLibrary.compute_value_per_share")
    def test_fallback_when_roic_or_rr_missing(
        self,
        mock_per_share,
        mock_bridge,
        mock_discount,
        mock_tv,
        mock_project,
        mock_rate,
        strategy,
        basic_company,
    ):
        """Test that execution continues when ROIC or RR is None (no calculation)."""
        mock_wacc_step = Mock(spec=CalculationStep)
        mock_wacc_step.get_variable = Mock(side_effect=lambda key: Mock(value=0.10 if key == "Ke" else 0.05))

        # Setup params with only manual growth (old behavior - backward compatible)
        # growth_rate=5.0 becomes 0.05 after scaling
        strategy_params = FCFFNormalizedParameters(fcf_norm=95000.0, projection_years=5, growth_rate=5.0)
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=0.04, market_risk_premium=0.05, beta=1.2, tax_rate=0.21),
            capital=CapitalStructureParameters(
                shares_outstanding=16000.0, total_debt=120000.0, cash_and_equivalents=50000.0
            ),
        )
        params = Parameters(
            structure=Company(ticker="AAPL", name="Apple Inc."), strategy=strategy_params, common=common
        )

        # Setup mocks
        mock_rate.return_value = (0.08, mock_wacc_step)
        mock_project.return_value = (
            [98800, 102752, 106862, 111136, 115582],
            CalculationStep(step_key="PROJ", label="Projection", result=115582),
        )
        mock_tv.return_value = (1800000, CalculationStep(step_key="TV", label="TV", result=1800000), [])
        mock_discount.return_value = (1500000, CalculationStep(step_key="DISC", label="Disc", result=1500000))
        mock_bridge.return_value = (1430000, CalculationStep(step_key="BRIDGE", label="Bridge", result=1430000))
        mock_per_share.return_value = (89.375, CalculationStep(step_key="PS", label="PS", result=89.375))

        # Execute - should work with old behavior (no ROIC/RR)
        result = strategy.execute(basic_company, params)

        # Should execute normally without ROIC calculation
        assert result is not None
        assert result.results.common.intrinsic_value_per_share == 89.375
        # Growth rate should remain as provided (0.05)
        assert params.strategy.growth_rate == 0.05
