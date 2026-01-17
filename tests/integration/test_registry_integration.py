"""
tests/integration/test_registry_integration.py
Tests d'Intégration — Registre Centralisé

Ces tests vérifient la cohérence entre les différents registres.
Migration depuis test_integration_registry.py (legacy).
"""

import pytest
from core.models import ValuationMode


class TestRegistrySynchronization:
    """Tests de synchronisation entre registres."""
    
    def test_central_and_legacy_registries_match(self):
        """Le registre centralisé et le legacy sont synchronisés."""
        from core.valuation.registry import get_all_strategies
        from core.valuation.engines import STRATEGY_REGISTRY
        
        central_modes = set(get_all_strategies().keys())
        legacy_modes = set(STRATEGY_REGISTRY.keys())
        
        assert central_modes == legacy_modes, "Registres désynchronisés"
    
    def test_display_names_match_modes(self):
        """Chaque mode a un display_name."""
        from core.valuation.registry import get_display_names
        
        names = get_display_names()
        
        for mode in ValuationMode:
            # Vérifier que les modes principaux ont un nom
            if mode in [
                ValuationMode.FCFF_TWO_STAGE,
                ValuationMode.GRAHAM_1974_REVISED,
            ]:
                assert mode in names, f"{mode} n'a pas de display_name"
    
    def test_auditors_match_modes(self):
        """Chaque mode enregistré a un auditeur."""
        from core.valuation.registry import get_auditor, get_all_strategies
        
        for mode in get_all_strategies().keys():
            auditor = get_auditor(mode)
            assert auditor is not None, f"Auditeur manquant pour {mode}"
            assert hasattr(auditor, "audit_pillars"), f"Auditeur invalide pour {mode}"


class TestUIRegistryIntegration:
    """Tests d'intégration avec l'UI."""
    
    def test_expert_ui_registry_populated(self):
        """EXPERT_UI_REGISTRY est correctement peuplé."""
        from app.main import EXPERT_UI_REGISTRY
        
        assert len(EXPERT_UI_REGISTRY) >= 7
        
        for mode, renderer in EXPERT_UI_REGISTRY.items():
            assert callable(renderer), f"Renderer non callable pour {mode}"
    
    def test_valuation_display_names_populated(self):
        """VALUATION_DISPLAY_NAMES est correctement peuplé."""
        from app.main import VALUATION_DISPLAY_NAMES
        
        assert len(VALUATION_DISPLAY_NAMES) >= 7
        
        # Vérifier quelques noms attendus
        assert ValuationMode.FCFF_TWO_STAGE in VALUATION_DISPLAY_NAMES
        assert "FCFF" in VALUATION_DISPLAY_NAMES[ValuationMode.FCFF_TWO_STAGE]


class TestAuditFactoryIntegration:
    """Tests d'intégration avec AuditorFactory."""
    
    def test_factory_uses_centralized_registry(self):
        """AuditorFactory utilise le registre centralisé."""
        from infra.auditing.audit_engine import AuditorFactory
        from core.valuation.registry import get_auditor
        
        # Les deux méthodes doivent retourner le même type
        factory_auditor = AuditorFactory.get_auditor(ValuationMode.FCFF_TWO_STAGE)
        registry_auditor = get_auditor(ValuationMode.FCFF_TWO_STAGE)
        
        assert type(factory_auditor) == type(registry_auditor)
    
    def test_correct_auditor_types(self):
        """Les bons types d'auditeurs sont retournés."""
        from infra.auditing.audit_engine import AuditorFactory
        from infra.auditing.auditors import (
            DCFAuditor, RIMAuditor, GrahamAuditor, FCFEAuditor, DDMAuditor
        )
        
        # FCFF modes → DCFAuditor
        assert isinstance(
            AuditorFactory.get_auditor(ValuationMode.FCFF_TWO_STAGE), 
            DCFAuditor
        )
        
        # RIM → RIMAuditor
        assert isinstance(
            AuditorFactory.get_auditor(ValuationMode.RESIDUAL_INCOME_MODEL), 
            RIMAuditor
        )
        
        # Graham → GrahamAuditor
        assert isinstance(
            AuditorFactory.get_auditor(ValuationMode.GRAHAM_1974_REVISED), 
            GrahamAuditor
        )
        
        # FCFE → FCFEAuditor
        assert isinstance(
            AuditorFactory.get_auditor(ValuationMode.FCFE_TWO_STAGE), 
            FCFEAuditor
        )
        
        # DDM → DDMAuditor
        assert isinstance(
            AuditorFactory.get_auditor(ValuationMode.DDM_GORDON_GROWTH), 
            DDMAuditor
        )
