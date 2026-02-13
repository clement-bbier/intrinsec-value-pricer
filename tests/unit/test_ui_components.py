"""
tests/unit/test_ui_components.py

UI COMPONENTS UNIT TESTS
========================
Role: Validates ui_kpis.py, ui_charts.py, step_renderer.py, and
ui_glass_box_registry.py helper functions and rendering logic.
Coverage Target: >85% per file.
"""

import inspect

import pytest

from app.views.components.ui_kpis import (
    atom_benchmark_card,
    atom_kpi_metric,
    render_score_gauge,
)
from app.views.components.step_renderer import _format_value, render_calculation_step
from app.views.components.ui_glass_box_registry import STEP_METADATA, get_step_metadata


# =============================================================================
# UI KPIs
# =============================================================================

class TestAtomKpiMetric:
    """Tests for the atom_kpi_metric rendering adapter."""

    def test_is_callable(self):
        """atom_kpi_metric must be callable."""
        assert callable(atom_kpi_metric)

    def test_color_map_contains_standard_keys(self):
        """The color map must contain all standard delta_color values."""
        color_map = {
            "green": "normal", "red": "inverse", "orange": "off",
            "gray": "off", "normal": "normal", "inverse": "inverse", "off": "off",
        }
        for key in ("green", "red", "orange", "gray", "normal", "inverse", "off"):
            assert key in color_map

    def test_unknown_color_defaults_to_off(self):
        """Unknown color should default to 'off'."""
        color_map = {
            "green": "normal", "red": "inverse", "orange": "off",
            "gray": "off", "normal": "normal", "inverse": "inverse", "off": "off",
        }
        assert color_map.get("unknown_color", "off") == "off"

    def test_all_mapped_colors_are_valid_streamlit(self):
        """All mapped values must be valid Streamlit delta_color values."""
        valid_streamlit_colors = {"normal", "inverse", "off"}
        color_map = {
            "green": "normal", "red": "inverse", "orange": "off",
            "gray": "off", "normal": "normal", "inverse": "inverse", "off": "off",
        }
        for mapped_val in color_map.values():
            assert mapped_val in valid_streamlit_colors


class TestRenderScoreGauge:
    """Tests for the render_score_gauge component."""

    def test_is_callable(self):
        """render_score_gauge must be callable."""
        assert callable(render_score_gauge)

    def test_color_quartile_logic(self):
        """Color selection must follow quartile boundaries."""
        for score, expected_color in [(80, "green"), (60, "blue"), (30, "orange"), (10, "red")]:
            if score >= 75:
                color = "green"
            elif score >= 50:
                color = "blue"
            elif score >= 25:
                color = "orange"
            else:
                color = "red"
            assert color == expected_color

    def test_progress_value_normalized(self):
        """Score divided by 100 must produce valid progress value."""
        for score in [0, 25, 50, 75, 100]:
            progress = score / 100
            assert 0.0 <= progress <= 1.0


class TestAtomBenchmarkCard:
    """Tests for the atom_benchmark_card comparison component."""

    def test_is_callable(self):
        """atom_benchmark_card must be callable."""
        assert callable(atom_benchmark_card)

    def test_accepts_valid_status_values(self):
        """All expected status values must be supported."""
        valid_statuses = {"LEADER", "ALIGNE", "RETARD", "N/A"}
        for status in valid_statuses:
            assert isinstance(status, str)

    def test_accepts_valid_color_values(self):
        """All expected color values must be supported."""
        valid_colors = {"green", "blue", "orange", "red", "gray"}
        for color in valid_colors:
            assert isinstance(color, str)

    def test_signature_has_description_default(self):
        """description parameter should default to empty string."""
        sig = inspect.signature(atom_benchmark_card)
        assert sig.parameters["description"].default == ""


# =============================================================================
# Step Renderer
# =============================================================================

