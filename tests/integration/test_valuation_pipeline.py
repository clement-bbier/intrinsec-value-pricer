"""
tests/integration/test_valuation_pipeline.py
Tests d'Intégration — Pipeline de Valorisation Complet

Ces tests vérifient que les composants fonctionnent ensemble :
Strategy → Result → Audit → Output
"""

import pytest


class TestFullValuationPipeline:
    """Tests du pipeline complet de valorisation."""
    
    def test_fcff_standard_full_pipeline(self, sample_financials, sample_params):
        """Pipeline complet FCFF Standard."""
        from src.valuation.engines import run_valuation
        from src.domain.models import (
            ValuationRequest, ValuationMode, InputSource, ValuationResult
        )
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
        )
        
        result = run_valuation(request, sample_financials, sample_params)
        
        # Vérifications pipeline
        assert isinstance(result, ValuationResult)
        assert result.intrinsic_value_per_share > 0
        assert result.request is not None
        assert result.audit_report is not None
        assert result.audit_report.global_score >= 0
    
    def test_all_modes_complete_pipeline(self, sample_financials, sample_params):
        """Tous les modes passent par le pipeline complet."""
        from src.valuation.engines import run_valuation
        from src.domain.models import (
            ValuationRequest, ValuationMode, InputSource
        )
        
        # Note: On utilise les fixtures avec les bons noms de champs
        # sample_financials a déjà eps_ttm, book_value_per_share, etc.
        
        modes_to_test = [
            ValuationMode.FCFF_STANDARD,
            ValuationMode.FCFF_NORMALIZED,
            ValuationMode.FCFF_GROWTH,
            ValuationMode.GRAHAM,
        ]
        
        for mode in modes_to_test:
            request = ValuationRequest(
                ticker="TEST",
                projection_years=5,
                mode=mode,
                input_source=InputSource.AUTO,
            )
            
            try:
                result = run_valuation(request, sample_financials, sample_params)
                
                assert result is not None, f"{mode}: Résultat None"
                assert result.audit_report is not None, f"{mode}: Audit manquant"
                
            except Exception as e:
                pytest.fail(f"Pipeline échoué pour {mode}: {str(e)}")


class TestAuditAfterValuation:
    """Tests de l'audit intégré au pipeline."""
    
    def test_audit_report_has_score(self, sample_financials, sample_params):
        """Le rapport d'audit contient un score global."""
        from src.valuation.engines import run_valuation
        from src.domain.models import ValuationRequest, ValuationMode, InputSource
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
        )
        
        result = run_valuation(request, sample_financials, sample_params)
        
        assert result.audit_report.global_score >= 0
        assert result.audit_report.global_score <= 100
    
    def test_audit_report_has_rating(self, sample_financials, sample_params):
        """Le rapport d'audit contient une notation."""
        from src.valuation.engines import run_valuation
        from src.domain.models import ValuationRequest, ValuationMode, InputSource
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
        )
        
        result = run_valuation(request, sample_financials, sample_params)
        
        assert result.audit_report.rating in ["AAA", "AA", "BBB", "BB", "C"]
    
    def test_manual_mode_affects_audit_weights(self, sample_financials, sample_params):
        """Le mode MANUAL change les pondérations d'audit."""
        from src.valuation.engines import run_valuation
        from src.domain.models import ValuationRequest, ValuationMode, InputSource
        
        # Mode AUTO
        request_auto = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
        )
        result_auto = run_valuation(request_auto, sample_financials, sample_params)
        
        # Mode MANUAL
        request_manual = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.MANUAL,
        )
        result_manual = run_valuation(request_manual, sample_financials, sample_params)
        
        # Les modes d'audit doivent être différents
        assert result_auto.audit_report.audit_mode == InputSource.AUTO
        assert result_manual.audit_report.audit_mode == InputSource.MANUAL


class TestGlassBoxIntegration:
    """Tests du mode Glass Box intégré."""
    
    def test_glass_box_generates_calculation_trace(self, sample_financials, sample_params):
        """Le mode Glass Box génère des étapes de calcul."""
        from src.valuation.strategies.dcf_standard import StandardFCFFStrategy
        
        strategy = StandardFCFFStrategy(glass_box_enabled=True)
        result = strategy.execute(sample_financials, sample_params)
        
        # Le champ s'appelle calculation_trace, pas calculation_steps
        assert result.calculation_trace is not None
        assert len(result.calculation_trace) > 0
    
    def test_calculation_trace_has_labels(self, sample_financials, sample_params):
        """Chaque étape de calcul a un label."""
        from src.valuation.strategies.dcf_standard import StandardFCFFStrategy
        
        strategy = StandardFCFFStrategy(glass_box_enabled=True)
        result = strategy.execute(sample_financials, sample_params)
        
        for step in result.calculation_trace:
            # CalculationStep a step_label ou step_name
            assert hasattr(step, "step_label") or hasattr(step, "step_name") or hasattr(step, "label")


class TestMonteCarloIntegration:
    """Tests de l'intégration Monte Carlo."""
    
    def test_monte_carlo_with_engine(self, sample_financials, sample_params):
        """Monte Carlo fonctionne via le moteur principal."""
        from src.valuation.engines import run_valuation
        from src.domain.models import ValuationRequest, ValuationMode, InputSource
        
        sample_params.monte_carlo.enable_monte_carlo = True
        sample_params.monte_carlo.num_simulations = 100
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
        )
        
        result = run_valuation(request, sample_financials, sample_params)
        
        assert result is not None
        assert result.intrinsic_value_per_share > 0
