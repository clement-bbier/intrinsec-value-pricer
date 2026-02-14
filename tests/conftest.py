"""
tests/conftest.py

SHARED TEST FIXTURES
====================
Role: Provides distinct reusable data objects for testing.
Scope: Global (available to all tests automatically).
"""

from datetime import datetime, timezone

import pytest

from src.models.company import Company, CompanySnapshot
from src.models.enums import CompanySector, ValuationMethodology
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import CommonParameters, FinancialRatesParameters
from src.models.parameters.strategies import FCFFStandardParameters
from src.models.valuation import ValuationRequest


@pytest.fixture
def mock_apple_identity():
    """Returns a basic identity for Apple Inc with timezone-aware datetime."""
    return Company(
        ticker="AAPL",
        name="Apple Inc.",
        sector=CompanySector.TECHNOLOGY,
        current_price=150.0,
        currency="USD",
        last_update=datetime.now(timezone.utc),  # Timezone-aware
    )


@pytest.fixture
def mock_apple_snapshot():
    """
    A 'Golden Dataset' representing a robust, profitable tech company.
    Based on rough 2023 figures for realism.
    """
    return CompanySnapshot(
        ticker="AAPL",
        name="Apple Inc.",
        sector="Technology",
        current_price=150.0,
        # Balance Sheet (Micro)
        total_debt=120_000.0,  # $120B
        cash_and_equivalents=50_000.0,  # $50B
        shares_outstanding=16_000.0,  # 16B shares
        # Income Statement (Micro)
        revenue_ttm=380_000.0,  # $380B
        ebit_ttm=110_000.0,  # $110B
        net_income_ttm=95_000.0,  # $95B
        interest_expense=3_000.0,  # $3B
        # Cash Flow (Micro)
        fcf_ttm=100_000.0,  # $100B
        capex_ttm=10_000.0,  # $10B
        # Macro / Market
        beta=1.2,
        risk_free_rate=0.04,  # 4%
        market_risk_premium=0.05,  # 5%
        tax_rate=0.21,  # 21%
    )


@pytest.fixture
def fcff_request_standard(mock_apple_identity):
    """
    A valid request for a Standard FCFF Valuation.
    """
    # 1. Create Empty Strategy Params (Ghost)
    strategy_params = FCFFStandardParameters(
        projection_years=5,
        growth_rate_p1=0.05,  # 5% growth override
    )

    # 2. Bundle into global Parameters
    params = Parameters(
        structure=mock_apple_identity,
        strategy=strategy_params,
        # Extensions are default (None/False)
    )

    # 3. Wrap in Request
    return ValuationRequest(mode=ValuationMethodology.FCFF_STANDARD, parameters=params)


@pytest.fixture
def mock_parameters_with_rates():
    """
    A Parameters object with explicit rates (not None).
    Used for testing scenarios where all financial rates are provided.
    """
    company = Company(ticker="AAPL", name="Apple Inc.")

    # Explicit rates (not ghost)
    common_params = CommonParameters(
        rates=FinancialRatesParameters(
            risk_free_rate=0.04,  # 4%
            market_risk_premium=0.05,  # 5%
            beta=1.2,
            tax_rate=0.21,  # 21%
        )
    )

    strategy = FCFFStandardParameters(projection_years=5)

    return Parameters(structure=company, common=common_params, strategy=strategy)


@pytest.fixture
def mock_parameters_ghost():
    """
    A Parameters object with all None rates (ghost state).
    Used for testing fallback behavior to MacroDefaults.
    """
    company = Company(ticker="TSLA", name="Tesla Inc.")

    # Ghost state - all None
    common_params = CommonParameters(
        rates=FinancialRatesParameters(risk_free_rate=None, market_risk_premium=None, beta=None, tax_rate=None)
    )

    strategy = FCFFStandardParameters(projection_years=5)

    return Parameters(structure=company, common=common_params, strategy=strategy)
