"""
tests/unit/test_core_formatting.py

UNIT TESTS FOR FORMATTING UTILITIES
===================================
Role: Validates formatting functions for numbers, currencies, and colors.
Coverage: format_smart_number, get_delta_color functions.
Architecture: Core Utilities Tests.
Style: Pytest with parametrize for various input scenarios.
"""

import pytest
import math
from src.core.formatting import (
    format_smart_number,
    get_delta_color,
    COLOR_POSITIVE,
    COLOR_NEGATIVE,
    COLOR_NEUTRAL,
)


class TestFormatSmartNumberNullHandling:
    """Test suite for null/NaN handling in format_smart_number."""
    
    def test_none_returns_dash(self):
        """format_smart_number(None) should return '-'."""
        result = format_smart_number(None)
        assert result == "-"
    
    def test_nan_returns_dash(self):
        """format_smart_number(float('nan')) should return '-'."""
        result = format_smart_number(float('nan'))
        assert result == "-"


class TestFormatSmartNumberMagnitudes:
    """Test suite for magnitude formatting (M, B, T)."""
    
    def test_million_magnitude(self):
        """1,500,000 should format with 'M' suffix."""
        result = format_smart_number(1_500_000)
        
        # Should contain 'M' for millions
        assert 'M' in result
        # Should not contain B or T
        assert 'B' not in result
        assert 'T' not in result
    
    def test_billion_magnitude(self):
        """2,300,000,000 should format with 'B' suffix."""
        result = format_smart_number(2_300_000_000)
        
        # Should contain 'B' for billions
        assert 'B' in result
        # Should not contain M or T
        assert 'M' not in result
        assert 'T' not in result
    
    def test_trillion_magnitude(self):
        """1,200,000,000,000 should format with 'T' suffix."""
        result = format_smart_number(1_200_000_000_000)
        
        # Should contain 'T' for trillions
        assert 'T' in result
        # Should not contain M or B
        assert 'M' not in result
        assert 'B' not in result
    
    def test_small_number_no_suffix(self):
        """150 should format without M/B/T suffix."""
        result = format_smart_number(150.0)
        
        # Should not contain any suffix
        assert 'M' not in result
        assert 'B' not in result
        assert 'T' not in result


class TestFormatSmartNumberPercentage:
    """Test suite for percentage formatting."""
    
    def test_percentage_format(self):
        """0.05 with is_pct=True should return '5.00%'."""
        result = format_smart_number(0.05, is_pct=True)
        
        # Should contain % symbol
        assert '%' in result
        # Should be properly formatted (5.00% or similar)
        assert '5' in result
    
    def test_percentage_format_with_decimals(self):
        """Percentage formatting should respect decimal places."""
        result = format_smart_number(0.1234, is_pct=True, decimals=2)
        
        assert '%' in result
        # With decimals=2, should show 12.34%
        assert '12.34' in result


class TestFormatSmartNumberCurrency:
    """Test suite for currency formatting."""
    
    def test_currency_included(self):
        """150.0 with currency='USD' should include 'USD' in output."""
        result = format_smart_number(150.0, currency="USD")
        
        assert 'USD' in result
    
    def test_currency_with_magnitude(self):
        """Large numbers with currency should show both."""
        result = format_smart_number(1_500_000, currency="EUR")
        
        assert 'EUR' in result
        assert 'M' in result
    
    def test_empty_currency_no_suffix(self):
        """Empty currency string should not add extra spacing."""
        result = format_smart_number(100.0, currency="")
        
        # Should just be the number without currency
        assert 'USD' not in result
        assert 'EUR' not in result


class TestFormatSmartNumberEdgeCases:
    """Test suite for edge cases and special values."""
    
    def test_zero_value(self):
        """format_smart_number(0) should handle zero gracefully."""
        result = format_smart_number(0)
        
        assert result is not None
        assert result != "-"  # Should not be treated as None
        assert '0' in result
    
    def test_negative_values(self):
        """Negative values should format correctly."""
        result = format_smart_number(-1_500_000)
        
        assert 'M' in result
        # Should show negative somehow (either '-' or in formatting)
        assert '-' in result or result.startswith('(')
    
    def test_very_small_positive(self):
        """Very small positive numbers should format."""
        result = format_smart_number(0.01)
        
        assert result != "-"
        assert result is not None


class TestGetDeltaColor:
    """Test suite for delta color assignment."""
    
    def test_positive_value_green(self):
        """get_delta_color(0.15) should return COLOR_POSITIVE (green)."""
        result = get_delta_color(0.15)
        
        assert result == COLOR_POSITIVE
        assert result == "#22C55E"
    
    def test_negative_value_red(self):
        """get_delta_color(-0.10) should return COLOR_NEGATIVE (red)."""
        result = get_delta_color(-0.10)
        
        assert result == COLOR_NEGATIVE
        assert result == "#EF4444"
    
    def test_zero_value_neutral(self):
        """get_delta_color(0) should return COLOR_NEUTRAL (gray)."""
        result = get_delta_color(0)
        
        assert result == COLOR_NEUTRAL
        assert result == "#808080"
    
    def test_positive_value_inverse_red(self):
        """get_delta_color(0.15, inverse=True) should return COLOR_NEGATIVE."""
        result = get_delta_color(0.15, inverse=True)
        
        # With inverse=True, positive should be negative color
        assert result == COLOR_NEGATIVE
        assert result == "#EF4444"
    
    def test_negative_value_inverse_green(self):
        """get_delta_color(-0.10, inverse=True) should return COLOR_POSITIVE."""
        result = get_delta_color(-0.10, inverse=True)
        
        # With inverse=True, negative should be positive color
        assert result == COLOR_POSITIVE
        assert result == "#22C55E"
    
    def test_zero_value_inverse_neutral(self):
        """get_delta_color(0, inverse=True) should still return COLOR_NEUTRAL."""
        result = get_delta_color(0, inverse=True)
        
        # Zero should always be neutral, regardless of inverse
        assert result == COLOR_NEUTRAL


class TestColorConstants:
    """Test suite for color constant definitions."""
    
    def test_color_positive_defined(self):
        """COLOR_POSITIVE should be defined as green hex."""
        assert COLOR_POSITIVE == "#22C55E"
    
    def test_color_negative_defined(self):
        """COLOR_NEGATIVE should be defined as red hex."""
        assert COLOR_NEGATIVE == "#EF4444"
    
    def test_color_neutral_defined(self):
        """COLOR_NEUTRAL should be defined as gray hex."""
        assert COLOR_NEUTRAL == "#808080"
