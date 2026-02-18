"""
tests/unit/test_math.py

COMPREHENSIVE TEST SUITE FOR FINANCIAL MATH MODULE
=================================================
Role: Tests all public functions in src/computation/financial_math.py
Coverage Target: 80-90% line coverage
Standards: pytest best practices with approx for floats, raises for exceptions
"""

from unittest.mock import Mock

import pytest

from src.computation.financial_math import (
    WACCBreakdown,
    apply_dilution_adjustment,
    calculate_cost_of_equity,
    # Cost of capital
    calculate_cost_of_equity_capm,
    calculate_dilution_factor,
    # Time value & terminal values
    calculate_discount_factors,
    calculate_fcfe_base,
    # Shareholder models
    calculate_fcfe_reconstruction,
    # Specific models
    calculate_graham_1974_value,
    # Structure adjustments & dilution
    calculate_historical_share_growth,
    calculate_npv,
    calculate_price_from_ev_multiple,
    # Multiples & triangulation
    calculate_price_from_pe_multiple,
    calculate_rim_vectors,
    calculate_sustainable_growth,
    calculate_synthetic_cost_of_debt,
    calculate_terminal_value_exit_multiple,
    calculate_terminal_value_gordon,
    calculate_terminal_value_pe,
    calculate_triangulated_price,
    calculate_wacc,
    compute_diluted_shares,
    compute_proportions,
    normalize_terminal_flow_for_stable_state,
    relever_beta,
    unlever_beta,
)
from src.config.constants import MacroDefaults, ModelDefaults, ValuationEngineDefaults
from src.core.exceptions import CalculationError
from src.models import CapitalStructureParameters, CommonParameters, Company, FinancialRatesParameters, Parameters

# ==============================================================================
# 1. TIME VALUE OF MONEY & TERMINAL VALUES
# ==============================================================================


@pytest.mark.unit
class TestCalculateDiscountFactors:
    """Test discount factors calculation."""

    def test_normal_case(self):
        """Test normal discount factors generation."""
        factors = calculate_discount_factors(0.10, 5)
        expected = [1 / 1.1, 1 / (1.1**2), 1 / (1.1**3), 1 / (1.1**4), 1 / (1.1**5)]
        assert len(factors) == 5
        for calc, exp in zip(factors, expected):
            assert calc == pytest.approx(exp, rel=1e-6)

    def test_zero_years(self):
        """Test with zero years returns empty list."""
        factors = calculate_discount_factors(0.10, 0)
        assert factors == []

    def test_rate_negative_one_raises(self):
        """Test that rate <= -1 raises CalculationError."""
        with pytest.raises(CalculationError) as exc_info:
            calculate_discount_factors(-1.0, 5)
        assert "invalid" in str(exc_info.value).lower()

    def test_rate_less_than_negative_one_raises(self):
        """Test that rate < -1 raises CalculationError."""
        with pytest.raises(CalculationError):
            calculate_discount_factors(-1.5, 3)


@pytest.mark.unit
class TestCalculateNPV:
    """Test NPV calculation."""

    def test_standard_case(self):
        """Test standard NPV calculation."""
        flows = [100.0, 100.0, 100.0]
        rate = 0.10
        npv = calculate_npv(flows, rate)
        # Manual calculation: 100/1.1 + 100/1.21 + 100/1.331
        expected = 100 / 1.1 + 100 / (1.1**2) + 100 / (1.1**3)
        assert npv == pytest.approx(expected, rel=1e-6)

    def test_empty_flows(self):
        """Test NPV with empty flows list."""
        npv = calculate_npv([], 0.10)
        assert npv == 0.0

    def test_single_flow(self):
        """Test NPV with single flow."""
        npv = calculate_npv([100.0], 0.10)
        assert npv == pytest.approx(100.0 / 1.1, rel=1e-6)


@pytest.mark.unit
class TestCalculateTerminalValueGordon:
    """Test Gordon Growth terminal value."""

    def test_normal_case(self):
        """Test normal Gordon Growth calculation."""
        tv = calculate_terminal_value_gordon(100.0, 0.10, 0.02)
        # TV = 100 * (1 + 0.02) / (0.10 - 0.02) = 102 / 0.08 = 1275
        expected = 100.0 * 1.02 / 0.08
        assert tv == pytest.approx(expected, rel=1e-6)

    def test_rate_equal_growth_raises(self):
        """Test that rate == g raises CalculationError."""
        with pytest.raises(CalculationError) as exc_info:
            calculate_terminal_value_gordon(100.0, 0.05, 0.05)
        assert "convergence" in str(exc_info.value).lower()

    def test_rate_less_than_growth_raises(self):
        """Test that rate < g raises CalculationError."""
        with pytest.raises(CalculationError) as exc_info:
            calculate_terminal_value_gordon(100.0, 0.03, 0.05)
        assert "convergence" in str(exc_info.value).lower()


