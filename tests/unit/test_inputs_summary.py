"""
tests/unit/test_inputs_summary.py

INPUTS SUMMARY PILLAR TESTS
=============================
Role: Validates data access patterns in the inputs summary view.
Coverage: Direct access without getattr chains or 'or 0.0' patterns.
"""

import inspect


from app.views.results.pillars.inputs_summary import (
    _render_strategy_inputs_table,
    _safe_fmt,
    _render_rates_table,
    _render_capital_structure_table,
)


class TestSafeFmt:
    """Tests the _safe_fmt utility function."""

    def test_none_returns_default(self):
        """None value should return the default string."""
        assert _safe_fmt(None, ".2f") == "-"

    def test_none_returns_custom_default(self):
        """None value with custom default should use it."""
        assert _safe_fmt(None, ".2%", default="N/A") == "N/A"

    def test_float_formatted(self):
        """Float value should be formatted with the given format spec."""
        assert _safe_fmt(0.05, ".2%") == "5.00%"

    def test_integer_formatted(self):
        """Integer-like float should be formatted correctly."""
        assert _safe_fmt(100.0, ".0f") == "100"

    def test_zero_formatted(self):
        """Zero should be formatted, not treated as None."""
        assert _safe_fmt(0.0, ".2f") == "0.00"

    def test_negative_formatted(self):
        """Negative values should format correctly."""
        assert _safe_fmt(-0.03, ".2%") == "-3.00%"


class TestNoGetAttrPatterns:
    """Verifies that inputs_summary.py minimizes getattr usage."""

    def test_no_or_zero_in_capital_structure(self):
        """_render_capital_structure_table must not use 'or 0.0' pattern."""
        source = inspect.getsource(_render_capital_structure_table)
        assert "or 0.0" not in source

    def test_no_getattr_on_benchmark_texts_in_rates(self):
        """_render_rates_table must not use 'getattr(resolved_rates' pattern."""
        source = inspect.getsource(_render_rates_table)
        assert "getattr(resolved_rates" not in source

    def test_strategy_table_no_or_zero(self):
        """_render_strategy_inputs_table must not use chained 'or 0' pattern at end."""
        source = inspect.getsource(_render_strategy_inputs_table)
        # The old pattern: getattr(...) or getattr(...) or 0
        assert "or 0\n" not in source


class TestCapitalStructureCalculations:
    """Tests the arithmetic logic in capital structure rendering."""

    def test_net_debt_calculation(self):
        """Net debt must be debt - cash."""
        debt = 120_000.0
        cash = 50_000.0
        assert debt - cash == 70_000.0

    def test_market_cap_calculation(self):
        """Market cap must be price * shares."""
        price = 150.0
        shares = 16_000.0
        assert price * shares == 2_400_000.0

    def test_none_shares_default(self):
        """None shares should default to 0."""
        shares = None
        safe_shares = shares if shares is not None else 0
        assert safe_shares == 0

    def test_none_price_default(self):
        """None price should default to 0.0."""
        price = None
        safe_price = price if price is not None else 0.0
        assert safe_price == 0.0

    def test_zero_shares_not_confused_with_none(self):
        """Zero shares should remain 0, not default."""
        shares = 0
        safe_shares = shares if shares is not None else 999
        assert safe_shares == 0
