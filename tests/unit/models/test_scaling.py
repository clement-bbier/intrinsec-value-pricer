import pytest
from src.models.parameters.common import FinancialRatesParameters, CapitalStructureParameters
from src.models.parameters.strategies import FCFFStandardParameters

def test_financial_rates_scaling():
    """Vérifie que les taux sont divisés par 100 et les prix restent bruts."""
    data = {"risk_free_rate": 4.5, "market_risk_premium": 6.0, "manual_beta": 1.1}
    params = FinancialRatesParameters(**data)
    assert params.risk_free_rate == 0.045
    assert params.market_risk_premium == 0.06
    assert params.manual_beta == 1.1

def test_capital_structure_scaling():
    """Vérifie que les millions sont convertis en unités absolues."""
    data = {"total_debt": 100.0, "cash_and_equivalents": 10.0} # en M$
    params = CapitalStructureParameters(**data)
    assert params.total_debt == 100_000_000.0
    assert params.cash_and_equivalents == 10_000_000.0

def test_strategy_validation():
    """Vérifie que les contraintes métier (ex: années > 0) sont respectées."""
    with pytest.raises(ValueError):
        FCFFStandardParameters(projection_years=-1) # Doit lever une erreur Pydantic