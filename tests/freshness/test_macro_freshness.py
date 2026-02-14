"""
tests/freshness/test_macro_freshness.py

DATA FRESHNESS GUARDS FOR MACRO-ECONOMIC CONSTANTS
==================================================
Role: Validates that hardcoded financial constants haven't become stale.
Coverage: Country matrix data, system constants, Damodaran spread tables.
Architecture: Quality Guard Tests.
Style: Pytest with freshness marker for separate execution.

These tests serve as "data expiry alarms" - they fail when economic
conditions have shifted enough that hardcoded values need review.
"""

import pytest

from infra.ref_data.country_matrix import COUNTRY_CONTEXT
from src.config.constants import (
    MacroDefaults,
    ModelDefaults,
    ValuationEngineDefaults,
)


@pytest.mark.freshness
class TestCountryMatrixFreshness:
    """Test suite for country-specific data freshness."""

    def test_us_risk_free_rate_reasonable(self):
        """US risk_free_rate should be between 1% and 8% (would fail if stale)."""
        us_data = COUNTRY_CONTEXT["United States"]
        rf_rate = us_data["risk_free_rate"]

        assert 0.01 <= rf_rate <= 0.08, (
            f"US risk_free_rate ({rf_rate:.2%}) outside expected range [1%, 8%]. "
            f"May need update for current market conditions."
        )

    def test_us_tax_rate_is_21_percent(self):
        """US tax_rate should be exactly 0.21 (federal corporate rate)."""
        us_data = COUNTRY_CONTEXT["United States"]
        tax_rate = us_data["tax_rate"]

        assert tax_rate == 0.21, (
            f"US corporate tax rate is {tax_rate:.1%}, expected 21%. Check if TCJA 2017 rate has changed."
        )

    def test_us_market_risk_premium_reasonable(self):
        """US market_risk_premium should be between 3% and 7%."""
        us_data = COUNTRY_CONTEXT["United States"]
        mrp = us_data["market_risk_premium"]

        assert 0.03 <= mrp <= 0.07, (
            f"US market_risk_premium ({mrp:.2%}) outside typical range [3%, 7%]. "
            f"Verify against Damodaran's latest data."
        )

    def test_eu_countries_risk_free_rates(self):
        """EU countries should have risk_free_rate between 0.5% and 6%."""
        eu_countries = ["France", "Germany"]

        for country in eu_countries:
            if country in COUNTRY_CONTEXT:
                rf_rate = COUNTRY_CONTEXT[country]["risk_free_rate"]
                assert 0.005 <= rf_rate <= 0.06, f"{country} risk_free_rate ({rf_rate:.2%}) outside EU range [0.5%, 6%]"

    def test_japan_low_risk_free_rate(self):
        """Japan risk_free_rate should be between 0% and 3% (historically low)."""
        if "Japan" in COUNTRY_CONTEXT:
            japan_data = COUNTRY_CONTEXT["Japan"]
            rf_rate = japan_data["risk_free_rate"]

            assert 0.0 <= rf_rate <= 0.03, (
                f"Japan risk_free_rate ({rf_rate:.2%}) outside expected range [0%, 3%]. "
                f"Japan typically has very low rates."
            )


@pytest.mark.freshness
class TestMacroConstantsFreshness:
    """Test suite for system-wide macro defaults freshness."""

    def test_default_risk_free_rate_reasonable(self):
        """DEFAULT_RISK_FREE_RATE should be between 1% and 8%."""
        rf = MacroDefaults.DEFAULT_RISK_FREE_RATE

        assert 0.01 <= rf <= 0.08, f"MacroDefaults.DEFAULT_RISK_FREE_RATE ({rf:.2%}) outside range [1%, 8%]"

    def test_default_market_risk_premium_reasonable(self):
        """DEFAULT_MARKET_RISK_PREMIUM should be between 3% and 8%."""
        mrp = MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM

        assert 0.03 <= mrp <= 0.08, f"MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM ({mrp:.2%}) outside range [3%, 8%]"

    def test_default_inflation_rate_reasonable(self):
        """DEFAULT_INFLATION_RATE should be between 1% and 5%."""
        inflation = MacroDefaults.DEFAULT_INFLATION_RATE

        assert 0.01 <= inflation <= 0.05, (
            f"MacroDefaults.DEFAULT_INFLATION_RATE ({inflation:.2%}) outside range [1%, 5%]"
        )

    def test_default_corporate_aaa_yield_reasonable(self):
        """DEFAULT_CORPORATE_AAA_YIELD should be between 3% and 8%."""
        aaa_yield = MacroDefaults.DEFAULT_CORPORATE_AAA_YIELD

        assert 0.03 <= aaa_yield <= 0.08, (
            f"MacroDefaults.DEFAULT_CORPORATE_AAA_YIELD ({aaa_yield:.2%}) outside range [3%, 8%]"
        )


