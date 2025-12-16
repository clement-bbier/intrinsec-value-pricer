import pytest
from core.valuation.strategies.dcf_standard import SimpleFCFFStrategy
from core.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy
from core.valuation.strategies.monte_carlo import MonteCarloDCFStrategy
from core.exceptions import CalculationError


def test_simple_strategy_execution(sample_financials, sample_params):
    """Vérifie que la stratégie Simple s'exécute et produit un résultat cohérent."""
    strategy = SimpleFCFFStrategy()
    result = strategy.execute(sample_financials, sample_params)

    assert result.intrinsic_value_per_share > 0
    assert len(result.projected_fcfs) == sample_params.projection_years
    # Le WACC doit être cohérent avec les inputs (ex: ~8-9% avec les params par défaut)
    assert 0.05 < result.wacc < 0.15


def test_fundamental_strategy_missing_data(sample_financials, sample_params):
    """La stratégie Fondamentale doit échouer proprement si le FCF lissé manque."""
    sample_financials.fcf_fundamental_smoothed = None
    strategy = FundamentalFCFFStrategy()

    with pytest.raises(CalculationError, match="Donnée manquante"):
        strategy.execute(sample_financials, sample_params)


def test_monte_carlo_strategy_structure(sample_financials, sample_params):
    """Vérifie que Monte Carlo retourne bien une distribution et des quantiles."""
    # Setup volatilités pour MC
    sample_params.beta_volatility = 0.10
    sample_params.growth_volatility = 0.02
    # On force un petit nombre de sims pour que le test soit rapide
    sample_params.num_simulations = 50

    strategy = MonteCarloDCFStrategy()
    result = strategy.execute(sample_financials, sample_params)

    assert result.simulation_results is not None
    assert len(result.simulation_results) <= 50
    assert result.quantiles is not None
    assert "P50" in result.quantiles
    assert result.quantiles["P10"] <= result.quantiles["P90"]