"""
tests/contracts/test_models_contracts.py
Tests de Contrats — Modèles Pydantic

Ces tests garantissent que les schémas de données restent stables.
Si un champ obligatoire est supprimé ou renommé, ces tests échoueront.

RÈGLE D'OR : Ces tests NE DOIVENT PAS CHANGER lors des refactorings.
"""

import pytest
from pydantic import ValidationError


class TestCompanyFinancialsContract:
    """Contrat de stabilité pour CompanyFinancials."""
    
    def test_required_fields_exist(self):
        """Vérifie que les champs obligatoires existent."""
        from core.models import CompanyFinancials
        
        # Ces champs DOIVENT exister et être obligatoires
        required_fields = [
            "ticker",
            "currency", 
            "current_price",
            "shares_outstanding",
        ]
        
        schema = CompanyFinancials.model_json_schema()
        properties = schema.get("properties", {})
        
        for field in required_fields:
            assert field in properties, f"Champ obligatoire '{field}' manquant"
    
    def test_minimal_instantiation(self):
        """Vérifie qu'on peut créer une instance avec les champs minimaux."""
        from core.models import CompanyFinancials
        
        # Doit fonctionner avec les champs minimaux
        financials = CompanyFinancials(
            ticker="TEST",
            currency="USD",
            current_price=100.0,
            shares_outstanding=1_000_000,
        )
        
        assert financials.ticker == "TEST"
        assert financials.current_price == 100.0


class TestDCFParametersContract:
    """Contrat de stabilité pour DCFParameters."""
    
    def test_segmented_architecture(self):
        """Vérifie l'architecture segmentée V9.0+ (rates, growth, monte_carlo)."""
        from core.models import DCFParameters
        
        schema = DCFParameters.model_json_schema()
        properties = schema.get("properties", {})
        
        # L'architecture segmentée DOIT être respectée
        assert "rates" in properties, "Segment 'rates' manquant"
        assert "growth" in properties, "Segment 'growth' manquant"
        assert "monte_carlo" in properties, "Segment 'monte_carlo' manquant"
    
    def test_default_instantiation(self):
        """Vérifie qu'on peut créer une instance avec les défauts."""
        from core.models import DCFParameters, CoreRateParameters, GrowthParameters, MonteCarloConfig
        
        params = DCFParameters(
            rates=CoreRateParameters(),
            growth=GrowthParameters(),
            monte_carlo=MonteCarloConfig(),
        )
        
        assert params.rates is not None
        assert params.growth is not None
        assert params.monte_carlo is not None


class TestValuationResultContract:
    """Contrat de stabilité pour ValuationResult."""
    
    def test_core_output_fields(self):
        """Vérifie que les champs de sortie principaux existent."""
        from core.models import DCFValuationResult
        
        schema = DCFValuationResult.model_json_schema()
        properties = schema.get("properties", {})
        
        # Ces champs DOIVENT exister dans tout résultat de valorisation
        # Note: upside_pct remplace margin_of_safety, calculation_trace existe
        core_fields = [
            "intrinsic_value_per_share",
            "upside_pct",
            "calculation_trace",
        ]
        
        for field in core_fields:
            assert field in properties, f"Champ de sortie '{field}' manquant"


class TestValuationRequestContract:
    """Contrat de stabilité pour ValuationRequest."""
    
    def test_request_fields(self):
        """Vérifie les champs de requête."""
        from core.models import ValuationRequest, ValuationMode, InputSource
        
        request = ValuationRequest(
            ticker="AAPL",
            projection_years=5,
            mode=ValuationMode.FCFF_TWO_STAGE,
            input_source=InputSource.AUTO,
        )
        
        assert request.ticker == "AAPL"
        assert request.projection_years == 5
        assert request.mode == ValuationMode.FCFF_TWO_STAGE


class TestValuationModeContract:
    """Contrat de stabilité pour ValuationMode enum."""
    
    def test_all_modes_exist(self):
        """Vérifie que tous les modes de valorisation existent."""
        from core.models import ValuationMode
        
        # Ces modes DOIVENT exister
        expected_modes = [
            "FCFF_TWO_STAGE",
            "FCFF_NORMALIZED",
            "FCFF_REVENUE_DRIVEN",
            "FCFE_TWO_STAGE",
            "DDM_GORDON_GROWTH",
            "RESIDUAL_INCOME_MODEL",
            "GRAHAM_1974_REVISED",
        ]
        
        actual_modes = [m.name for m in ValuationMode]
        
        for mode in expected_modes:
            assert mode in actual_modes, f"Mode '{mode}' manquant dans ValuationMode"
    
    def test_monte_carlo_support_property(self):
        """Vérifie que la propriété supports_monte_carlo existe."""
        from core.models import ValuationMode
        
        # Cette propriété DOIT exister sur chaque mode
        for mode in ValuationMode:
            assert hasattr(mode, "supports_monte_carlo"), f"{mode} n'a pas supports_monte_carlo"


class TestAuditReportContract:
    """Contrat de stabilité pour AuditReport."""
    
    def test_audit_output_fields(self):
        """Vérifie les champs de sortie d'audit."""
        from core.models import AuditReport
        
        schema = AuditReport.model_json_schema()
        properties = schema.get("properties", {})
        
        # Ces champs DOIVENT exister
        required_fields = [
            "global_score",
            "rating",
            "audit_depth",
        ]
        
        for field in required_fields:
            assert field in properties, f"Champ d'audit '{field}' manquant"
