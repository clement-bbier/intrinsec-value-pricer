"""
tests/unit/test_infra_ref_data.py

UNIT TESTS FOR REFERENCE DATA INFRASTRUCTURE
============================================
Role: Validates Country Matrix and Sector Fallback data integrity.
Coverage: Country context retrieval, sector benchmark lookups, data validation.
Architecture: Infrastructure Layer Tests.
Style: Pytest with parametrize for data validation.
"""

import pytest
from infra.ref_data.country_matrix import (
    COUNTRY_CONTEXT,
    DEFAULT_COUNTRY,
    get_country_context
)
from infra.ref_data.sector_fallback import get_sector_data
from src.config.sector_multiples import SECTORS


class TestCountryMatrixDataIntegrity:
    """Test suite for validating Country Matrix data structure and values."""
    
    def test_all_countries_have_required_fields(self):
        """Every country entry must have ALL required CountryData fields."""
        required_fields = [
            "tax_rate",
            "risk_free_rate",
            "market_risk_premium",
            "inflation_rate",
            "rf_ticker",
            "url_central_bank",
            "url_tax_source",
            "url_risk_premium"
        ]
        
        for country_name, country_data in COUNTRY_CONTEXT.items():
            for field in required_fields:
                assert field in country_data, (
                    f"Country '{country_name}' is missing required field: {field}"
                )
    
    @pytest.mark.parametrize("country_name", list(COUNTRY_CONTEXT.keys()))
    def test_risk_free_rate_bounds(self, country_name):
        """Risk-free rate must be between 0% and 20%."""
        data = COUNTRY_CONTEXT[country_name]
        rf_rate = data["risk_free_rate"]
        assert 0.0 <= rf_rate <= 0.20, (
            f"{country_name}: risk_free_rate={rf_rate} outside bounds [0.0, 0.20]"
        )
    
    @pytest.mark.parametrize("country_name", list(COUNTRY_CONTEXT.keys()))
    def test_market_risk_premium_bounds(self, country_name):
        """Market risk premium must be between 2% and 15%."""
        data = COUNTRY_CONTEXT[country_name]
        mrp = data["market_risk_premium"]
        assert 0.02 <= mrp <= 0.15, (
            f"{country_name}: market_risk_premium={mrp} outside bounds [0.02, 0.15]"
        )
    
    @pytest.mark.parametrize("country_name", list(COUNTRY_CONTEXT.keys()))
    def test_tax_rate_bounds(self, country_name):
        """Tax rate must be between 0% and 60%."""
        data = COUNTRY_CONTEXT[country_name]
        tax_rate = data["tax_rate"]
        assert 0.0 <= tax_rate <= 0.60, (
            f"{country_name}: tax_rate={tax_rate} outside bounds [0.0, 0.60]"
        )
    
    @pytest.mark.parametrize("country_name", list(COUNTRY_CONTEXT.keys()))
    def test_inflation_rate_bounds(self, country_name):
        """Inflation rate must be between 0% and 30%."""
        data = COUNTRY_CONTEXT[country_name]
        inflation = data["inflation_rate"]
        assert 0.0 <= inflation <= 0.30, (
            f"{country_name}: inflation_rate={inflation} outside bounds [0.0, 0.30]"
        )


class TestGetCountryContext:
    """Test suite for country context retrieval logic."""
    
    def test_united_states_exact_match(self):
        """get_country_context('United States') returns valid US data."""
        result = get_country_context("United States")
        
        assert result is not None
        assert result["tax_rate"] == 0.21
        assert "risk_free_rate" in result
        assert "market_risk_premium" in result
        assert result["rf_ticker"] == "^TNX"
    
    def test_none_country_returns_default(self):
        """get_country_context(None) returns the DEFAULT_COUNTRY fallback."""
        result = get_country_context(None)
        
        assert result == DEFAULT_COUNTRY
        assert result == COUNTRY_CONTEXT["United States"]
    
    def test_empty_string_returns_default(self):
        """get_country_context('') returns the DEFAULT_COUNTRY fallback."""
        result = get_country_context("")
        
        assert result == DEFAULT_COUNTRY
    
    def test_non_existent_country_returns_default(self):
        """get_country_context('NonExistentCountry') returns DEFAULT_COUNTRY."""
        result = get_country_context("NonExistentCountry")
        
        assert result == DEFAULT_COUNTRY
    
    def test_partial_matching_works(self):
        """Partial country name matching should work."""
        # Test case-insensitive partial match
        result = get_country_context("france")
        
        # Should match 'France' in the matrix
        assert result["tax_rate"] == COUNTRY_CONTEXT["France"]["tax_rate"]
    
    def test_exact_match_case_sensitive(self):
        """Exact match should work for properly cased country names."""
        for country_name in COUNTRY_CONTEXT.keys():
            result = get_country_context(country_name)
            assert result == COUNTRY_CONTEXT[country_name]


class TestSectorFallbackData:
    """Test suite for sector benchmark fallback data."""
    
    def test_get_sector_data_returns_valid_object(self):
        """get_sector_data() returns a valid object with required attributes."""
        result = get_sector_data("Technology", "Technology")
        
        # Check that the result has the expected attributes
        assert hasattr(result, "pe_ratio") or "pe_ratio" in result
        assert hasattr(result, "ev_ebitda") or "ev_ebitda" in result
        assert hasattr(result, "ev_revenue") or "ev_revenue" in result
    
    def test_unknown_sector_returns_default(self):
        """Unknown sectors return the default fallback without crashing."""
        result = get_sector_data("UnknownIndustry", "UnknownSector")
        
        # Should return the 'default' fallback
        assert result is not None
        assert result == SECTORS["default"]
    
    def test_fallback_values_in_reasonable_ranges(self):
        """All sector fallback values must be in reasonable institutional ranges."""
        for sector_key, sector_data in SECTORS.items():
            pe = sector_data.pe_ratio
            ev_ebitda = sector_data.ev_ebitda
            ev_revenue = sector_data.ev_revenue
            
            # PE ratio: 5-100 (institutional ranges)
            assert 5.0 <= pe <= 100.0, (
                f"Sector '{sector_key}': PE ratio {pe} outside range [5, 100]"
            )
            
            # EV/EBITDA: 3-50 (None is acceptable for financials)
            if ev_ebitda is not None:
                assert 3.0 <= ev_ebitda <= 50.0, (
                    f"Sector '{sector_key}': EV/EBITDA {ev_ebitda} outside range [3, 50]"
                )
            
            # EV/Revenue: 0.5-30 (None is acceptable for financials)
            if ev_revenue is not None:
                assert 0.5 <= ev_revenue <= 30.0, (
                    f"Sector '{sector_key}': EV/Revenue {ev_revenue} outside range [0.5, 30]"
                )
    
    def test_technology_sector_has_data(self):
        """Technology sector should have valid benchmark data."""
        result = get_sector_data("Semiconductors", "Technology")
        
        assert result is not None
        assert result.pe_ratio > 0
        assert result.ev_ebitda > 0
        assert result.ev_revenue > 0
    
    def test_financial_services_has_data(self):
        """Financial Services sector should have valid benchmark data."""
        result = get_sector_data(None, "Financial Services")
        
        assert result is not None
        assert result.pe_ratio > 0
    
    def test_none_inputs_returns_default(self):
        """Calling get_sector_data with None inputs returns default fallback."""
        result = get_sector_data(None, None)
        
        assert result == SECTORS["default"]
