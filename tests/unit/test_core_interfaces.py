"""
tests/unit/test_core_interfaces.py

COMPREHENSIVE TEST SUITE FOR CORE INTERFACES
============================================
Role: Tests all abstract interfaces and their implementations.
Coverage Target: 90%+ line coverage for src/core/interfaces.py
Standards: pytest best practices with concrete implementations
"""

from unittest.mock import Mock

import pytest

from src.core.interfaces import DataProviderProtocol, IResultRenderer, IUIProgressHandler, NullProgressHandler
from src.models.valuation import ValuationResult

# ==============================================================================
# 1. DATA PROVIDER PROTOCOL TESTS
# ==============================================================================

@pytest.mark.unit
class TestDataProviderProtocol:
    """Test DataProviderProtocol implementation."""

    def test_protocol_has_get_company_name_method(self):
        """Test that protocol defines get_company_name method."""
        # Create a mock that implements the protocol
        mock_provider = Mock(spec=DataProviderProtocol)
        mock_provider.get_company_name = Mock(return_value="Apple Inc.")

        # Verify method exists and works
        assert hasattr(mock_provider, 'get_company_name')
        assert mock_provider.get_company_name("AAPL") == "Apple Inc."

    def test_concrete_implementation_satisfies_protocol(self):
        """Test that a concrete implementation can satisfy the protocol."""

        class ConcreteProvider:
            def get_company_name(self, ticker: str) -> str:
                return f"Company for {ticker}"

        provider = ConcreteProvider()
        # Should work as a protocol implementation
        result = provider.get_company_name("MSFT")
        assert result == "Company for MSFT"


# ==============================================================================
# 2. PROGRESS HANDLER INTERFACE TESTS
# ==============================================================================

@pytest.mark.unit
class TestIUIProgressHandler:
    """Test IUIProgressHandler abstract interface."""

    def test_abstract_interface_cannot_be_instantiated(self):
        """Test that abstract interface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IUIProgressHandler()

    def test_concrete_implementation_must_implement_all_methods(self):
        """Test that concrete implementation must implement all abstract methods."""

        class IncompleteHandler(IUIProgressHandler):
            # Missing implementations - should not work
            pass

        with pytest.raises(TypeError):
            IncompleteHandler()

    def test_complete_concrete_implementation(self):
        """Test a complete concrete implementation."""

        class ConcreteHandler(IUIProgressHandler):
            def __init__(self):
                self.messages = []

            def start_status(self, label: str) -> 'ConcreteHandler':
                self.messages.append(f"START: {label}")
                return self

            def update_status(self, message: str) -> None:
                self.messages.append(f"UPDATE: {message}")

            def complete_status(self, label: str, state: str = "complete") -> None:
                self.messages.append(f"COMPLETE: {label} ({state})")

            def error_status(self, label: str) -> None:
                self.messages.append(f"ERROR: {label}")

        handler = ConcreteHandler()
        handler.start_status("Test Task")
        handler.update_status("Processing...")
        handler.complete_status("Test Task")
        handler.error_status("Failed Task")

        assert len(handler.messages) == 4
        assert "START: Test Task" in handler.messages
        assert "UPDATE: Processing..." in handler.messages
        assert "COMPLETE: Test Task (complete)" in handler.messages
        assert "ERROR: Failed Task" in handler.messages

    def test_context_manager_support(self):
        """Test that handler can be used as context manager."""

        class ContextHandler(IUIProgressHandler):
            def __init__(self):
                self.entered = False
                self.exited = False

            def start_status(self, label: str) -> 'ContextHandler':
                return self

            def update_status(self, message: str) -> None:
                pass

            def complete_status(self, label: str, state: str = "complete") -> None:
                pass

            def error_status(self, label: str) -> None:
                pass

            def __enter__(self):
                self.entered = True
                return super().__enter__()

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.exited = True
                return super().__exit__(exc_type, exc_val, exc_tb)

        handler = ContextHandler()
        with handler:
            assert handler.entered
        assert handler.exited


@pytest.mark.unit
class TestNullProgressHandler:
    """Test NullProgressHandler implementation (Null Object Pattern)."""

    def test_can_instantiate_null_handler(self):
        """Test that NullProgressHandler can be instantiated."""
        handler = NullProgressHandler()
        assert isinstance(handler, IUIProgressHandler)

    def test_start_status_returns_self(self):
        """Test that start_status returns self for chaining."""
        handler = NullProgressHandler()
        result = handler.start_status("Task")
        assert result is handler

    def test_update_status_does_nothing(self):
        """Test that update_status is a no-op."""
        handler = NullProgressHandler()
        # Should not raise any exceptions
        handler.update_status("Some message")

    def test_complete_status_does_nothing(self):
        """Test that complete_status is a no-op."""
        handler = NullProgressHandler()
        handler.complete_status("Task")
        handler.complete_status("Task", state="success")

    def test_error_status_does_nothing(self):
        """Test that error_status is a no-op."""
        handler = NullProgressHandler()
        handler.error_status("Failed Task")

    def test_can_be_used_as_context_manager(self):
        """Test that NullProgressHandler works as context manager."""
        handler = NullProgressHandler()
        with handler as h:
            assert h is handler
            handler.start_status("Task")
            handler.update_status("Working...")
            handler.complete_status("Task")

    def test_chaining_works(self):
        """Test that method chaining works properly."""
        handler = NullProgressHandler()
        result = handler.start_status("Task 1").start_status("Task 2")
        assert result is handler

    def test_null_handler_in_production_scenario(self):
        """Test NullProgressHandler in a typical usage scenario."""
        handler = NullProgressHandler()

        # Simulate a workflow
        handler.start_status("Loading data")
        handler.update_status("Fetching from API...")
        handler.update_status("Parsing response...")
        handler.complete_status("Loading data", state="complete")

        handler.start_status("Calculating valuation")
        handler.update_status("Running DCF...")
        # Simulate error
        handler.error_status("Calculating valuation")

        # No exceptions should be raised


# ==============================================================================
# 3. RESULT RENDERER INTERFACE TESTS
# ==============================================================================

@pytest.mark.unit
class TestIResultRenderer:
    """Test IResultRenderer abstract interface."""

    def test_abstract_interface_cannot_be_instantiated(self):
        """Test that abstract interface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IResultRenderer()

    def test_concrete_implementation_must_implement_all_methods(self):
        """Test that concrete implementation must implement all abstract methods."""

        class IncompleteRenderer(IResultRenderer):
            # Missing implementations
            pass

        with pytest.raises(TypeError):
            IncompleteRenderer()

    def test_complete_concrete_implementation(self):
        """Test a complete concrete implementation."""

        class ConcreteRenderer(IResultRenderer):
            def __init__(self):
                self.rendered_items = []

            def render_executive_summary(self, result: ValuationResult) -> None:
                self.rendered_items.append("summary")

            def render_results(
                self,
                result: ValuationResult,
                provider: DataProviderProtocol | None = None
            ) -> None:
                self.rendered_items.append("results")

            def display_error(self, message: str, details: str | None = None) -> None:
                self.rendered_items.append(f"error: {message}")

        renderer = ConcreteRenderer()
        mock_result = Mock(spec=ValuationResult)

        renderer.render_executive_summary(mock_result)
        renderer.render_results(mock_result)
        renderer.render_results(mock_result, provider=None)
        renderer.display_error("Test error")
        renderer.display_error("Test error", details="Stack trace")

        assert len(renderer.rendered_items) == 5
        assert "summary" in renderer.rendered_items
        assert "results" in renderer.rendered_items
        assert "error: Test error" in renderer.rendered_items

    def test_render_results_with_provider(self):
        """Test render_results with optional provider parameter."""

        class TestRenderer(IResultRenderer):
            def __init__(self):
                self.last_provider = None

            def render_executive_summary(self, result: ValuationResult) -> None:
                pass

            def render_results(
                self,
                result: ValuationResult,
                provider: DataProviderProtocol | None = None
            ) -> None:
                self.last_provider = provider

            def display_error(self, message: str, details: str | None = None) -> None:
                pass

        renderer = TestRenderer()
        mock_result = Mock(spec=ValuationResult)
        mock_provider = Mock(spec=DataProviderProtocol)

        # Call with provider
        renderer.render_results(mock_result, provider=mock_provider)
        assert renderer.last_provider is mock_provider

        # Call without provider
        renderer.render_results(mock_result)
        assert renderer.last_provider is None

    def test_display_error_with_optional_details(self):
        """Test display_error with optional details parameter."""

        class TestRenderer(IResultRenderer):
            def __init__(self):
                self.errors = []

            def render_executive_summary(self, result: ValuationResult) -> None:
                pass

            def render_results(
                self,
                result: ValuationResult,
                provider: DataProviderProtocol | None = None
            ) -> None:
                pass

            def display_error(self, message: str, details: str | None = None) -> None:
                self.errors.append((message, details))

        renderer = TestRenderer()

        # Error with details
        renderer.display_error("Critical error", details="Traceback: ...")
        assert len(renderer.errors) == 1
        assert renderer.errors[0] == ("Critical error", "Traceback: ...")

        # Error without details
        renderer.display_error("Simple error")
        assert len(renderer.errors) == 2
        assert renderer.errors[1] == ("Simple error", None)


