"""
tests/unit/test_shared_widgets.py
Suite de tests exhaustifs pour les widgets de saisie expert.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from app.ui.expert.terminals.shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
    widget_cost_of_capital,
    widget_terminal_value_dcf,
    widget_terminal_value_rim,
    widget_equity_bridge,
    widget_monte_carlo,
    widget_peer_triangulation,
    widget_scenarios,
    widget_sotp,
    build_dcf_parameters
)
from src.models import (
    ValuationMode, TerminalValueMethod, DCFParameters, SOTPMethod, ScenarioParameters
)

# Cible exacte pour le patch Streamlit
TARGET = 'app.ui.expert_terminals.shared_widgets'

class TestBasicInputWidgets:
    """Validation des widgets de base (Slider, Number Input)."""

    @patch(f'{TARGET}.st')
    def test_widget_projection_years(self, mock_st):
        mock_st.slider.return_value = 10
        res = widget_projection_years(key_prefix="unit")

        _, kwargs = mock_st.slider.call_args
        assert kwargs['key'] == "unit_years"
        assert res == 10

    @patch(f'{TARGET}.st')
    def test_widget_growth_rate(self, mock_st):
        mock_st.number_input.return_value = 0.04
        res = widget_growth_rate(label="Growth", key_prefix="unit")

        args, kwargs = mock_st.number_input.call_args
        assert "Growth" in args[0]
        assert kwargs['key'] == "unit_growth_rate"
        assert res == 0.04

class TestFinancialLogicWidgets:
    """Validation des widgets complexes (WACC, Bridge, TV)."""

    @patch(f'{TARGET}.st')
    def test_widget_cost_of_capital_wacc(self, mock_st):
        """Vérifie la saisie WACC avec colonnes."""
        mock_col = MagicMock()
        mock_st.columns.return_value = [mock_col, mock_col]
        # Simule : Price, RF, Beta, MRP, KD, Tax
        mock_col.number_input.side_effect = [150.0, 0.04, 1.2, 0.05, 0.06, 0.25]

        res = widget_cost_of_capital(ValuationMode.FCFF_STANDARD)
        assert res['risk_free_rate'] == 0.04
        assert res['cost_of_debt'] == 0.06

    @patch(f'{TARGET}.st')
    def test_widget_terminal_value_dcf_gordon(self, mock_st):
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.radio.return_value = TerminalValueMethod.GORDON_GROWTH
        mock_st.number_input.return_value = 0.02

        res = widget_terminal_value_dcf()
        assert res['terminal_method'] == TerminalValueMethod.GORDON_GROWTH
        assert res['perpetual_growth_rate'] == 0.02

    @patch(f'{TARGET}.st')
    def test_widget_equity_bridge_entity_mode(self, mock_st):
        """Vérifie le bridge complet (Dette, Cash, SBC)."""
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        # Simule les inputs successifs pour Entity mode
        mock_st.number_input.side_effect = [1000.0, 200.0, 50.0, 30.0, 10e6, 0.02]

        res = widget_equity_bridge("formula", ValuationMode.FCFF_STANDARD)
        assert res['manual_total_debt'] == 1000.0
        assert res['stock_based_compensation_rate'] == 0.02

class TestStrategicWidgets:
    """Validation Monte Carlo, Scénarios et SOTP."""

    @patch(f'{TARGET}.st')
    def test_widget_monte_carlo_enabled(self, mock_st):
        mock_st.toggle.return_value = True
        mock_st.select_slider.return_value = 10000
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        # Flow Vol, Beta Vol, Growth Vol
        mock_st.number_input.side_effect = [0.20, 0.15, 0.05]

        res = widget_monte_carlo(ValuationMode.FCFF_STANDARD)
        assert res['enable_monte_carlo'] is True
        assert res['num_simulations'] == 10000
        assert res['base_flow_volatility'] == 0.20

    @patch(f'{TARGET}.st')
    def test_widget_peer_triangulation_parsing(self, mock_st):
        mock_st.toggle.return_value = True
        mock_st.text_input.return_value = "AAPL, MSFT , GOOGL"

        res = widget_peer_triangulation()
        assert res['manual_peers'] == ["AAPL", "MSFT", "GOOGL"]

    @patch(f'{TARGET}.st')
    def test_widget_scenarios_valid_sum(self, mock_st):
        """Vérifie la création de ScenarioParameters si somme == 100%."""
        mock_st.toggle.return_value = True
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        # Bull(25, g), Base(50, g), Bear(25, g) -> Sum 100
        mock_st.number_input.side_effect = [25.0, 0.1, 50.0, 0.05, 25.0, 0.01]

        res = widget_scenarios(ValuationMode.FCFF_STANDARD)
        assert isinstance(res, ScenarioParameters)
        assert res.enabled is True
        assert res.bull.probability == 0.25

    @patch(f'{TARGET}.st')
    def test_widget_sotp_data_parsing(self, mock_st):
        """Vérifie la transformation de l'éditeur de données en BusinessUnits."""
        mock_st.toggle.return_value = True
        # Simulation du retour de st.data_editor
        df = pd.DataFrame([
            {"Nom du Segment": "Cloud", "Valeur (EV)": 5000.0, "Méthode": "DCF"},
            {"Nom du Segment": "Ads", "Valeur (EV)": 2000.0, "Méthode": "Multiples"}
        ])
        mock_st.data_editor.return_value = df
        mock_st.slider.return_value = 10 # 10% discount

        params = DCFParameters.from_legacy({})
        widget_sotp(params, is_conglomerate=True)

        assert len(params.sotp.segments) == 2
        assert params.sotp.segments[0].name == "Cloud"
        assert params.sotp.conglomerate_discount == 0.10

class TestParameterConstruction:
    """Validation de la fusion logique (Build)."""

    def test_build_dcf_parameters_merge_logic(self):
        collected = {
            "projection_years": 7,
            "risk_free_rate": 0.045,
            "manual_beta": 1.2,
            "enable_monte_carlo": True
        }
        params = build_dcf_parameters(collected)

        assert params.growth.projection_years == 7
        assert params.rates.risk_free_rate == 0.045
        assert params.monte_carlo.enable_monte_carlo is True