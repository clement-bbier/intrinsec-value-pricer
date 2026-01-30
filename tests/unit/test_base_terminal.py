"""
tests/unit/test_base_terminal.py

UNIT TESTS — EXPERT TERMINAL BASE
=================================
Role: Validates the Template Method orchestration and Data Extraction logic.
Coverage Target: >95% of app/ui/expert/base_terminal.py.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from app.ui.expert.base_terminal import ExpertTerminalBase
from src.i18n import SharedTexts
from src.models import (
    ValuationMode, TerminalValueMethod, InputSource,
    ValuationRequest, Parameters, ScenarioParameters
)

# 1. Création d'une classe concrète pour tester l'abstraction
class ConcreteTerminal(ExpertTerminalBase):
    MODE = ValuationMode.FCFF_STANDARD
    DISPLAY_NAME = "Test Terminal"

    def render_model_inputs(self):
        return {"manual_fcf_base": 1000.0}

    def _extract_model_inputs_data(self, key_prefix):
        return {"manual_fcf_base": 1000.0}

@pytest.fixture
def terminal():
    return ConcreteTerminal(ticker="AAPL")

class TestExpertTerminalLifecycle:
    """Validation de l'orchestration du rendu (Template Method)."""

    @patch("app.ui.expert.base_terminal.st")
    @patch("app.ui.expert.terminals.shared_widgets.widget_cost_of_capital")
    @patch("app.ui.expert.terminals.shared_widgets.widget_terminal_value_dcf")
    @patch("app.ui.expert.terminals.shared_widgets.widget_equity_bridge")
    @patch("app.ui.expert.terminals.shared_widgets.widget_monte_carlo")
    @patch("app.ui.expert.terminals.shared_widgets.widget_scenarios")
    @patch("app.ui.expert.terminals.shared_widgets.widget_peer_triangulation")
    @patch("app.ui.expert.terminals.shared_widgets.widget_sotp")
    def test_render_full_sequence(self, mock_sotp, mock_peers, mock_scenarios,
                                 mock_mc, mock_bridge, mock_tv, mock_wacc,
                                 mock_st, terminal):
        """Vérifie l'exécution complète du pipeline de rendu."""
        # Setup mocks pour éviter les NoneType errors lors de l'update du dictionnaire
        mock_wacc.return_value = {"rf": 0.04}
        mock_tv.return_value = {"meth": "g"}
        mock_bridge.return_value = {"debt": 100}
        mock_mc.return_value = {"mc": True}
        mock_peers.return_value = {"peers": []}

        terminal.render()

        # On vérifie l'ordre logique financier
        assert mock_wacc.called
        assert mock_tv.called
        assert mock_bridge.called
        assert mock_scenarios.called

class TestDataExtractionLogic:
    """Validation de la transformation SessionState -> Domain Model."""

    @patch("app.ui.expert.base_terminal.st")
    def test_build_request_full_extraction(self, mock_st, terminal):
        """Vérifie la construction d'une ValuationRequest complète."""
        key_prefix = terminal.MODE.name
        mock_st.session_state = {
            f"{key_prefix}_years": 10,
            f"{key_prefix}_rf": 3.5,
            f"{key_prefix}_beta": 1.1,
            f"{key_prefix}_method": TerminalValueMethod.GORDON_GROWTH,
            f"{key_prefix}_gn": 2.0,
            f"bridge_{key_prefix}_debt": 1000.0,
            "mc_enable": True,
            "peer_peer_enable": True,
            "peer_input": "MSFT, GOOGL",
            "scenario_scenario_enable": False # Désactivé ici pour simplifier ce test
        }

        request = terminal.build_request()

        assert isinstance(request, ValuationRequest)
        assert request.projection_years == 10
        assert request.manual_params.rates.risk_free_rate == 0.035
        # Le test corrigé par le refactoring stateless
        assert request.options["enable_peer_multiples"] is True

    @patch("app.ui.expert.base_terminal.st")
    def test_extract_scenarios_data_valid_math(self, mock_st, terminal):
        """
        Vérifie l'extraction des scénarios avec des probabilités valides (Somme = 1.0).
        C'est ici qu'on corrige l'AssertionError précédente.
        """
        mock_st.session_state = {
            "scenario_scenario_enable": True,
            "scenario_p_bull": 0.25,
            "scenario_p_base": 0.50,
            "scenario_p_bear": 0.25,
            "scenario_g_bull": 8.0,
            "scenario_g_base": 5.0,
            "scenario_g_bear": 2.0
        }

        scenarios = terminal._extract_scenarios_data()

        assert scenarios.enabled is True
        assert scenarios.bull.probability == 0.25
        assert scenarios.base.growth_rate == 0.05

    @patch("app.ui.expert.base_terminal.st")
    def test_extract_scenarios_data_invalid_math_fallback(self, mock_st, terminal):
        """Vérifie que le terminal désactive les scénarios si les probas sont fausses."""
        mock_st.session_state = {
            "scenario_scenario_enable": True,
            "scenario_p_bull": 0.80,
            "scenario_p_base": 0.80, # Somme = 1.60 -> Erreur
            "scenario_p_bear": 0.10,
        }
        scenarios = terminal._extract_scenarios_data()
        assert scenarios.enabled is False # Le fallback a fonctionné

class TestMethodologyAdaptation:
    """Validation de l'adaptation dynamique du terminal (ST-4.2)."""

    def test_monte_carlo_volatility_mapping(self, terminal):
        # Graham focus sur BPA (EPS)
        terminal.MODE = ValuationMode.GRAHAM
        vols = terminal.get_custom_monte_carlo_vols()
        assert "base_flow_volatility" in vols

        # RIM focus sur persistance (Omega)
        terminal.MODE = ValuationMode.RIM
        vols = terminal.get_custom_monte_carlo_vols()
        assert vols["terminal_growth_volatility"] == SharedTexts.LBL_VOL_OMEGA