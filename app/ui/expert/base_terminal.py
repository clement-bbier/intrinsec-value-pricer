"""
app/ui/expert/base_terminal.py

ABSTRACT CLASS — Expert Entry Terminal (V15 - Continuous Flow)
==============================================================
Renders inputs following the professional valuation sequence:
1. Header → 2. Operational (Hook) → 3. Risk (WACC) → 4. Exit (TV)
→ 5. Bridge (inc. SBC) → 6. Monte Carlo → 7. Peers → 8. Scenarios → 9. SOTP → 10. Backtest

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

# ==============================================================================
# NORMALIZATION CONSTANTS
# ==============================================================================

_PERCENTAGE_DIVISOR = 100.0
"""Divisor for converting percentage inputs (e.g., 5% entered as 5) to decimals (0.05)."""


class ExpertTerminalBase(ABC):
    """
    Abstract base class defining the expert valuation entry workflow.

    This class implements the Template Method pattern, orchestrating a 10-step
    valuation input sequence while allowing concrete terminals to customize
    model-specific operational inputs (Step 2).

    Attributes
    ----------
    MODE : ValuationMode
        The valuation methodology this terminal implements.
    DISPLAY_NAME : str
        Human-readable name shown in the UI header.
    DESCRIPTION : str
        Brief description of the methodology.
    ICON : str
        Optional emoji/icon for visual identification.
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
    SHOW_BACKTEST: bool = True
    SHOW_SCENARIOS: bool = True
    SHOW_SOTP: bool = True
    SHOW_PEER_TRIANGULATION: bool = True
    SHOW_SUBMIT_BUTTON: bool = False

    # LaTeX Formulas
    TERMINAL_VALUE_FORMULA: str = r"TV_n = f(FCF_n, g_n, WACC)"
    BRIDGE_FORMULA: str = SharedTexts.FORMULA_BRIDGE

    def __init__(self, ticker: str):
        """
        Initializes the expert terminal with a target ticker.

        Parameters
        ----------
        ticker : str
            The stock ticker symbol for valuation.
        """
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

        Returns
        -------
        Optional[ValuationRequest]
            The constructed request if submission is triggered, None otherwise.
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

        # 6 to 10. ENGINEERING STEPS (Optional Extensions)
        self._render_optional_features()

        # 11. EXECUTION BUTTON
        return self._render_submit()

    # ══════════════════════════════════════════════════════════════════════════
    # INTERNAL RENDERING METHODS
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _render_step_header(title: str, description: str) -> None:
        """
        Displays a standardized step header.

        Parameters
        ----------
        title : str
            The step title (typically from i18n).
        description : str
            Brief description shown in an info box.
        """
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
        Direct equity models use a simplified bridge formula.

        Returns
        -------
        Dict[str, Any]
            Bridge parameters collected from UI widgets.
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
        """Coordinates complementary analytical modules (Steps 6 to 10)."""
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

        # 10. Historical Backtest
        if self.SHOW_BACKTEST:
            from app.ui.expert.terminals.shared_widgets import widget_backtest
            backtest_data = widget_backtest()
            self._collected_data.update(backtest_data or {})

    def get_custom_monte_carlo_vols(self) -> Optional[Dict[str, str]]:
        """
        Dynamically adjusts Monte Carlo inputs based on methodology (ST-4.2).

        Returns
        -------
        Optional[Dict[str, str]]
            Custom volatility labels for the Monte Carlo widget, or None for defaults.
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
        """
        Final submission button rendering.

        Returns
        -------
        Optional[ValuationRequest]
            The constructed request if button is clicked, None otherwise.
        """
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

        Aggregates all collected data from UI widgets, applies percentage
        normalization, and builds the complete request for the valuation engine.

        Returns
        -------
        Optional[ValuationRequest]
            The fully constructed valuation request.
        """
        from app.ui.expert.terminals.shared_widgets import build_dcf_parameters

        key_prefix = self.MODE.name
        collected_data = {"projection_years": st.session_state.get(f"{key_prefix}_years", 5)}

        # Block-based data extraction with normalization
        collected_data.update(self._extract_discount_data(key_prefix))
        if self.SHOW_TERMINAL_SECTION:
            collected_data.update(self._extract_terminal_data(key_prefix))
        if self.SHOW_BRIDGE_SECTION:
            collected_data.update(self._extract_bridge_data(key_prefix))
        if self.SHOW_MONTE_CARLO:
            collected_data.update(self._extract_monte_carlo_data())
        if self.SHOW_PEER_TRIANGULATION:
            collected_data.update(self._extract_peer_triangulation_data())
        if self.SHOW_BACKTEST:
            collected_data.update(self._extract_backtest_data())

        # Model-specific inputs (Anchoring & Growth) - with normalization
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
        """
        Retrieves SOTP segments stored during Step 9 rendering.

        Returns
        -------
        Optional[SOTPParameters]
            The SOTP configuration, or None if not set.
        """
        return self._collected_data.get("sotp")

    # ══════════════════════════════════════════════════════════════════════════
    # PRIVATE EXTRACTION HELPERS — WITH PERCENTAGE NORMALIZATION
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _normalize_percentage(value: Optional[float]) -> Optional[float]:
        """
        Converts a percentage value (e.g., 5 for 5%) to decimal (0.05).

        Parameters
        ----------
        value : Optional[float]
            Raw percentage value from UI input (e.g., 5 for 5%).

        Returns
        -------
        Optional[float]
            Normalized decimal value (e.g., 0.05), or None if input is None.
        """
        if value is None:
            return None
        return value / _PERCENTAGE_DIVISOR

    @staticmethod
    def _extract_discount_data(key_prefix: str) -> Dict[str, Any]:
        """
        Maps Rf, Beta, MRP, Price, Kd, and Tax from session state.

        Rates (Rf, MRP, Kd, Tax) are normalized from percentage to decimal.
        Beta and Price remain unchanged as they are not percentages.

        Parameters
        ----------
        key_prefix : str
            Session state key prefix (typically the ValuationMode name).

        Returns
        -------
        Dict[str, Any]
            Extracted and normalized discount parameters.
        """
        data = {}

        # Fields requiring percentage normalization
        rate_fields = {
            f"{key_prefix}_rf": "risk_free_rate",
            f"{key_prefix}_mrp": "market_risk_premium",
            f"{key_prefix}_kd": "cost_of_debt",
            f"{key_prefix}_tax": "tax_rate"
        }

        # Fields NOT requiring normalization (absolute values)
        absolute_fields = {
            f"{key_prefix}_beta": "manual_beta",
            f"{key_prefix}_price": "manual_stock_price"
        }

        # Extract and normalize rate fields
        for key, field in rate_fields.items():
            if key in st.session_state:
                raw_value = st.session_state[key]
                data[field] = ExpertTerminalBase._normalize_percentage(raw_value)

        # Extract absolute fields without normalization
        for key, field in absolute_fields.items():
            if key in st.session_state:
                data[field] = st.session_state[key]

        return data

    @staticmethod
    def _extract_bridge_data(key_prefix: str) -> Dict[str, Any]:
        """
        Maps Balance Sheet structure and SBC dilution from session state.

        SBC dilution rate is normalized from percentage to decimal.
        Currency amounts remain unchanged.

        Parameters
        ----------
        key_prefix : str
            Session state key prefix (typically the ValuationMode name).

        Returns
        -------
        Dict[str, Any]
            Extracted and normalized bridge parameters.
        """
        data = {}
        p = f"bridge_{key_prefix}"

        # Fields NOT requiring normalization (absolute values in currency)
        absolute_fields = {
            f"{p}_debt": "manual_total_debt",
            f"{p}_cash": "manual_cash",
            f"{p}_min": "manual_minority_interests",
            f"{p}_pen": "manual_pension_provisions",
            f"{p}_shares": "manual_shares_outstanding",
            f"{p}_shares_direct": "manual_shares_outstanding"
        }

        # Field requiring percentage normalization
        rate_field_key = f"{p}_sbc_rate"
        rate_field_name = "stock_based_compensation_rate"

        # Extract absolute fields
        for k, f in absolute_fields.items():
            if k in st.session_state:
                data[f] = st.session_state[k]

        # Extract and normalize SBC rate
        if rate_field_key in st.session_state:
            raw_value = st.session_state[rate_field_key]
            data[rate_field_name] = ExpertTerminalBase._normalize_percentage(raw_value)

        return data

    @staticmethod
    def _extract_terminal_data(key_prefix: str) -> Dict[str, Any]:
        """
        Extracts Terminal Value parameters (Gordon or Exit Multiples).

        If Gordon Growth method is selected, perpetual_growth_rate is normalized
        from percentage to decimal. Exit multiples remain unchanged.

        Parameters
        ----------
        key_prefix : str
            Session state key prefix (typically the ValuationMode name).

        Returns
        -------
        Dict[str, Any]
            Extracted and normalized terminal value parameters.
        """
        data = {}
        method_key = f"{key_prefix}_method"

        if method_key in st.session_state:
            method = st.session_state[method_key]
            data["terminal_method"] = method

            if method == TerminalValueMethod.GORDON_GROWTH:
                # Normalize perpetual growth rate from percentage to decimal
                raw_gn = st.session_state.get(f"{key_prefix}_gn")
                data["perpetual_growth_rate"] = ExpertTerminalBase._normalize_percentage(raw_gn)
            else:
                # Exit multiple is not a percentage, no normalization needed
                data["exit_multiple_value"] = st.session_state.get(f"{key_prefix}_exit_mult")

        return data

    @staticmethod
    def _extract_monte_carlo_data() -> Dict[str, Any]:
        """
        Extracts Monte Carlo configuration with safety checks.

        All volatility parameters are normalized from percentage to decimal.

        Returns
        -------
        Dict[str, Any]
            Monte Carlo configuration with normalized volatilities.
        """
        p = "mc"
        if not st.session_state.get(f"{p}_enable", False):
            return {"enable_monte_carlo": False}

        # Helper for volatility normalization
        def normalize_vol(key: str) -> Optional[float]:
            raw = st.session_state.get(key)
            return ExpertTerminalBase._normalize_percentage(raw)

        return {
            "enable_monte_carlo": True,
            "num_simulations": st.session_state.get(f"{p}_sims", 5000),
            "base_flow_volatility": normalize_vol(f"{p}_vol_flow"),
            "beta_volatility": normalize_vol(f"{p}_vol_beta"),
            "growth_volatility": normalize_vol(f"{p}_vol_growth"),
            "exit_multiple_volatility": normalize_vol(f"{p}_vol_exit_m")
        }

    @staticmethod
    def _extract_peer_triangulation_data() -> Dict[str, Any]:
        """
        Extracts peer cohort tickers for multiples triangulation.

        Returns
        -------
        Dict[str, Any]
            Peer triangulation configuration.
        """
        data = {}
        if st.session_state.get("peer_peer_enable"):
            data["enable_peer_multiples"] = True
            raw = st.session_state.get("peer_input", "")
            if raw:
                data["manual_peers"] = [p.strip().upper() for p in raw.split(",") if p.strip()]
        return data

    @staticmethod
    def _extract_scenarios_data() -> Optional[ScenarioParameters]:
        """
        Extracts Bull/Base/Bear scenario variants.

        Growth rates and FCF margins are normalized from percentage to decimal.
        Probabilities remain unchanged (already in decimal form 0-1).

        Returns
        -------
        Optional[ScenarioParameters]
            Scenario configuration with normalized rates, or disabled if not set.
        """
        from src.models import ScenarioVariant
        p = "scenario"

        if not st.session_state.get(f"{p}_scenario_enable"):
            return ScenarioParameters(enabled=False)

        # Helper for percentage normalization
        def normalize(key: str) -> Optional[float]:
            raw = st.session_state.get(key)
            return ExpertTerminalBase._normalize_percentage(raw)

        try:
            return ScenarioParameters(
                enabled=True,
                bull=ScenarioVariant(
                    label=SharedTexts.LBL_BULL,
                    probability=st.session_state[f"{p}_p_bull"],
                    growth_rate=normalize(f"{p}_g_bull"),
                    target_fcf_margin=normalize(f"{p}_m_bull")
                ),
                base=ScenarioVariant(
                    label=SharedTexts.LBL_BASE,
                    probability=st.session_state[f"{p}_p_base"],
                    growth_rate=normalize(f"{p}_g_base"),
                    target_fcf_margin=normalize(f"{p}_m_base")
                ),
                bear=ScenarioVariant(
                    label=SharedTexts.LBL_BEAR,
                    probability=st.session_state[f"{p}_p_bear"],
                    growth_rate=normalize(f"{p}_g_bear"),
                    target_fcf_margin=normalize(f"{p}_m_bear")
                )
            )
        except (KeyError, RuntimeError, ValueError):
            return ScenarioParameters(enabled=False)

    @staticmethod
    def _extract_backtest_data() -> Dict[str, Any]:
        """
        Extracts historical backtest configuration.

        Returns
        -------
        Dict[str, Any]
            Backtest enable flag.
        """
        return {"enable_backtest": st.session_state.get("bt_enable", False)}

    def _build_options(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sets internal flags for final request construction.

        Parameters
        ----------
        data : Dict[str, Any]
            Collected data dictionary.

        Returns
        -------
        Dict[str, Any]
            Options dictionary for ValuationRequest.
        """
        return {
            "manual_peers": self._manual_peers,
            "enable_peer_multiples": data.get("enable_peer_multiples", False),
            "enable_backtest": data.get("enable_backtest", False),
        }

    @abstractmethod
    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Abstract hook for specific model operational inputs.

        Each concrete terminal must implement this to render model-specific
        widgets for Step 2 (Operational Anchoring & Growth).

        Returns
        -------
        Dict[str, Any]
            Model-specific parameters collected from UI widgets.
        """
        pass

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Default hook for model-specific data extraction.

        Override this in concrete terminals to extract and normalize
        model-specific parameters from session state.

        Parameters
        ----------
        key_prefix : str
            Session state key prefix (typically the ValuationMode name).

        Returns
        -------
        Dict[str, Any]
            Empty dict by default, overridden by concrete terminals.
        """
        return {}