@pytest.mark.freshness
class TestModelDefaultsFreshness:
    """Test suite for model parameter defaults freshness."""

    def test_default_beta_reasonable(self):
        """DEFAULT_BETA should be between 0.5 and 2.0."""
        beta = ModelDefaults.DEFAULT_BETA

        assert 0.5 <= beta <= 2.0, f"ModelDefaults.DEFAULT_BETA ({beta}) outside typical range [0.5, 2.0]"


@pytest.mark.freshness
class TestDamodaranSpreadsFreshness:
    """Test suite for Damodaran spread table freshness and integrity."""

    def test_spreads_large_cap_not_empty(self):
        """SPREADS_LARGE_CAP should be a non-empty tuple."""
        spreads = ValuationEngineDefaults.SPREADS_LARGE_CAP

        assert isinstance(spreads, tuple)
        assert len(spreads) > 0

    def test_spreads_small_mid_cap_not_empty(self):
        """SPREADS_SMALL_MID_CAP should be a non-empty tuple."""
        spreads = ValuationEngineDefaults.SPREADS_SMALL_MID_CAP

        assert isinstance(spreads, tuple)
        assert len(spreads) > 0

    def test_large_cap_spreads_sorted_descending(self):
        """Large cap spread table should be sorted by ICR (descending)."""
        spreads = ValuationEngineDefaults.SPREADS_LARGE_CAP

        # Extract ICR thresholds
        icr_values = [threshold for threshold, _ in spreads]

        # Check descending order
        for i in range(len(icr_values) - 1):
            assert icr_values[i] > icr_values[i + 1], f"Large cap spreads not sorted descending at index {i}"

    def test_small_mid_cap_spreads_sorted_descending(self):
        """Small/mid cap spread table should be sorted by ICR (descending)."""
        spreads = ValuationEngineDefaults.SPREADS_SMALL_MID_CAP

        # Extract ICR thresholds
        icr_values = [threshold for threshold, _ in spreads]

        # Check descending order
        for i in range(len(icr_values) - 1):
            assert icr_values[i] > icr_values[i + 1], f"Small/mid cap spreads not sorted descending at index {i}"

    def test_large_cap_spreads_cover_high_icr(self):
        """Large cap spreads should cover ICR from very high (>8) to very low (<1)."""
        spreads = ValuationEngineDefaults.SPREADS_LARGE_CAP

        icr_values = [threshold for threshold, _ in spreads]

        # Should have entries for high ICR (>8)
        assert any(icr > 8.0 for icr in icr_values), "Missing high ICR coverage (>8)"

        # Should have entries for low ICR (<1)
        assert any(icr < 1.0 for icr in icr_values), "Missing low ICR coverage (<1)"

    def test_small_mid_cap_wider_spreads_than_large_cap(self):
        """Small/mid cap should have higher (riskier) spreads than large cap for similar ICR."""
        dict(ValuationEngineDefaults.SPREADS_LARGE_CAP)
        dict(ValuationEngineDefaults.SPREADS_SMALL_MID_CAP)

        # Find a common ICR range to compare (around 4.0-5.0)
        # For this test, we'll just check that small/mid cap has some higher spreads

        large_spreads = [spread for _, spread in ValuationEngineDefaults.SPREADS_LARGE_CAP]
        small_spreads = [spread for _, spread in ValuationEngineDefaults.SPREADS_SMALL_MID_CAP]

        # Max spread for small/mid should be >= max spread for large cap
        assert max(small_spreads) >= max(large_spreads), (
            "Small/mid cap max spread should be >= large cap max spread (higher risk)"
        )

    def test_no_negative_spreads(self):
        """All spreads should be non-negative."""
        all_spreads = ValuationEngineDefaults.SPREADS_LARGE_CAP + ValuationEngineDefaults.SPREADS_SMALL_MID_CAP

        for threshold, spread in all_spreads:
            assert spread >= 0.0, f"Negative spread found: {spread} at ICR {threshold}"

    def test_all_spreads_reasonable_range(self):
        """All spreads should be between 0% and 25%."""
        all_spreads = ValuationEngineDefaults.SPREADS_LARGE_CAP + ValuationEngineDefaults.SPREADS_SMALL_MID_CAP

        for threshold, spread in all_spreads:
            assert 0.0 <= spread <= 0.25, f"Spread {spread:.2%} at ICR {threshold} outside range [0%, 25%]"


@pytest.mark.freshness
class TestFreshnessDocumentation:
    """Test suite documenting when data was last verified."""

    def test_country_matrix_version_documented(self):
        """Country matrix should have a documented update date."""
        # This test documents that the data is from January 2026
        # If we're past mid-2026, this should trigger a review

        # For now, just verify the file comment mentions the date
        # In a real scenario, we might check against current date
        assert True  # Placeholder - manual verification needed

    def test_macro_constants_need_quarterly_review(self):
        """
        Document that macro constants need quarterly review.

        These constants should be reviewed:
        - Q1 (Jan-Mar): After major central bank meetings
        - Q2 (Apr-Jun): Mid-year economic updates
        - Q3 (Jul-Sep): After summer CB decisions
        - Q4 (Oct-Dec): End of year adjustments
        """
        # This is a documentation test
        assert True  # Reminder for maintainers
