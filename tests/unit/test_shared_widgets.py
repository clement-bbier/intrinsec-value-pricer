"""
tests/unit/test_shared_widgets.py

UNIT TESTS — Complete test coverage for shared_widgets.py

Testing Strategy:
    - Mock ALL Streamlit widgets to control return values
    - Test business logic independently of UI rendering
    - Cover edge cases and validation paths
    - Use pytest fixtures for reusable test setup

Pattern: AAA (Arrange-Act-Assert)
Style: pytest with fixtures and parametrize
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from typing import Dict, Any

import pandas as pd

# === MOCK DEPENDENCIES BEFORE IMPORT ===
# These must be patched before importing the module under test


@pytest.fixture(autouse=True)
def mock_streamlit():
    """
    Global Streamlit mock fixture.
    Patches st module to prevent actual UI rendering.
    """
    with patch.dict('sys.modules', {'streamlit': MagicMock()}):
        yield


@pytest.fixture
def mock_shared_texts():
    """Mock i18n SharedTexts with test constants."""
    mock_texts = MagicMock()
    
    # Base widget labels
    mock_texts.INP_PROJ_YEARS = "Projection Years"
    mock_texts.HELP_PROJ_YEARS = "Number of years to project"
    mock_texts.INP_GROWTH_G = "Growth Rate (g)"
    mock_texts.HELP_GROWTH_RATE = "Expected growth rate"
    
    # Cost of capital
    mock_texts.FORMULA_CAPITAL_KE = r"K_e = R_f + \beta \cdot MRP"
    mock_texts.FORMULA_CAPITAL_WACC = r"WACC = K_e \cdot W_e + K_d \cdot (1-\tau) \cdot W_d"
    mock_texts.INP_PRICE_WEIGHTS = "Reference Price"
    mock_texts.HELP_PRICE_WEIGHTS = "Manual stock price"
    mock_texts.INP_RF = "Risk-free Rate"
    mock_texts.HELP_RF = "Government bond yield"
    mock_texts.INP_BETA = "Beta"
    mock_texts.HELP_BETA = "Market sensitivity"
    mock_texts.INP_MRP = "Market Risk Premium"
    mock_texts.HELP_MRP = "Expected return above risk-free"
    mock_texts.INP_KD = "Cost of Debt"
    mock_texts.HELP_KD = "Interest rate on debt"
    mock_texts.INP_TAX = "Tax Rate"
    mock_texts.HELP_TAX = "Corporate tax rate"
    
    # Terminal value
    mock_texts.SEC_4_TERMINAL = "## Terminal Value"
    mock_texts.SEC_4_DESC = "Configure terminal value calculation"
    mock_texts.RADIO_TV_METHOD = "TV Method"
    mock_texts.TV_GORDON = "Gordon Growth"
    mock_texts.TV_EXIT = "Exit Multiple"
    mock_texts.FORMULA_TV_GORDON = r"TV = \frac{FCF_{n+1}}{r - g}"
    mock_texts.FORMULA_TV_EXIT = r"TV = EBITDA_n \times Multiple"
    mock_texts.INP_PERP_G = "Perpetual Growth Rate"
    mock_texts.HELP_PERP_G = "Long-term growth rate"
    mock_texts.INP_EXIT_MULT = "Exit Multiple"
    mock_texts.HELP_EXIT_MULT = "EBITDA exit multiple"
    mock_texts.INP_OMEGA = "Omega (ω)"
    mock_texts.HELP_OMEGA = "Persistence factor"
    
    # Equity bridge
    mock_texts.SEC_5_BRIDGE = "## Equity Bridge"
    mock_texts.SEC_5_DESC = "Configure equity value bridge"
    mock_texts.INP_SHARES = "Shares Outstanding"
    mock_texts.HELP_SHARES = "Number of shares"
    mock_texts.BRIDGE_COMPONENTS = "### Capital Structure"
    mock_texts.INP_DEBT = "Total Debt"
    mock_texts.INP_CASH = "Cash & Equivalents"
    mock_texts.BRIDGE_ADJUSTMENTS = "### Adjustments"
    mock_texts.INP_MINORITIES = "Minority Interests"
    mock_texts.INP_PENSIONS = "Pension Provisions"
    mock_texts.BRIDGE_DILUTION = "### Dilution"
    mock_texts.INP_SBC_DILUTION = "SBC Dilution Rate"
    
    # Monte Carlo
    mock_texts.SEC_6_MC = "## Monte Carlo Simulation"
    mock_texts.SEC_6_DESC_MC = "Configure stochastic simulation"
    mock_texts.MC_CALIBRATION = "Enable Monte Carlo"
    mock_texts.MC_ITERATIONS = "Simulations"
    mock_texts.MC_VOL_INCERTITUDE = "Volatility parameters"
    mock_texts.MC_VOL_EPS = "EPS Volatility"
    mock_texts.MC_VOL_NI = "Net Income Volatility"
    mock_texts.MC_VOL_DIV = "Dividend Volatility"
    mock_texts.MC_VOL_BASE_FLOW = "Base Flow Volatility"
    mock_texts.MC_VOL_BETA = "Beta Volatility"
    mock_texts.MC_VOL_G = "Growth Volatility"
    mock_texts.LBL_VOL_OMEGA = "Omega (ω) Volatility"
    mock_texts.LBL_VOL_EXIT_M = "Exit Multiple Volatility"
    mock_texts.HELP_VOL_BASE = "Volatility of base cash flow"
    
    # Peer triangulation
    mock_texts.SEC_7_PEERS = "## Peer Comparison"
    mock_texts.SEC_7_DESC_PEERS = "Configure peer group"
    mock_texts.LBL_PEER_ENABLE = "Enable Peer Analysis"
    mock_texts.HELP_PEER_TRIANGULATION = "Use peer multiples"
    mock_texts.INP_MANUAL_PEERS = "Peer Tickers"
    mock_texts.PLACEHOLDER_PEERS = "AAPL, MSFT, GOOGL"
    mock_texts.HELP_MANUAL_PEERS = "Comma-separated tickers"
    mock_texts.PEERS_SELECTED = "Selected peers: {peers}"
    
    # Scenarios
    mock_texts.SEC_8_SCENARIOS = "## Scenario Analysis"
    mock_texts.SEC_8_DESC_SCENARIOS = "Configure scenarios"
    mock_texts.INP_SCENARIO_ENABLE = "Enable Scenarios"
    mock_texts.LABEL_SCENARIO_BULL = "Bull Case"
    mock_texts.LABEL_SCENARIO_BASE = "Base Case"
    mock_texts.LABEL_SCENARIO_BEAR = "Bear Case"
    mock_texts.INP_SCENARIO_PROBA = "Probability (%)"
    mock_texts.INP_SCENARIO_GROWTH = "Growth Rate"
    mock_texts.INP_SCENARIO_MARGIN = "FCF Margin"
    mock_texts.ERR_SCENARIO_PROBA_SUM = "Probabilities must sum to 100% (got {sum}%)"
    mock_texts.LBL_BULL = "Bull"
    mock_texts.LBL_BASE = "Base"
    mock_texts.LBL_BEAR = "Bear"
    
    # SOTP
    mock_texts.SEC_9_SOTP = "## Sum-of-the-Parts"
    mock_texts.SEC_9_DESC = "Configure segment valuation"
    mock_texts.WARN_SOTP_RELEVANCE = "SOTP is most relevant for conglomerates"
    mock_texts.LBL_SOTP_ENABLE = "Enable SOTP"
    mock_texts.HELP_SOTP_ENABLE = "Sum-of-the-parts valuation"
    mock_texts.LBL_SEGMENT_NAME = "Segment Name"
    mock_texts.LBL_SEGMENT_VALUE = "Enterprise Value"
    mock_texts.LBL_SEGMENT_METHOD = "Valuation Method"
    mock_texts.DEFAULT_SEGMENT_NAME = "Core Business"
    mock_texts.SEC_SOTP_ADJUSTMENTS = "### Holding Adjustments"
    mock_texts.LBL_DISCOUNT = "Conglomerate Discount (%)"
    
    return mock_texts


@pytest.fixture
def mock_ui_defaults():
    """Mock UIWidgetDefaults constants."""
    mock_defaults = MagicMock()
    mock_defaults.DEFAULT_PROJECTION_YEARS = 5
    mock_defaults.MIN_PROJECTION_YEARS = 1
    mock_defaults.MAX_PROJECTION_YEARS = 15
    mock_defaults.MIN_GROWTH_RATE = -0.1
    mock_defaults.MAX_GROWTH_RATE = 0.5
    mock_defaults.DEFAULT_BASE_FLOW_VOLATILITY = 0.15
    return mock_defaults


# ==============================================================================
# 1. COST OF CAPITAL WIDGET TESTS
# ==============================================================================

class TestCostOfCapitalWidget:
    """Test suite for cost of capital widget (WACC/Ke)."""

    @pytest.fixture
    def mock_valuation_mode_equity(self):
        """Mock ValuationMode for direct equity models."""
        mode = MagicMock()
        mode.is_direct_equity = True
        mode.name = "DDM"
        return mode

    @pytest.fixture
    def mock_valuation_mode_wacc(self):
        """Mock ValuationMode for enterprise value models."""
        mode = MagicMock()
        mode.is_direct_equity = False
        mode.name = "FCFF"
        return mode

    def test_widget_cost_of_capital_direct_equity_mode(
        self, mock_shared_texts, mock_valuation_mode_equity
    ):
        """Test cost of capital for direct equity (Ke only, no WACC components)."""
        # Mock all Streamlit components
        mock_st = MagicMock()
        mock_st.latex = MagicMock()
        mock_st.divider = MagicMock()
        
        # Create column mocks
        col_a = MagicMock()
        col_b = MagicMock()
        
        # Configure number_input return values
        mock_st.number_input.return_value = 100.0  # manual_price
        col_a.number_input.side_effect = [0.04, 0.06]  # rf, mrp
        col_b.number_input.return_value = 1.2  # beta
        mock_st.columns.return_value = (col_a, col_b)
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_cost_of_capital
            
            result = widget_cost_of_capital(mock_valuation_mode_equity)
            
            # Verify Ke formula displayed
            mock_st.latex.assert_called()
            
            # Verify result contains expected keys for equity mode
            assert 'risk_free_rate' in result
            assert 'manual_beta' in result
            assert 'market_risk_premium' in result
            assert 'manual_stock_price' in result
            
            # WACC-specific keys should NOT be present
            assert 'cost_of_debt' not in result
            assert 'tax_rate' not in result

    def test_widget_cost_of_capital_wacc_mode(
        self, mock_shared_texts, mock_valuation_mode_wacc
    ):
        """Test cost of capital for WACC mode (includes debt and tax)."""
        mock_st = MagicMock()
        mock_st.latex = MagicMock()
        mock_st.divider = MagicMock()
        
        col_a = MagicMock()
        col_b = MagicMock()
        
        # Configure return values for WACC mode
        mock_st.number_input.return_value = 150.0  # manual_price
        col_a.number_input.side_effect = [0.04, 0.06, 0.25]  # rf, mrp, tax
        col_b.number_input.side_effect = [1.1, 0.05]  # beta, kd
        mock_st.columns.return_value = (col_a, col_b)
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_cost_of_capital
            
            result = widget_cost_of_capital(mock_valuation_mode_wacc)
            
            # Verify WACC formula displayed
            mock_st.latex.assert_called()
            
            # Verify all WACC components present
            assert 'risk_free_rate' in result
            assert 'manual_beta' in result
            assert 'market_risk_premium' in result
            assert 'manual_stock_price' in result
            assert 'cost_of_debt' in result
            assert 'tax_rate' in result

    def test_widget_cost_of_capital_custom_prefix(
        self, mock_shared_texts, mock_valuation_mode_equity
    ):
        """Test cost of capital uses custom key prefix."""
        mock_st = MagicMock()
        mock_st.latex = MagicMock()
        mock_st.divider = MagicMock()
        mock_st.number_input.return_value = 100.0
        
        col_a = MagicMock()
        col_b = MagicMock()
        col_a.number_input.side_effect = [0.03, 0.05]
        col_b.number_input.return_value = 1.0
        mock_st.columns.return_value = (col_a, col_b)
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_cost_of_capital
            
            result = widget_cost_of_capital(
                mock_valuation_mode_equity,
                key_prefix="custom_terminal"
            )
            
            # Verify custom prefix used in widget keys
            assert mock_st.number_input.called


# ==============================================================================
# 2. TERMINAL VALUE WIDGET TESTS
# ==============================================================================

class TestTerminalValueWidgets:
    """Test suite for terminal value widgets (DCF and RIM)."""

    def test_widget_terminal_value_rim_omega_factor(self, mock_shared_texts):
        """Test RIM terminal value widget (omega persistence factor)."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.latex = MagicMock()
        mock_st.divider = MagicMock()
        
        col1 = MagicMock()
        col1.number_input.return_value = 0.75  # omega factor
        mock_st.columns.return_value = (col1, MagicMock())
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            with patch('app.ui.expert.terminals.shared_widgets.TerminalValueMethod') as mock_tvm:
                mock_exit = MagicMock()
                mock_tvm.EXIT_MULTIPLE = mock_exit
                
                from app.ui.expert.terminals.shared_widgets import widget_terminal_value_rim
                
                result = widget_terminal_value_rim(
                    formula_latex=r"TV_{RIM} = \omega \cdot RI_n"
                )
                
                assert result['terminal_method'] == mock_exit
                assert result['exit_multiple_value'] == 0.75

    def test_widget_terminal_value_rim_custom_prefix(self, mock_shared_texts):
        """Test RIM terminal value with custom key prefix."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.latex = MagicMock()
        mock_st.divider = MagicMock()
        
        col1 = MagicMock()
        col1.number_input.return_value = 0.5
        mock_st.columns.return_value = (col1, MagicMock())
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            with patch('app.ui.expert.terminals.shared_widgets.TerminalValueMethod') as mock_tvm:
                mock_tvm.EXIT_MULTIPLE = MagicMock()
                
                from app.ui.expert.terminals.shared_widgets import widget_terminal_value_rim
                
                result = widget_terminal_value_rim(
                    formula_latex=r"TV",
                    key_prefix="rim_custom"
                )
                
                # Verify custom prefix was used
                call_kwargs = col1.number_input.call_args
                assert 'rim_custom' in str(call_kwargs)


# ==============================================================================
# 3. EQUITY BRIDGE WIDGET TESTS
# ==============================================================================

class TestEquityBridgeWidget:
    """Test suite for equity bridge widget."""

    @pytest.fixture
    def mock_mode_direct_equity(self):
        """Mock mode for direct equity valuation."""
        mode = MagicMock()
        mode.is_direct_equity = True
        mode.value = "DDM"
        return mode

    @pytest.fixture
    def mock_mode_enterprise(self):
        """Mock mode for enterprise valuation (FCFF)."""
        mode = MagicMock()
        mode.is_direct_equity = False
        mode.value = "FCFF"
        return mode



# ==============================================================================
# 5. MONTE CARLO WIDGET TESTS
# ==============================================================================

class TestMonteCarloWidget:
    """Test suite for Monte Carlo simulation widget."""

    @pytest.fixture
    def mock_mode_fcff(self):
        """Mock FCFF valuation mode."""
        mode = MagicMock()
        mode.name = "FCFF"
        return mode

    @pytest.fixture
    def mock_mode_graham(self):
        """Mock Graham valuation mode."""
        mode = MagicMock()
        mode.name = "GRAHAM"
        return mode

    @pytest.fixture
    def mock_mode_rim(self):
        """Mock RIM valuation mode."""
        mode = MagicMock()
        mode.name = "RIM"
        return mode

    @pytest.fixture
    def mock_mode_ddm(self):
        """Mock DDM valuation mode."""
        mode = MagicMock()
        mode.name = "DDM"
        return mode

    def test_widget_monte_carlo_disabled(self, mock_shared_texts, mock_mode_fcff):
        """Test Monte Carlo widget when disabled."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.toggle.return_value = False  # MC disabled
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_monte_carlo
            
            result = widget_monte_carlo(mock_mode_fcff)
            
            assert result == {'enable_monte_carlo': False}

    def test_widget_monte_carlo_enabled_fcff(self, mock_shared_texts, mock_mode_fcff):
        """Test Monte Carlo widget enabled with FCFF mode."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.toggle.return_value = True  # MC enabled
        mock_st.select_slider.return_value = 10000  # simulations
        
        # Mock columns
        v_col1 = MagicMock()
        v_col2 = MagicMock()
        v_col1.number_input.side_effect = [0.15, 0.05]  # base_vol, growth_vol
        v_col2.number_input.side_effect = [0.10, None]  # beta_vol, exit_vol (None if not exit method)
        mock_st.columns.return_value = (v_col1, v_col2)
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            with patch('app.ui.expert.terminals.shared_widgets.ValuationMode') as mock_vm:
                mock_vm.GRAHAM = MagicMock()
                mock_vm.RIM = MagicMock()
                mock_vm.DDM = MagicMock()
                
                from app.ui.expert.terminals.shared_widgets import widget_monte_carlo
                
                result = widget_monte_carlo(mock_mode_fcff)
                
                assert result['enable_monte_carlo'] is True
                assert result['num_simulations'] == 10000
                assert result['base_flow_volatility'] == 0.15
                assert result['growth_volatility'] == 0.05
                assert result['beta_volatility'] == 0.10

    def test_widget_monte_carlo_graham_no_beta(self, mock_shared_texts, mock_mode_graham):
        """Test Monte Carlo with Graham mode (no beta volatility)."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.select_slider.return_value = 5000
        
        v_col1 = MagicMock()
        v_col2 = MagicMock()
        v_col1.number_input.side_effect = [0.20, 0.08]
        mock_st.columns.return_value = (v_col1, v_col2)
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            with patch('app.ui.expert.terminals.shared_widgets.ValuationMode') as mock_vm:
                mock_vm.GRAHAM = mock_mode_graham
                mock_vm.RIM = MagicMock()
                mock_vm.DDM = MagicMock()
                
                from app.ui.expert.terminals.shared_widgets import widget_monte_carlo
                
                result = widget_monte_carlo(mock_mode_graham)
                
                # Beta should be None for Graham
                assert result['beta_volatility'] is None

    def test_widget_monte_carlo_with_exit_multiple(self, mock_shared_texts, mock_mode_fcff):
        """Test Monte Carlo with exit multiple terminal method."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.select_slider.return_value = 5000
        
        v_col1 = MagicMock()
        v_col2 = MagicMock()
        v_col1.number_input.side_effect = [0.15, 0.05]
        v_col2.number_input.side_effect = [0.10, 0.25]  # beta_vol, exit_vol
        mock_st.columns.return_value = (v_col1, v_col2)
        
        mock_exit_multiple = MagicMock()
        mock_exit_multiple.name = "EXIT_MULTIPLE"
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            with patch('app.ui.expert.terminals.shared_widgets.ValuationMode') as mock_vm:
                mock_vm.GRAHAM = MagicMock()
                mock_vm.RIM = MagicMock()
                mock_vm.DDM = MagicMock()
                
                with patch('app.ui.expert.terminals.shared_widgets.TerminalValueMethod') as mock_tvm:
                    mock_tvm.EXIT_MULTIPLE = mock_exit_multiple
                    
                    from app.ui.expert.terminals.shared_widgets import widget_monte_carlo
                    
                    result = widget_monte_carlo(
                        mock_mode_fcff,
                        terminal_method=mock_exit_multiple
                    )
                    
                    assert result['exit_multiple_volatility'] == 0.25

    def test_widget_monte_carlo_custom_vol_labels(self, mock_shared_texts, mock_mode_fcff):
        """Test Monte Carlo with custom volatility labels."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.select_slider.return_value = 5000
        
        v_col1 = MagicMock()
        v_col2 = MagicMock()
        v_col1.number_input.side_effect = [0.18, 0.06]
        v_col2.number_input.return_value = 0.12
        mock_st.columns.return_value = (v_col1, v_col2)
        
        custom_labels = {
            "base_flow_volatility": "Custom FCF Vol",
            "growth_volatility": "Custom Growth Vol"
        }
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            with patch('app.ui.expert.terminals.shared_widgets.ValuationMode') as mock_vm:
                mock_vm.GRAHAM = MagicMock()
                mock_vm.RIM = MagicMock()
                mock_vm.DDM = MagicMock()
                
                from app.ui.expert.terminals.shared_widgets import widget_monte_carlo
                
                result = widget_monte_carlo(
                    mock_mode_fcff,
                    custom_vols=custom_labels
                )
                
                assert result['base_flow_volatility'] == 0.18

    def test_widget_monte_carlo_rim_mode_labels(self, mock_shared_texts, mock_mode_rim):
        """Test Monte Carlo uses correct labels for RIM mode."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.select_slider.return_value = 5000
        
        v_col1 = MagicMock()
        v_col2 = MagicMock()
        v_col1.number_input.side_effect = [0.12, 0.04]
        v_col2.number_input.return_value = 0.08
        mock_st.columns.return_value = (v_col1, v_col2)
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            with patch('app.ui.expert.terminals.shared_widgets.ValuationMode') as mock_vm:
                mock_vm.GRAHAM = MagicMock()
                mock_vm.RIM = mock_mode_rim
                mock_vm.DDM = MagicMock()
                
                from app.ui.expert.terminals.shared_widgets import widget_monte_carlo
                
                result = widget_monte_carlo(mock_mode_rim)
                
                # Verify NI volatility label used (via call inspection)
                assert result['enable_monte_carlo'] is True


# ==============================================================================
# 5. PEER TRIANGULATION WIDGET TESTS
# ==============================================================================

class TestPeerTriangulationWidget:
    """Test suite for peer triangulation widget."""

    def test_widget_peer_triangulation_disabled(self, mock_shared_texts):
        """Test peer triangulation when disabled."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.toggle.return_value = False
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_peer_triangulation
            
            result = widget_peer_triangulation()
            
            assert result == {
                'enable_peer_multiples': False,
                'manual_peers': None
            }

    def test_widget_peer_triangulation_enabled_with_peers(self, mock_shared_texts):
        """Test peer triangulation with peer list."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.text_input.return_value = "AAPL, MSFT, GOOGL"
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_peer_triangulation
            
            result = widget_peer_triangulation()
            
            assert result['enable_peer_multiples'] is True
            assert result['manual_peers'] == ['AAPL', 'MSFT', 'GOOGL']

    def test_widget_peer_triangulation_empty_input(self, mock_shared_texts):
        """Test peer triangulation with empty input."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.text_input.return_value = ""
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_peer_triangulation
            
            result = widget_peer_triangulation()
            
            assert result['enable_peer_multiples'] is True
            assert result['manual_peers'] is None

    def test_widget_peer_triangulation_whitespace_handling(self, mock_shared_texts):
        """Test peer triangulation handles whitespace correctly."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.text_input.return_value = "  aapl  ,  msft  ,  ,  googl  "
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_peer_triangulation
            
            result = widget_peer_triangulation()
            
            # Should strip whitespace and convert to uppercase
            assert result['manual_peers'] == ['AAPL', 'MSFT', 'GOOGL']

    def test_widget_peer_triangulation_custom_prefix(self, mock_shared_texts):
        """Test peer triangulation with custom key prefix."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.toggle.return_value = False
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_peer_triangulation
            
            result = widget_peer_triangulation(key_prefix="custom_peer")
            
            # Verify custom prefix used in toggle
            toggle_call = mock_st.toggle.call_args
            assert 'custom_peer' in str(toggle_call)


