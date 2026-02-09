"""
app/views/inputs/base_strategy.py

ABSTRACT CLASS — Base Strategy View
===================================
Role: Template for all valuation input forms.
Responsibility: Renders the common sections (Header, Risk, Bridge, Extensions).
Architecture: MVC View Layer (Stateless rendering to SessionState).

Style: NumPy docstrings.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict

import streamlit as st

from src.models import ValuationMethodology
from src.i18n import SharedTexts

from app.views.inputs.strategies.shared_widgets import (
    widget_cost_of_capital,
    widget_terminal_value_rim,
    widget_terminal_value_dcf,
    widget_equity_bridge,
    widget_monte_carlo,
    widget_scenarios,
    widget_peer_triangulation,
    widget_backtest
)

logger = logging.getLogger(__name__)


class BaseStrategyView(ABC):
    """
    Abstract base view orchestrating the valuation input workflow.

    This class handles the layout of shared sections (Risk, Exit, Bridge, Extensions)
    and delegates the specific operational inputs to concrete subclasses.
    """

    # --- Default Configuration (Overridden by concrete views) ---
    MODE: ValuationMethodology = None
    DISPLAY_NAME: str = "Expert View"
    DESCRIPTION: str = ""
    ICON: str = ""

    # Rendering Options (Feature Flags)
    SHOW_DISCOUNT_SECTION: bool = True
    SHOW_TERMINAL_SECTION: bool = True
    SHOW_BRIDGE_SECTION: bool = True

    # Extensions Flags
    SHOW_MONTE_CARLO: bool = True
    SHOW_BACKTEST: bool = True
    SHOW_SCENARIOS: bool = True
    SHOW_SOTP: bool = True
    SHOW_PEER_TRIANGULATION: bool = True

    def __init__(self, ticker: str):
        """
        Initializes the view.

        Parameters
        ----------
        ticker : str
            The target ticker symbol (used for display labels).
        """
        self.ticker = ticker

    # ══════════════════════════════════════════════════════════════════════════
    # TEMPLATE METHOD — UI RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def render(self) -> None:
        """
        Orchestrates the full rendering sequence.
        Writes directly to st.session_state via widgets.
        """
        # Step 1: Header (Identity)
        self._render_header()

        # Step 2: Operational (Concrete implementation hook)
        # This is where FCFF/DDM specific inputs are drawn
        self.render_model_inputs()

        # Step 3: Risk & Capital (Shared widget)
        if self.SHOW_DISCOUNT_SECTION:
            self._render_step_header(SharedTexts.SEC_3_CAPITAL, SharedTexts.SEC_3_DESC)
            widget_cost_of_capital(self.MODE)

        # Step 4: Exit Value (Terminal Value logic)
        if self.SHOW_TERMINAL_SECTION:
            if self.MODE == ValuationMethodology.RIM:
                widget_terminal_value_rim(
                    formula_latex=SharedTexts.FORMULA_TV_RIM,
                    key_prefix=self.MODE.name
                )
            else:
                widget_terminal_value_dcf(
                    mode=self.MODE,
                    key_prefix=self.MODE.name
                )

        # Step 5: Equity Bridge (Structure adjustments)
        if self.SHOW_BRIDGE_SECTION:
            self._render_equity_bridge()

        # Steps 6-10: Analytical Extensions
        self._render_optional_features()

        # Note: The "Submit/Run" button is now in the Sidebar (AppController).

    # ══════════════════════════════════════════════════════════════════════════
    # SHARED UI HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _render_header(self) -> None:
        """Displays the model identity header."""
        title = f"{self.ICON} {self.DISPLAY_NAME}" if self.ICON else self.DISPLAY_NAME
        st.subheader(title)
        if self.DESCRIPTION:
            st.caption(self.DESCRIPTION)
        st.divider()

    @staticmethod
    def _render_step_header(title: str, description: str) -> None:
        """Displays a standardized step header with i18n support."""
        st.markdown(title)
        st.info(description)

    def _render_equity_bridge(self) -> None:
        """Renders the Equity Bridge section with context-aware formulas."""
        formula = SharedTexts.FORMULA_BRIDGE_SIMPLE if self.MODE.is_direct_equity else SharedTexts.FORMULA_BRIDGE
        widget_equity_bridge(formula, self.MODE)
        st.divider()

    def _render_optional_features(self) -> None:
        """Coordinates complementary analytical modules."""

        # 6. Monte Carlo Simulation
        if self.SHOW_MONTE_CARLO:
            widget_monte_carlo(
                self.MODE,
                st.session_state.get(f"{self.MODE.name}_method"),
                custom_vols=self.get_custom_monte_carlo_vols()
            )

        # 7. Scenario Analysis
        if self.SHOW_SCENARIOS:
            widget_scenarios(self.MODE)

        # 8. Historical Backtest
        if self.SHOW_BACKTEST:
            widget_backtest()

        # 9. Peer Triangulation
        if self.SHOW_PEER_TRIANGULATION:
            widget_peer_triangulation()

    # ══════════════════════════════════════════════════════════════════════════
    # UI LOGIC MAPPING
    # ══════════════════════════════════════════════════════════════════════════

    def get_custom_monte_carlo_vols(self) -> Optional[Dict[str, str]]:
        """
        Maps Methodology to specific UI labels for Monte Carlo volatilities.
        """
        mapping = {
            ValuationMethodology.GRAHAM: {"vol_flow": SharedTexts.MC_VOL_EPS},
            ValuationMethodology.RIM: {"vol_flow": SharedTexts.MC_VOL_NI},
            ValuationMethodology.DDM: {"vol_flow": SharedTexts.MC_VOL_DIV}
        }
        return mapping.get(self.MODE)

    # ══════════════════════════════════════════════════════════════════════════
    # ABSTRACT INTERFACE
    # ══════════════════════════════════════════════════════════════════════════

    @abstractmethod
    def render_model_inputs(self) -> None:
        """
        Concrete views must implement Step 2 UI here.
        This method should invoke streamlit widgets that write to session_state
        using keys compatible with InputFactory.
        """
        pass