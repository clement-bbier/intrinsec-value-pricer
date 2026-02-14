"""
tests/unit/test_strategies_fcfe.py

FREE CASH FLOW TO EQUITY (FCFE) STRATEGY TESTS
==============================================
Comprehensive test suite for FCFE valuation strategy.
Target: ≥90% coverage of src/valuation/strategies/fcfe.py
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from src.models.company import Company
from src.models.enums import CompanySector, ValuationMethodology
from src.models.glass_box import CalculationStep
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import CapitalStructureParameters, CommonParameters, FinancialRatesParameters
from src.models.parameters.strategies import FCFEParameters
from src.valuation.strategies.fcfe import FCFEStrategy


class TestFCFEStrategy:
    """Test suite for Free Cash Flow to Equity strategy."""

    @pytest.fixture
    def strategy(self):
        """Create an FCFE strategy instance."""
        return FCFEStrategy()

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
        company.net_income_ttm = 95000.0
        return company

    @pytest.fixture
    def basic_params(self):
        """Create basic FCFE parameters."""
        strategy = FCFEParameters(fcfe_anchor=80000.0, projection_years=5, growth_rate=0.05)
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

    @patch("src.valuation.strategies.fcfe.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_value_per_share")
    def test_execute_with_valid_inputs(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate, strategy, basic_company, basic_params
    ):
        """Test successful execution with valid inputs."""
        # Setup mocks
        mock_rate.return_value = (
            0.10,
            CalculationStep(
                step_key="KE",
                label="Cost of Equity",
                result=0.10,
                theoretical_formula="CAPM",
                actual_calculation="0.04 + 1.2 × 0.05",
            ),
        )
        mock_project.return_value = (
            [84000, 88200, 92610, 97240, 102102],
            CalculationStep(step_key="PROJ", label="Projection", result=102102),
        )
        mock_tv.return_value = (1500000, CalculationStep(step_key="TV", label="Terminal Value", result=1500000))
        mock_discount.return_value = (950000, CalculationStep(step_key="DISC", label="Discounting", result=950000))
        mock_per_share.return_value = (62.5, CalculationStep(step_key="PS", label="Per Share", result=62.5))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Assertions
        assert result is not None
        assert result.request.mode == ValuationMethodology.FCFE
        assert result.results.common.intrinsic_value_per_share == 62.5
        assert result.results.common.rates.cost_of_equity == 0.10
        assert len(result.results.common.bridge_trace) > 0

        # Verify mocks called with use_cost_of_equity_only=True
        assert mock_rate.call_args[1]["use_cost_of_equity_only"] is True

    @patch("src.valuation.strategies.fcfe.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.project_flows_manual")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_value_per_share")
    def test_execute_with_manual_growth_vector(
        self, mock_per_share, mock_discount, mock_tv, mock_project_manual, mock_rate, strategy, basic_company
    ):
        """Test execution with manual growth vector."""
        # Setup params with manual vector
        strategy_params = FCFEParameters(
            fcfe_anchor=80000.0, projection_years=3, manual_growth_vector=[0.10, 0.08, 0.05]
        )
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=0.04, market_risk_premium=0.05, beta=1.2),
            capital=CapitalStructureParameters(shares_outstanding=16000.0, cash_and_equivalents=50000.0),
        )
        params = Parameters(
            structure=Company(ticker="AAPL", name="Apple Inc."), strategy=strategy_params, common=common
        )

        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project_manual.return_value = (
            [88000, 95040, 99792],
            CalculationStep(step_key="PROJ_MANUAL", label="Manual Projection", result=99792),
        )
        mock_tv.return_value = (1400000, CalculationStep(step_key="TV", label="TV", result=1400000))
        mock_discount.return_value = (900000, CalculationStep(step_key="DISC", label="Disc", result=900000))
        mock_per_share.return_value = (59.4, CalculationStep(step_key="PS", label="PS", result=59.4))

        # Execute
        result = strategy.execute(basic_company, params)

        # Verify manual projection was used
        mock_project_manual.assert_called_once()
        assert result.results.common.intrinsic_value_per_share == 59.4

    @patch("src.valuation.strategies.fcfe.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_value_per_share")
    def test_execute_with_zero_fcfe_anchor(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate, strategy, basic_company, basic_params
    ):
        """Test execution with zero FCFE anchor."""
        basic_params.strategy.fcfe_anchor = 0.0

        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = ([0, 0, 0, 0, 0], CalculationStep(step_key="PROJ", label="Proj", result=0))
        mock_tv.return_value = (0, CalculationStep(step_key="TV", label="TV", result=0))
        mock_discount.return_value = (0, CalculationStep(step_key="DISC", label="Disc", result=0))
        mock_per_share.return_value = (3.125, CalculationStep(step_key="PS", label="PS", result=3.125))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Should handle zero anchor gracefully (cash only adds value)
        assert result.results.common.intrinsic_value_per_share == 3.125

    @patch("src.valuation.strategies.fcfe.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_value_per_share")
    def test_execute_with_glass_box_disabled(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate, strategy, basic_company, basic_params
    ):
        """Test execution with glass box disabled."""
        strategy.glass_box_enabled = False

        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [84000, 88200, 92610, 97240, 102102],
            CalculationStep(step_key="PROJ", label="Proj", result=102102),
        )
        mock_tv.return_value = (1500000, CalculationStep(step_key="TV", label="TV", result=1500000))
        mock_discount.return_value = (950000, CalculationStep(step_key="DISC", label="Disc", result=950000))
        mock_per_share.return_value = (62.5, CalculationStep(step_key="PS", label="PS", result=62.5))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Bridge trace should be empty when glass box is disabled
        assert len(result.results.common.bridge_trace) == 0
        assert result.results.common.intrinsic_value_per_share == 62.5

    @patch("src.valuation.strategies.fcfe.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_value_per_share")
    def test_equity_value_includes_cash(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate, strategy, basic_company, basic_params
    ):
        """Test that total equity value includes cash correctly."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [84000, 88200, 92610, 97240, 102102],
            CalculationStep(step_key="PROJ", label="Proj", result=102102),
        )
        mock_tv.return_value = (1500000, CalculationStep(step_key="TV", label="TV", result=1500000))
        # PV of operating FCFE
        mock_discount.return_value = (950000, CalculationStep(step_key="DISC", label="Disc", result=950000))
        mock_per_share.return_value = (62.5, CalculationStep(step_key="PS", label="PS", result=62.5))

        # Execute
        strategy.execute(basic_company, basic_params)

        # Total equity = PV(FCFE) + Cash
        # Note: cash_and_equivalents=50000.0 gets scaled to 50000000000 via BaseNormalizedModel
        # (BaseNormalizedModel applies scale="million" multiplier: 50000 * 1_000_000 = 50B)
        pv_equity = 950000
        scaled_cash = 50000 * 1_000_000  # 50000000000
        expected_equity_value = pv_equity + scaled_cash

        # This value is passed to compute_value_per_share
        mock_per_share.assert_called_once()
        call_args = mock_per_share.call_args[0]
        assert call_args[0] == expected_equity_value

    @patch("src.valuation.strategies.fcfe.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_value_per_share")
    @patch("src.valuation.strategies.fcfe.calculate_discount_factors")
    def test_terminal_value_weight_calculation(
        self,
        mock_disc_factors,
        mock_per_share,
        mock_discount,
        mock_tv,
        mock_project,
        mock_rate,
        strategy,
        basic_company,
        basic_params,
    ):
        """Test terminal value weight percentage calculation."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [84000, 88200, 92610, 97240, 102102],
            CalculationStep(step_key="PROJ", label="Proj", result=102102),
        )
        mock_tv.return_value = (1500000, CalculationStep(step_key="TV", label="TV", result=1500000))
        mock_discount.return_value = (950000, CalculationStep(step_key="DISC", label="Disc", result=950000))
        mock_per_share.return_value = (62.5, CalculationStep(step_key="PS", label="PS", result=62.5))
        mock_disc_factors.return_value = [0.909, 0.826, 0.751, 0.683, 0.621]

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # TV weight = PV(TV) / Total PV(Operating FCFE)
        pv_tv = 1500000 * 0.621  # 931500
        expected_weight = pv_tv / 950000  # ~0.981
        assert result.results.strategy.tv_weight_pct == pytest.approx(expected_weight, rel=0.01)

    @patch("src.valuation.strategies.fcfe.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_value_per_share")
    def test_capital_structure_reconstruction(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate, strategy, basic_company, basic_params
    ):
        """Test capital structure values are properly reconstructed."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [84000, 88200, 92610, 97240, 102102],
            CalculationStep(step_key="PROJ", label="Proj", result=102102),
        )
        mock_tv.return_value = (1500000, CalculationStep(step_key="TV", label="TV", result=1500000))
        mock_discount.return_value = (950000, CalculationStep(step_key="DISC", label="Disc", result=950000))
        mock_per_share.return_value = (62.5, CalculationStep(step_key="PS", label="PS", result=62.5))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Calculate expected values accounting for BaseNormalizedModel scaling
        # (scale="million" multiplier applies: value * 1_000_000)
        scale_factor = 1_000_000
        pv_equity = 950000
        cash_base = 50000
        debt_base = 120000
        shares_base = 16000
        current_price = 150.0

        scaled_cash = cash_base * scale_factor  # 50B
        scaled_debt = debt_base * scale_factor  # 120B
        scaled_shares = shares_base * scale_factor  # 16B

        expected_equity_value = pv_equity + scaled_cash
        expected_net_debt = scaled_debt - scaled_cash
        expected_ev = expected_equity_value + scaled_debt - scaled_cash
        expected_market_cap = scaled_shares * current_price

        assert result.results.common.capital.equity_value_total == expected_equity_value
        assert result.results.common.capital.net_debt_resolved == expected_net_debt
        assert result.results.common.capital.enterprise_value == expected_ev
        assert result.results.common.capital.market_cap == expected_market_cap

    @patch("src.valuation.strategies.fcfe.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_value_per_share")
    def test_upside_calculation(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate, strategy, basic_company, basic_params
    ):
        """Test upside percentage calculation."""
        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [84000, 88200, 92610, 97240, 102102],
            CalculationStep(step_key="PROJ", label="Proj", result=102102),
        )
        mock_tv.return_value = (1500000, CalculationStep(step_key="TV", label="TV", result=1500000))
        mock_discount.return_value = (950000, CalculationStep(step_key="DISC", label="Disc", result=950000))
        mock_per_share.return_value = (180.0, CalculationStep(step_key="PS", label="PS", result=180.0))

        # Execute (current price is 150.0)
        result = strategy.execute(basic_company, basic_params)

        # Upside = (180 - 150) / 150 = 0.20 (20%)
        assert result.results.common.upside_pct == pytest.approx(0.20, rel=0.01)

    @patch("src.valuation.strategies.fcfe.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_value_per_share")
    def test_empty_flows_handling(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate, strategy, basic_company, basic_params
    ):
        """Test handling of empty projected flows."""
        # Setup mocks with empty flows
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = ([], CalculationStep(step_key="PROJ", label="Proj", result=0))
        mock_tv.return_value = (0, CalculationStep(step_key="TV", label="TV", result=0))
        mock_discount.return_value = (0, CalculationStep(step_key="DISC", label="Disc", result=0))
        mock_per_share.return_value = (3.125, CalculationStep(step_key="PS", label="PS", result=3.125))

        # Execute
        result = strategy.execute(basic_company, basic_params)

        # Should handle empty flows gracefully
        assert result.results.strategy.projected_flows == []
        assert result.results.common.intrinsic_value_per_share == 3.125

    @patch("src.valuation.strategies.fcfe.CommonLibrary.resolve_discount_rate")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.project_flows_simple")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_terminal_value")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_discounting")
    @patch("src.valuation.strategies.fcfe.DCFLibrary.compute_value_per_share")
    def test_no_cash_handling(
        self, mock_per_share, mock_discount, mock_tv, mock_project, mock_rate, strategy, basic_company
    ):
        """Test execution with zero cash."""
        # Setup params with no cash
        strategy_params = FCFEParameters(fcfe_anchor=80000.0, projection_years=5)
        common = CommonParameters(
            rates=FinancialRatesParameters(risk_free_rate=0.04, market_risk_premium=0.05, beta=1.2),
            capital=CapitalStructureParameters(
                shares_outstanding=16000.0, total_debt=120000.0, cash_and_equivalents=0.0
            ),
        )
        params = Parameters(
            structure=Company(ticker="AAPL", name="Apple Inc."), strategy=strategy_params, common=common
        )

        # Setup mocks
        mock_rate.return_value = (0.10, CalculationStep(step_key="KE", label="Ke", result=0.10))
        mock_project.return_value = (
            [84000, 88200, 92610, 97240, 102102],
            CalculationStep(step_key="PROJ", label="Proj", result=102102),
        )
        mock_tv.return_value = (1500000, CalculationStep(step_key="TV", label="TV", result=1500000))
        mock_discount.return_value = (950000, CalculationStep(step_key="DISC", label="Disc", result=950000))
        mock_per_share.return_value = (59.375, CalculationStep(step_key="PS", label="PS", result=59.375))

        # Execute
        strategy.execute(basic_company, params)

        # Total equity should equal PV(FCFE) only (no cash to add)
        mock_per_share.assert_called_once()
        call_args = mock_per_share.call_args[0]
        assert call_args[0] == 950000
