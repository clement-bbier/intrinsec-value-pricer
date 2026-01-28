"""
app/ui/expert/base_terminal.py

ABSTRACT CLASS — Expert Entry Terminal (V15 - Continuous Flow)
==============================================================
Renders inputs following the professional valuation sequence:
1. Header → 2. Operational (Hook) → 3. Risk (WACC) → 4. Exit (TV)
→ 5. Bridge (inc. SBC) → 6. Monte Carlo → 7. Peers → 8. Scenarios → 9. SOTP

Pattern: Template Method (GoF)
Style: Numpy docstrings
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

import streamlit as st

from src.models import (
    InputSource,
    ValuationMode,
    ValuationRequest,
    ScenarioParameters,
    TerminalValueMethod,
    SOTPParameters
)
from src.i18n import SharedTexts

logger = logging.getLogger(__name__)


class ExpertTerminalBase(ABC):
    """
    Abstract base class defining the expert valuation entry workflow.
    """

    # --- Default Configuration (Overridden by concrete terminals) ---
    MODE: ValuationMode = None
    DISPLAY_NAME: str = "Expert Terminal"
    DESCRIPTION: str = ""
    ICON: str = ""

    # Rendering Options
    SHOW_DISCOUNT_SECTION: bool = True
    SHOW_TERMINAL_SECTION: bool = True
    SHOW_BRIDGE_SECTION: bool = True
    SHOW_MONTE_CARLO: bool = True
    SHOW_SCENARIOS: bool = True
    SHOW_SOTP: bool = True
    SHOW_PEER_TRIANGULATION: bool = True
    SHOW_SUBMIT_BUTTON: bool = False

    # LaTeX Formulas
    TERMINAL_VALUE_FORMULA: str = r"TV_n = f(FCF_n, g_n, WACC)"
    BRIDGE_FORMULA: str = SharedTexts.FORMULA_BRIDGE

    def __init__(self, ticker: str):
        """Initializes the expert terminal with a target ticker."""
        self.ticker = ticker
        self._collected_data: Dict[str, Any] = {}
        self._scenarios: Optional[ScenarioParameters] = None
        self._manual_peers: Optional[List[str]] = None

    # ══════════════════════════════════════════════════════════════════════════
    # TEMPLATE METHOD — UI RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def render(self) -> Optional[ValuationRequest]:
        """
        Orchestrates the full rendering sequence based on analyst logic.
        Sequence: Operational -> Risk -> Exit -> Structure -> Engineering.
        """
        # 1. HEADER (Model Identity)
        self._render_header()

        # 2. OPERATIONAL STEP (Model-specific Anchoring & Growth)
        model_data = self.render_model_inputs()
        self._collected_data.update(model_data or {})

        # 3. RISK & CAPITAL STEP (Discounting / WACC / Ke)
        if self.SHOW_DISCOUNT_SECTION:
            self._render_step_header(SharedTexts.SEC_3_CAPITAL, SharedTexts.SEC_3_DESC)
            from app.ui.expert.terminals.shared_widgets import widget_cost_of_capital
            self._collected_data.update(widget_cost_of_capital(self.MODE) or {})

        # 4. EXIT VALUE STEP (Terminal Value / Horizon)
        if self.SHOW_TERMINAL_SECTION:
            if self.MODE == ValuationMode.RIM:
                from app.ui.expert.terminals.shared_widgets import widget_terminal_value_rim
                self._collected_data.update(widget_terminal_value_rim(
                    formula_latex=SharedTexts.FORMULA_TV_RIM,
                    key_prefix=self.MODE.name
                ) or {})
            else:
                from app.ui.expert.terminals.shared_widgets import widget_terminal_value_dcf
                self._collected_data.update(widget_terminal_value_dcf(key_prefix=self.MODE.name) or {})

        # 5. STRUCTURE & ADJUSTMENTS STEP (Equity Bridge / SBC / Debt)
        if self.SHOW_BRIDGE_SECTION:
            self._collected_data.update(self._render_equity_bridge() or {})
            st.divider()

        # 6 to 9. ENGINEERING STEPS (Optional Extensions)
        self._render_optional_features()

        # 10. EXECUTION BUTTON
        return self._render_submit()

    # ══════════════════════════════════════════════════════════════════════════
    # INTERNAL RENDERING METHODS
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _render_step_header(title: str, description: str) -> None:
        """Displays a standardized step header."""
        st.markdown(title)
        st.info(description)

    def _render_header(self) -> None:
        """Displays the main terminal title and description."""
        title = f"{self.ICON} {self.DISPLAY_NAME}" if self.ICON else self.DISPLAY_NAME
        st.subheader(title)
        if self.DESCRIPTION:
            st.caption(self.DESCRIPTION)
        st.divider()

    def _render_equity_bridge(self) -> Dict[str, Any]:
        """
        Section 5: Structure adjustments (Equity Bridge).
        Adapts LaTeX formula and complexity based on valuation mode.
        """
        from app.ui.expert.terminals.shared_widgets import widget_equity_bridge

        # RELEVANCE LOGIC:
        # If Direct Equity (DDM, RIM, FCFE), display a simplified bridge formula
        if self.MODE.is_direct_equity:
            formula = SharedTexts.FORMULA_BRIDGE_SIMPLE
        else:
            # Full Enterprise Value -> Equity Bridge (FCFF)
            formula = self.BRIDGE_FORMULA

        return widget_equity_bridge(formula, self.MODE)

    def _render_optional_features(self) -> None:
        """Coordinates complementary analytical modules (Steps 6 to 9)."""
        from app.ui.expert.terminals.shared_widgets import (
            widget_monte_carlo, widget_scenarios, widget_peer_triangulation, widget_sotp
        )

        # 6. Monte Carlo Simulation
        if self.SHOW_MONTE_CARLO:
            terminal_method = self._collected_data.get("terminal_method")
            mc_data = widget_monte_carlo(
                self.MODE,
                terminal_method,
                custom_vols=self.get_custom_monte_carlo_vols()
            )
            self._collected_data.update(mc_data or {})

        # 7. Peer Discovery (Triangulation)
        if self.SHOW_PEER_TRIANGULATION:
            peer_data = widget_peer_triangulation()
            self._collected_data.update(peer_data or {})
            self._manual_peers = peer_data.get("manual_peers")

        # 8. Scenario Analysis (Convictions)
        if self.SHOW_SCENARIOS:
            self._scenarios = widget_scenarios(self.MODE)

        # 9. SOTP (Final Segmentation)
        if self.SHOW_SOTP:
            from app.ui.expert.terminals.shared_widgets import build_dcf_parameters
            temp_params = build_dcf_parameters(self._collected_data)
            widget_sotp(temp_params, is_conglomerate=False)
            self._collected_data["sotp"] = temp_params.sotp

    def get_custom_monte_carlo_vols(self) -> Optional[Dict[str, str]]:
        """
        Dynamically adjusts Monte Carlo inputs based on methodology (ST-4.2).
        """
        # 1. Cash Flow models: focus on growth volatility (g)
        if self.MODE in [
            ValuationMode.FCFF_STANDARD,
            ValuationMode.FCFF_NORMALIZED,
            ValuationMode.FCFF_GROWTH,
            ValuationMode.FCFE,
            ValuationMode.DDM
        ]:
            return {"growth_volatility": SharedTexts.MC_VOL_G}

        # 2. RIM Model: focus on residual income persistence (omega)
        if self.MODE == ValuationMode.RIM:
            return {"terminal_growth_volatility": SharedTexts.LBL_VOL_OMEGA}

        # 3. Graham Model: focus on Earnings Per Share (EPS) uncertainty
        if self.MODE == ValuationMode.GRAHAM:
            return {
                "base_flow_volatility": SharedTexts.MC_VOL_BASE_FLOW,
                "growth_volatility": SharedTexts.MC_VOL_G
            }

        return None

    def _render_submit(self) -> Optional[ValuationRequest]:
        """Final submission button rendering."""
        if not self.SHOW_SUBMIT_BUTTON:
            return None
        st.divider()
        if st.button(SharedTexts.BTN_VALUATE_STD.format(ticker=self.ticker), type="primary"):
            return self.build_request()
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # DATA EXTRACTION (SessionState Mapping)
    # ══════════════════════════════════════════════════════════════════════════

    def build_request(self) -> Optional[ValuationRequest]:
        """
        Constructs the final ValuationRequest domain object.
        """
        from app.ui.expert.terminals.shared_widgets import build_dcf_parameters

        key_prefix = self.MODE.name
        collected_data = {"projection_years": st.session_state.get(f"{key_prefix}_years", 5)}

        # Block-based data extraction
        collected_data.update(self._extract_discount_data(key_prefix))
        if self.SHOW_TERMINAL_SECTION:
            collected_data.update(self._extract_terminal_data(key_prefix))
        if self.SHOW_BRIDGE_SECTION:
            collected_data.update(self._extract_bridge_data(key_prefix))
        if self.SHOW_MONTE_CARLO:
            collected_data.update(self._extract_monte_carlo_data())
        if self.SHOW_PEER_TRIANGULATION:
            collected_data.update(self._extract_peer_triangulation_data())

        # Model-specific inputs (Anchoring & Growth)
        collected_data.update(self._extract_model_inputs_data(key_prefix))

        # Build parameters object
        params = build_dcf_parameters(collected_data)

        # Scenarios and SOTP data injection
        if self.SHOW_SCENARIOS:
            params.scenarios = self._extract_scenarios_data()
        if self.SHOW_SOTP:
            params.sotp = self._extract_sotp_data()

        return ValuationRequest(
            ticker=self.ticker,
            mode=self.MODE,
            projection_years=collected_data.get("projection_years", 5),
            input_source=InputSource.MANUAL,
            manual_params=params,
            options=self._build_options(collected_data),
        )

    def _extract_sotp_data(self) -> Optional[SOTPParameters]:
        """Retrieves SOTP segments stored during Step 9 rendering."""
        return self._collected_data.get("sotp")

    # ══════════════════════════════════════════════════════════════════════════
    # PRIVATE EXTRACTION HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _extract_discount_data(key_prefix: str) -> Dict[str, Any]:
        """Maps Rf, Beta, MRP, Price, Kd, and Tax from session state."""
        data = {}
        mapping = {
            f"{key_prefix}_rf": "risk_free_rate", f"{key_prefix}_beta": "manual_beta",
            f"{key_prefix}_mrp": "market_risk_premium", f"{key_prefix}_price": "manual_stock_price",
            f"{key_prefix}_kd": "cost_of_debt", f"{key_prefix}_tax": "tax_rate"
        }
        for key, field in mapping.items():
            if key in st.session_state:
                data[field] = st.session_state[key]
        return data

    @staticmethod
    def _extract_bridge_data(key_prefix: str) -> Dict[str, Any]:
        """Maps Balance Sheet structure and SBC dilution from session state."""
        data = {}
        p = f"bridge_{key_prefix}"
        mapping = {
            f"{p}_debt": "manual_total_debt", f"{p}_cash": "manual_cash",
            f"{p}_min": "manual_minority_interests", f"{p}_pen": "manual_pension_provisions",
            f"{p}_shares": "manual_shares_outstanding", f"{p}_shares_direct": "manual_shares_outstanding",
            f"{p}_sbc_rate": "stock_based_compensation_rate"
        }
        for k, f in mapping.items():
            if k in st.session_state:
                data[f] = st.session_state[k]
        return data

    @staticmethod
    def _extract_monte_carlo_data() -> Dict[str, Any]:
        """Extracts Monte Carlo configuration with safety checks."""
        p = "mc"
        if not st.session_state.get(f"{p}_enable", False):
            return {"enable_monte_carlo": False}

        return {
            "enable_monte_carlo": True,
            "num_simulations": st.session_state.get(f"{p}_sims", 5000),
            "base_flow_volatility": st.session_state.get(f"{p}_vol_flow"),
            "beta_volatility": st.session_state.get(f"{p}_vol_beta"),
            "growth_volatility": st.session_state.get(f"{p}_vol_growth"),
            "exit_multiple_volatility": st.session_state.get(f"{p}_vol_exit_m")
        }

    @staticmethod
    def _extract_peer_triangulation_data() -> Dict[str, Any]:
        """Extracts peer cohort tickers."""
        data = {}
        if st.session_state.get("peer_peer_enable"):
            data["enable_peer_multiples"] = True
            raw = st.session_state.get("peer_input", "")
            if raw:
                data["manual_peers"] = [p.strip().upper() for p in raw.split(",") if p.strip()]
        return data

    @staticmethod
    def _extract_scenarios_data() -> Optional[ScenarioParameters]:
        """Extracts Bull/Base/Bear scenario variants."""
        from src.models import ScenarioVariant
        p = "scenario"
        if not st.session_state.get(f"{p}_scenario_enable"):
            return ScenarioParameters(enabled=False)
        try:
            return ScenarioParameters(
                enabled=True,
                bull=ScenarioVariant(label=SharedTexts.LBL_BULL, probability=st.session_state[f"{p}_p_bull"], growth_rate=st.session_state.get(f"{p}_g_bull"), target_fcf_margin=st.session_state.get(f"{p}_m_bull")),
                base=ScenarioVariant(label=SharedTexts.LBL_BASE, probability=st.session_state[f"{p}_p_base"], growth_rate=st.session_state.get(f"{p}_g_base"), target_fcf_margin=st.session_state.get(f"{p}_m_base")),
                bear=ScenarioVariant(label=SharedTexts.LBL_BEAR, probability=st.session_state[f"{p}_p_bear"], growth_rate=st.session_state.get(f"{p}_g_bear"), target_fcf_margin=st.session_state.get(f"{p}_m_bear"))
            )
        except (KeyError, RuntimeError, ValueError):
            return ScenarioParameters(enabled=False)

    def _build_options(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sets internal flags for final request construction."""
        return {
            "manual_peers": self._manual_peers,
            "enable_peer_multiples": data.get("enable_peer_multiples", False),
        }

    @abstractmethod
    def render_model_inputs(self) -> Dict[str, Any]:
        """Abstract hook for specific model operational inputs."""
        pass

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """Default hook for model-specific data extraction."""
        return {}

    @staticmethod
    def _extract_terminal_data(key_prefix: str) -> Dict[str, Any]:
        """Extracts Terminal Value parameters (Gordon or Exit Multiples)."""
        data = {}
        method_key = f"{key_prefix}_method"

        if method_key in st.session_state:
            method = st.session_state[method_key]
            data["terminal_method"] = method
            if method == TerminalValueMethod.GORDON_GROWTH:
                data["perpetual_growth_rate"] = st.session_state.get(f"{key_prefix}_gn")
            else:
                data["exit_multiple_value"] = st.session_state.get(f"{key_prefix}_exit_mult")
        return data