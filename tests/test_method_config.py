import pytest
import math
from core.models import (
    DCFParameters,
    ValuationMode,
    SimpleDCFConfig,
    MonteCarloDCFConfig,
    FundamentalDCFConfig,
    ConfigFactory
)


# --- Fixtures (Données de test réutilisables) ---

def _make_standard_params(**kwargs):
    """Crée un jeu de paramètres standard valide par défaut."""
    defaults = dict(
        risk_free_rate=0.03,  # 3%
        market_risk_premium=0.06,  # 6%
        cost_of_debt=0.04,  # 4%
        tax_rate=0.25,  # 25%
        fcf_growth_rate=0.05,  # 5%
        perpetual_growth_rate=0.02,  # 2% (g < WACC)
        projection_years=5,
        target_equity_weight=0.80,  # 80% Equity
        target_debt_weight=0.20,  # 20% Dette
        # Volatilités nulles par défaut
        beta_volatility=0.0,
        growth_volatility=0.0,
        terminal_growth_volatility=0.0
    )
    defaults.update(kwargs)
    return DCFParameters(**defaults)


# --- Tests des Règles Globales (Toutes Méthodes) ---

def test_global_constraint_wacc_vs_growth_crash():
    """
    Doit lever une erreur si la croissance terminale (g) est supérieure au WACC.
    C'est la règle d'or de Gordon Shapiro : le modèle explose mathématiquement.
    """
    # WACC approx : 0.8*(3%+6%) + 0.2*(4%*(1-25%)) = 0.8*9% + 0.2*3% = 7.2% + 0.6% = 7.8%
    # Si on met g_perp à 8%, ça doit casser.
    params = _make_standard_params(perpetual_growth_rate=0.08)

    config = SimpleDCFConfig(ValuationMode.SIMPLE_FCFF, params)

    # On simule un Beta de 1.0
    with pytest.raises(ValueError, match="WACC estimé"):
        config.validate(context_beta=1.0)


def test_global_constraint_weights_sum_crash():
    """
    Doit lever une erreur si la somme des poids Equity + Dette != 100%.
    """
    params = _make_standard_params(
        target_equity_weight=0.50,
        target_debt_weight=0.20
    )  # Somme = 70%

    config = SimpleDCFConfig(ValuationMode.SIMPLE_FCFF, params)

    with pytest.raises(ValueError, match="doit être égale à 100%"):
        config.validate(context_beta=1.0)


def test_global_constraint_valid_configuration():
    """
    Une configuration saine ne doit lever aucune erreur.
    """
    params = _make_standard_params()  # Tout est par défaut (g=2%, WACC~7.8%)
    config = SimpleDCFConfig(ValuationMode.SIMPLE_FCFF, params)

    # Ne doit pas lever d'exception
    config.validate(context_beta=1.0)


# --- Tests Spécifiques Monte Carlo ---

def test_monte_carlo_volatility_crash_if_negative():
    """
    Les volatilités ne peuvent pas être négatives.
    """
    params = _make_standard_params(beta_volatility=-0.1)
    config = MonteCarloDCFConfig(ValuationMode.MONTE_CARLO, params)

    with pytest.raises(ValueError, match="négatives"):
        config.validate(context_beta=1.0)


def test_monte_carlo_volatility_crash_if_excessive():
    """
    Si la volatilité est absurde (>50%), on arrête pour éviter des résultats incohérents.
    """
    params = _make_standard_params(growth_volatility=0.60)
    config = MonteCarloDCFConfig(ValuationMode.MONTE_CARLO, params)

    with pytest.raises(ValueError, match="excessive"):
        config.validate(context_beta=1.0)


# --- Test Factory ---

def test_factory_dispatch_correct_class():
    """
    La factory doit instancier la bonne classe de config selon l'Enum.
    """
    params = _make_standard_params()

    # Test Simple
    config_simple = ConfigFactory.get_config(ValuationMode.SIMPLE_FCFF, params)
    assert isinstance(config_simple, SimpleDCFConfig)

    # Test Fondamental
    config_fund = ConfigFactory.get_config(ValuationMode.FUNDAMENTAL_FCFF, params)
    assert isinstance(config_fund, FundamentalDCFConfig)

    # Test Monte Carlo
    config_mc = ConfigFactory.get_config(ValuationMode.MONTE_CARLO, params)
    assert isinstance(config_mc, MonteCarloDCFConfig)