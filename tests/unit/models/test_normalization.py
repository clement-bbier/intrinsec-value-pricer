import pytest
from src.models.parameters.common import FinancialRatesParameters, CapitalStructureParameters
from src.models.parameters.options import MCParameters

def test_financial_rates_normalization():
    """Vérifie que les taux % deviennent des décimaux et que le Beta reste brut."""
    data = {
        "risk_free_rate": 4.5,      # Saisi: 4.5%
        "market_risk_premium": 6.0, # Saisi: 6.0%
        "beta": 1.1                 # Saisi: 1.1 (raw)
    }
    params = FinancialRatesParameters(**data)
    assert params.risk_free_rate == 0.045
    assert params.market_risk_premium == 0.06
    assert params.beta == 1.1

def test_capital_structure_normalization():
    """Vérifie que les millions (M$) sont convertis en unités absolues."""
    data = {
        "total_debt": 100.0,         # 100M
        "shares_outstanding": 10.0   # 10M d'actions
    }
    params = CapitalStructureParameters(**data)
    assert params.total_debt == 100_000_000.0
    assert params.shares_outstanding == 10_000_000.0

def test_monte_carlo_normalization():
    """Vérifie le scaling des volatilités dans le bloc Monte Carlo."""
    data = {"vol_flow": 20.0, "vol_growth": 15.0} #
    params = MCParameters(**data)
    assert params.vol_flow == 0.20
    assert params.vol_growth == 0.15