from app.ui.expert.terminals import RIMBankTerminalExpert, GrahamValueTerminalExpert


def test_monte_carlo_dynamic_labels():
    """Vérifie que les labels s'adaptent au modèle (EPS pour Graham, etc.)."""
    from src.models import ValuationMethodology
    from src.i18n import SharedTexts

    # Graham
    terminal_graham = GrahamValueTerminalExpert("GOOGL")
    labels_graham = terminal_graham.get_custom_monte_carlo_vols()
    assert labels_graham["vol_flow"] == SharedTexts.MC_VOL_EPS

    # RIM
    terminal_rim = RIMBankTerminalExpert("BNP")
    labels_rim = terminal_rim.get_custom_monte_carlo_vols()
    assert labels_rim["vol_flow"] == SharedTexts.MC_VOL_NI