# ==============================================================================
# 4. INTEGRATION TESTS
# ==============================================================================

@pytest.mark.unit
class TestInterfaceIntegration:
    """Test how interfaces work together in realistic scenarios."""

    def test_null_handler_with_renderer(self):
        """Test NullProgressHandler used with a renderer."""

        class SimpleRenderer(IResultRenderer):
            def render_executive_summary(self, result: ValuationResult) -> None:
                pass

            def render_results(
                self,
                result: ValuationResult,
                provider: DataProviderProtocol | None = None
            ) -> None:
                pass

            def display_error(self, message: str, details: str | None = None) -> None:
                pass

        handler = NullProgressHandler()
        renderer = SimpleRenderer()

        # Simulate a workflow
        with handler:
            handler.start_status("Rendering")
            renderer.render_executive_summary(Mock(spec=ValuationResult))
            handler.complete_status("Rendering")

    def test_all_interfaces_can_coexist(self):
        """Test that all interfaces can be used together."""

        # Create implementations
        mock_provider = Mock(spec=DataProviderProtocol)
        mock_provider.get_company_name.return_value = "Test Company"

        handler = NullProgressHandler()

        class TestRenderer(IResultRenderer):
            def render_executive_summary(self, result: ValuationResult) -> None:
                pass
            def render_results(
                self,
                result: ValuationResult,
                provider: DataProviderProtocol | None = None
            ) -> None:
                pass
            def display_error(self, message: str, details: str | None = None) -> None:
                pass

        renderer = TestRenderer()

        # Use them together
        with handler:
            company_name = mock_provider.get_company_name("TEST")
            assert company_name == "Test Company"

            handler.start_status("Processing")
            mock_result = Mock(spec=ValuationResult)
            renderer.render_results(mock_result, provider=mock_provider)
            handler.complete_status("Processing")