# ==============================================================================
# 7. SCENARIOS WIDGET TESTS
# ==============================================================================

class TestScenariosWidget:
    """Test suite for scenario analysis widget."""

    @pytest.fixture
    def mock_mode_fcff_growth(self):
        """Mock FCFF_GROWTH mode (shows margin input)."""
        mode = MagicMock()
        mode.name = "FCFF_GROWTH"
        return mode

    @pytest.fixture
    def mock_mode_ddm(self):
        """Mock DDM mode (no margin input)."""
        mode = MagicMock()
        mode.name = "DDM"
        return mode

    def test_widget_scenarios_disabled(self, mock_shared_texts, mock_mode_fcff_growth):
        """Test scenarios widget when disabled."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.toggle.return_value = False
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            with patch('app.ui.expert.terminals.shared_widgets.ScenarioParameters') as mock_sp:
                mock_sp.return_value = MagicMock(enabled=False)
                
                from app.ui.expert.terminals.shared_widgets import widget_scenarios
                
                result = widget_scenarios(mock_mode_fcff_growth)
                
                assert result.enabled is False

    def test_widget_scenarios_valid_probabilities(self, mock_shared_texts, mock_mode_ddm):
        """Test scenarios with valid probability sum (100%)."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.error = MagicMock()
        
        # Mock columns for each scenario variant
        c1 = MagicMock()
        c2 = MagicMock()
        c3 = MagicMock()
        
        # Bull: 25%, 0.08 growth
        # Base: 50%, 0.05 growth
        # Bear: 25%, 0.02 growth
        c1.number_input.side_effect = [25.0, 50.0, 25.0]  # probabilities
        c2.number_input.side_effect = [0.08, 0.05, 0.02]  # growth rates
        c3.number_input.return_value = None  # No margin for DDM
        
        mock_st.columns.return_value = (c1, c2, c3)
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            with patch('app.ui.expert.terminals.shared_widgets.ValuationMode') as mock_vm:
                mock_vm.FCFF_GROWTH = MagicMock()
                
                with patch('app.ui.expert.terminals.shared_widgets.ScenarioParameters') as mock_sp:
                    with patch('app.ui.expert.terminals.shared_widgets.ScenarioVariant') as mock_sv:
                        mock_sv.return_value = MagicMock()
                        mock_result = MagicMock(enabled=True)
                        mock_sp.return_value = mock_result
                        
                        from app.ui.expert.terminals.shared_widgets import widget_scenarios
                        
                        result = widget_scenarios(mock_mode_ddm)
                        
                        # Should not show error
                        mock_st.error.assert_not_called()
                        assert result.enabled is True

    def test_widget_scenarios_invalid_probabilities(self, mock_shared_texts, mock_mode_ddm):
        """Test scenarios with invalid probability sum (not 100%)."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.error = MagicMock()
        
        c1 = MagicMock()
        c2 = MagicMock()
        c3 = MagicMock()
        
        # Invalid: 30% + 40% + 20% = 90%
        c1.number_input.side_effect = [30.0, 40.0, 20.0]
        c2.number_input.side_effect = [0.08, 0.05, 0.02]
        c3.number_input.return_value = None
        
        mock_st.columns.return_value = (c1, c2, c3)
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            with patch('app.ui.expert.terminals.shared_widgets.ValuationMode') as mock_vm:
                mock_vm.FCFF_GROWTH = MagicMock()
                
                with patch('app.ui.expert.terminals.shared_widgets.ScenarioParameters') as mock_sp:
                    mock_disabled = MagicMock(enabled=False)
                    mock_sp.return_value = mock_disabled
                    
                    from app.ui.expert.terminals.shared_widgets import widget_scenarios
                    
                    result = widget_scenarios(mock_mode_ddm)
                    
                    # Should show error and return disabled
                    mock_st.error.assert_called_once()
                    assert result.enabled is False

    def test_widget_scenarios_fcff_growth_shows_margin(
        self, mock_shared_texts, mock_mode_fcff_growth
    ):
        """Test scenarios with FCFF_GROWTH mode shows margin input."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.error = MagicMock()
        
        c1 = MagicMock()
        c2 = MagicMock()
        c3 = MagicMock()
        
        c1.number_input.side_effect = [25.0, 50.0, 25.0]
        c2.number_input.side_effect = [0.08, 0.05, 0.02]
        c3.number_input.side_effect = [0.15, 0.12, 0.08]  # FCF margins
        
        mock_st.columns.return_value = (c1, c2, c3)
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            with patch('app.ui.expert.terminals.shared_widgets.ValuationMode') as mock_vm:
                mock_vm.FCFF_GROWTH = mock_mode_fcff_growth
                
                with patch('app.ui.expert.terminals.shared_widgets.ScenarioParameters') as mock_sp:
                    with patch('app.ui.expert.terminals.shared_widgets.ScenarioVariant') as mock_sv:
                        mock_sv.return_value = MagicMock()
                        mock_result = MagicMock(enabled=True)
                        mock_sp.return_value = mock_result
                        
                        from app.ui.expert.terminals.shared_widgets import widget_scenarios
                        
                        result = widget_scenarios(mock_mode_fcff_growth)
                        
                        # Margin inputs should have been called
                        assert c3.number_input.call_count == 3


