"""
app/ui/expert/base_terminal.py

ABSTRACT CLASS — Expert Entry Terminal (V16 - Unified Scale Normalization)
==========================================================================
Renders inputs following the professional valuation sequence:
1. Header → 2. Operational (Hook) → 3. Risk (WACC) → 4. Exit (TV)
→ 5. Bridge (inc. SBC) → 6. Monte Carlo → 7. Peers → 8. Scenarios → 9. SOTP → 10. Backtest

Pattern: Template Method (GoF)
Style: Numpy docstrings

IMPORTANT - SCALE CONVENTION:
-----------------------------
All UI widgets accept HUMAN-READABLE PERCENTAGES (e.g., 5 for 5%).
All extraction methods NORMALIZE to DECIMALS (e.g., 0.05) for the calculation pipeline.
This normalization is centralized in this base class to ensure consistency.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Set

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

_PERCENTAGE_DIVISOR: float = 100.0
_MILLION_MULTIPLIER: float = 1_000_000.0
"""
Divisor for converting percentage inputs to decimals.

UI Convention: Users enter percentages as human-readable values (e.g., 5 for 5%).
Pipeline Convention: Calculation engine expects decimals (e.g., 0.05 for 5%).

All percentage fields are normalized in the _extract_*_data() methods using
_normalize_percentage() to ensure consistency across the entire codebase.
"""

# ==============================================================================
# FIELD CLASSIFICATION FOR NORMALIZATION
# ==============================================================================

# Fields that represent PERCENTAGES and MUST be normalized (divided by 100)
_PERCENTAGE_FIELDS: Set[str] = {
    # Discount / Cost of Capital fields
    "risk_free_rate",
    "market_risk_premium",
    "cost_of_debt",
    "tax_rate",
    "cost_of_equity",

    # Terminal Value fields
    "perpetual_growth_rate",

    # Bridge fields
    "stock_based_compensation_rate",
    "annual_dilution_rate",

    # Monte Carlo volatility fields
    "base_flow_volatility",
    "beta_volatility",
    "growth_volatility",
    "exit_multiple_volatility",
    "terminal_growth_volatility",
    "wacc_volatility",

    # Scenario fields
    "growth_rate",
    "target_fcf_margin",

    # Model-specific growth rates
    "revenue_growth_rate",
    "earnings_growth_rate",
    "dividend_growth_rate",
    "fcf_growth_rate",
    "residual_income_growth_rate",
    "corporate_aaa_yield"
}

_MILLION_FIELDS: Set[str] = {
    "manual_fcf_base",
    "manual_book_value",
    "manual_total_debt",
    "manual_cash",
    "manual_minority_interests",
    "manual_pension_provisions",
    "manual_shares_outstanding",
}

# Fields that are ABSOLUTE VALUES and must NOT be normalized
_ABSOLUTE_FIELDS: Set[str] = {
    # Control Fields
    "terminal_method",
    "enable_monte_carlo",
    "enable_peer_multiples",
    "enable_backtest",

    # Discount fields
    "manual_beta",
    "manual_stock_price",

    # Terminal Value fields
    "exit_multiple_value",

    # Monte Carlo config
    "num_simulations",

    # Projection config
    "projection_years",

    # Scenario probabilities (already 0-1 from slider)
    "probability",
    "manual_dividend_base"
}


class ExpertTerminalBase(ABC):
    """
    Abstract base class defining the expert valuation entry workflow.

    This class implements the Template Method pattern, orchestrating a 10-step
    valuation input sequence while allowing concrete terminals to customize
    model-specific operational inputs (Step 2).

    Scale Normalization Contract
    ----------------------------
    This base class guarantees that ALL percentage values collected from UI
    widgets are normalized to decimals before being passed to the calculation
    pipeline. Concrete terminals should:

    1. Use `_normalize_percentage()` for any custom percentage extraction
    2. Use `apply_field_scaling()` for conditional normalization
    3. Document clearly if a field is a percentage or absolute value

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

        # 7. Scenario Analysis (Convictions)
        if self.SHOW_SCENARIOS:
            self._scenarios = widget_scenarios(self.MODE)

        # 8. Historical Backtest
        if self.SHOW_BACKTEST:
            from app.ui.expert.terminals.shared_widgets import widget_backtest
            backtest_data = widget_backtest()
            self._collected_data.update(backtest_data or {})

        # 9. Peer Discovery (Triangulation)
        if self.SHOW_PEER_TRIANGULATION:
            peer_data = widget_peer_triangulation()
            self._collected_data.update(peer_data or {})
            self._manual_peers = peer_data.get("manual_peers")

        # 10. SOTP (Final Segmentation)
        if self.SHOW_SOTP:
            from app.ui.expert.terminals.shared_widgets import build_dcf_parameters
            temp_params = build_dcf_parameters(self._collected_data)
            widget_sotp(temp_params, is_conglomerate=False)
            self._collected_data["sotp"] = temp_params.sotp

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
    # SCALE NORMALIZATION UTILITIES
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _normalize_percentage(value: Optional[float]) -> Optional[float]:
        """
        Converts a percentage value (e.g., 5 for 5%) to decimal (0.05).

        This is the CANONICAL normalization method. All percentage fields
        from UI widgets MUST be normalized using this method before being
        passed to the calculation pipeline.

        Parameters
        ----------
        value : Optional[float]
            Raw percentage value from UI input (e.g., 5 for 5%).

        Returns
        -------
        Optional[float]
            Normalized decimal value (e.g., 0.05), or None if input is None.

        Examples
        --------
        >> ExpertTerminalBase._normalize_percentage(5.0)
        0.05
        >> ExpertTerminalBase._normalize_percentage(None)
        None
        >> ExpertTerminalBase._normalize_percentage(0.0)
        0.0
        """
        if value is None:
            return None
        return value / _PERCENTAGE_DIVISOR

    @staticmethod
    def _normalize_million(value: Optional[float]) -> Optional[float]:
        """
        Scales a value from Millions (UI) to absolute Units (Engine).

        Parameters
        ----------
        value : Optional[float]
            Raw value in millions (e.g., 68_000 for 68B).

        Returns
        -------
        Optional[float]
            Scaled value in units (e.g., 68,000,000,000.0), or None.

        Examples
        --------
        >> ExpertTerminalBase._normalize_million(5.0)
        5000000.0
        """
        if value is None:
            return None
        return value * _MILLION_MULTIPLIER

    @staticmethod
    def _normalize_rate(value: Optional[float]) -> Optional[float]:
        """
        Logic imported from Pydantic: Guesses if a value is a percentage.
        If value > 1.0 (ex: 5.0), assumes it's a percentage and returns 0.05.
        """
        if value is None:
            return None
        return value / 100.0 if abs(value) > 1.0 else value

    @staticmethod
    def apply_field_scaling(field_name: str, value: Optional[float]) -> Optional[float]:
        """
        Applies canonical scaling based on field classification.

        Uses _PERCENTAGE_FIELDS, _MILLION_FIELDS, and _ABSOLUTE_FIELDS
        to ensure the engine receives data in the correct mathematical unit.

        Parameters
        ----------
        field_name : str
            The canonical field name.
        value : Optional[float]
            The raw value from UI input.

        Returns
        -------
        Optional[float]
            Scaled value (decimal for %, units for Millions, raw for Absolute).
        """
        if value is None:
            return None

        # Security, if not a number, not normalization
        if not isinstance(value, (int, float)):
            return value

        if field_name in _PERCENTAGE_FIELDS:
            return ExpertTerminalBase._normalize_percentage(value)
        elif field_name in _MILLION_FIELDS:
            return ExpertTerminalBase._normalize_million(value)
        elif field_name in _ABSOLUTE_FIELDS:
            return value

        else:
            # Log warning for unclassified fields (helps catch new fields)
            logger.warning(
                f"Field '{field_name}' is not classified as percentage, absolute or million. "
                f"Returning raw value. Please add to _PERCENTAGE_FIELDS, _ABSOLUTE_FIELDS or _MILLION_FIELDS."
            )
            return ExpertTerminalBase._normalize_rate(value)

    @staticmethod
    def _bulk_normalize(
        data: Dict[str, Any],
        percentage_keys: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Normalizes multiple fields in a dictionary based on field classification.

        This utility method processes an entire data dictionary, normalizing
        percentage fields while leaving absolute fields unchanged.

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary containing field values to normalize.
        percentage_keys : Optional[Set[str]]
            Explicit set of keys to treat as percentages. If None, uses
            the global _PERCENTAGE_FIELDS classification.

        Returns
        -------
        Dict[str, Any]
            New dictionary with normalized values.

        Examples
        --------
        >> data = {"risk_free_rate": 4.0, "manual_beta": 1.2}
        >> ExpertTerminalBase._bulk_normalize(data)
        {"risk_free_rate": 0.04, "manual_beta": 1.2}
        """
        keys_to_normalize = percentage_keys or _PERCENTAGE_FIELDS
        result = {}

        for key, value in data.items():
            if key in keys_to_normalize and isinstance(value, (int, float)):
                result[key] = ExpertTerminalBase._normalize_percentage(value)
            else:
                result[key] = value

        return result

    # ══════════════════════════════════════════════════════════════════════════
    # DATA EXTRACTION (SessionState Mapping)
    # ══════════════════════════════════════════════════════════════════════════

    def build_request(self) -> Optional[ValuationRequest]:
        """
        Constructs the final ValuationRequest domain object.

        Aggregates all collected data from UI widgets, applies percentage
        normalization, and builds the complete request for the valuation engine.

        IMPORTANT: All percentage values are normalized to decimals in the
        respective _extract_*_data() methods. The calculation pipeline
        receives only decimal values (e.g., 0.05 for 5%).

        Returns
        -------
        Optional[ValuationRequest]
            The fully constructed valuation request.
        """
        from app.ui.expert.terminals.shared_widgets import build_dcf_parameters

        key_prefix = self.MODE.name
        collected_data = {"projection_years": st.session_state.get(f"{key_prefix}_years", 5)}

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

        collected_data.update(self._extract_model_inputs_data(key_prefix))

        final_collected_data = {}
        for field_name, value in collected_data.items():
            final_collected_data[field_name] = self.apply_field_scaling(field_name, value)

        params = build_dcf_parameters(final_collected_data)

        if self.SHOW_SCENARIOS:
            params.scenarios = self._extract_scenarios_data()
        if self.SHOW_SOTP:
            params.sotp = self._extract_sotp_data()

        return ValuationRequest(
            ticker=self.ticker,
            mode=self.MODE,
            projection_years=final_collected_data.get("projection_years", 5),
            input_source=InputSource.MANUAL,
            manual_params=params,
            options=self._build_options(final_collected_data),
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
    def _extract_discount_data(key_prefix: str) -> Dict[str, Any]:
        """
        Maps Rf, Beta, MRP, Price, Kd, Ke, and Tax from session state.

        NORMALIZATION CONTRACT:
        - Rates (Rf, MRP, Kd, Ke, Tax) are normalized from percentage to decimal.
        - Beta and Price remain unchanged as they are not percentages.

        Parameters
        ----------
        key_prefix : str
            Session state key prefix (typically the ValuationMode name).

        Returns
        -------
        Dict[str, Any]
            Extracted and normalized discount parameters.

        Examples
        --------
        If session state contains:
            FCFF_STANDARD_rf: 4.0  (user entered 4%)
            FCFF_STANDARD_beta: 1.2

        Returns:
            {"risk_free_rate": 0.04, "manual_beta": 1.2}
        """
        data = {}

        # Fields requiring percentage normalization (rates)
        field_mapping = {
            f"{key_prefix}_rf": "risk_free_rate",
            f"{key_prefix}_mrp": "market_risk_premium",
            f"{key_prefix}_kd": "cost_of_debt",
            f"{key_prefix}_ke": "cost_of_equity",  # For direct equity models
            f"{key_prefix}_tax": "tax_rate",
            f"{key_prefix}_beta": "manual_beta",
            f"{key_prefix}_price": "manual_stock_price"
        }

        # Extract absolute fields without normalization
        for session_key, field_name in field_mapping.items():
            if session_key in st.session_state:
                data[field_name] = st.session_state[session_key]

        return data

    @staticmethod
    def _extract_bridge_data(key_prefix: str) -> Dict[str, Any]:
        """
        Maps Balance Sheet structure and SBC dilution from session state.

        NORMALIZATION CONTRACT:
        - SBC dilution rate is normalized from percentage to decimal.
        - Currency amounts (debt, cash, etc.) remain unchanged.
        - Share counts remain unchanged.

        Parameters
        ----------
        key_prefix : str
            Session state key prefix (typically the ValuationMode name).

        Returns
        -------
        Dict[str, Any]
            Extracted and normalized bridge parameters.

        Examples
        --------
        If session state contains:
            bridge_FCFF_STANDARD_sbc_rate: 2.5  (user entered 2.5%)
            bridge_FCFF_STANDARD_debt: 1000000

        Returns:
            {"stock_based_compensation_rate": 0.025, "manual_total_debt": 1_000_000}
        """
        data = {}
        p = f"bridge_{key_prefix}"

        # Mapping complet des champs du Bridge
        field_mapping = {
            f"{p}_debt": "manual_total_debt",
            f"{p}_cash": "manual_cash",
            f"{p}_min": "manual_minority_interests",
            f"{p}_pen": "manual_pension_provisions",
            f"{p}_shares": "manual_shares_outstanding",
            f"{p}_shares_direct": "manual_shares_outstanding",
            f"{p}_sbc_rate": "stock_based_compensation_rate",
        }

        for session_key, field_name in field_mapping.items():
            if session_key in st.session_state:
                data[field_name] = st.session_state[session_key]

        return data

    @staticmethod
    def _extract_terminal_data(key_prefix: str) -> Dict[str, Any]:
        """
        Extracts Terminal Value parameters (Gordon or Exit Multiples).

        NORMALIZATION CONTRACT:
        - Gordon Growth: perpetual_growth_rate is normalized (% -> decimal).
        - Exit Multiple: exit_multiple_value is NOT normalized (absolute multiple).

        Parameters
        ----------
        key_prefix : str
            Session state key prefix (typically the ValuationMode name).

        Returns
        -------
        Dict[str, Any]
            Extracted and normalized terminal value parameters.

        Examples
        --------
        Gordon Growth with session state:
            FCFF_STANDARD_method: TerminalValueMethod.GORDON_GROWTH
            FCFF_STANDARD_gn: 2.5  (user entered 2.5%)

        Returns:
            {"terminal_method": GORDON_GROWTH, "perpetual_growth_rate": 0.025}

        Exit Multiple with session state:
            FCFF_STANDARD_method: TerminalValueMethod.EXIT_MULTIPLE
            FCFF_STANDARD_exit_mult: 12.0

        Returns:
            {"terminal_method": EXIT_MULTIPLE, "exit_multiple_value": 12.0}
        """
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

    @staticmethod
    def _extract_monte_carlo_data() -> Dict[str, Any]:
        """
        Extracts Monte Carlo configuration with safety checks.

        NORMALIZATION CONTRACT:
        - All volatility parameters are normalized from percentage to decimal.
        - num_simulations is NOT normalized (absolute count).
        - enable_monte_carlo is NOT normalized (boolean).

        Returns
        -------
        Dict[str, Any]
            Monte Carlo configuration with normalized volatilities.

        Examples
        --------
        If session state contains:
            mc_enable: True
            mc_sims: 5000
            mc_vol_flow: 15.0  (user entered 15%)
            mc_vol_growth: 20.0  (user entered 20%)

        Returns:
            {
                "enable_monte_carlo": True,
                "num_simulations": 5000,
                "base_flow_volatility": 0.15,
                "growth_volatility": 0.20,
                ...
            }
        """
        p = "mc"
        if not st.session_state.get(f"{p}_enable", False):
            return {"enable_monte_carlo": False}

        return {
            "enable_monte_carlo": True,
            "num_simulations": st.session_state.get(f"{p}_sims", 5000),
            "base_flow_volatility": st.session_state.get(f"{p}_vol_flow"),
            "beta_volatility": st.session_state.get(f"{p}_vol_beta"),
            "growth_volatility": st.session_state.get(f"{p}_vol_growth"),
            "exit_multiple_volatility": st.session_state.get(f"{p}_vol_exit_m"),
            "terminal_growth_volatility": st.session_state.get(f"{p}_vol_gn"),
            "wacc_volatility": st.session_state.get(f"{p}_vol_wacc"),
        }

    @staticmethod
    def _extract_peer_triangulation_data() -> Dict[str, Any]:
        """
        Extracts peer cohort tickers for multiples triangulation.

        No normalization required - peer tickers are strings.

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

        NORMALIZATION CONTRACT:
        - Growth rates are normalized from percentage to decimal.
        - FCF margins are normalized from percentage to decimal.
        - Probabilities are NOT normalized (already 0-1 from slider widget).

        Returns
        -------
        Optional[ScenarioParameters]
            Scenario configuration with normalized rates, or disabled if not set.

        Examples
        --------
        If session state contains:
            scenario_p_bull: 0.25 (probability, already decimal)
            scenario_g_bull: 8.0  (user entered 8% growth)
            scenario_m_bull: 15.0 (user entered 15% margin)

        Returns ScenarioVariant with:
            probability=0.25, growth_rate=0.08, target_fcf_margin=0.15
        """
        from src.models import ScenarioVariant
        p = "scenario"

        if not st.session_state.get(f"{p}_scenario_enable"):
            return ScenarioParameters(enabled=False)

        # Helper for percentage normalization with logging
        def normalize(key: str, field_desc: str) -> Optional[float]:
            raw = st.session_state.get(key)
            if raw is None:
                return None
            normalized = ExpertTerminalBase._normalize_percentage(raw)
            logger.debug(f"Normalized {field_desc}: {raw}% -> {normalized}")
            return normalized

        try:
            return ScenarioParameters(
                enabled=True,
                bull=ScenarioVariant(
                    label=SharedTexts.LBL_BULL,
                    probability=st.session_state[f"{p}_p_bull"],  # Already 0-1
                    growth_rate=normalize(f"{p}_g_bull", "bull.growth_rate"),
                    target_fcf_margin=normalize(f"{p}_m_bull", "bull.target_fcf_margin"),
                ),
                base=ScenarioVariant(
                    label=SharedTexts.LBL_BASE,
                    probability=st.session_state[f"{p}_p_base"],  # Already 0-1
                    growth_rate=normalize(f"{p}_g_base", "base.growth_rate"),
                    target_fcf_margin=normalize(f"{p}_m_base", "base.target_fcf_margin"),
                ),
                bear=ScenarioVariant(
                    label=SharedTexts.LBL_BEAR,
                    probability=st.session_state[f"{p}_p_bear"],  # Already 0-1
                    growth_rate=normalize(f"{p}_g_bear", "bear.growth_rate"),
                    target_fcf_margin=normalize(f"{p}_m_bear", "bear.target_fcf_margin"),
                ),
            )
        except (KeyError, RuntimeError, ValueError) as e:
            logger.warning(f"Failed to extract scenarios data: {e}")
            return ScenarioParameters(enabled=False)

    @staticmethod
    def _extract_backtest_data() -> Dict[str, Any]:
        """
        Extracts historical backtest configuration.

        No normalization required - boolean flag only.

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

    # ══════════════════════════════════════════════════════════════════════════
    # ABSTRACT METHODS — TO BE IMPLEMENTED BY CONCRETE TERMINALS
    # ══════════════════════════════════════════════════════════════════════════

    @abstractmethod
    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Abstract hook for specific model operational inputs.

        Each concrete terminal must implement this to render model-specific
        widgets for Step 2 (Operational Anchoring & Growth).

        IMPORTANT: This method should return RAW values from UI widgets.
        Normalization should be handled in _extract_model_inputs_data().

        Returns
        -------
        Dict[str, Any]
            Model-specific parameters collected from UI widgets (RAW values).
        """
        pass

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Default hook for model-specific data extraction with normalization.

        Override this in concrete terminals to extract and normalize
        model-specific parameters from session state.

        NORMALIZATION CONTRACT:
        Concrete implementations MUST normalize all percentage fields using
        _normalize_percentage() or apply_field_scaling().

        Common percentage fields in model inputs:
        - Growth rates (revenue, earnings, dividend, FCF, etc.)
        - Margins (FCF margin, EBIT margin, etc.)
        - Return rates (ROE, ROIC, etc.)

        Parameters
        ----------
        key_prefix : str
            Session state key prefix (typically the ValuationMode name).

        Returns
        -------
        Dict[str, Any]
            Empty dict by default, overridden by concrete terminals
            with normalized values.

        Examples
        --------
        In a concrete terminal (e.g., FCFFStandardTerminal):

        def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
            data = {}

            # Growth rate is a percentage - MUST normalize
            raw_growth = st.session_state.get(f"{key_prefix}_growth_rate")
            data["revenue_growth_rate"] = self._normalize_percentage(raw_growth)

            # FCF margin is a percentage - MUST normalize
            raw_margin = st.session_state.get(f"{key_prefix}_fcf_margin")
            data["target_fcf_margin"] = self._normalize_percentage(raw_margin)

            # Base revenue is absolute - do NOT normalize
            data["base_revenue"] = st.session_state.get(f"{key_prefix}_base_revenue")

            return data
        """
        return {}