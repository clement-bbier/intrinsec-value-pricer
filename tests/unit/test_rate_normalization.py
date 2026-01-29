import pytest


class TestRateNormalization:
    """Boundary testing for rate conversion."""

    @pytest.mark.parametrize("input_val,expected", [
        (5.0, 0.05),  # 5% → 0.05
        (0.05, 0.05),  # Already decimal
        (100.0, 1.0),  # Edge case
        (1.5, 0.015),  # 1.5% → 0.015
        (None, None),
        ("", None),
    ])
    def test_rate_normalization(self, input_val, expected):
        from src.models.dcf_parameters import _normalize_rate
        assert _normalize_rate(input_val) == expected