@pytest.mark.unit
class TestCalculateTerminalValueExitMultiple:
    """Test exit multiple terminal value."""

    def test_normal_case(self):
        """Test normal exit multiple calculation."""
        tv = calculate_terminal_value_exit_multiple(1000.0, 15.0)
        assert tv == 15000.0

    def test_negative_multiple_raises(self):
        """Test that negative multiple raises CalculationError."""
        with pytest.raises(CalculationError) as exc_info:
            calculate_terminal_value_exit_multiple(1000.0, -5.0)
        assert "multiple" in str(exc_info.value).lower()

    def test_zero_multiple(self):
        """Test zero multiple returns zero."""
        tv = calculate_terminal_value_exit_multiple(1000.0, 0.0)
        assert tv == 0.0


@pytest.mark.unit
class TestCalculateTerminalValuePE:
    """Test P/E terminal value."""

    def test_normal_case(self):
        """Test normal P/E terminal value calculation."""
        tv = calculate_terminal_value_pe(100.0, 20.0)
        assert tv == 2000.0

    def test_pe_zero_raises(self):
        """Test that PE == 0 raises CalculationError."""
        with pytest.raises(CalculationError) as exc_info:
            calculate_terminal_value_pe(100.0, 0.0)
        assert "p/e" in str(exc_info.value).lower()

    def test_pe_negative_raises(self):
        """Test that PE < 0 raises CalculationError."""
        with pytest.raises(CalculationError):
            calculate_terminal_value_pe(100.0, -10.0)


