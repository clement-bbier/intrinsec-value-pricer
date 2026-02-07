import pytest
from src.computation.financial_math import calculate_historical_share_growth, calculate_dilution_factor
from src.core.diagnostics import DiagnosticRegistry


def test_sbc_math_precision():
    """Vérifie la précision du calcul de dilution (CAGR et Effet Composé)."""
    # 1. Test du CAGR (100 -> 110 en 2 ans)
    shares = [100.0, 105.0, 110.25]
    assert calculate_historical_share_growth(shares) == pytest.approx(0.05)

    # 2. Test du plafonnement (Clamping à 10%)
    shares_extreme = [100.0, 200.0]  # +100%
    assert calculate_historical_share_growth(shares_extreme) == 0.10

    # 3. Test du facteur de dilution (2% sur 5 ans)
    assert calculate_dilution_factor(0.02, 5) == pytest.approx(1.10408, rel=1e-4)


def test_sbc_audit_trigger():
    """Vérifie que l'alerte d'audit se génère correctement pour la Tech."""
    event = DiagnosticRegistry.risk_missing_sbc_dilution("Technology", 0.0)
    assert event.code == "RISK_MISSING_SBC_DILUTION"
    assert event.severity.value == "WARNING"
    # Vérifie que le message contient bien le secteur
    assert "Technology" in event.message