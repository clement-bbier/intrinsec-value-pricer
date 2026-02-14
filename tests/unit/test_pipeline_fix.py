"""
tests/unit/test_pipeline_fix.py

PIPELINE FIX VALIDATION TESTS
==============================
Role: Validates the fixes for the disconnected pipe issue.
Coverage:
  1. ExtensionTexts label completeness.
  2. InputFactory extension key mapping (GLOBAL, no prefix).
  3. Auto Form extension checkbox keys.
  4. Orchestrator _process_extensions signature accepts ticker.
  5. Inputs summary emoji removal.
"""

import inspect

import pytest

from src.i18n import ExtensionTexts
from src.models.parameters.options import (
    BacktestParameters,
    MCParameters,
    PeersParameters,
    ScenariosParameters,
    SensitivityParameters,
    SOTPParameters,
)


class TestExtensionTextsCompleteness:
    """All six extension labels must be defined in ExtensionTexts."""

    def test_title_defined(self):
        """TITLE must be a non-empty string."""
        assert isinstance(ExtensionTexts.TITLE, str)
        assert len(ExtensionTexts.TITLE) > 0

    def test_monte_carlo_label(self):
        """MONTE_CARLO label must exist."""
        assert hasattr(ExtensionTexts, "MONTE_CARLO")
        assert isinstance(ExtensionTexts.MONTE_CARLO, str)

    def test_sensitivity_label(self):
        """SENSITIVITY label must exist."""
        assert hasattr(ExtensionTexts, "SENSITIVITY")
        assert isinstance(ExtensionTexts.SENSITIVITY, str)

    def test_scenarios_label(self):
        """SCENARIOS label must exist."""
        assert hasattr(ExtensionTexts, "SCENARIOS")
        assert isinstance(ExtensionTexts.SCENARIOS, str)

    def test_backtest_label(self):
        """BACKTEST label must exist."""
        assert hasattr(ExtensionTexts, "BACKTEST")
        assert isinstance(ExtensionTexts.BACKTEST, str)

    def test_peers_label(self):
        """PEERS label must exist."""
        assert hasattr(ExtensionTexts, "PEERS")
        assert isinstance(ExtensionTexts.PEERS, str)

    def test_sotp_label(self):
        """SOTP label must exist."""
        assert hasattr(ExtensionTexts, "SOTP")
        assert isinstance(ExtensionTexts.SOTP, str)


class TestExtensionBundleUIKeys:
    """Extension UIKey suffixes must be GLOBAL (no strategy prefix)."""

    def test_mc_enable_key(self):
        """Monte Carlo 'enabled' UIKey suffix must be 'mc_enable'."""
        from src.models.parameters.input_metadata import UIKey

        meta = next(
            (m for m in MCParameters.model_fields["enabled"].metadata if isinstance(m, UIKey)),
            None,
        )
        assert meta is not None
        assert meta.suffix == "mc_enable"

    def test_sensitivity_enable_key(self):
        """Sensitivity 'enabled' UIKey suffix must be 'sens_enable'."""
        from src.models.parameters.input_metadata import UIKey

        meta = next(
            (m for m in SensitivityParameters.model_fields["enabled"].metadata if isinstance(m, UIKey)),
            None,
        )
        assert meta is not None
        assert meta.suffix == "sens_enable"

    def test_scenario_enable_key(self):
        """Scenarios 'enabled' UIKey suffix must be 'scenario_enable'."""
        from src.models.parameters.input_metadata import UIKey

        meta = next(
            (m for m in ScenariosParameters.model_fields["enabled"].metadata if isinstance(m, UIKey)),
            None,
        )
        assert meta is not None
        assert meta.suffix == "scenario_enable"

    def test_backtest_enable_key(self):
        """Backtest 'enabled' UIKey suffix must be 'bt_enable'."""
        from src.models.parameters.input_metadata import UIKey

        meta = next(
            (m for m in BacktestParameters.model_fields["enabled"].metadata if isinstance(m, UIKey)),
            None,
        )
        assert meta is not None
        assert meta.suffix == "bt_enable"

    def test_peer_enable_key(self):
        """Peers 'enabled' UIKey suffix must be 'peer_enable'."""
        from src.models.parameters.input_metadata import UIKey

        meta = next(
            (m for m in PeersParameters.model_fields["enabled"].metadata if isinstance(m, UIKey)),
            None,
        )
        assert meta is not None
        assert meta.suffix == "peer_enable"

    def test_sotp_enable_key(self):
        """SOTP 'enabled' UIKey suffix must be 'sotp_enable'."""
        from src.models.parameters.input_metadata import UIKey

        meta = next(
            (m for m in SOTPParameters.model_fields["enabled"].metadata if isinstance(m, UIKey)),
            None,
        )
        assert meta is not None
        assert meta.suffix == "sotp_enable"

    def test_mc_iterations_key(self):
        """Monte Carlo 'iterations' UIKey suffix must be 'mc_sims'."""
        from src.models.parameters.input_metadata import UIKey

        meta = next(
            (m for m in MCParameters.model_fields["iterations"].metadata if isinstance(m, UIKey)),
            None,
        )
        assert meta is not None
        assert meta.suffix == "mc_sims"

    def test_sensitivity_steps_key(self):
        """Sensitivity 'steps' UIKey suffix must be 'sens_range'."""
        from src.models.parameters.input_metadata import UIKey

        meta = next(
            (m for m in SensitivityParameters.model_fields["steps"].metadata if isinstance(m, UIKey)),
            None,
        )
        assert meta is not None
        assert meta.suffix == "sens_range"

    def test_sotp_discount_key(self):
        """SOTP 'conglomerate_discount' UIKey suffix must be 'sotp_discount'."""
        from src.models.parameters.input_metadata import UIKey

        meta = next(
            (m for m in SOTPParameters.model_fields["conglomerate_discount"].metadata if isinstance(m, UIKey)),
            None,
        )
        assert meta is not None
        assert meta.suffix == "sotp_discount"