@pytest.mark.unit
class TestNormalizeTerminalFlowForStableState:
    """Test the Golden Rule normalization for terminal flow."""

    def test_normal_case_with_growth_and_roic(self):
        """Test normal case: positive growth with positive ROIC."""
        # 3% growth with 15% ROIC requires 20% reinvestment
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(1000.0, 0.03, 0.15)

        expected_reinv_rate = 0.03 / 0.15  # = 0.2 (20%)
        expected_adjusted_flow = 1000.0 * (1.0 - 0.2)  # = 800.0

        assert reinv_rate == pytest.approx(expected_reinv_rate, rel=1e-6)
        assert adjusted_flow == pytest.approx(expected_adjusted_flow, rel=1e-6)

    def test_zero_growth_no_adjustment(self):
        """Test zero growth: no reinvestment needed."""
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(1000.0, 0.0, 0.15)

        assert reinv_rate == 0.0
        assert adjusted_flow == 1000.0

    def test_negative_growth_no_adjustment(self):
        """Test negative growth: no reinvestment needed."""
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(1000.0, -0.02, 0.15)

        assert reinv_rate == 0.0
        assert adjusted_flow == 1000.0

    def test_none_roic_no_adjustment(self):
        """Test None ROIC: conservative approach, no adjustment."""
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(1000.0, 0.03, None)

        assert reinv_rate == 0.0
        assert adjusted_flow == 1000.0

    def test_zero_roic_no_adjustment(self):
        """Test zero ROIC: prevents division by zero, no adjustment."""
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(1000.0, 0.03, 0.0)

        assert reinv_rate == 0.0
        assert adjusted_flow == 1000.0

    def test_negative_roic_no_adjustment(self):
        """Test negative ROIC: conservative approach, no adjustment."""
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(1000.0, 0.03, -0.05)

        assert reinv_rate == 0.0
        assert adjusted_flow == 1000.0

    def test_high_growth_high_roic(self):
        """Test high growth with high ROIC."""
        # 5% growth with 25% ROIC requires 20% reinvestment
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(2000.0, 0.05, 0.25)

        expected_reinv_rate = 0.05 / 0.25  # = 0.2 (20%)
        expected_adjusted_flow = 2000.0 * (1.0 - 0.2)  # = 1600.0

        assert reinv_rate == pytest.approx(expected_reinv_rate, rel=1e-6)
        assert adjusted_flow == pytest.approx(expected_adjusted_flow, rel=1e-6)

    def test_low_growth_low_roic(self):
        """Test low growth with low ROIC."""
        # 1% growth with 5% ROIC requires 20% reinvestment
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(1000.0, 0.01, 0.05)

        expected_reinv_rate = 0.01 / 0.05  # = 0.2 (20%)
        expected_adjusted_flow = 1000.0 * (1.0 - 0.2)  # = 800.0

        assert reinv_rate == pytest.approx(expected_reinv_rate, rel=1e-6)
        assert adjusted_flow == pytest.approx(expected_adjusted_flow, rel=1e-6)

    def test_growth_equals_roic(self):
        """Test edge case where growth equals ROIC (100% reinvestment)."""
        # 10% growth with 10% ROIC requires 100% reinvestment
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(1000.0, 0.10, 0.10)

        expected_reinv_rate = 1.0  # 100%
        expected_adjusted_flow = 1000.0 * (1.0 - 1.0)  # = 0.0

        assert reinv_rate == pytest.approx(expected_reinv_rate, rel=1e-6)
        assert adjusted_flow == pytest.approx(expected_adjusted_flow, rel=1e-6)

    def test_growth_exceeds_roic(self):
        """Test case where growth exceeds ROIC (>100% reinvestment) - NOW CLAMPED."""
        # 15% growth with 10% ROIC would require 150% reinvestment (unsustainable)
        # With clamping, reinvestment is limited to 100%
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(1000.0, 0.15, 0.10)

        # After clamping, reinvestment rate should be 1.0 (100%)
        assert reinv_rate == pytest.approx(1.0, rel=1e-6)
        # Adjusted flow should be zero (all flow reinvested)
        assert adjusted_flow == pytest.approx(0.0, rel=1e-6)

    def test_clamping_at_boundary(self):
        """Test clamping behavior at exactly 100% reinvestment (growth = ROIC)."""
        # When growth equals ROIC, reinvestment is exactly 100%
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(1000.0, 0.10, 0.10)

        assert reinv_rate == pytest.approx(1.0, rel=1e-6)
        assert adjusted_flow == pytest.approx(0.0, rel=1e-6)

    def test_clamping_extreme_case(self):
        """Test clamping with extreme mismatch between growth and ROIC."""
        # 20% growth with 5% ROIC would require 400% reinvestment (absurd)
        # Should be clamped to 100%
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(1000.0, 0.20, 0.05)

        assert reinv_rate == pytest.approx(1.0, rel=1e-6)
        assert adjusted_flow == pytest.approx(0.0, rel=1e-6)

    def test_small_numbers(self):
        """Test with small flow values."""
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(10.0, 0.02, 0.08)

        expected_reinv_rate = 0.02 / 0.08  # = 0.25
        expected_adjusted_flow = 10.0 * (1.0 - 0.25)  # = 7.5

        assert reinv_rate == pytest.approx(expected_reinv_rate, rel=1e-6)
        assert adjusted_flow == pytest.approx(expected_adjusted_flow, rel=1e-6)

    def test_large_numbers(self):
        """Test with large flow values."""
        adjusted_flow, reinv_rate = normalize_terminal_flow_for_stable_state(1_000_000.0, 0.03, 0.12)

        expected_reinv_rate = 0.03 / 0.12  # = 0.25
        expected_adjusted_flow = 1_000_000.0 * (1.0 - 0.25)  # = 750,000

        assert reinv_rate == pytest.approx(expected_reinv_rate, rel=1e-6)
        assert adjusted_flow == pytest.approx(expected_adjusted_flow, rel=1e-6)


# ==============================================================================
# 2. STRUCTURE ADJUSTMENTS & DILUTION
# ==============================================================================


@pytest.mark.unit
class TestCalculateHistoricalShareGrowth:
    """Test historical share growth (CAGR)."""

    def test_normal_cagr(self):
        """Test normal CAGR calculation."""
        shares = [100.0, 110.0, 121.0]  # 10% CAGR
        cagr = calculate_historical_share_growth(shares)
        expected = (121.0 / 100.0) ** (1.0 / 2.0) - 1.0
        assert cagr == pytest.approx(expected, rel=1e-6)

    def test_single_element_returns_zero(self):
        """Test single element returns 0."""
        cagr = calculate_historical_share_growth([100.0])
        assert cagr == 0.0

    def test_buyback_clamping_negative(self):
        """Test that negative growth (buybacks) returns 0."""
        shares = [100.0, 90.0, 80.0]  # Declining shares
        cagr = calculate_historical_share_growth(shares)
        assert cagr == 0.0

    def test_excessive_growth_clamping(self):
        """Test that excessive growth is clamped to MAX_DILUTION_CLAMPING."""
        shares = [100.0, 200.0]  # 100% growth
        cagr = calculate_historical_share_growth(shares)
        assert cagr == pytest.approx(ValuationEngineDefaults.MAX_DILUTION_CLAMPING)

    def test_zero_shares_returns_zero(self):
        """Test that zero or negative shares return 0."""
        cagr = calculate_historical_share_growth([100.0, 0.0])
        assert cagr == 0.0


