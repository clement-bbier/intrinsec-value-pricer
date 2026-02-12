"""
tests/unit/test_projection_years_flow.py

Tests for projection_years flow from sidebar to request.

Validates:
- ExpertTerminalBase accepts external projection_years via set_projection_years()
- projection_years propagates correctly to _build_request()
- Auto mode creates request with correct projection_years
"""

import pytest
from unittest.mock import patch, MagicMock

from src.domain.models import (
    ValuationMode,
    InputSource,
    DCFParameters,
    CoreRateParameters,
    GrowthParameters,
    MonteCarloConfig,
    SOTPParameters,
    ScenarioParameters,
    ValuationRequest,
)


class TestExpertTerminalProjectionYears:
    """Tests for projection_years handling in ExpertTerminalBase."""

    def test_default_projection_years(self):
        """Terminal should have default projection_years of 5."""
        from app.ui.base.expert_terminal import ExpertTerminalBase

        class DummyTerminal(ExpertTerminalBase):
            MODE = ValuationMode.FCFF_STANDARD
            DISPLAY_NAME = "Test"

            def render_model_inputs(self):
                return {}

        terminal = DummyTerminal("TEST")
        assert terminal._projection_years == 5

    def test_set_projection_years(self):
        """set_projection_years() should update the internal value."""
        from app.ui.base.expert_terminal import ExpertTerminalBase

        class DummyTerminal(ExpertTerminalBase):
            MODE = ValuationMode.FCFF_STANDARD
            DISPLAY_NAME = "Test"

            def render_model_inputs(self):
                return {}

        terminal = DummyTerminal("TEST")
        terminal.set_projection_years(10)
        assert terminal._projection_years == 10

    def test_projection_years_injected_in_build_request(self):
        """_build_request() should use projection_years from set_projection_years()."""
        from app.ui.base.expert_terminal import ExpertTerminalBase

        class DummyTerminal(ExpertTerminalBase):
            MODE = ValuationMode.FCFF_STANDARD
            DISPLAY_NAME = "Test"

            def render_model_inputs(self):
                return {"fcf_growth_rate": 0.05}

        terminal = DummyTerminal("TEST")
        terminal.set_projection_years(8)
        terminal._collected_data = {"fcf_growth_rate": 0.05}

        request = terminal._build_request()

        assert request.projection_years == 8
        assert request.ticker == "TEST"
        assert request.mode == ValuationMode.FCFF_STANDARD
        assert request.input_source == InputSource.MANUAL


class TestAutoModeProjectionYears:
    """Tests for projection_years in auto mode request creation."""

    def test_auto_request_uses_projection_years(self):
        """Auto mode should create request with specified projection_years."""
        projection_years = 7

        params = DCFParameters(
            rates=CoreRateParameters(),
            growth=GrowthParameters(projection_years=projection_years),
            monte_carlo=MonteCarloConfig(enable_monte_carlo=False),
            scenarios=ScenarioParameters(enabled=False),
            sotp=SOTPParameters(enabled=False),
        )

        request = ValuationRequest(
            ticker="AAPL",
            projection_years=projection_years,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
            manual_params=params,
        )

        assert request.projection_years == 7
        assert request.manual_params.growth.projection_years == 7

    def test_projection_years_range(self):
        """Projection years should accept values in valid range (1-15)."""
        for years in [1, 5, 10, 15]:
            params = DCFParameters(
                rates=CoreRateParameters(),
                growth=GrowthParameters(projection_years=years),
                monte_carlo=MonteCarloConfig(enable_monte_carlo=False),
                scenarios=ScenarioParameters(enabled=False),
                sotp=SOTPParameters(enabled=False),
            )

            request = ValuationRequest(
                ticker="TEST",
                projection_years=years,
                mode=ValuationMode.FCFF_STANDARD,
                input_source=InputSource.AUTO,
                manual_params=params,
            )

            assert request.projection_years == years
