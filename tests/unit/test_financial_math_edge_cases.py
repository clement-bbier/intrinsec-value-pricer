import pytest
from src.computation.financial_math import (
    calculate_discount_factors,
    calculate_npv,
    calculate_terminal_value_gordon,
    calculate_terminal_value_exit_multiple,
    calculate_terminal_value_pe,
    unlever_beta,
    relever_beta,
    calculate_cost_of_equity,
    calculate_synthetic_cost_of_debt,
    calculate_wacc,
    calculate_fcfe_reconstruction,
    calculate_fcfe_base,
    calculate_sustainable_growth,
    calculate_graham_1974_value,
    compute_proportions,
    calculate_price_from_pe_multiple,
    calculate_price_from_ev_multiple,
    calculate_triangulated_price
)
from src.exceptions import CalculationError


# ==============================================================================
# 1. TESTS TIME VALUE OF MONEY & TV (Lignes 60-90)
# ==============================================================================

class TestTVMAndTerminalValue:
    def test_discount_factors_errors(self):
        with pytest.raises(CalculationError):
            calculate_discount_factors(-1.5, 5) # Taux <= -1.0
            
    def test_npv_empty(self):
        assert calculate_npv([], 0.1) == 0.0

    def test_gordon_convergence_error(self):
        with pytest.raises(CalculationError):
            calculate_terminal_value_gordon(100, 0.02, 0.03) # rate <= g_perp

    def test_exit_multiple_errors(self):
        with pytest.raises(CalculationError):
            calculate_terminal_value_exit_multiple(100, -1) # multiple < 0
        with pytest.raises(CalculationError):
            calculate_terminal_value_pe(100, 0) # multiple <= 0

# ==============================================================================
# 2. TESTS BÊTA & CAPM (Lignes 100-150)
# ==============================================================================

class TestBetaAndEquityCost:
    def test_unlever_relever_zero_debt(self):
        # Cas où le ratio D/E est nul (Ligne 116 & 126)
        assert unlever_beta(1.2, 0.25, 0.0) == 1.2
        assert relever_beta(1.0, 0.25, 0.0) == 1.0

    def test_calculate_cost_of_equity_fallbacks(self, sample_financials, sample_params):
        # Test des fallbacks None (Rf=0.04, MRP=0.05, Beta=1.0)
        sample_params.rates.risk_free_rate = None
        sample_params.rates.market_risk_premium = None
        sample_params.rates.manual_beta = None
        sample_financials.beta = None 
        # Ke = 0.04 + (1.0 * 0.05) = 0.09
        assert calculate_cost_of_equity(sample_financials, sample_params) == 0.09
        
        # Test override manuel (Ligne 138)
        sample_params.rates.manual_cost_of_equity = 0.12
        assert calculate_cost_of_equity(sample_financials, sample_params) == 0.12

# ==============================================================================
# 3. TESTS SYNTHETIC DEBT & WACC (Lignes 150-210) - LES PLUS CRITIQUES
# ==============================================================================

class TestDebtAndWACC:
    def test_synthetic_cost_of_debt_edge_cases(self):
        # EBIT ou Intérêts <= 0 (Ligne 155)
        assert calculate_synthetic_cost_of_debt(0.04, 0, 100, 1e9) == 0.04 + 0.0107
        
        # Test Large Cap vs Small Cap thresholds (Lignes 160-165)
        # Très haut ICR (AAA)
        kd_aaa = calculate_synthetic_cost_of_debt(0.04, 1000, 1, 10e12) 
        assert kd_aaa < 0.05
        
        # Très bas ICR (D-rated / Fallback 0.1900)
        kd_bad = calculate_synthetic_cost_of_debt(0.04, 1, 1000, 1e6)
        assert kd_bad == 0.04 + 0.1900

    def test_wacc_complex_scenarios(self, sample_financials, sample_params):
        # 1. Cas Capitalisation totale nulle (Ligne 185)
        sample_financials.current_price = 0
        sample_financials.shares_outstanding = 0
        sample_params.growth.manual_total_debt = 0
        breakdown = calculate_wacc(sample_financials, sample_params)
        assert breakdown.weight_equity == 1.0
        
        # 2. Cas réendettement du Bêta (Hamada) (Lignes 193-197)
        sample_financials.current_price = 100
        sample_financials.shares_outstanding = 1e6
        sample_params.growth.target_equity_weight = 0.5
        sample_params.growth.target_debt_weight = 0.5
        breakdown = calculate_wacc(sample_financials, sample_params)
        assert breakdown.beta_adjusted is True
        assert breakdown.beta_used != sample_financials.beta

