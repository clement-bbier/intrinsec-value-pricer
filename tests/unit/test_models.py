"""
tests/unit/test_models.py

COMPREHENSIVE MODEL TESTING
===========================
Role: Validates all Pydantic models across the src/models/ package.
Coverage: Company, Enums, Parameters (with scaling), Valuation envelopes.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.models import (
    CapitalStructureParameters,
    CommonParameters,
    # Identity & Snapshots
    Company,
    CompanySector,
    CompanySnapshot,
    ExtensionBundleParameters,
    # Parameters
    FinancialRatesParameters,
    MCParameters,
    Parameters,
    ParametersSource,
    TerminalValueMethod,
    # Enums
    ValuationMethodology,
    # Valuation Envelopes
    ValuationRequest,
    ValuationResult,
    VariableSource,
)
from src.models.parameters.options import ScenariosParameters, SensitivityParameters
from src.models.parameters.strategies import FCFFStandardParameters, GrahamParameters
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedCapital, ResolvedRates
from src.models.results.options import ExtensionBundleResults
from src.models.results.strategies import FCFFStandardResults

# ==============================================================================
# 1. COMPANY & IDENTITY MODELS
# ==============================================================================

@pytest.mark.unit
def test_company_creation_minimal():
    """Test Company creation with minimal required fields."""
    company = Company(ticker="AAPL")

    assert company.ticker == "AAPL"
    assert company.name == "Unknown Entity"
    assert company.sector == CompanySector.UNKNOWN
    assert company.currency == "USD"
    assert company.current_price == 0.0
    assert isinstance(company.last_update, datetime)


@pytest.mark.unit
def test_company_creation_full():
    """Test Company creation with all fields."""
    update_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    company = Company(
        ticker="MSFT",
        name="Microsoft Corporation",
        sector=CompanySector.TECHNOLOGY,
        industry="Software",
        country="USA",
        currency="USD",
        current_price=350.50,
        last_update=update_time
    )

    assert company.ticker == "MSFT"
    assert company.name == "Microsoft Corporation"
    assert company.sector == CompanySector.TECHNOLOGY
    assert company.industry == "Software"
    assert company.country == "USA"
    assert company.current_price == 350.50
    assert company.last_update == update_time


@pytest.mark.unit
def test_company_frozen_model():
    """Test that Company model is immutable (frozen)."""
    company = Company(ticker="AAPL", name="Apple Inc.")

    with pytest.raises(ValidationError):
        company.ticker = "MSFT"


@pytest.mark.unit
def test_company_display_name_property():
    """Test the display_name computed property."""
    company = Company(ticker="TSLA", name="Tesla Inc.")

    assert company.display_name == "TSLA - Tesla Inc."


@pytest.mark.unit
def test_company_timezone_aware_default():
    """Test that last_update uses timezone-aware datetime by default."""
    company = Company(ticker="GOOG")

    assert company.last_update.tzinfo == timezone.utc


@pytest.mark.unit
def test_company_negative_price_validation():
    """Test that negative current_price is rejected."""
    with pytest.raises(ValidationError):
        Company(ticker="AAPL", current_price=-10.0)


@pytest.mark.unit
def test_company_snapshot_minimal():
    """Test CompanySnapshot with minimal data."""
    snapshot = CompanySnapshot(ticker="AAPL")

    assert snapshot.ticker == "AAPL"
    assert snapshot.name is None
    assert snapshot.current_price is None
    assert snapshot.total_debt is None


@pytest.mark.unit
def test_company_snapshot_full():
    """Test CompanySnapshot with comprehensive data."""
    snapshot = CompanySnapshot(
        ticker="AAPL",
        name="Apple Inc.",
        sector="Technology",
        current_price=150.0,
        total_debt=120_000.0,
        cash_and_equivalents=50_000.0,
        shares_outstanding=16_000.0,
        revenue_ttm=380_000.0,
        ebit_ttm=110_000.0,
        net_income_ttm=95_000.0,
        beta=1.2,
        risk_free_rate=0.04,
        market_risk_premium=0.05,
        tax_rate=0.21
    )

    assert snapshot.ticker == "AAPL"
    assert snapshot.name == "Apple Inc."
    assert snapshot.total_debt == 120_000.0
    assert snapshot.beta == 1.2


@pytest.mark.unit
def test_company_snapshot_extra_ignore():
    """Test that extra fields are ignored (extra='ignore')."""
    snapshot = CompanySnapshot(
        ticker="AAPL",
        unknown_field="should_be_ignored",
        another_extra=123
    )

    assert snapshot.ticker == "AAPL"
    assert not hasattr(snapshot, "unknown_field")
    assert not hasattr(snapshot, "another_extra")


# ==============================================================================
# 2. ENUMS
# ==============================================================================

@pytest.mark.unit
def test_valuation_methodology_enum_values():
    """Test all ValuationMethodology enum values."""
    assert ValuationMethodology.FCFF_STANDARD == "FCFF_STANDARD"
    assert ValuationMethodology.FCFF_NORMALIZED == "FCFF_NORMALIZED"
    assert ValuationMethodology.FCFF_GROWTH == "FCFF_GROWTH"
    assert ValuationMethodology.FCFE == "FCFE"
    assert ValuationMethodology.DDM == "DDM"
    assert ValuationMethodology.RIM == "RIM"
    assert ValuationMethodology.GRAHAM == "GRAHAM"


@pytest.mark.unit
def test_valuation_methodology_is_direct_equity_true():
    """Test is_direct_equity property returns True for equity models."""
    assert ValuationMethodology.DDM.is_direct_equity is True
    assert ValuationMethodology.RIM.is_direct_equity is True
    assert ValuationMethodology.FCFE.is_direct_equity is True


@pytest.mark.unit
def test_valuation_methodology_is_direct_equity_false():
    """Test is_direct_equity property returns False for enterprise value models."""
    assert ValuationMethodology.FCFF_STANDARD.is_direct_equity is False
    assert ValuationMethodology.FCFF_NORMALIZED.is_direct_equity is False
    assert ValuationMethodology.FCFF_GROWTH.is_direct_equity is False
    assert ValuationMethodology.GRAHAM.is_direct_equity is False


@pytest.mark.unit
def test_terminal_value_method_enum():
    """Test TerminalValueMethod enum instantiation."""
    assert TerminalValueMethod.GORDON_GROWTH == "GORDON_GROWTH"
    assert TerminalValueMethod.EXIT_MULTIPLE == "EXIT_MULTIPLE"
    assert TerminalValueMethod.PERPETUAL_GROWTH == "Perpetual Growth"


@pytest.mark.unit
def test_company_sector_enum():
    """Test CompanySector enum instantiation."""
    assert CompanySector.TECHNOLOGY.value
    assert CompanySector.FINANCIAL_SERVICES.value
    assert CompanySector.HEALTHCARE.value
    assert CompanySector.UNKNOWN.value


@pytest.mark.unit
def test_parameters_source_enum():
    """Test ParametersSource enum instantiation."""
    assert ParametersSource.MANUAL == "USER_INPUT"
    assert ParametersSource.AUTO == "PROVIDER_INPUT"
    assert ParametersSource.SYSTEM == "SYSTEM_INPUT"
    assert ParametersSource.EMPTY == "EMPTY"


@pytest.mark.unit
def test_variable_source_enum():
    """Test VariableSource enum instantiation."""
    assert VariableSource.YAHOO_FINANCE == "YAHOO_FINANCE"
    assert VariableSource.MANUAL_OVERRIDE == "MANUAL_OVERRIDE"
    assert VariableSource.SYSTEM == "SYSTEM"
    assert VariableSource.CALCULATED == "CALCULATED"


# ==============================================================================
# 3. PARAMETERS WITH SCALING
# ==============================================================================

@pytest.mark.unit
def test_financial_rates_parameters_percentage_scaling():
    """Test UIKey percentage scaling (5.0 → 0.05)."""
    params = FinancialRatesParameters(
        risk_free_rate=5.0,  # Should become 0.05
        market_risk_premium=7.5,  # Should become 0.075
        tax_rate=21.0  # Should become 0.21
    )

    assert params.risk_free_rate == pytest.approx(0.05)
    assert params.market_risk_premium == pytest.approx(0.075)
    assert params.tax_rate == pytest.approx(0.21)


@pytest.mark.unit
def test_financial_rates_parameters_already_scaled():
    """Test that already-scaled values (< 1.0) are not re-scaled."""
    params = FinancialRatesParameters(
        risk_free_rate=0.05,  # Already in decimal form
        beta=1.2  # Raw scale, no change
    )

    assert params.risk_free_rate == pytest.approx(0.05)
    assert params.beta == pytest.approx(1.2)


@pytest.mark.unit
def test_financial_rates_parameters_none_values():
    """Test that None values are preserved during scaling."""
    params = FinancialRatesParameters(
        risk_free_rate=None,
        beta=None
    )

    assert params.risk_free_rate is None
    assert params.beta is None


@pytest.mark.unit
def test_capital_structure_parameters_million_scaling():
    """Test UIKey million scaling (100 → 100_000_000)."""
    params = CapitalStructureParameters(
        total_debt=100.0,  # Should become 100M
        cash_and_equivalents=50.0,  # Should become 50M
        shares_outstanding=1.5  # Should become 1.5M
    )

    assert params.total_debt == pytest.approx(100_000_000.0)
    assert params.cash_and_equivalents == pytest.approx(50_000_000.0)
    assert params.shares_outstanding == pytest.approx(1_500_000.0)


@pytest.mark.unit
def test_capital_structure_parameters_dilution_rate_scaling():
    """Test percentage scaling for annual_dilution_rate."""
    params = CapitalStructureParameters(
        annual_dilution_rate=2.5  # Should become 0.025
    )

    assert params.annual_dilution_rate == pytest.approx(0.025)


@pytest.mark.unit
def test_common_parameters_default_factory():
    """Test CommonParameters creates nested defaults."""
    params = CommonParameters()

    assert isinstance(params.rates, FinancialRatesParameters)
    assert isinstance(params.capital, CapitalStructureParameters)
    assert params.rates.risk_free_rate is None
    assert params.capital.total_debt is None


# ==============================================================================
# 4. STRATEGY PARAMETERS
# ==============================================================================

@pytest.mark.unit
def test_fcff_standard_parameters_creation():
    """Test FCFFStandardParameters with defaults."""
    params = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=5.0  # Should scale to 0.05
    )

    assert params.mode == ValuationMethodology.FCFF_STANDARD
    assert params.projection_years == 5
    assert params.growth_rate_p1 == pytest.approx(0.05)
    assert isinstance(params.terminal_value, object)


@pytest.mark.unit
def test_fcff_standard_parameters_validation():
    """Test validation bounds on projection_years."""
    with pytest.raises(ValidationError):
        FCFFStandardParameters(projection_years=0)  # Must be >= 1

    with pytest.raises(ValidationError):
        FCFFStandardParameters(projection_years=100)  # Must be <= 50


@pytest.mark.unit
def test_graham_parameters_creation():
    """Test GrahamParameters with defaults."""
    params = GrahamParameters(
        eps_normalized=5.0,
        growth_estimate=10.0  # Should scale to 0.10
    )

    assert params.mode == ValuationMethodology.GRAHAM
    assert params.eps_normalized == pytest.approx(5.0)  # Raw scale
    assert params.growth_estimate == pytest.approx(0.10)


# ==============================================================================
# 5. EXTENSION BUNDLE PARAMETERS
# ==============================================================================

@pytest.mark.unit
def test_extension_bundle_parameters_default_disabled():
    """Test ExtensionBundleParameters defaults — all extensions disabled."""
    bundle = ExtensionBundleParameters()

    assert isinstance(bundle.monte_carlo, MCParameters)
    assert bundle.monte_carlo.enabled is False

    assert isinstance(bundle.sensitivity, SensitivityParameters)
    assert bundle.sensitivity.enabled is False

    assert isinstance(bundle.scenarios, ScenariosParameters)
    assert bundle.scenarios.enabled is False


@pytest.mark.unit
def test_mc_parameters_bounds_validation():
    """Test MCParameters iterations bounds (min/max)."""
    # Valid range
    params = MCParameters(enabled=True, iterations=5000)
    assert params.iterations == 5000

    # Test minimum bound
    with pytest.raises(ValidationError):
        MCParameters(iterations=50)  # Below minimum

    # Test maximum bound
    with pytest.raises(ValidationError):
        MCParameters(iterations=100_000)  # Above maximum


@pytest.mark.unit
def test_sensitivity_parameters_bounds_validation():
    """Test SensitivityParameters steps bounds (3-9)."""
    # Valid range
    params = SensitivityParameters(enabled=True, steps=5)
    assert params.steps == 5

    # Test minimum bound
    with pytest.raises(ValidationError):
        SensitivityParameters(steps=2)  # Below minimum

    # Test maximum bound
    with pytest.raises(ValidationError):
        SensitivityParameters(steps=10)  # Above maximum


@pytest.mark.unit
def test_scenarios_parameters_creation():
    """Test ScenariosParameters with empty cases list."""
    params = ScenariosParameters(enabled=True)

    assert params.enabled is True
    assert params.cases == []


# ==============================================================================
# 6. VALUATION REQUEST & RESULT
# ==============================================================================

@pytest.mark.unit
def test_valuation_request_construction():
    """Test ValuationRequest construction with valid data."""
    company = Company(ticker="AAPL", name="Apple Inc.")
    strategy = FCFFStandardParameters(projection_years=5)
    params = Parameters(structure=company, strategy=strategy)

    request = ValuationRequest(
        mode=ValuationMethodology.FCFF_STANDARD,
        parameters=params
    )

    assert request.mode == ValuationMethodology.FCFF_STANDARD
    assert request.parameters.structure.ticker == "AAPL"
    assert isinstance(request.parameters.strategy, FCFFStandardParameters)


@pytest.mark.unit
def test_valuation_result_construction():
    """Test ValuationResult construction."""
    company = Company(ticker="AAPL", current_price=150.0)
    strategy = FCFFStandardParameters(projection_years=5)
    params = Parameters(structure=company, strategy=strategy)
    request = ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)

    # Create minimal results
    rates = ResolvedRates(cost_of_equity=0.08, cost_of_debt_after_tax=0.03, wacc=0.07)
    capital = ResolvedCapital(
        market_cap=2_400_000_000_000.0,
        enterprise_value=2_950_000_000_000.0,
        net_debt_resolved=70_000_000_000.0,
        equity_value_total=2_880_000_000_000.0
    )
    common_results = CommonResults(
        rates=rates,
        capital=capital,
        intrinsic_value_per_share=180.0,
        upside_pct=0.2
    )
    strategy_results = FCFFStandardResults(
        projected_flows=[100.0, 105.0, 110.0, 115.0, 120.0],
        discount_factors=[0.935, 0.873, 0.816, 0.763, 0.713],
        terminal_value=2400.0,
        discounted_terminal_value=1711.2,
        tv_weight_pct=75.0
    )
    extensions = ExtensionBundleResults()
    results = Results(common=common_results, strategy=strategy_results, extensions=extensions)

    result = ValuationResult(request=request, results=results)

    assert result.request.mode == ValuationMethodology.FCFF_STANDARD
    assert result.results.common.intrinsic_value_per_share == pytest.approx(180.0)


@pytest.mark.unit
def test_valuation_result_compute_upside_positive_market_price():
    """Test compute_upside() with valid market_price > 0."""
    company = Company(ticker="AAPL", current_price=150.0)
    strategy = FCFFStandardParameters(projection_years=5)
    params = Parameters(structure=company, strategy=strategy)
    request = ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)

    rates = ResolvedRates(cost_of_equity=0.08, cost_of_debt_after_tax=0.03, wacc=0.07)
    capital = ResolvedCapital(
        market_cap=2_400_000_000_000.0,
        enterprise_value=2_950_000_000_000.0,
        net_debt_resolved=70_000_000_000.0,
        equity_value_total=2_880_000_000_000.0
    )
    common_results = CommonResults(
        rates=rates,
        capital=capital,
        intrinsic_value_per_share=180.0,
        upside_pct=0.0  # Will be calculated
    )
    strategy_results = FCFFStandardResults(
        projected_flows=[100.0, 105.0],
        discount_factors=[0.935, 0.873],
        terminal_value=2400.0,
        discounted_terminal_value=1711.2,
        tv_weight_pct=75.0
    )
    extensions = ExtensionBundleResults()
    results = Results(common=common_results, strategy=strategy_results, extensions=extensions)

    result = ValuationResult(request=request, results=results)
    result.compute_upside()

    # Upside = (180 - 150) / 150 = 0.2 (20%)
    assert result.upside_pct == pytest.approx(0.2)


@pytest.mark.unit
def test_valuation_result_compute_upside_zero_market_price():
    """Test compute_upside() returns None when market_price = 0."""
    company = Company(ticker="AAPL", current_price=0.0)
    strategy = FCFFStandardParameters(projection_years=5)
    params = Parameters(structure=company, strategy=strategy)
    request = ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)

    rates = ResolvedRates(cost_of_equity=0.08, cost_of_debt_after_tax=0.03, wacc=0.07)
    capital = ResolvedCapital(
        market_cap=0.0,
        enterprise_value=2_950_000_000_000.0,
        net_debt_resolved=70_000_000_000.0,
        equity_value_total=2_880_000_000_000.0
    )
    common_results = CommonResults(
        rates=rates,
        capital=capital,
        intrinsic_value_per_share=180.0,
        upside_pct=0.0
    )
    strategy_results = FCFFStandardResults(
        projected_flows=[100.0],
        discount_factors=[0.935],
        terminal_value=2400.0,
        discounted_terminal_value=1711.2,
        tv_weight_pct=75.0
    )
    extensions = ExtensionBundleResults()
    results = Results(common=common_results, strategy=strategy_results, extensions=extensions)

    result = ValuationResult(request=request, results=results)
    result.compute_upside()

    assert result.upside_pct is None


@pytest.mark.unit
def test_valuation_result_compute_upside_none_iv():
    """Test compute_upside() returns None when intrinsic_value is None."""
    company = Company(ticker="AAPL", current_price=150.0)
    strategy = FCFFStandardParameters(projection_years=5)
    params = Parameters(structure=company, strategy=strategy)
    request = ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)

    rates = ResolvedRates(cost_of_equity=0.08, cost_of_debt_after_tax=0.03, wacc=0.07)
    capital = ResolvedCapital(
        market_cap=2_400_000_000_000.0,
        enterprise_value=0.0,
        net_debt_resolved=0.0,
        equity_value_total=0.0
    )
    # Set intrinsic_value_per_share to 0 (invalid state)
    common_results = CommonResults(
        rates=rates,
        capital=capital,
        intrinsic_value_per_share=0.0,
        upside_pct=0.0
    )
    strategy_results = FCFFStandardResults(
        projected_flows=[100.0],
        discount_factors=[0.935],
        terminal_value=2400.0,
        discounted_terminal_value=1711.2,
        tv_weight_pct=75.0
    )
    extensions = ExtensionBundleResults()
    results = Results(common=common_results, strategy=strategy_results, extensions=extensions)

    result = ValuationResult(request=request, results=results)
    # Manually set IV to None to test the None case
    result.results.common.intrinsic_value_per_share = None  # type: ignore
    result.compute_upside()

    assert result.upside_pct is None


@pytest.mark.unit
def test_valuation_result_compute_upside_negative():
    """Test compute_upside() with undervalued scenario (negative upside)."""
    company = Company(ticker="AAPL", current_price=200.0)
    strategy = FCFFStandardParameters(projection_years=5)
    params = Parameters(structure=company, strategy=strategy)
    request = ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)

    rates = ResolvedRates(cost_of_equity=0.08, cost_of_debt_after_tax=0.03, wacc=0.07)
    capital = ResolvedCapital(
        market_cap=3_200_000_000_000.0,
        enterprise_value=2_520_000_000_000.0,
        net_debt_resolved=120_000_000_000.0,
        equity_value_total=2_400_000_000_000.0
    )
    common_results = CommonResults(
        rates=rates,
        capital=capital,
        intrinsic_value_per_share=150.0,
        upside_pct=0.0
    )
    strategy_results = FCFFStandardResults(
        projected_flows=[100.0],
        discount_factors=[0.935],
        terminal_value=2400.0,
        discounted_terminal_value=1711.2,
        tv_weight_pct=75.0
    )
    extensions = ExtensionBundleResults()
    results = Results(common=common_results, strategy=strategy_results, extensions=extensions)

    result = ValuationResult(request=request, results=results)
    result.compute_upside()

    # Upside = (150 - 200) / 200 = -0.25 (-25%)
    assert result.upside_pct == pytest.approx(-0.25)


# ==============================================================================
# 7. GHOST PATTERN — SYSTEM CONSTANTS (Group B) FALLBACK
# ==============================================================================

@pytest.mark.unit
def test_sensitivity_steps_default_from_constant():
    """SensitivityParameters.steps must default to SensitivityDefaults.DEFAULT_STEPS."""
    from src.config.constants import SensitivityDefaults
    params = SensitivityParameters()
    assert params.steps == SensitivityDefaults.DEFAULT_STEPS


@pytest.mark.unit
def test_sensitivity_steps_rejects_below_three():
    """SensitivityParameters.steps must reject values below 3 (ge=3)."""
    with pytest.raises(ValidationError):
        SensitivityParameters(steps=1)
    with pytest.raises(ValidationError):
        SensitivityParameters(steps=2)


@pytest.mark.unit
def test_sensitivity_steps_accepts_three():
    """SensitivityParameters.steps must accept the minimum value of 3."""
    params = SensitivityParameters(steps=3)
    assert params.steps == 3


@pytest.mark.unit
def test_mc_iterations_default_from_constant():
    """MCParameters.iterations must default to MonteCarloDefaults.DEFAULT_SIMULATIONS."""
    from src.config.constants import MonteCarloDefaults
    params = MCParameters()
    assert params.iterations == MonteCarloDefaults.DEFAULT_SIMULATIONS


@pytest.mark.unit
def test_backtest_lookback_default_from_constant():
    """BacktestParameters.lookback_years must default to BacktestDefaults constant."""
    from src.config.constants import BacktestDefaults
    from src.models.parameters.options import BacktestParameters
    params = BacktestParameters()
    assert params.lookback_years == BacktestDefaults.DEFAULT_LOOKBACK_YEARS


@pytest.mark.unit
def test_market_params_default_to_none_for_resolver():
    """Financial market parameters (Group A) must default to None for the Resolver cascade."""
    params = FinancialRatesParameters()
    assert params.risk_free_rate is None
    assert params.market_risk_premium is None
    assert params.beta is None
    assert params.cost_of_debt is None
    assert params.tax_rate is None


@pytest.mark.unit
def test_sotp_discount_default_from_constant():
    """SOTPParameters.conglomerate_discount must default to SOTPDefaults constant."""
    from src.config.constants import SOTPDefaults
    from src.models.parameters.options import SOTPParameters
    params = SOTPParameters()
    assert params.conglomerate_discount == SOTPDefaults.DEFAULT_CONGLOMERATE_DISCOUNT
