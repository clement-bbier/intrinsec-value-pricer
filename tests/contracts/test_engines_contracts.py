"""
tests/contracts/test_engines_contracts.py
Tests de Contrats — API du Moteur de Valorisation

Ces tests garantissent que l'API publique de run_valuation() reste stable.
Même après refactoring interne, ces signatures DOIVENT rester compatibles.

RÈGLE D'OR : Ces tests NE DOIVENT PAS CHANGER lors des refactorings.
"""

from inspect import signature


class TestRunValuationContract:
    """Contrat de stabilité pour run_valuation()."""
    
    def test_function_exists(self):
        """Vérifie que run_valuation est importable."""
        from src.valuation.engines import run_valuation
        
        assert callable(run_valuation)
    
    def test_signature_parameters(self):
        """Vérifie la signature de run_valuation."""
        from src.valuation.engines import run_valuation
        
        sig = signature(run_valuation)
        params = list(sig.parameters.keys())
        
        # Ces paramètres DOIVENT exister dans cet ordre
        assert "request" in params, "Paramètre 'request' manquant"
        assert "financials" in params, "Paramètre 'financials' manquant"
        assert "params" in params, "Paramètre 'params' manquant"
    
    def test_return_type_is_valuation_result(self, sample_financials, sample_params):
        """Vérifie que run_valuation retourne un ValuationResult."""
        from src.valuation.engines import run_valuation
        from src.models import ValuationRequest, ValuationMode, InputSource, ValuationResult
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
        )
        
        result = run_valuation(request, sample_financials, sample_params)
        
        assert isinstance(result, ValuationResult)
        assert result.intrinsic_value_per_share > 0
        assert result.audit_report is not None


class TestStrategyRegistryContract:
    """Contrat de stabilité pour STRATEGY_REGISTRY."""
    
    def test_registry_exists(self):
        """Vérifie que STRATEGY_REGISTRY est accessible."""
        from src.valuation.engines import STRATEGY_REGISTRY
        
        assert isinstance(STRATEGY_REGISTRY, dict)
        assert len(STRATEGY_REGISTRY) >= 7, "Moins de 7 stratégies enregistrées"
    
    def test_all_modes_have_strategies(self):
        """Vérifie que tous les modes ont une stratégie."""
        from src.valuation.engines import STRATEGY_REGISTRY
        from src.models import ValuationMode
        
        expected_modes = [
            ValuationMode.FCFF_STANDARD,
            ValuationMode.FCFF_NORMALIZED,
            ValuationMode.FCFF_GROWTH,
            ValuationMode.FCFE,
            ValuationMode.DDM,
            ValuationMode.RIM,
            ValuationMode.GRAHAM,
        ]
        
        for mode in expected_modes:
            assert mode in STRATEGY_REGISTRY, f"Stratégie manquante pour {mode}"


class TestCentralizedRegistryContract:
    """Contrat de stabilité pour le registre centralisé."""
    
    def test_public_api_functions(self):
        """Vérifie que les fonctions publiques sont accessibles."""
        from src.valuation.registry import (
            get_strategy,
            get_auditor,
            get_display_names,
            get_all_strategies,
        )
        
        # Toutes ces fonctions DOIVENT exister
        assert callable(get_strategy)
        assert callable(get_auditor)
        assert callable(get_display_names)
        assert callable(get_all_strategies)
    
    def test_get_display_names_returns_dict(self):
        """Vérifie que get_display_names retourne un dict."""
        from src.valuation.registry import get_display_names
        from src.models import ValuationMode
        
        names = get_display_names()
        
        assert isinstance(names, dict)
        assert len(names) >= 7
        
        # Les clés doivent être des ValuationMode
        for key in names.keys():
            assert isinstance(key, ValuationMode)
    
    def test_get_strategy_returns_class(self):
        """Vérifie que get_strategy retourne une classe."""
        from src.valuation.registry import get_strategy
        from src.valuation.strategies.abstract import ValuationStrategy
        from src.models import ValuationMode
        
        strategy_cls = get_strategy(ValuationMode.FCFF_STANDARD)
        
        assert strategy_cls is not None
        assert issubclass(strategy_cls, ValuationStrategy)
    
    def test_get_auditor_returns_instance(self):
        """Vérifie que get_auditor retourne une instance."""
        from src.valuation.registry import get_auditor
        from src.models import ValuationMode
        
        auditor = get_auditor(ValuationMode.FCFF_STANDARD)
        
        assert auditor is not None
        assert hasattr(auditor, "audit_pillars")
