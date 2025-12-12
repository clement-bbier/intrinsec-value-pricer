import pytest
from core.exceptions import CalculationError
from core.computation.discounting import calculate_terminal_value, calculate_wacc_full_context


def test_invariant_wacc_gt_growth():
    """
    Règle d'Or : Le WACC doit être strictement supérieur à la croissance terminale (g).
    Sinon, la valeur terminale est mathématiquement infinie ou négative (Gordon Shapiro).
    """
    wacc = 0.03
    g = 0.03  # WACC = g -> Division par zéro
    fcf = 100

    with pytest.raises(CalculationError, match="Convergence impossible"):
        calculate_terminal_value(fcf, wacc, g)

    # Cas g > WACC -> Valeur négative absurde pour une entreprise en croissance
    with pytest.raises(CalculationError):
        calculate_terminal_value(fcf, 0.02, 0.03)


def test_wacc_calculation_coherence(sample_financials, sample_params):
    """
    Le WACC calculé doit toujours être positif et les poids normalisés à 100%.
    """
    ctx = calculate_wacc_full_context(sample_financials, sample_params)

    assert ctx.wacc > 0, "Le WACC ne peut pas être négatif ou nul"
    assert 0 <= ctx.weight_equity <= 1
    assert 0 <= ctx.weight_debt <= 1
    # La somme des poids doit être 1.0 (à epsilon près)
    assert abs(ctx.weight_equity + ctx.weight_debt - 1.0) < 1e-5