@pytest.mark.unit
class TestCalculateDilutionFactor:
    """Test dilution factor calculation."""

    def test_none_rate_returns_one(self):
        """Test that None rate returns 1.0."""
        factor = calculate_dilution_factor(None, 5)
        assert factor == 1.0

    def test_zero_rate_returns_one(self):
        """Test that zero rate returns 1.0."""
        factor = calculate_dilution_factor(0.0, 5)
        assert factor == 1.0

    def test_negative_rate_returns_one(self):
        """Test that negative rate returns 1.0."""
        factor = calculate_dilution_factor(-0.02, 5)
        assert factor == 1.0

    def test_positive_rate(self):
        """Test positive dilution rate calculation."""
        factor = calculate_dilution_factor(0.02, 5)
        expected = (1.02) ** 5
        assert factor == pytest.approx(expected, rel=1e-6)


@pytest.mark.unit
class TestComputeDilutedShares:
    """Test diluted shares computation."""

    def test_basic_math(self):
        """Test basic diluted shares calculation."""
        diluted = compute_diluted_shares(100.0, 0.02, 5)
        expected = 100.0 * (1.02**5)
        assert diluted == pytest.approx(expected, rel=1e-6)

    def test_none_rate(self):
        """Test with None rate returns original shares."""
        diluted = compute_diluted_shares(100.0, None, 5)
        assert diluted == 100.0


@pytest.mark.unit
class TestApplyDilutionAdjustment:
    """Test dilution adjustment to price."""

    def test_factor_less_than_one_unchanged(self):
        """Test that factor <= 1 returns price unchanged."""
        price = apply_dilution_adjustment(100.0, 0.9)
        assert price == 100.0

    def test_factor_equal_one_unchanged(self):
        """Test that factor == 1 returns price unchanged."""
        price = apply_dilution_adjustment(100.0, 1.0)
        assert price == 100.0

    def test_factor_greater_than_one_adjusts(self):
        """Test that factor > 1 adjusts price downward."""
        price = apply_dilution_adjustment(100.0, 1.1)
        expected = 100.0 / 1.1
        assert price == pytest.approx(expected, rel=1e-6)


# ==============================================================================
# 3. COST OF CAPITAL (WACC / Ke / SYNTHETIC DEBT)
# ==============================================================================


@pytest.mark.unit
class TestCalculateCostOfEquityCAPM:
    """Test CAPM cost of equity calculation."""

    def test_basic_capm_formula(self):
        """Test basic CAPM formula: Ke = Rf + Beta * MRP."""
        ke = calculate_cost_of_equity_capm(0.04, 1.2, 0.05)
        expected = 0.04 + 1.2 * 0.05
        assert ke == pytest.approx(expected, rel=1e-6)

    def test_zero_beta(self):
        """Test with zero beta returns risk-free rate."""
        ke = calculate_cost_of_equity_capm(0.04, 0.0, 0.05)
        assert ke == pytest.approx(0.04)


@pytest.mark.unit
class TestUnleverBeta:
    """Test Hamada formula for unlevering beta."""

    def test_hamada_formula(self):
        """Test Hamada unlevering formula."""
        beta_u = unlever_beta(1.5, 0.25, 0.5)
        # beta_u = 1.5 / (1 + (1 - 0.25) * 0.5) = 1.5 / 1.375
        expected = 1.5 / (1 + 0.75 * 0.5)
        assert beta_u == pytest.approx(expected, rel=1e-6)

    def test_de_ratio_zero_returns_levered(self):
        """Test that D/E <= 0 returns levered beta unchanged."""
        beta_u = unlever_beta(1.5, 0.25, 0.0)
        assert beta_u == 1.5

    def test_de_ratio_negative_returns_levered(self):
        """Test that negative D/E returns levered beta unchanged."""
        beta_u = unlever_beta(1.5, 0.25, -0.2)
        assert beta_u == 1.5


@pytest.mark.unit
class TestReleverBeta:
    """Test Hamada formula for relevering beta."""

    def test_hamada_formula(self):
        """Test Hamada relevering formula."""
        beta_l = relever_beta(1.0, 0.25, 0.5)
        # beta_l = 1.0 * (1 + (1 - 0.25) * 0.5) = 1.0 * 1.375
        expected = 1.0 * (1 + 0.75 * 0.5)
        assert beta_l == pytest.approx(expected, rel=1e-6)

    def test_target_de_ratio_zero_returns_unlevered(self):
        """Test that target D/E <= 0 returns unlevered beta unchanged."""
        beta_l = relever_beta(1.0, 0.25, 0.0)
        assert beta_l == 1.0

    def test_target_de_ratio_negative_returns_unlevered(self):
        """Test that negative target D/E returns unlevered beta unchanged."""
        beta_l = relever_beta(1.0, 0.25, -0.2)
        assert beta_l == 1.0


