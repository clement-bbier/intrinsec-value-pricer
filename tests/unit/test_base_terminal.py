"""
tests/unit/test_base_terminal.py

UNIT TESTS — EXPERT TERMINAL BASE
=================================
Role: Validates the Template Method orchestration and Data Extraction logic.
Fixes: Aligned session state keys with targeted extraction methods (V16).
"""

import pytest
from unittest.mock import patch, MagicMock
from app.ui.expert.base_terminal import BaseTerminalExpert
from src.i18n import SharedTexts
from src.models import (
    ValuationMethodology, TerminalValueMethod, ParametersSource,
    ValuationRequest, Parameters
)

# 1. Création d'une classe concrète pour tester l'abstraction
class ConcreteTerminalTerminalExpert(BaseTerminalExpert):
    MODE = ValuationMethodology.FCFF_STANDARD
    DISPLAY_NAME = "Test Terminal"

    def render_model_inputs(self):
        return {"manual_fcf_base": 1000.0}

    def _extract_model_inputs_data(self, key_prefix):
        # Simule l'extraction normalisée des inputs spécifiques au modèle
        return {"manual_fcf_base": 1000.0}

@pytest.fixture
def terminal():
    return ConcreteTerminalTerminalExpert(ticker="AAPL")

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
        mock_wacc.return_value = {"risk_free_rate": 0.04}
        mock_tv.return_value = {"terminal_method": TerminalValueMethod.GORDON_GROWTH}
        mock_bridge.return_value = {"manual_total_debt": 100}
        mock_mc.return_value = {"enable_monte_carlo": True}
        mock_peers.return_value = {"enable_peer_multiples": False}

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
        """
        Vérifie la construction d'une ValuationRequest complète.
        CORRECTIF : Aligné sur les méthodes d'extraction ciblées.
        """
        prefix = terminal.MODE.name # FCFF_STANDARD

        # On simule le SessionState EXACT utilisé par les méthodes _extract_*_data
        mock_st.session_state = {
            # 1. Discount Data
            f"{prefix}_rf": 4.1,        # 4.1%
            f"{prefix}_beta": 1.1,
            f"{prefix}_mrp": 5.5,

            # 2. Terminal Data
            f"{prefix}_method": TerminalValueMethod.GORDON_GROWTH,
            f"{prefix}_gn": 2.5,        # 2.5%

            # 3. Bridge Data
            f"bridge_{prefix}_debt": 100.0,
            f"bridge_{prefix}_sbc_rate": -2.0, # Rachat de 2%

            # 4. Years
            f"{prefix}_years": 10,

            # 5. Optional Features (Monte Carlo & Peers)
            "mc_enable": True,
            "mc_sims": 10000,
            "mc_vol_flow": 15.0,

            "peer_peer_enable": True,
            "peer_input": "MSFT, GOOGL",

            # 6. Scenarios (Désactivé pour ce test)
            "scenario_scenario_enable": False
        }

        # Déclenchement de la construction
        request = terminal.build_request()

        # assertions
        assert isinstance(request, ValuationRequest)
        assert request.projection_years == 10

        # Vérification du SSOT via Parameters
        params = request.params
        assert params.rates.risk_free_rate == pytest.approx(0.041)
        assert params.growth.perpetual_growth_rate == pytest.approx(0.025)

        # Vérification des options (Le test qui échouait)
        assert request.options["enable_peer_multiples"] is True
        assert params.monte_carlo.enabled is True

    @patch("app.ui.expert.base_terminal.st")
    def test_extract_scenarios_data_valid_math(self, mock_st, terminal):
        """Vérifie l'extraction des scénarios avec probabilités valides."""
        mock_st.session_state = {
            "scenario_scenario_enable": True,
            "scenario_p_bull": 0.25,
            "scenario_p_base": 0.50,
            "scenario_p_bear": 0.25,
            "scenario_g_bull": 8.0, # 8%
            "scenario_g_base": 5.0,
            "scenario_g_bear": 2.0
        }

        scenarios = terminal._extract_scenarios_data()

        assert scenarios.enabled is True
        assert scenarios.bull.probability == 0.25
        assert scenarios.base.growth_rate == pytest.approx(0.05)

    @patch("app.ui.expert.base_terminal.st")
    def test_extract_scenarios_data_invalid_math_fallback(self, mock_st, terminal):
        """Vérifie le fallback si les probabilités ne somment pas à 1.0."""
        mock_st.session_state = {
            "scenario_scenario_enable": True,
            "scenario_p_bull": 0.80,
            "scenario_p_base": 0.50, # Somme > 1.0
            "scenario_p_bear": 0.10,
        }
        scenarios = terminal._extract_scenarios_data()
        assert scenarios.enabled is False

class TestMethodologyAdaptation:
    """Validation de l'adaptation dynamique (ST-4.2)."""

    def test_monte_carlo_volatility_mapping(self, terminal):
        # Graham focus sur BPA (EPS)
        terminal.MODE = ValuationMethodology.GRAHAM
        vols = terminal.get_custom_monte_carlo_vols()
        assert "base_flow_volatility" in vols

        # RIM focus sur persistance (Omega)
        terminal.MODE = ValuationMethodology.RIM
        vols = terminal.get_custom_monte_carlo_vols()
        assert vols["terminal_growth_volatility"] == SharedTexts.LBL_VOL_OMEGA