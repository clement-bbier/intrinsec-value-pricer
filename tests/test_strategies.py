import pytest
from src.valuation.strategies.standard_fcff import StandardFCFFStrategy
from src.valuation.strategies.fundamental_fcff import FundamentalFCFFStrategy
from src.valuation.strategies.monte_carlo import MonteCarloGenericStrategy
from src.exceptions import CalculationError
from src.i18n import CalculationErrors

def test_standard_strategy_execution(sample_financials, sample_params):
    """Vérifie que la stratégie Standard s'exécute avec les segments V9."""
    # sample_params est supposé être un objet DCFParameters segmenté
    strategy = StandardFCFFStrategy()
    result = strategy.execute(sample_financials, sample_params)

    assert result.intrinsic_value_per_share > 0
    # Accès via le segment growth
    assert len(result.projected_fcfs) == sample_params.growth.projection_years
    # Le WACC doit être cohérent (~8-9% par défaut)
    assert 0.05 < result.wacc < 0.15


def test_fundamental_strategy_missing_data(sample_financials, sample_params):
    """La stratégie Fondamentale doit échouer proprement si le FCF lissé manque."""
    sample_financials.fcf_fundamental_smoothed = None
    strategy = FundamentalFCFFStrategy()

    # Utilisation de la constante i18n pour le matching d'erreur
    expected_error = CalculationErrors.MISSING_FCF_NORM.split("(")[0] # On match le début du message
    with pytest.raises(CalculationError, match=expected_error):
        strategy.execute(sample_financials, sample_params)


def test_monte_carlo_strategy_structure(sample_financials, sample_params):
    """Vérifie que Monte Carlo utilise le segment monte_carlo et retourne des quantiles."""
    # Setup via le segment monte_carlo
    mc = sample_params.monte_carlo
    mc.enable_monte_carlo = True
    mc.beta_volatility = 0.10
    mc.growth_volatility = 0.02
    mc.num_simulations = 50 # Simulations réduites pour le test

    # Utilisation du wrapper générique mis à jour
    strategy = MonteCarloGenericStrategy(strategy_cls=StandardFCFFStrategy)
    result = strategy.execute(sample_financials, sample_params)

    assert result.simulation_results is not None
    assert len(result.simulation_results) <= 50
    assert result.quantiles is not None
    assert "P50" in result.quantiles
    assert result.quantiles["P10"] <= result.quantiles["P90"]
