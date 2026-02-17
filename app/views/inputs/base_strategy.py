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

import streamlit as st

from app.views.inputs.strategies.shared_widgets import (
    widget_backtest,
    widget_cost_of_capital,
    widget_equity_bridge,
    widget_monte_carlo,
    widget_peer_triangulation,
    widget_scenarios,
    widget_sensitivity,
    widget_sotp,
    widget_terminal_value_dcf,
    widget_terminal_value_rim,
)
from src.config.constants import UIKeys
from src.i18n.fr.ui.terminals import CommonTerminals, RIMTexts
from src.models import ValuationMethodology

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
    FORMULA_GLOBAL: str = ""
    ICON: str = ""

    # Rendering Options (Sections principales)
    SHOW_DISCOUNT_SECTION: bool = True
    SHOW_TERMINAL_SECTION: bool = True
    SHOW_BRIDGE_SECTION: bool = True

    # Extensions Flags (Must be explicitly overridden by child views)
    SHOW_MONTE_CARLO: bool = True
    SHOW_SENSITIVITY: bool = True
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
        self.render_model_inputs()

        # Step 3: Risk & Capital (Shared widget)
        if self.SHOW_DISCOUNT_SECTION:
            # Titrage Dynamique : Firm (WACC) vs Equity (Ke)
            step_3_title = (
                CommonTerminals.STEP_3_TITLE_WACC if not self.MODE.is_direct_equity else CommonTerminals.STEP_3_TITLE_KE
            )
            self._render_step_header(step_3_title, CommonTerminals.STEP_3_DESC)
            widget_cost_of_capital(self.MODE)

        # Step 4: Exit Value (Terminal Value logic)
        if self.SHOW_TERMINAL_SECTION:
            if self.MODE == ValuationMethodology.RIM:
                widget_terminal_value_rim(formula_latex=RIMTexts.FORMULA_TV_RIM, key_prefix=self.MODE.name)
            else:
                widget_terminal_value_dcf(mode=self.MODE, key_prefix=self.MODE.name)

        # Step 5: Equity Bridge (Structure adjustments)
        if self.SHOW_BRIDGE_SECTION:
            self._render_equity_bridge()

        # Steps 6-11: Analytical Extensions
        self._render_optional_features()

    # ══════════════════════════════════════════════════════════════════════════
    # SHARED UI HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _render_header(self) -> None:
        """Displays the model identity header."""
        title = f"{self.ICON} {self.DISPLAY_NAME}" if self.ICON else self.DISPLAY_NAME
        st.subheader(title)
        if self.FORMULA_GLOBAL:
            st.latex(self.FORMULA_GLOBAL)
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
        formula = CommonTerminals.FORMULA_BRIDGE_SIMPLE if self.MODE.is_direct_equity else CommonTerminals.FORMULA_BRIDGE
        widget_equity_bridge(formula, self.MODE)
        st.divider()

    def _render_optional_features(self) -> None:
        """Coordinates complementary analytical modules."""

        # The key_prefix is crucial to avoid Streamlit ID conflicts
        prefix = self.MODE.name

        # 6. Monte Carlo Simulation
        if self.SHOW_MONTE_CARLO:
            # Retrieve chosen terminal method (if applicable) to adjust MC inputs
            term_method_key = f"{prefix}_{UIKeys.TV_METHOD}"
            term_method = st.session_state.get(term_method_key)

            widget_monte_carlo(self.MODE, term_method, custom_vols=self.get_custom_monte_carlo_vols())

        # 7. Sensitivity Analysis (WACC vs g)
        # Uses default "sens" prefix for global extension keys (no strategy prefix).
        if self.SHOW_SENSITIVITY:
            widget_sensitivity()

        # 8. Scenario Analysis (Bull/Bear)
        if self.SHOW_SCENARIOS:
            widget_scenarios(self.MODE)

        # 9. Historical Backtest
        if self.SHOW_BACKTEST:
            widget_backtest()

        # 10. Peer Triangulation
        if self.SHOW_PEER_TRIANGULATION:
            widget_peer_triangulation()

        # 11. SOTP (Sum of the Parts)
        if self.SHOW_SOTP:
            widget_sotp()

    # ══════════════════════════════════════════════════════════════════════════
    # UI LOGIC MAPPING
    # ══════════════════════════════════════════════════════════════════════════

    def get_custom_monte_carlo_vols(self) -> dict[str, str] | None:
        """
        Maps Methodology to specific UI labels for Monte Carlo volatilities.
        """
        mapping = {
            ValuationMethodology.GRAHAM: {"base_flow_volatility": CommonTerminals.MC_VOL_EPS},
            ValuationMethodology.RIM: {"base_flow_volatility": CommonTerminals.MC_VOL_NI},
            ValuationMethodology.DDM: {"base_flow_volatility": CommonTerminals.MC_VOL_DIV},
        }
        return mapping.get(self.MODE)

    # ══════════════════════════════════════════════════════════════════════════
    # ABSTRACT INTERFACE
    # ══════════════════════════════════════════════════════════════════════════

    @abstractmethod
    def render_model_inputs(self) -> None:
        """
        Concrete views must implement Step 2 UI here.
        """
        pass
