"""
app/ui/expert/base_terminal.py

ABSTRACT CLASS — Expert Entry Terminal (V16 - Metadata-Driven)
==============================================================
Orchestrates the professional valuation sequence.
Data extraction is now automated via UIBinder and self-normalizing models.

Pattern: Template Method (GoF)
Architecture: V16 (Dumb Pipe Extraction)
Style: Numpy docstrings
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict

import streamlit as st
from pydantic import ValidationError

from src.models import (
    ValuationMethodology,
    ValuationRequest,
    Parameters, Company
)
from src.models.parameters.common import FinancialRatesParameters, CapitalStructureParameters, CommonParameters
from src.models.parameters.options import (
    MCParameters,
    ScenariosParameters,
    ExtensionBundleParameters,
    PeersParameters,
    BacktestParameters,
    SOTPParameters
)
from app.adapters.ui_binder import UIBinder
from src.i18n import SharedTexts

logger = logging.getLogger(__name__)

class BaseTerminalExpert(ABC):
    """
    Abstract base class defining the expert valuation entry workflow.

    This class handles the shared UI sections (Risk, Exit, Bridge, Extensions)
    and delegates model-specific inputs to concrete subclasses.
    """

    # --- Default Configuration (Overridden by concrete terminals) ---
    MODE: ValuationMethodology = None
    DISPLAY_NAME: str = "Expert Terminal"
    DESCRIPTION: str = ""
    ICON: str = ""

    # Rendering Options
    SHOW_DISCOUNT_SECTION: bool = True
    SHOW_TERMINAL_SECTION: bool = True
    SHOW_BRIDGE_SECTION: bool = True
    SHOW_MONTE_CARLO: bool = True
    SHOW_BACKTEST: bool = True
    SHOW_SCENARIOS: bool = True
    SHOW_SOTP: bool = True
    SHOW_PEER_TRIANGULATION: bool = True
    SHOW_SUBMIT_BUTTON: bool = False

    def __init__(self, ticker: str):
        """
        Initializes the terminal with the target ticker.

        Parameters
        ----------
        ticker : str
            The stock ticker symbol.
        """
        self.ticker = ticker

    # ══════════════════════════════════════════════════════════════════════════
    # TEMPLATE METHOD — UI RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def render(self) -> Optional[ValuationRequest]:
        """
        Orchestrates the full rendering sequence following the professional workflow.

        Returns
        -------
        Optional[ValuationRequest]
            The constructed request if submission is triggered, None otherwise.
        """
        # Step 1: Header (Identity)
        self._render_header()

        # Step 2: Operational (Concrete implementation hook)
        self.render_model_inputs()

        # Step 3: Risk & Capital (Shared widget using session state)
        if self.SHOW_DISCOUNT_SECTION:
            self._render_step_header(SharedTexts.SEC_3_CAPITAL, SharedTexts.SEC_3_DESC)
            from app.ui.expert.terminals.shared_widgets import widget_cost_of_capital
            widget_cost_of_capital(self.MODE)

        # Step 4: Exit Value (Terminal Value logic)
        if self.SHOW_TERMINAL_SECTION:
            if self.MODE == ValuationMethodology.RIM:
                from app.ui.expert.terminals.shared_widgets import widget_terminal_value_rim
                widget_terminal_value_rim(
                    formula_latex=SharedTexts.FORMULA_TV_RIM,
                    key_prefix=self.MODE.name
                )
            else:
                from app.ui.expert.terminals.shared_widgets import widget_terminal_value_dcf
                widget_terminal_value_dcf(
                    mode=self.MODE,
                    key_prefix=self.MODE.name
                )

        # Step 5: Equity Bridge (Structure adjustments)
        if self.SHOW_BRIDGE_SECTION:
            self._render_equity_bridge()

        # Steps 6-10: Analytical Extensions
        self._render_optional_features()

        return self._render_submit()

    # ══════════════════════════════════════════════════════════════════════════
    # DATA EXTRACTION (The V16 Engine)
    # ══════════════════════════════════════════════════════════════════════════

    def build_request(self) -> Optional[ValuationRequest]:
        """
        Constructs the final ValuationRequest using surgical UIBinder extraction.

        This method leverages the Metadata-Driven architecture to pull and
        self-normalize data via Pydantic models.

        Returns
        -------
        Optional[ValuationRequest]
            A validated instruction for the backend, or None if validation fails.
        """
        prefix = self.MODE.name

        try:
            # --- 1. STRATEGY BLOCK (Pillar 3: Model Specific) ---
            strategy_params = self._extract_model_inputs_data(prefix)

            # --- 2. COMMON BLOCKS (Pillar 2: Rates & Capital) ---
            rates = FinancialRatesParameters(**UIBinder.pull(FinancialRatesParameters, prefix=prefix))
            capital = CapitalStructureParameters(**UIBinder.pull(CapitalStructureParameters, prefix=f"bridge_{prefix}"))

            # --- 3. EXTENSION BLOCKS (Pillars 4 & 5: Analytical Options) ---
            extensions = ExtensionBundleParameters(
                monte_carlo=MCParameters(**UIBinder.pull(MCParameters, prefix="mc")),
                scenarios=ScenariosParameters(**UIBinder.pull(ScenariosParameters, prefix="scenario")),
                backtest=BacktestParameters(**UIBinder.pull(BacktestParameters, prefix="bt")),
                peers=PeersParameters(**UIBinder.pull(PeersParameters, prefix="peer")),
                sotp=SOTPParameters(**UIBinder.pull(SOTPParameters, prefix="sotp"))
            )

            # --- 4. FINAL ASSEMBLY (The Global Parameters Bundle) ---
            params = Parameters(
                structure=Company(ticker=self.ticker),
                common=CommonParameters(rates=rates, capital=capital),
                strategy=strategy_params,
                extensions=extensions
            )

            # --- 5. ENVELOPE (The Valuation Trigger) ---
            return ValuationRequest(
                mode=self.MODE,
                parameters=params
            )

        except ValidationError as ve:
            logger.error(f"Validation failed for {prefix} request: {ve}")
            for error in ve.errors():
                field_path = " -> ".join(map(str, error['loc']))
                st.error(f"**{SharedTexts.ERR_VALIDATION}** ({field_path}): {error['msg']}")
            return None

        except (AttributeError, KeyError, ValueError) as runtime_err:
            logger.error(f"Data mapping error in {prefix} Terminal: {runtime_err}")
            st.error(SharedTexts.ERR_CRITICAL)
            return None

        except Exception as e:
            logger.exception(f"Critical system failure during build_request {e} for {prefix}")
            st.error(SharedTexts.ERR_CRITICAL)
            return None

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
        from app.ui.expert.terminals.shared_widgets import widget_equity_bridge
        formula = SharedTexts.FORMULA_BRIDGE_SIMPLE if self.MODE.is_direct_equity else SharedTexts.FORMULA_BRIDGE
        widget_equity_bridge(formula, self.MODE)
        st.divider()

    def _render_optional_features(self) -> None:
        """Coordinates complementary analytical modules."""
        from app.ui.expert.terminals.shared_widgets import (
            widget_monte_carlo, widget_scenarios, widget_peer_triangulation, widget_backtest
        )

        # 6. Monte Carlo Simulation with dynamic labels
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

    def _render_submit(self) -> Optional[ValuationRequest]:
        """Renders the final valuate button."""
        if not self.SHOW_SUBMIT_BUTTON:
            return None
        st.divider()
        if st.button(SharedTexts.BTN_VALUATE_STD.format(ticker=self.ticker), type="primary"):
            return self.build_request()
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # UI LOGIC MAPPING
    # ══════════════════════════════════════════════════════════════════════════

    def get_custom_monte_carlo_vols(self) -> Optional[Dict[str, str]]:
        """
        Maps Methodology to specific UI labels for Monte Carlo volatilities.

        Returns
        -------
        Optional[Dict[str, str]]
            Dictionary mapping field suffixes to localized labels.
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
        """Concrete terminals must implement Step 2 UI here."""
        pass

    @abstractmethod
    def _extract_model_inputs_data(self, key_prefix: str) -> Any:
        """Concrete terminals must extract their strategy-specific block here."""
        pass