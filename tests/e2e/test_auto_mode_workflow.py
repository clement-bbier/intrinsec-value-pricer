"""
tests/e2e/test_auto_mode_workflow.py
Tests End-to-End — Workflow Mode Auto

Ces tests simulent le parcours complet d'un utilisateur en mode Auto.
Ils ne font PAS d'appels réseau réels (mockés).
"""

import pytest
from unittest.mock import patch, MagicMock


class TestAutoModeWorkflow:
    """Tests du workflow Auto complet."""
    
    def test_complete_auto_workflow_mocked(self, sample_financials, sample_params):
        """Workflow Auto complet avec données mockées."""
        from core.valuation.engines import run_valuation
        from core.models import (
            ValuationRequest, ValuationMode, InputSource, 
            DCFParameters, CoreRateParameters, GrowthParameters, MonteCarloConfig
        )
        
        # Simuler une requête utilisateur Auto
        request = ValuationRequest(
            ticker="AAPL",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
            manual_params=sample_params,
        )
        
        # Exécuter le workflow
        result = run_valuation(request, sample_financials, sample_params)
        
        # Vérifications utilisateur (upside_pct remplace margin_of_safety)
        assert result.intrinsic_value_per_share > 0, "Valeur intrinsèque invalide"
        assert result.upside_pct is not None, "Upside manquant"
        assert result.audit_report is not None, "Rapport d'audit manquant"
        assert result.audit_report.rating is not None, "Rating manquant"
    
    def test_workflow_handles_different_modes(self, sample_financials, sample_params):
        """Le workflow gère tous les modes de valorisation."""
        from core.valuation.engines import run_valuation
        from core.models import ValuationRequest, ValuationMode, InputSource
        
        # Préparer données supplémentaires
        sample_financials.eps_ttm = 5.0
        sample_financials.book_value_per_share = 30.0
        
        modes = [
            ValuationMode.FCFF_STANDARD,
            ValuationMode.FCFF_NORMALIZED,
            ValuationMode.GRAHAM,
        ]
        
        for mode in modes:
            request = ValuationRequest(
                ticker="TEST",
                projection_years=5,
                mode=mode,
                input_source=InputSource.AUTO,
            )
            
            result = run_valuation(request, sample_financials, sample_params)
            
            assert result is not None, f"{mode}: Résultat None"
            assert result.intrinsic_value_per_share > 0, f"{mode}: IV <= 0"


class TestAutoModeOutputValidation:
    """Tests de validation des sorties mode Auto."""
    
    def test_output_has_all_required_fields(self, sample_financials, sample_params):
        """La sortie contient tous les champs requis pour l'affichage."""
        from core.valuation.engines import run_valuation
        from core.models import ValuationRequest, ValuationMode, InputSource
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
        )
        
        result = run_valuation(request, sample_financials, sample_params)
        
        # Champs requis pour l'UI (API réelle)
        assert hasattr(result, "intrinsic_value_per_share")
        assert hasattr(result, "upside_pct")  # Pas margin_of_safety
        assert hasattr(result, "calculation_trace")  # Pas model_name
        assert hasattr(result, "audit_report")
        
        # Le rapport d'audit a ses champs
        assert hasattr(result.audit_report, "global_score")
        assert hasattr(result.audit_report, "rating")
    
    def test_output_values_are_reasonable(self, sample_financials, sample_params):
        """Les valeurs de sortie sont dans des plages raisonnables."""
        from core.valuation.engines import run_valuation
        from core.models import ValuationRequest, ValuationMode, InputSource
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
        )
        
        result = run_valuation(request, sample_financials, sample_params)
        
        # Valeur intrinsèque positive et pas astronomique
        assert result.intrinsic_value_per_share > 0
        assert result.intrinsic_value_per_share < 1_000_000  # Sanity check
        
        # Upside entre -90% et +1000% (plage large mais réaliste)
        assert result.upside_pct is not None
        assert -0.9 <= result.upside_pct <= 10.0
        
        # Score d'audit entre 0 et 100
        assert 0 <= result.audit_report.global_score <= 100


class TestAutoModeErrorHandling:
    """Tests de gestion des erreurs mode Auto."""
    
    def test_invalid_ticker_format_handled(self):
        """Format de ticker invalide est géré."""
        from core.models import ValuationRequest, ValuationMode, InputSource
        
        # Un ticker vide devrait être accepté par le modèle
        # mais la validation métier devrait se faire ailleurs
        request = ValuationRequest(
            ticker="",  # Vide mais accepté par Pydantic
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
        )
        
        assert request.ticker == ""
    
    def test_extreme_parameters_handled(self, sample_financials, sample_params):
        """Paramètres extrêmes sont gérés sans crash."""
        from core.valuation.engines import run_valuation
        from core.models import ValuationRequest, ValuationMode, InputSource
        from core.exceptions import CalculationError, ValuationException
        
        # Paramètres extrêmes mais valides
        sample_params.growth.perpetual_growth_rate = 0.001  # Très faible
        sample_params.rates.risk_free_rate = 0.15  # Très élevé
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
        )
        
        # Ne doit pas planter (peut lever une exception métier)
        try:
            result = run_valuation(request, sample_financials, sample_params)
            assert result is not None
        except (CalculationError, ValuationException):
            # Exception métier attendue avec paramètres extrêmes
            pass
