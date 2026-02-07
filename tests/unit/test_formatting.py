"""
tests/unit/test_formatting.py

UNIT TESTS — INSTITUTIONAL FORMATTING
=====================================
Role: Validates numeric representation, financial scales, and UI color logic.
Coverage Target: 100% of src/utilities/formatting.py.
"""

import pytest
import numpy as np
from src.core.formatting import format_smart_number, get_delta_color, format_audit_score
from src.i18n import CommonTexts

class TestSmartNumberFormatting:
    """Tests human-readable institutional notation (M, B, T)."""

    def test_format_not_available(self):
        """Verifies handling of None and NaN values."""
        assert format_smart_number(None) == CommonTexts.VALUE_NOT_AVAILABLE
        assert format_smart_number(np.nan) == CommonTexts.VALUE_NOT_AVAILABLE

    def test_format_percentage(self):
        """Verifies percentage formatting with custom decimals."""
        assert format_smart_number(0.0845, is_pct=True) == "8.45%"
        assert format_smart_number(0.08456, is_pct=True, decimals=3) == "8.456%"

    def test_format_magnitude_scales(self):
        """Verifies Trillions, Billions, and Millions scales (Bloomberg style)."""
        # Trillions
        assert format_smart_number(1.5e12, currency="$") == "1.50 T $"
        # Billions
        assert format_smart_number(2.3e9, currency="€") == "2.30 B €"
        # Millions
        assert format_smart_number(950.5e6) == "950.50 M"
        # Standard
        assert format_smart_number(1234.567, decimals=1) == "1,234.6"

    def test_format_negative_values(self):
        """Ensures magnitudes work correctly with negative flows (e.g., Net Debt)."""
        assert format_smart_number(-1.2e9, currency="USD") == "-1.20 B USD"

class TestDeltaColorLogic:
    """Tests the semantic color engine for UI rendering."""

    def test_color_standard_logic(self):
        """Positive is Green, Negative is Red, Zero is Gray."""
        assert get_delta_color(0.10) == "#22C55E"   # Green
        assert get_delta_color(-0.10) == "#EF4444"  # Red
        assert get_delta_color(0) == "#808080"      # Gray

    def test_color_inverse_logic(self):
        """Tests Cost/Risk metrics where positive growth is bad (e.g., WACC)."""
        # Increase in WACC is bad (Red)
        assert get_delta_color(0.05, inverse=True) == "#EF4444"
        # Decrease in Debt/Risk is good (Green)
        assert get_delta_color(-0.05, inverse=True) == "#22C55E"

class TestAuditScoreFormatting:
    """Tests qualitative rank mapping for reliability reports."""

    @pytest.mark.parametrize("score, expected", [
        (95.0, "95.0/100 (AAA)"),
        (85.5, "85.5/100 (A)"),
        (72.0, "72.0/100 (B)"),
        (60.0, "60.0/100 (C)"),
        (30.0, "30.0/100 (F)"),
    ])
    def test_audit_ranks(self, score, expected):
        """Verifies that each numeric bracket maps to the correct rank."""
        assert format_audit_score(score) == expected