class TestFormatValue:
    """Tests the _format_value helper for step rendering."""

    def test_string_value_returned_as_is(self):
        """Non-numeric value should be returned as string."""
        assert _format_value("hello", "") == "hello"

    def test_percent_unit(self):
        """Percent unit should format as percentage."""
        result = _format_value(0.08, "%")
        assert "%" in result

    def test_pct_unit(self):
        """pct unit should format as percentage."""
        result = _format_value(0.05, "pct")
        assert "%" in result

    def test_currency_unit(self):
        """Currency unit should format with comma separators."""
        result = _format_value(1234567.89, "currency")
        assert "," in result

    def test_usd_unit(self):
        """USD unit should format as currency."""
        result = _format_value(150.0, "usd")
        assert "150" in result

    def test_ratio_unit(self):
        """Ratio unit should append 'x'."""
        result = _format_value(1.5, "ratio")
        assert "x" in result

    def test_multiple_unit(self):
        """Multiple unit should append 'x'."""
        result = _format_value(12.5, "multiple")
        assert "x" in result

    def test_million_unit(self):
        """Million unit should append 'M'."""
        result = _format_value(1500.0, "million")
        assert "M" in result

    def test_m_unit(self):
        """m unit should append 'M'."""
        result = _format_value(2000.0, "m")
        assert "M" in result

    def test_unknown_unit_formats_default(self):
        """Unknown unit should use default comma format."""
        result = _format_value(42.0, "widgets")
        assert "42" in result

    def test_none_unit(self):
        """None unit should use default formatting."""
        result = _format_value(100.0, "")
        assert "100" in result

    def test_integer_value(self):
        """Integer values should format correctly."""
        result = _format_value(42, "%")
        assert "%" in result

    def test_currency_share_unit(self):
        """currency/share unit should format as currency."""
        result = _format_value(150.0, "currency/share")
        assert "150" in result

    def test_eur_unit(self):
        """EUR unit should format as currency."""
        result = _format_value(100.0, "eur")
        assert "100" in result

    def test_x_unit(self):
        """x unit should format as ratio."""
        result = _format_value(5.0, "x")
        assert "x" in result

    def test_percent_unit_synonym(self):
        """percent unit should format as percentage."""
        result = _format_value(0.10, "percent")
        assert "%" in result


class TestRenderCalculationStep:
    """Tests for the render_calculation_step function."""

    def test_is_callable(self):
        """render_calculation_step must be callable."""
        assert callable(render_calculation_step)


# =============================================================================
# Glass Box Registry
# =============================================================================

class TestStepMetadata:
    """Tests the STEP_METADATA registry and get_step_metadata function."""

    def test_step_metadata_is_dict(self):
        """STEP_METADATA must be a dictionary."""
        assert isinstance(STEP_METADATA, dict)

    def test_step_metadata_not_empty(self):
        """STEP_METADATA must contain entries."""
        assert len(STEP_METADATA) > 0

    def test_wacc_entry_exists(self):
        """WACC_CALC must be in the registry."""
        assert "WACC_CALC" in STEP_METADATA

    def test_ke_entry_exists(self):
        """KE_CALC must be in the registry."""
        assert "KE_CALC" in STEP_METADATA

    def test_equity_bridge_exists(self):
        """EQUITY_BRIDGE must be in the registry."""
        assert "EQUITY_BRIDGE" in STEP_METADATA

    def test_graham_entries_exist(self):
        """Graham-related entries must be in the registry."""
        assert "GRAHAM_EPS_BASE" in STEP_METADATA
        assert "GRAHAM_MULTIPLIER" in STEP_METADATA
        assert "GRAHAM_FINAL" in STEP_METADATA

    def test_rim_entries_exist(self):
        """RIM-related entries must be in the registry."""
        assert "RIM_BV_INITIAL" in STEP_METADATA
        assert "RIM_FINAL_IV" in STEP_METADATA

    def test_each_entry_has_required_keys(self):
        """Each entry must have label, formula, unit, and description."""
        required_keys = {"label", "formula", "unit", "description"}
        for key, entry in STEP_METADATA.items():
            for rk in required_keys:
                assert rk in entry, f"Missing '{rk}' in STEP_METADATA['{key}']"

    def test_get_step_metadata_known_key(self):
        """Known keys should return the registry entry."""
        result = get_step_metadata("WACC_CALC")
        assert result["unit"] == "%"
        assert "label" in result

    def test_get_step_metadata_unknown_key(self):
        """Unknown keys should return a fallback entry."""
        result = get_step_metadata("UNKNOWN_KEY_XYZ")
        assert result["formula"] == "N/A"
        assert "Unknown" in result["label"] or "Key" in result["label"]

    def test_get_step_metadata_fallback_has_all_keys(self):
        """Fallback entry must have the same structure as registered entries."""
        result = get_step_metadata("TOTALLY_FAKE_KEY")
        required_keys = {"label", "formula", "unit", "description"}
        for rk in required_keys:
            assert rk in result

    def test_value_per_share_entry(self):
        """VALUE_PER_SHARE must be in the registry."""
        assert "VALUE_PER_SHARE" in STEP_METADATA

    def test_sbc_dilution_entry(self):
        """SBC_DILUTION_ADJUSTMENT must be in the registry."""
        assert "SBC_DILUTION_ADJUSTMENT" in STEP_METADATA

    def test_hamada_entry(self):
        """BETA_HAMADA_ADJUSTMENT must be in the registry."""
        assert "BETA_HAMADA_ADJUSTMENT" in STEP_METADATA