@pytest.mark.unit
class TestCalculateCostOfEquity:
    """Test cost of equity with Parameters object."""

    def test_with_explicit_values(self):
        """Test with explicit parameter values."""
        rates = FinancialRatesParameters(
            risk_free_rate=4.0, market_risk_premium=6.0, beta=1.3, tax_rate=25.0, cost_of_debt=None
        )
        common = CommonParameters(rates=rates, capital=CapitalStructureParameters())

        # Mock Parameters with just what we need
        params = Mock(spec=Parameters)
        params.common = common

        ke = calculate_cost_of_equity(params)
        expected = 0.04 + 1.3 * 0.06
        assert ke == pytest.approx(expected, rel=1e-6)

    def test_with_none_fallbacks_to_defaults(self):
        """Test that None values fallback to MacroDefaults."""
        rates = FinancialRatesParameters(
            risk_free_rate=None, market_risk_premium=None, beta=None, tax_rate=25.0, cost_of_debt=None
        )
        common = CommonParameters(rates=rates, capital=CapitalStructureParameters())

        # Mock Parameters with just what we need
        params = Mock(spec=Parameters)
        params.common = common

        ke = calculate_cost_of_equity(params)
        expected = (
            MacroDefaults.DEFAULT_RISK_FREE_RATE
            + ModelDefaults.DEFAULT_BETA * MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM
        )
        assert ke == pytest.approx(expected, rel=1e-6)


@pytest.mark.unit
class TestCalculateSyntheticCostOfDebt:
    """Test synthetic cost of debt calculation using ICR."""

    def test_icr_lookup_large_cap(self):
        """Test ICR lookup for large cap company."""
        # Large cap with good ICR
        kd = calculate_synthetic_cost_of_debt(
            rf=0.04,
            ebit=1000.0,
            interest_expense=100.0,  # ICR = 10
            market_cap=10_000_000_000,
        )
        # ICR = 10, Large Cap -> should use SPREADS_LARGE_CAP
        # ICR >= 8.5 -> AAA spread = 0.0069
        expected = 0.04 + 0.0069
        assert kd == pytest.approx(expected, rel=1e-6)

    def test_icr_lookup_small_cap(self):
        """Test ICR lookup for small cap company."""
        # Small cap with moderate ICR
        kd = calculate_synthetic_cost_of_debt(
            rf=0.04,
            ebit=500.0,
            interest_expense=100.0,  # ICR = 5
            market_cap=1_000_000_000,
        )
        # ICR = 5, Small Cap -> should use SPREADS_SMALL_MID_CAP
        # ICR < 6.0 but >= 4.5 -> A- spread = 0.0133
        expected = 0.04 + 0.0133
        assert kd == pytest.approx(expected, rel=1e-6)

    def test_zero_interest_fallback(self):
        """Test zero interest expense returns A-rated proxy spread."""
        kd = calculate_synthetic_cost_of_debt(rf=0.04, ebit=1000.0, interest_expense=0.0, market_cap=1_000_000_000)
        expected = 0.04 + 0.0107  # A-rated proxy
        assert kd == pytest.approx(expected, rel=1e-6)

    def test_negative_ebit_fallback(self):
        """Test negative EBIT returns A-rated proxy spread."""
        kd = calculate_synthetic_cost_of_debt(rf=0.04, ebit=-100.0, interest_expense=50.0, market_cap=1_000_000_000)
        expected = 0.04 + 0.0107
        assert kd == pytest.approx(expected, rel=1e-6)

    def test_very_low_icr_distressed(self):
        """Test very low ICR returns distressed/junk spread."""
        kd = calculate_synthetic_cost_of_debt(
            rf=0.04,
            ebit=10.0,
            interest_expense=1000.0,  # ICR = 0.01 (very distressed)
            market_cap=1_000_000_000,
        )
        # ICR < 0.5 (small cap) -> Default to 0.2000
        expected = 0.04 + 0.2000
        assert kd == pytest.approx(expected, rel=1e-6)


