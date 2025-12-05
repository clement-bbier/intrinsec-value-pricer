import pytest

from core.models import CompanyFinancials, DCFParameters
from core.dcf.valuation import run_dcf
from core.dcf.fundamental_engine import run_dcf_fundamental_fcff
from core.exceptions import CalculationError


def _make_dummy_financials() -> CompanyFinancials:
    return CompanyFinancials(
        ticker="TEST",
        currency="USD",
        current_price=100.0,
        shares_outstanding=1_000_000,      # 1 million shares
        total_debt=200_000_000.0,          # 200M debt
        cash_and_equivalents=50_000_000.0, # 50M cash
        fcf_last=10_000_000.0,             # 10M last FCFF (Méthode 1)
        beta=1.0,
        # Pour la Méthode 2, ce champ pourra être surchargé dans les tests
        fcf_fundamental_smoothed=None,
    )


def _make_dummy_params() -> DCFParameters:
    return DCFParameters(
        risk_free_rate=0.04,
        market_risk_premium=0.05,
        cost_of_debt=0.05,
        tax_rate=0.25,
        fcf_growth_rate=0.03,
        perpetual_growth_rate=0.02,
        projection_years=5,
    )


def test_run_dcf_basic_sanity():
    financials = _make_dummy_financials()
    params = _make_dummy_params()

    result = run_dcf(financials, params)

    # Basic sanity checks
    assert result.wacc > 0
    assert result.wacc > params.perpetual_growth_rate
    assert len(result.projected_fcfs) == params.projection_years
    assert len(result.discount_factors) == params.projection_years
    assert result.enterprise_value > 0
    assert result.equity_value > 0
    assert result.intrinsic_value_per_share > 0


def test_run_dcf_raises_when_wacc_below_growth():
    financials = _make_dummy_financials()

    # Force a very high perpetual growth vs very low discount rate
    params = DCFParameters(
        risk_free_rate=0.01,
        market_risk_premium=0.0,   # so cost of equity ~= 1%
        cost_of_debt=0.01,
        tax_rate=0.0,
        fcf_growth_rate=0.03,
        perpetual_growth_rate=0.05,   # g > WACC
        projection_years=5,
    )

    with pytest.raises(CalculationError):
        run_dcf(financials, params)


# ---------------------------------------------------------------------------
# Nouveaux tests – Méthode 2 : DCF Fondamental (3-Statement Light)
# ---------------------------------------------------------------------------

def test_run_dcf_fundamental_raises_if_no_smoothed_fcf():
    """
    Si fcf_fundamental_smoothed est None, le moteur fondamental doit
    lever une CalculationError (données insuffisantes).
    """
    financials = _make_dummy_financials()
    financials.fcf_fundamental_smoothed = None  # explicite

    params = _make_dummy_params()

    with pytest.raises(CalculationError):
        run_dcf_fundamental_fcff(financials, params)


def test_run_dcf_fundamental_uses_smoothed_fcf_and_differs_from_basic():
    """
    Vérifie que la Méthode 2 (fondamentale) utilise bien le FCFF lissé
    comme point de départ et produit un résultat différent de la Méthode 1
    lorsque ce FCFF_0 est significativement différent.
    """
    financials = _make_dummy_financials()
    params = _make_dummy_params()

    # On force un FCFF fondamental significativement différent
    financials.fcf_fundamental_smoothed = financials.fcf_last * 2.0

    # Résultat Méthode 1 (basic run_dcf → FCFF simple)
    basic_result = run_dcf(financials, params)

    # Résultat Méthode 2 (fondamental)
    fundamental_result = run_dcf_fundamental_fcff(financials, params)

    assert fundamental_result.wacc == pytest.approx(basic_result.wacc)
    assert fundamental_result.intrinsic_value_per_share != pytest.approx(
        basic_result.intrinsic_value_per_share
    )
    assert fundamental_result.intrinsic_value_per_share > 0