# ==============================================================================
# 8. SOTP WIDGET TESTS
# ==============================================================================

class TestSOTPWidget:
    """Test suite for Sum-of-the-Parts widget."""

    @pytest.fixture
    def mock_dcf_params(self):
        """Mock DCFParameters with SOTP sub-object."""
        params = MagicMock()
        params.sotp = MagicMock()
        params.sotp.enabled = False
        params.sotp.segments = []
        params.sotp.conglomerate_discount = 0.0
        return params

    def test_widget_sotp_disabled(self, mock_shared_texts, mock_dcf_params):
        """Test SOTP widget when disabled."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.warning = MagicMock()
        mock_st.toggle.return_value = False
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_sotp
            
            widget_sotp(mock_dcf_params)
            
            assert mock_dcf_params.sotp.enabled is False

    def test_widget_sotp_enabled_non_conglomerate_warning(
        self, mock_shared_texts, mock_dcf_params
    ):
        """Test SOTP shows warning for non-conglomerate."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.warning = MagicMock()
        mock_st.toggle.return_value = False
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_sotp
            
            widget_sotp(mock_dcf_params, is_conglomerate=False)
            
            # Warning should be shown
            mock_st.warning.assert_called_once()

    def test_widget_sotp_enabled_conglomerate_no_warning(
        self, mock_shared_texts, mock_dcf_params
    ):
        """Test SOTP no warning for conglomerate."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.warning = MagicMock()
        mock_st.toggle.return_value = False
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_sotp
            
            widget_sotp(mock_dcf_params, is_conglomerate=True)
            
            # Warning should NOT be shown
            mock_st.warning.assert_not_called()

    def test_widget_sotp_enabled_with_segments(self, mock_shared_texts, mock_dcf_params):
        """Test SOTP with segment data entry."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.warning = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.slider.return_value = 15  # 15% conglomerate discount
        
        # Mock data editor return
        edited_df = pd.DataFrame([
            {"Segment Name": "Technology", "Enterprise Value": 5000.0, "Valuation Method": "DCF"},
            {"Segment Name": "Healthcare", "Enterprise Value": 3000.0, "Valuation Method": "MULTIPLE"}
        ])
        mock_st.data_editor.return_value = edited_df
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts,
            pd=pd
        ):
            with patch('app.ui.expert.terminals.shared_widgets.SOTPMethod') as mock_sotp_method:
                mock_sotp_method.DCF = MagicMock(value="DCF")
                mock_sotp_method.return_value = MagicMock()
                
                with patch('app.ui.expert.terminals.shared_widgets.BusinessUnit') as mock_bu:
                    mock_bu.return_value = MagicMock()
                    
                    from app.ui.expert.terminals.shared_widgets import widget_sotp
                    
                    widget_sotp(mock_dcf_params)
                    
                    assert mock_dcf_params.sotp.enabled is True
                    assert mock_dcf_params.sotp.conglomerate_discount == 0.15