@pytest.mark.unit
class TestCalculateWACC:
    """Test WACC calculation."""

    def test_full_breakdown_validation(self):
        """Test full WACC breakdown with all components."""
        # Create mock Company
        company = Mock(spec=Company)
        company.current_price = 100.0
        company.ebit_ttm = 1000.0
        company.interest_expense = 100.0

        # Create Parameters
        rates = FinancialRatesParameters(
            risk_free_rate=4.0, market_risk_premium=5.0, beta=1.2, tax_rate=25.0, cost_of_debt=None
        )
        capital = CapitalStructureParameters(total_debt=5000.0, shares_outstanding=1000.0)
        common = CommonParameters(rates=rates, capital=capital)

        # Mock Parameters with just what we need
        params = Mock(spec=Parameters)
        params.common = common

        breakdown = calculate_wacc(company, params)

        # Verify structure
        assert isinstance(breakdown, WACCBreakdown)
        assert breakdown.cost_of_equity > 0
        assert breakdown.cost_of_debt_pre_tax > 0
        assert breakdown.cost_of_debt_after_tax > 0
        assert breakdown.weight_equity + breakdown.weight_debt == pytest.approx(1.0)
        assert breakdown.wacc > 0
        assert breakdown.beta_used == 1.2
        assert breakdown.beta_adjusted is False

    def test_zero_debt(self):
        """Test WACC with zero debt."""
        company = Mock(spec=Company)
        company.current_price = 100.0
        company.ebit_ttm = 1000.0
        company.interest_expense = 0.0

        rates = FinancialRatesParameters(
            risk_free_rate=4.0, market_risk_premium=5.0, beta=1.0, tax_rate=25.0, cost_of_debt=None
        )
        capital = CapitalStructureParameters(total_debt=0.0, shares_outstanding=1000.0)
        common = CommonParameters(rates=rates, capital=capital)

        # Mock Parameters with just what we need
        params = Mock(spec=Parameters)
        params.common = common

        breakdown = calculate_wacc(company, params)

        assert breakdown.weight_equity == pytest.approx(1.0)
        assert breakdown.weight_debt == pytest.approx(0.0)
        assert breakdown.wacc == pytest.approx(breakdown.cost_of_equity)

    def test_manual_cost_of_debt_override(self):
        """Test WACC with manual cost of debt override."""
        company = Mock(spec=Company)
        company.current_price = 100.0
        company.ebit_ttm = 1000.0
        company.interest_expense = 100.0

        rates = FinancialRatesParameters(
            risk_free_rate=4.0,
            market_risk_premium=5.0,
            beta=1.2,
            tax_rate=25.0,
            cost_of_debt=8.0,  # Manual override
        )
        capital = CapitalStructureParameters(total_debt=5000.0, shares_outstanding=1000.0)
        common = CommonParameters(rates=rates, capital=capital)

        # Mock Parameters
        params = Mock(spec=Parameters)
        params.common = common

        breakdown = calculate_wacc(company, params)

        # Verify manual Kd was used
        assert breakdown.cost_of_debt_pre_tax == pytest.approx(0.08)
        assert breakdown.cost_of_debt_after_tax == pytest.approx(0.08 * 0.75)


# ==============================================================================
# 4. SHAREHOLDER MODELS (FCFE & DDM)
# ==============================================================================


@pytest.mark.unit
class TestCalculateFCFEReconstruction:
    """Test FCFE reconstruction from NI."""

    def test_basic_reconstruction(self):
        """Test basic FCFE reconstruction."""
        fcfe = calculate_fcfe_reconstruction(ni=1000.0, adjustments=200.0, net_borrowing=100.0)
        assert fcfe == 1300.0


@pytest.mark.unit
class TestCalculateFCFEBase:
    """Test FCFE from FCFF."""

    def test_fcfe_from_fcff(self):
        """Test FCFE derivation from FCFF."""
        fcfe = calculate_fcfe_base(fcff=1000.0, interest=100.0, tax_rate=0.25, net_borrowing=50.0)
        # FCFE = 1000 - 100 * (1 - 0.25) + 50 = 1000 - 75 + 50 = 975
        expected = 1000.0 - 100.0 * 0.75 + 50.0
        assert fcfe == pytest.approx(expected, rel=1e-6)


@pytest.mark.unit
class TestCalculateSustainableGrowth:
    """Test sustainable growth rate calculation."""

    def test_normal_sgr(self):
        """Test normal SGR calculation."""
        sgr = calculate_sustainable_growth(roe=0.15, payout_ratio=0.40)
        # g = 0.15 * (1 - 0.40) = 0.15 * 0.60 = 0.09
        expected = 0.15 * 0.60
        assert sgr == pytest.approx(expected, rel=1e-6)

    def test_none_payout_ratio(self):
        """Test with None payout ratio treats as 0."""
        sgr = calculate_sustainable_growth(roe=0.15, payout_ratio=None)
        expected = 0.15 * 1.0
        assert sgr == pytest.approx(expected, rel=1e-6)


