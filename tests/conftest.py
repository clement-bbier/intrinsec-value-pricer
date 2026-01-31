"""
tests/conftest.py
Fixtures partagées pour toute la suite de tests.

Ces fixtures fournissent des données de test réutilisables.
Elles sont automatiquement disponibles dans tous les fichiers de test.
"""

import pytest
from src.models import (
    CompanyFinancials,
    Parameters,
    CoreRateParameters,
    GrowthParameters,
    MonteCarloParameters,
    ValuationMode,
    InputSource,
    ValuationRequest,
    SOTPParameters,
    ScenarioParameters,
)
import streamlit as st

st.cache_data = lambda **kwargs: lambda f: f
st.cache_resource = lambda **kwargs: lambda f: f

# =============================================================================
# FIXTURES DE DONNÉES FINANCIÈRES
# =============================================================================

@pytest.fixture
def sample_financials():
    """
    Fixture de données financières complètes pour les tests.

    Représente une entreprise Tech typique avec :
    - Prix actuel : 100 USD
    - Market Cap : 100M USD
    - FCF : 10M USD (yield 10%)
    - Levier modéré (20M dette)
    """
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
        # Champs optionnels pour tests Graham/DDM/RIM
        # Note: Noms de champs selon le modèle réel
        eps_ttm=5.0,
        book_value_per_share=30.0,
        dividend_share=2.0,  # Pas dividend_per_share
        revenue_ttm=100_000_000,
        net_income_ttm=15_000_000,
    )


@pytest.fixture
def sample_financials_minimal():
    """Fixture avec le minimum de données requis."""
    return CompanyFinancials(
        ticker="MIN",
        currency="USD",
        current_price=50.0,
        shares_outstanding=500_000,
    )


@pytest.fixture
def sample_financials_bank():
    """Fixture pour tests de valorisation bancaire (RIM)."""
    return CompanyFinancials(
        ticker="BANK",
        currency="USD",
        sector="Financial Services",
        industry="Banks",
        country="United States",
        current_price=45.0,
        shares_outstanding=2_000_000,
        total_debt=0,  # Les banques ont une structure différente
        cash_and_equivalents=100_000_000,
        beta=1.1,
        eps_ttm=4.5,
        book_value_per_share=40.0,
        net_income_ttm=9_000_000,
    )


# =============================================================================
# FIXTURES DE PARAMÈTRES
# =============================================================================

@pytest.fixture
def sample_params():
    """
    Fixture de paramètres DCF standard.

    Architecture segmentée V9.0+ avec :
    - Rf = 4%, MRP = 5% → Ke ≈ 10%
    - Croissance FCF = 5%, g terminal = 2%
    - Monte Carlo désactivé
    """
    return Parameters(
        rates=CoreRateParameters(
            risk_free_rate=0.04,
            market_risk_premium=0.05,
            cost_of_debt=0.06,
            tax_rate=0.25
        ),
        growth=GrowthParameters(
            fcf_growth_rate=0.05,
            perpetual_growth_rate=0.02,
            projection_years=5,
            annual_dilution_rate=0.02
        ),
        monte_carlo=MonteCarloParameters(
            enabled=False
        ),
        sotp=SOTPParameters(enabled=False),
        scenarios=ScenarioParameters(enabled=False),
    )


@pytest.fixture
def sample_params_monte_carlo():
    """Fixture avec Monte Carlo activé (petit échantillon pour tests)."""
    return Parameters(
        rates=CoreRateParameters(
            risk_free_rate=0.04,
            market_risk_premium=0.05,
        ),
        growth=GrowthParameters(
            fcf_growth_rate=0.05,
            perpetual_growth_rate=0.02,
            projection_years=5,
        ),
        monte_carlo=MonteCarloParameters(
            enabled=True,
            num_simulations=100,  # Petit pour tests rapides
        ),
        sotp=SOTPParameters(enabled=False),
        scenarios=ScenarioParameters(enabled=False),
    )


@pytest.fixture
def sample_params_pessimistic():
    """Fixture de paramètres pessimistes."""
    return Parameters(
        rates=CoreRateParameters(
            risk_free_rate=0.05,
            market_risk_premium=0.07,  # MRP élevé
            cost_of_debt=0.08,
            tax_rate=0.30,
        ),
        growth=GrowthParameters(
            fcf_growth_rate=0.02,  # Croissance faible
            perpetual_growth_rate=0.01,
            projection_years=5,
        ),
        monte_carlo=MonteCarloParameters(enabled=False),
        sotp=SOTPParameters(enabled=False),
        scenarios=ScenarioParameters(enabled=False),
    )


# =============================================================================
# FIXTURES DE REQUÊTES
# =============================================================================

@pytest.fixture
def sample_request_auto(sample_params):
    """Requête de valorisation mode Auto."""
    return ValuationRequest(
        ticker="TEST",
        projection_years=5,
        mode=ValuationMode.FCFF_STANDARD,
        input_source=InputSource.AUTO,
        manual_params=sample_params,
    )


@pytest.fixture
def sample_request_expert(sample_params):
    """Requête de valorisation mode Expert."""
    return ValuationRequest(
        ticker="TEST",
        projection_years=5,
        mode=ValuationMode.FCFF_STANDARD,
        input_source=InputSource.MANUAL,
        manual_params=sample_params,
    )


# =============================================================================
# FIXTURES UTILITAIRES
# =============================================================================

@pytest.fixture
def all_valuation_modes():
    """Liste de tous les modes de valorisation."""
    return list(ValuationMode)


@pytest.fixture
def dcf_modes():
    """Modes DCF uniquement."""
    return [
        ValuationMode.FCFF_STANDARD,
        ValuationMode.FCFF_NORMALIZED,
        ValuationMode.FCFF_GROWTH,
    ]