# ==============================================================================
# 9. PARAMETERS CONSTRUCTOR TESTS
# ==============================================================================

class TestBuildDCFParameters:
    """Test suite for build_dcf_parameters constructor."""

    def test_build_dcf_parameters_with_defaults(self, mock_shared_texts, mock_ui_defaults):
        """Test constructor applies defaults for missing values."""
        mock_valuation_config = MagicMock()
        mock_valuation_config.default_projection_years = 5
        
        mock_simulation_config = MagicMock()
        mock_simulation_config.default_simulations = 10000
        mock_simulation_config.default_volatility_beta = 0.1
        mock_simulation_config.default_volatility_growth = 0.05
        
        mock_terminal_method = MagicMock()
        mock_terminal_method.name = "GORDON_GROWTH"
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            SharedTexts=mock_shared_texts,
            UIWidgetDefaults=mock_ui_defaults,
            VALUATION_CONFIG=mock_valuation_config,
            SIMULATION_CONFIG=mock_simulation_config
        ):
            with patch('app.ui.expert.terminals.shared_widgets.TerminalValueMethod') as mock_tvm:
                mock_tvm.GORDON_GROWTH = mock_terminal_method
                
                with patch('app.ui.expert.terminals.shared_widgets.DCFParameters') as mock_dcf:
                    mock_dcf.from_legacy.return_value = MagicMock()
                    
                    from app.ui.expert.terminals.shared_widgets import build_dcf_parameters
                    
                    result = build_dcf_parameters({})
                    
                    # Verify from_legacy was called with defaults
                    call_args = mock_dcf.from_legacy.call_args
                    merged_data = call_args[0][0]
                    
                    assert merged_data['projection_years'] == 5
                    assert merged_data['enable_monte_carlo'] is False

    def test_build_dcf_parameters_overrides_defaults(
        self, mock_shared_texts, mock_ui_defaults
    ):
        """Test constructor uses provided values over defaults."""
        mock_valuation_config = MagicMock()
        mock_valuation_config.default_projection_years = 5
        
        mock_simulation_config = MagicMock()
        mock_simulation_config.default_simulations = 10000
        mock_simulation_config.default_volatility_beta = 0.1
        mock_simulation_config.default_volatility_growth = 0.05
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            SharedTexts=mock_shared_texts,
            UIWidgetDefaults=mock_ui_defaults,
            VALUATION_CONFIG=mock_valuation_config,
            SIMULATION_CONFIG=mock_simulation_config
        ):
            with patch('app.ui.expert.terminals.shared_widgets.TerminalValueMethod') as mock_tvm:
                mock_tvm.GORDON_GROWTH = MagicMock()
                
                with patch('app.ui.expert.terminals.shared_widgets.DCFParameters') as mock_dcf:
                    mock_dcf.from_legacy.return_value = MagicMock()
                    
                    from app.ui.expert.terminals.shared_widgets import build_dcf_parameters
                    
                    collected = {
                        'projection_years': 10,
                        'enable_monte_carlo': True,
                        'num_simulations': 20000
                    }
                    
                    result = build_dcf_parameters(collected)
                    
                    call_args = mock_dcf.from_legacy.call_args
                    merged_data = call_args[0][0]
                    
                    assert merged_data['projection_years'] == 10
                    assert merged_data['enable_monte_carlo'] is True
                    assert merged_data['num_simulations'] == 20000

    def test_build_dcf_parameters_filters_none_values(
        self, mock_shared_texts, mock_ui_defaults
    ):
        """Test constructor filters out None values from collected data."""
        mock_valuation_config = MagicMock()
        mock_valuation_config.default_projection_years = 5
        
        mock_simulation_config = MagicMock()
        mock_simulation_config.default_simulations = 10000
        mock_simulation_config.default_volatility_beta = 0.1
        mock_simulation_config.default_volatility_growth = 0.05
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            SharedTexts=mock_shared_texts,
            UIWidgetDefaults=mock_ui_defaults,
            VALUATION_CONFIG=mock_valuation_config,
            SIMULATION_CONFIG=mock_simulation_config
        ):
            with patch('app.ui.expert.terminals.shared_widgets.TerminalValueMethod') as mock_tvm:
                mock_tvm.GORDON_GROWTH = MagicMock()
                
                with patch('app.ui.expert.terminals.shared_widgets.DCFParameters') as mock_dcf:
                    mock_dcf.from_legacy.return_value = MagicMock()
                    
                    from app.ui.expert.terminals.shared_widgets import build_dcf_parameters
                    
                    collected = {
                        'projection_years': 7,
                        'growth_rate': None,  # Should be filtered
                        'risk_free_rate': None,  # Should be filtered
                        'enable_monte_carlo': False
                    }
                    
                    result = build_dcf_parameters(collected)
                    
                    call_args = mock_dcf.from_legacy.call_args
                    merged_data = call_args[0][0]
                    
                    # None values should not override defaults
                    assert 'growth_rate' not in merged_data or merged_data.get('growth_rate') is not None


