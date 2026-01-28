"""
app/ui/base/base_result.py

ABSTRACT BASE CLASS — Result Tab Interface
==========================================
Role: Defines the standard interface for all valuation result tabs.
Pattern: Strategy (GoF)

Each tab implements this interface, while the orchestrator manages
display priority and conditional visibility.

Core Pillars (Always visible):
- InputsSummaryTab       : Pillar 1 (Hypotheses)
- CalculationProofTab    : Pillar 2 (Glass Box)
- AuditReportTab         : Pillar 3 (Reliability Score)

Optional Pillars (Conditional):
- MarketAnalysisTab      : Pillar 5 (Peers & SOTP)
- RiskEngineeringTab     : Pillar 4 (Monte Carlo, Scenarios, Backtest)

Style: Numpy docstrings
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.models import ValuationResult


class ResultTabBase(ABC):
    """
    Abstract interface for a valuation result tab.

    Attributes
    ----------
    TAB_ID : str
        Unique identifier for the tab (snake_case).
    LABEL : str
        Display label used in the Streamlit UI.
    ICON : str
        Representative icon (institutional style, minimal usage).
    ORDER : int
        Display priority (lower values appear first).
    IS_CORE : bool
        True if the tab is always visible, False if conditional.
    """

    # To be overridden in concrete subclasses
    TAB_ID: str = "base"
    LABEL: str = "Tab"
    ICON: str = ""
    ORDER: int = 100
    IS_CORE: bool = False

    @abstractmethod
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Renders the tab content within the Streamlit interface.

        Parameters
        ----------
        result : ValuationResult
            The processed valuation output containing financials and trace.
        **kwargs
            Additional context (e.g., mc_stats, calculation providers).
        """
        pass

    def is_visible(self, result: ValuationResult) -> bool:
        """
        Determines if the tab should be rendered based on results data.

        Core tabs always return True.
        Optional tabs check for specific data presence (e.g., mc_results).

        Parameters
        ----------
        result : ValuationResult
            The processed valuation output.

        Returns
        -------
        bool
            True if the tab should be visible.
        """
        return self.IS_CORE

    def get_display_label(self) -> str:
        """
        Constructs the final label for the st.tabs() component.

        Returns
        -------
        str
            The localized display label.
        """
        return self.LABEL