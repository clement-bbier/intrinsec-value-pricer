"""
src/interfaces/ui_handlers.py

ABSTRACT UI INTERFACES (DT-017 Resolution)
==========================================
Role: Defines abstract contracts for UI communication.
Pattern: Strategy + Null Object (GoF).
Style: Numpy Style docstrings.

Responsibility:
    Decouples src/ (Financial Core) from app/ (Streamlit UI).
    Interfaces are defined here; concrete implementations reside in app/adapters/.

Financial Impact:
-----------------
None. These interfaces manage presentation and status reporting only;
they do not affect intrinsic value calculations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models import ValuationResult
    from types import TracebackType


# ==============================================================================
# 1. STRUCTURAL PROTOCOLS (Prevention of Circular Dependencies)
# ==============================================================================

class DataProviderProtocol(Protocol):
    """
    Protocol defining the minimal interface required for a data provider.
    Used to resolve metadata without importing concrete infrastructure.
    """

    def get_company_name(self, ticker: str) -> str:
        """
        Retrieves the legal name of the entity.

        Parameters
        ----------
        ticker : str
            The stock symbol to resolve.
        """
        ...


# ==============================================================================
# 2. PROGRESS HANDLER INTERFACE (DT-017)
# ==============================================================================

class IUIProgressHandler(ABC):
    """
    Interface for UI progress management.

    Defines the contract for status indicators across Streamlit, CLI, or Tests.
    """

    @abstractmethod
    def start_status(self, label: str) -> IUIProgressHandler:
        """
        Initializes a status indicator.

        Parameters
        ----------
        label : str
            Localized title for the operation (i18n).
        """
        ...

    @abstractmethod
    def update_status(self, message: str) -> None:
        """
        Updates the current progress message.

        Parameters
        ----------
        message : str
            Localized progress description.
        """
        ...

    @abstractmethod
    def complete_status(self, label: str, state: str = "complete") -> None:
        """
        Finalizes the status indicator as successful.
        """
        ...

    @abstractmethod
    def error_status(self, label: str) -> None:
        """
        Marks the status indicator as failed.
        """
        ...

    def __enter__(self) -> IUIProgressHandler:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None
    ) -> None:
        """Context manager support for scoped status blocks."""
        pass


class NullProgressHandler(IUIProgressHandler):
    """
    Null Object implementation for Headless or Unit Test environments.

    Functions as a no-op handler that satisfies the interface contract.
    """

    def start_status(self, label: str) -> NullProgressHandler:
        return self

    def update_status(self, message: str) -> None:
        pass

    def complete_status(self, label: str, state: str = "complete") -> None:
        pass

    def error_status(self, label: str) -> None:
        pass


# ==============================================================================
# 3. RESULT RENDERER INTERFACE (DT-016)
# ==============================================================================

class IResultRenderer(ABC):
    """
    Interface for rendering valuation results.

    Decouples the logic orchestrator (workflow.py) from visual components.
    """

    @abstractmethod
    def render_executive_summary(self, result: ValuationResult) -> None:
        """
        Displays the high-level executive summary (Golden Header).

        Parameters
        ----------
        result : ValuationResult
            The comprehensive valuation result object.
        """
        ...

    @abstractmethod
    def render_results(
        self,
        result: ValuationResult,
        provider: DataProviderProtocol | None = None
    ) -> None:
        """
        Renders the complete multi-pillar results view.

        Standard Rendering Entry Point (ST 1.2 Naming Blueprint).

        Parameters
        ----------
        result : ValuationResult
            Result container to visualize.
        provider : DataProviderProtocol, optional
            Optional provider for supplemental metadata.
        """
        ...

    @abstractmethod
    def display_valuation_details(
        self,
        result: ValuationResult,
        provider: DataProviderProtocol
    ) -> None:
        """
        Renders granular valuation details.

        .. deprecated:: 2.0
            Use :meth:`render_results` instead.
        """
        ...

    @abstractmethod
    def display_error(self, message: str, details: Optional[str] = None) -> None:
        """
        Communicates a business or system error to the user.

        Parameters
        ----------
        message : str
            Primary error notification.
        details : str, optional
            Technical stack trace or diagnostic details.
        """
        ...


class NullResultRenderer(IResultRenderer):
    """
    Null Object implementation for Test Scenarios.

    Captures result objects internally for assertion checks without
    triggering UI components.
    """

    def __init__(self) -> None:
        self.last_result: ValuationResult | None = None
        self.last_error: str | None = None

    def render_executive_summary(self, result: ValuationResult) -> None:
        self.last_result = result

    def render_results(
        self,
        result: ValuationResult,
        provider: DataProviderProtocol | None = None
    ) -> None:
        self.last_result = result

    def display_valuation_details(
        self,
        result: ValuationResult,
        provider: DataProviderProtocol
    ) -> None:
        self.render_results(result, provider)

    def display_error(self, message: str, details: Optional[str] = None) -> None:
        self.last_error = message