# ==============================================================================
# 5. SPECIFIC MODELS (RIM & GRAHAM)
# ==============================================================================


@pytest.mark.unit
class TestCalculateGraham1974Value:
    """Test Graham 1974 formula."""

    def test_normal_calculation(self):
        """Test normal Graham calculation."""
        value = calculate_graham_1974_value(eps=5.0, growth_rate=0.05, aaa_yield=0.045)
        # V = 5 * (8.5 + 2 * 5) * 4.4 / (0.045 * 100)
        # V = 5 * 18.5 * 4.4 / 4.5
        expected = 5.0 * (8.5 + 2.0 * 5.0) * 4.4 / (0.045 * 100)
        assert value == pytest.approx(expected, rel=1e-6)

    def test_zero_yield_fallback(self):
        """Test zero yield uses default AAA yield."""
        value = calculate_graham_1974_value(eps=5.0, growth_rate=0.05, aaa_yield=0.0)
        expected = 5.0 * (8.5 + 2.0 * 5.0) * 4.4 / (MacroDefaults.DEFAULT_CORPORATE_AAA_YIELD * 100)
        assert value == pytest.approx(expected, rel=1e-6)

    def test_none_yield_fallback(self):
        """Test None yield uses default AAA yield."""
        value = calculate_graham_1974_value(eps=5.0, growth_rate=0.05, aaa_yield=None)
        expected = 5.0 * (8.5 + 2.0 * 5.0) * 4.4 / (MacroDefaults.DEFAULT_CORPORATE_AAA_YIELD * 100)
        assert value == pytest.approx(expected, rel=1e-6)


@pytest.mark.unit
class TestCalculateRIMVectors:
    """Test Residual Income Model vectors generation."""

    def test_series_generation(self):
        """Test RI and BV series generation."""
        residual_incomes, book_values = calculate_rim_vectors(
            current_bv=1000.0, ke=0.10, earnings=[120.0, 130.0, 140.0], payout=0.50
        )

        assert len(residual_incomes) == 3
        assert len(book_values) == 3

        # Year 1: RI = 120 - (1000 * 0.10) = 20
        # BV = 1000 + 120 - (120 * 0.50) = 1060
        assert residual_incomes[0] == pytest.approx(20.0)
        assert book_values[0] == pytest.approx(1060.0)

        # Year 2: RI = 130 - (1060 * 0.10) = 24
        # BV = 1060 + 130 - (130 * 0.50) = 1125
        assert residual_incomes[1] == pytest.approx(24.0)
        assert book_values[1] == pytest.approx(1125.0)


@pytest.mark.unit
class TestComputeProportions:
    """Test proportions normalization."""

    def test_normal_proportions(self):
        """Test normal proportion calculation."""
        props = compute_proportions(100.0, 200.0, 300.0)
        assert len(props) == 3
        assert props[0] == pytest.approx(100.0 / 600.0)
        assert props[1] == pytest.approx(200.0 / 600.0)
        assert props[2] == pytest.approx(300.0 / 600.0)
        assert sum(props) == pytest.approx(1.0)

    def test_all_zeros(self):
        """Test all zeros assigns 100% to fallback index."""
        props = compute_proportions(0.0, 0.0, 0.0, fallback_index=1)
        assert props == [0.0, 1.0, 0.0]

    def test_single_value(self):
        """Test single non-zero value gets 100%."""
        props = compute_proportions(0.0, 500.0, 0.0)
        assert props == pytest.approx([0.0, 1.0, 0.0])

    def test_none_values_treated_as_zero(self):
        """Test None values treated as zero."""
        props = compute_proportions(100.0, None, 200.0)
        assert props[0] == pytest.approx(100.0 / 300.0)
        assert props[1] == pytest.approx(0.0)
        assert props[2] == pytest.approx(200.0 / 300.0)


# ==============================================================================
# 6. MULTIPLES & TRIANGULATION (RELATIVE VALUATION)
# ==============================================================================


@pytest.mark.unit
class TestCalculatePriceFromPEMultiple:
    """Test price from P/E multiple."""

    def test_normal_calculation(self):
        """Test normal P/E price calculation."""
        price = calculate_price_from_pe_multiple(net_income=1000.0, median_pe=20.0, shares=100.0)
        # Price = (1000 * 20) / 100 = 200
        assert price == pytest.approx(200.0)

    def test_zero_shares(self):
        """Test zero shares returns 0."""
        price = calculate_price_from_pe_multiple(net_income=1000.0, median_pe=20.0, shares=0.0)
        assert price == 0.0

    def test_negative_pe(self):
        """Test negative P/E returns 0."""
        price = calculate_price_from_pe_multiple(net_income=1000.0, median_pe=-5.0, shares=100.0)
        assert price == 0.0


