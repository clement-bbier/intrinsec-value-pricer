from app.ui.expert.terminals.fcff_standard_terminal import FCFFStandardTerminalExpert
from src.models import ValuationMethodology


def test_full_request_assembly(monkeypatch):
    """Simule une saisie utilisateur complète et vérifie l'objet final."""
    terminal = FCFFStandardTerminalExpert("AAPL")

    # Simulation d'un état Streamlit complet
    mock_state = {
        # Strategy
        "FCFF_STANDARD_fcf_base": 1000.0,
        "FCFF_STANDARD_growth_rate": 5.0,
        "FCFF_STANDARD_years": 5,
        # Common
        "FCFF_STANDARD_rf": 4.0,
        "bridge_FCFF_STANDARD_debt": 500.0,
        # Extensions
        "mc_enable": True,
        "mc_sims": 1000,
        "bt_enable": False,
        "scenario_enable": False,
        "peer_peer_enable": False,
        "sotp_enable": False
    }
    monkeypatch.setattr(st, "session_state", mock_state)

    request = terminal.build_request()

    assert request.ticker == "AAPL"
    assert request.mode == ValuationMethodology.FCFF_STANDARD

    # Vérification de la cascade de données
    params = request.params
    assert params.common.rates.risk_free_rate == 0.04
    assert params.strategy.fcf_anchor == 1000.0
    assert params.extensions.monte_carlo.enabled is True