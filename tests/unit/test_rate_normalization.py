import pytest
from app.ui.expert.base_terminal import BaseTerminalExpert

class TestRateNormalization:
    """Boundary testing for unified scaling (V16)."""

    @pytest.mark.parametrize("field_name, input_val, expected", [
        ("risk_free_rate", 5.0, 0.05),     # Classé % : 5.0 -> 0.05
        ("risk_free_rate", 0.05, 0.0005),  # Classé % : 0.05 -> 0.0005 (Rigueur absolue)
        ("tax_rate", 25.0, 0.25),          # Classé % : 25.0 -> 0.25
        ("manual_total_debt", 1000.0, 1_000_000_000.0), # Classé Million -> Unités
        ("manual_beta", 1.2, 1.2),         # Classé Absolute -> tel quel
        ("unclassified_field", 5.0, 0.05), # Non classé (> 1.0) -> Fallback %
        ("unclassified_field", 0.8, 0.8),  # Non classé (< 1.0) -> Fallback Absolute
        (None, None, None),
    ])
    def test_apply_field_scaling(self, field_name, input_val, expected):
        """Vérifie que le contrat ExpertTerminalBase.apply_field_scaling est respecté."""
        assert BaseTerminalExpert.apply_field_scaling(field_name, input_val) == expected