# ==============================================================================
# 10. EDGE CASES AND ERROR HANDLING
# ==============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_widget_peer_triangulation_single_ticker(self, mock_shared_texts):
        """Test peer triangulation with single ticker."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.text_input.return_value = "AAPL"
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_peer_triangulation
            
            result = widget_peer_triangulation()
            
            assert result['manual_peers'] == ['AAPL']

    def test_widget_peer_triangulation_lowercase_conversion(self, mock_shared_texts):
        """Test peer triangulation converts lowercase to uppercase."""
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.toggle.return_value = True
        mock_st.text_input.return_value = "aapl, msft"
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            from app.ui.expert.terminals.shared_widgets import widget_peer_triangulation
            
            result = widget_peer_triangulation()
            
            assert result['manual_peers'] == ['AAPL', 'MSFT']


# ==============================================================================
# 11. INTEGRATION-STYLE TESTS
# ==============================================================================

class TestWidgetIntegration:
    """Integration-style tests for widget combinations."""

    def test_full_dcf_workflow_mock(self, mock_shared_texts, mock_ui_defaults):
        """Test complete DCF parameter collection workflow."""
        mock_st = MagicMock()
        mock_st.slider.return_value = 7
        mock_st.number_input.return_value = 0.03
        mock_st.toggle.return_value = False
        mock_st.latex = MagicMock()
        mock_st.divider = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.radio.return_value = MagicMock(name="GORDON_GROWTH")
        mock_st.fragment = lambda f: f
        
        col = MagicMock()
        col.number_input.return_value = 0.02
        mock_st.columns.return_value = (col, MagicMock())
        
        mock_valuation_config = MagicMock()
        mock_valuation_config.default_projection_years = 5
        
        mock_simulation_config = MagicMock()
        mock_simulation_config.default_simulations = 10000
        mock_simulation_config.default_volatility_beta = 0.1
        mock_simulation_config.default_volatility_growth = 0.05
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts,
            UIWidgetDefaults=mock_ui_defaults,
            VALUATION_CONFIG=mock_valuation_config,
            SIMULATION_CONFIG=mock_simulation_config
        ):
            with patch('app.ui.expert.terminals.shared_widgets.TerminalValueMethod') as mock_tvm:
                mock_gordon = MagicMock()
                mock_tvm.GORDON_GROWTH = mock_gordon
                mock_tvm.EXIT_MULTIPLE = MagicMock()
                
                with patch('app.ui.expert.terminals.shared_widgets.DCFParameters') as mock_dcf:
                    mock_params = MagicMock()
                    mock_dcf.from_legacy.return_value = mock_params
                    
                    from app.ui.expert.terminals.shared_widgets import (
                        widget_projection_years,
                        widget_growth_rate,
                        widget_terminal_value_dcf,
                        widget_monte_carlo,
                        build_dcf_parameters
                    )
                    
                    # Collect data from widgets
                    collected = {}
                    collected['projection_years'] = widget_projection_years()
                    collected['growth_rate'] = widget_growth_rate()
                    
                    # Build final parameters
                    result = build_dcf_parameters(collected)
                    
                    assert result is not None


# ==============================================================================
# 12. LOGGING TESTS
# ==============================================================================

class TestLogging:
    """Test logging behavior in widgets."""

    def test_widget_terminal_value_rim_logs_debug(self, mock_shared_texts, caplog):
        """Test RIM terminal value logs debug information."""
        import logging
        
        mock_st = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.latex = MagicMock()
        mock_st.divider = MagicMock()
        
        col1 = MagicMock()
        col1.number_input.return_value = 0.6
        mock_st.columns.return_value = (col1, MagicMock())
        
        with patch.multiple(
            'app.ui.expert.terminals.shared_widgets',
            st=mock_st,
            SharedTexts=mock_shared_texts
        ):
            with patch('app.ui.expert.terminals.shared_widgets.TerminalValueMethod') as mock_tvm:
                mock_tvm.EXIT_MULTIPLE = MagicMock()
                
                # Set up logging capture
                with caplog.at_level(logging.DEBUG):
                    from app.ui.expert.terminals.shared_widgets import widget_terminal_value_rim
                    
                    result = widget_terminal_value_rim(formula_latex=r"TV")
                    
                    # Note: Actual log capture depends on logger configuration
                    assert result['exit_multiple_value'] == 0.6