@pytest.mark.unit
class TestCalculatePriceFromEVMultiple:
    """Test price from EV multiple."""

    def test_normal_calculation(self):
        """Test normal EV price calculation."""
        price = calculate_price_from_ev_multiple(
            metric_value=1000.0, median_ev_multiple=10.0, net_debt=2000.0, shares=100.0, minorities=100.0, pensions=50.0
        )
        # EV = 1000 * 10 = 10000
        # Equity = 10000 - 2000 - 100 - 50 = 7850
        # Price = 7850 / 100 = 78.5
        expected = (10000.0 - 2000.0 - 100.0 - 50.0) / 100.0
        assert price == pytest.approx(expected)

    def test_zero_shares(self):
        """Test zero shares returns 0."""
        price = calculate_price_from_ev_multiple(
            metric_value=1000.0, median_ev_multiple=10.0, net_debt=2000.0, shares=0.0
        )
        assert price == 0.0

    def test_negative_equity_value(self):
        """Test negative equity value clamped to 0."""
        price = calculate_price_from_ev_multiple(
            metric_value=100.0, median_ev_multiple=10.0, net_debt=5000.0, shares=100.0
        )
        # EV = 1000, Equity = 1000 - 5000 = -4000 -> clamped to 0
        assert price == 0.0


@pytest.mark.unit
class TestCalculateTriangulatedPrice:
    """Test triangulated price calculation."""

    def test_with_weights(self):
        """Test triangulation with explicit weights."""
        signals = {"DCF": 100.0, "PE": 120.0, "EV_EBITDA": 110.0}
        weights = {"DCF": 0.5, "PE": 0.3, "EV_EBITDA": 0.2}

        price = calculate_triangulated_price(signals, weights)
        # Weighted: (100 * 0.5 + 120 * 0.3 + 110 * 0.2) / 1.0
        # = (50 + 36 + 22) / 1.0 = 108
        expected = 100.0 * 0.5 + 120.0 * 0.3 + 110.0 * 0.2
        assert price == pytest.approx(expected)

    def test_without_weights_simple_average(self):
        """Test triangulation without weights uses simple average."""
        signals = {"DCF": 100.0, "PE": 120.0, "EV_EBITDA": 110.0}

        price = calculate_triangulated_price(signals, None)
        expected = (100.0 + 120.0 + 110.0) / 3.0
        assert price == pytest.approx(expected)

    def test_all_invalid_signals(self):
        """Test all invalid (non-positive) signals returns 0."""
        signals = {"DCF": 0.0, "PE": -50.0, "EV_EBITDA": 0.0}

        price = calculate_triangulated_price(signals, None)
        assert price == 0.0

    def test_partial_invalid_signals(self):
        """Test filters out invalid signals and averages valid ones."""
        signals = {"DCF": 100.0, "PE": 0.0, "EV_EBITDA": 120.0}

        price = calculate_triangulated_price(signals, None)
        # Only DCF and EV_EBITDA are valid
        expected = (100.0 + 120.0) / 2.0
        assert price == pytest.approx(expected)

    def test_weights_with_missing_signal(self):
        """Test weights when some signals are missing or invalid."""
        signals = {"DCF": 100.0, "PE": 0.0, "EV_EBITDA": 120.0}
        weights = {"DCF": 0.6, "PE": 0.2, "EV_EBITDA": 0.2}

        price = calculate_triangulated_price(signals, weights)
        # Only DCF and EV_EBITDA valid with weights 0.6 and 0.2
        # Weighted: (100 * 0.6 + 120 * 0.2) / (0.6 + 0.2)
        expected = (100.0 * 0.6 + 120.0 * 0.2) / (0.6 + 0.2)
        assert price == pytest.approx(expected)

    def test_weights_all_zero_falls_back_to_average(self):
        """Test that when all weights are zero or missing, falls back to simple average."""
        signals = {"DCF": 100.0, "PE": 120.0}
        # Provide weights but for methods not in valid signals
        weights = {"OTHER": 1.0}

        price = calculate_triangulated_price(signals, weights)
        # Should fallback to simple average since no active weights
        expected = (100.0 + 120.0) / 2.0
        assert price == pytest.approx(expected)