class TestInputFactoryExtensionMapping:
    """InputFactory must pull extensions with no prefix (GLOBAL keys)."""

    def test_build_request_calls_pull_model_without_prefix(self):
        """Extension _pull_model call must use prefix=None."""
        source = inspect.getsource(
            __import__("app.controllers.input_factory", fromlist=["InputFactory"]).InputFactory.build_request
        )
        assert "prefix=None" in source or "_pull_model(ExtensionBundleParameters)" in source


class TestAutoFormSimplified:
    """Auto form must NOT contain extension checkboxes (Auto mode is basic only)."""

    @pytest.fixture
    def auto_form_source(self):
        """Load auto_form source for static analysis."""
        return inspect.getsource(
            __import__("app.views.inputs.auto_form", fromlist=["render_auto_form"]).render_auto_form
        )

    def test_no_extension_checkboxes(self, auto_form_source):
        """Auto form must not contain extension checkbox widgets."""
        assert "st.checkbox" not in auto_form_source

    def test_no_extension_title(self, auto_form_source):
        """Auto form must not reference ExtensionTexts."""
        assert "ExtensionTexts" not in auto_form_source

    def test_contains_basic_info(self, auto_form_source):
        """Auto form must still display basic company and methodology info."""
        assert "state.ticker" in auto_form_source
        assert "state.selected_methodology" in auto_form_source


class TestOrchestratorPipelineLogging:
    """Orchestrator must call QuantLogger pipeline stages."""

    @pytest.fixture
    def orchestrator_source(self):
        """Load orchestrator module source."""
        import src.valuation.orchestrator as mod

        return inspect.getsource(mod)

    def test_log_stage_start_called(self, orchestrator_source):
        """run() must call log_stage_start."""
        assert "log_stage_start" in orchestrator_source

    def test_log_data_fetching_called(self, orchestrator_source):
        """run() must call log_data_fetching."""
        assert "log_data_fetching" in orchestrator_source

    def test_log_parameter_resolution_called(self, orchestrator_source):
        """run() must call log_parameter_resolution."""
        assert "log_parameter_resolution" in orchestrator_source

    def test_log_strategy_execution_called(self, orchestrator_source):
        """run() must call log_strategy_execution."""
        assert "log_strategy_execution" in orchestrator_source

    def test_log_extension_processing_called(self, orchestrator_source):
        """_process_extensions must call log_extension_processing."""
        assert "log_extension_processing" in orchestrator_source

    def test_log_final_packaging_called(self, orchestrator_source):
        """run() must call log_final_packaging."""
        assert "log_final_packaging" in orchestrator_source

    def test_process_extensions_accepts_ticker(self):
        """_process_extensions must accept a ticker parameter."""
        from src.valuation.orchestrator import ValuationOrchestrator

        sig = inspect.signature(ValuationOrchestrator._process_extensions)
        assert "ticker" in sig.parameters

    def test_extension_timing_present(self, orchestrator_source):
        """Each extension must measure compute time (not 0ms)."""
        # Verify time.time() is called around each extension
        assert orchestrator_source.count("ext_start = time.time()") >= 4


class TestInputsSummaryNoEmojis:
    """Inputs summary view must not contain emoji characters."""

    def test_no_emojis_in_inputs_summary(self):
        """inputs_summary.py must be free of emoji characters."""
        source = inspect.getsource(
            __import__("app.views.results.pillars.inputs_summary", fromlist=["render_detailed_inputs"])
        )
        forbidden = ["\U0001f3db", "\u2696", "\U0001f680", "\U0001f4da"]
        for emoji in forbidden:
            assert emoji not in source, f"Found forbidden emoji {repr(emoji)} in inputs_summary.py"
