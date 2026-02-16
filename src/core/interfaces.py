"""
src/core/interfaces.py

ABSTRACT CORE INTERFACES
========================
Role: Defines abstract contracts for system-wide components.
Pattern: Strategy + Null Object.
Style: Numpy docstrings.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from types import TracebackType

    from src.models.valuation import ValuationResult


# ==============================================================================
# 1. DATA PROVIDER PROTOCOL
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

        Returns
        -------
        str
            The legal company name.
        """
        pass


# ==============================================================================
# 2. PROGRESS HANDLER INTERFACE
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
            Title for the operation.

        Returns
        -------
        IUIProgressHandler
            The handler instance for chaining.
        """
        pass

    @abstractmethod
    def update_status(self, message: str) -> None:
        """
        Updates the current progress message.

        Parameters
        ----------
        message : str
            Progress description.
        """
        pass

    @abstractmethod
    def complete_status(self, label: str, state: str = "complete") -> None:
        """
        Finalizes the status indicator as successful.

        Parameters
        ----------
        label : str
            The label of the completed task.
        state : str, optional
            The completion state (default is "complete").
        """
        pass

    @abstractmethod
    def error_status(self, label: str) -> None:
        """
        Marks the status indicator as failed.

        Parameters
        ----------
        label : str
            The label of the failed task.
        """
        pass

    def __enter__(self) -> IUIProgressHandler:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        """Context manager support for scoped status blocks."""
        pass


class NullProgressHandler(IUIProgressHandler):
    """
    Null Object implementation for Headless or Unit Test environments.
    Functions as a no-op handler.
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
# 3. RESULT RENDERER INTERFACE
# ==============================================================================


class IResultRenderer(ABC):
    """
    Interface for rendering valuation results.
    Decouples the logic orchestrator from visual components.
    """

    @abstractmethod
    def render_executive_summary(self, result: ValuationResult) -> None:
        """
        Displays the high-level executive summary.

        Parameters
        ----------
        result : ValuationResult
            The comprehensive valuation result object.
        """
        pass

    @abstractmethod
    def render_results(self, result: ValuationResult, provider: DataProviderProtocol | None = None) -> None:
        """
        Renders the complete multi-pillar results view.

        Parameters
        ----------
        result : ValuationResult
            Result container to visualize.
        provider : DataProviderProtocol | None, optional
            Optional provider for supplemental metadata.
        """
        pass

    @abstractmethod
    def display_error(self, message: str, details: str | None = None) -> None:
        """
        Communicates a business or system error to the user.

        Parameters
        ----------
        message : str
            Primary error notification.
        details : str | None, optional
            Technical stack trace or diagnostic details.
        """
        pass