# ==============================================================================
# 4. TESTS MODÈLES SPÉCIFIQUES (Lignes 220-280)
# ==============================================================================

class TestSpecializedModels:
    def test_fcfe_formulas(self):
        # Reconstruction (Ligne 221)
        assert calculate_fcfe_reconstruction(100, 20, 10) == 130
        # Base (Ligne 225)
        assert calculate_fcfe_base(200, 50, 0.2, 10) == 200 - (50 * 0.8) + 10
        
    def test_sustainable_growth(self):
        # Payout ratio None (Ligne 233)
        assert calculate_sustainable_growth(0.2, None) == 0.2

    def test_graham_aaa_fallback(self):
        # Yield nul ou None (Ligne 240)
        val = calculate_graham_1974_value(5.0, 0.05, 0.0)
        assert val > 0 # Utilise le fallback 4.4%

    def test_compute_proportions_fallback(self):
        # Somme nulle (Ligne 265)
        res = compute_proportions(0, 0, 0, fallback_index=1)
        assert res == [0.0, 1.0, 0.0]

# ==============================================================================
# 5. MULTIPLES & TRIANGULATION (Lignes 280-330)
# ==============================================================================

class TestMultiplesAndTriangulation:
    def test_price_from_multiples_invalid(self):
        # Shares ou multiples <= 0 (Lignes 283, 301)
        assert calculate_price_from_pe_multiple(100, 15, 0) == 0.0
        assert calculate_price_from_ev_multiple(100, -5, 20, 1e6) == 0.0

    def test_triangulation_edge_cases(self):
        signals = {"DCF": 120.0, "Graham": -50.0, "RIM": 0.0}
        # Graham et RIM seront ignorés car <= 0 (Ligne 319)
        assert calculate_triangulated_price(signals) == 120.0
        
        # Poids totaux nuls (Ligne 330)
        weights = {"DCF": 0.0, "Graham": 0.0}
        assert calculate_triangulated_price(signals, weights) == 120.0

        # Pas de signaux valides
        assert calculate_triangulated_price({"A": 0, "B": -1}) == 0.0

def test_financial_math_100_percent_coverage(sample_financials, sample_params):
    from src.computation.financial_math import (
        calculate_terminal_value_pe, calculate_cost_of_equity,
        calculate_fcfe_base, calculate_sustainable_growth,
        calculate_rim_vectors, compute_proportions
    )
    from src.exceptions import CalculationError

    # Ligne 79 & 85 (Exceptions P/E)
    with pytest.raises(CalculationError):
        calculate_terminal_value_pe(100, 0) # Doit être > 0

    # Ligne 138 (Override Ke manuel)
    sample_params.rates.manual_cost_of_equity = 0.15
    assert calculate_cost_of_equity(sample_financials, sample_params) == 0.15

    # Ligne 225 (FCFE Base)
    res_fcfe = calculate_fcfe_base(1000, 100, 0.25, 50)
    assert res_fcfe == 1000 - (100 * 0.75) + 50 # 975

    # Ligne 235 (Sustainable growth payout None)
    assert calculate_sustainable_growth(0.2, None) == 0.2

    # Lignes 252-254 (RIM Vectors loop)
    ri, bv = calculate_rim_vectors(100, 0.1, [20, 30], 0.4)
    assert len(ri) == 2
    assert bv[0] == 100 + 20 - (20 * 0.4) # BV_prev + NI - Div

    # Lignes 280-281 (Proportions fallback)
    assert compute_proportions(0, 0, fallback_index=1) == [0.0, 1.0]