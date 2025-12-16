import pytest
from core.models import CompanyFinancials, DCFParameters

@pytest.fixture
def sample_financials():
    return CompanyFinancials(
        ticker="TEST",
        currency="USD",
        sector="Technology",
        industry="Software",
        country="United States",
        current_price=100.0,
        shares_outstanding=1_000_000,
        total_debt=20_000_000,
        cash_and_equivalents=5_000_000,
        interest_expense=1_000_000,
        beta=1.2,
        fcf_last=10_000_000,
        fcf_fundamental_smoothed=9_500_000,
        source_fcf="ttm"
    )

@pytest.fixture
def sample_params():
    return DCFParameters(
        risk_free_rate=0.04,
        market_risk_premium=0.05,
        cost_of_debt=0.06,
        tax_rate=0.25,
        fcf_growth_rate=0.05,
        perpetual_growth_rate=0.02,
        projection_years=5,
        target_equity_weight=0.8,
        target_debt_weight=0.2
    )