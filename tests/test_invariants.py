import pytest
from core.exceptions import CalculationError
# CORRECTION : On pointe vers le nouveau module
from core.computation.financial_math import calculate_terminal_value_gordon, calculate_wacc
from src.domain.models import CompanyFinancials, DCFParameters

def test_invariant_wacc_gt_growth():
    """
    Règle d'Or : Le WACC doit être strictement supérieur à la croissance terminale (g).
    Sinon, la valeur terminale est mathématiquement infinie ou négative (Gordon Shapiro).
    """
    wacc = 0.03
    g = 0.03  # WACC = g -> Division par zéro
    fcf = 100

    with pytest.raises(CalculationError, match="Convergence impossible"):
        # Note : Le nom de la fonction a changé pour être plus précis
        calculate_terminal_value_gordon(fcf, wacc, g)

    # Cas g > WACC -> Valeur négative absurde pour une entreprise en croissance
    with pytest.raises(CalculationError):
        calculate_terminal_value_gordon(fcf, 0.02, 0.03)


def test_wacc_calculation_coherence(sample_financials, sample_params):
    """
    Le WACC calculé doit toujours être positif et les poids normalisés à 100%.
    """
    # Note : Le nom de la fonction a changé
    ctx = calculate_wacc(sample_financials, sample_params)

    assert ctx.wacc > 0, "Le WACC ne peut pas être négatif ou nul"
    assert 0 <= ctx.weight_equity <= 1
    assert 0 <= ctx.weight_debt <= 1
    # La somme doit faire 1.0 (à epsilon près)
    assert abs((ctx.weight_equity + ctx.weight_debt) - 1.0) < 0.001


def test_manual_zero_sovereignty(sample_financials, sample_params):
    """
    Vérifie que le 0.0 manuel écrase la valeur automatique (Yahoo).
    
    Architecture V9.0 : Les surcharges manuelles sont dans sample_params.growth
    (ex: manual_total_debt, manual_cash, etc.)
    """
    sample_financials.total_debt = 5_000_000  # Yahoo dit 5M
    sample_params.growth.manual_total_debt = 0.0  # L'expert dit 0

    ctx = calculate_wacc(sample_financials, sample_params)

    # Si le patch fonctionne, wd (weight of debt) doit être exactement 0
    assert ctx.weight_debt == 0.0
    # Note: La methode retournee contient "Marche" ou "Marché" selon l'encodage
    assert "Marche" in ctx.method or "Marché" in ctx.method or ctx.method == "MARKET"
