"""
tests/contracts/test_audit_contracts.py
Tests de Contrats — API du Moteur d'Audit

Ces tests garantissent que l'API d'audit reste stable.

RÈGLE D'OR : Ces tests NE DOIVENT PAS CHANGER lors des refactorings.
"""

import pytest
from inspect import signature


class TestAuditEngineContract:
    """Contrat de stabilité pour AuditEngine."""
    
    def test_class_exists(self):
        """Vérifie que AuditEngine est importable."""
        from infra.auditing.audit_engine import AuditEngine
        
        assert AuditEngine is not None
    
    def test_compute_audit_method_exists(self):
        """Vérifie que compute_audit est accessible."""
        from infra.auditing.audit_engine import AuditEngine
        
        assert hasattr(AuditEngine, "compute_audit")
        assert callable(AuditEngine.compute_audit)
    
    def test_compute_audit_signature(self):
        """Vérifie la signature de compute_audit."""
        from infra.auditing.audit_engine import AuditEngine
        
        sig = signature(AuditEngine.compute_audit)
        params = list(sig.parameters.keys())
        
        # Le premier paramètre doit être 'result'
        assert "result" in params, "Paramètre 'result' manquant"
    
    def test_compute_audit_returns_audit_report(self, sample_financials, sample_params):
        """Vérifie que compute_audit retourne un AuditReport."""
        from infra.auditing.audit_engine import AuditEngine
        from src.domain.models import (
            AuditReport, ValuationRequest, ValuationMode, InputSource
        )
        from core.valuation.strategies.dcf_standard import StandardFCFFStrategy
        
        # Créer un ValuationResult via une stratégie
        strategy = StandardFCFFStrategy(glass_box_enabled=False)
        result = strategy.execute(sample_financials, sample_params)
        result.request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
        )
        
        report = AuditEngine.compute_audit(result)
        
        assert isinstance(report, AuditReport)
        assert 0 <= report.global_score <= 100
        assert report.rating in ["AAA", "AA", "BBB", "BB", "C"]


class TestAuditorFactoryContract:
    """Contrat de stabilité pour AuditorFactory."""
    
    def test_factory_exists(self):
        """Vérifie que AuditorFactory est importable."""
        from infra.auditing.audit_engine import AuditorFactory
        
        assert AuditorFactory is not None
    
    def test_get_auditor_method_exists(self):
        """Vérifie que get_auditor est accessible."""
        from infra.auditing.audit_engine import AuditorFactory
        
        assert hasattr(AuditorFactory, "get_auditor")
        assert callable(AuditorFactory.get_auditor)
    
    def test_returns_correct_auditor_types(self):
        """Vérifie que les bons types d'auditeurs sont retournés."""
        from infra.auditing.audit_engine import AuditorFactory
        from infra.auditing.auditors import DCFAuditor, RIMAuditor, GrahamAuditor
        from src.domain.models import ValuationMode
        
        # DCF modes → DCFAuditor
        for mode in [ValuationMode.FCFF_STANDARD, ValuationMode.FCFF_NORMALIZED]:
            auditor = AuditorFactory.get_auditor(mode)
            assert isinstance(auditor, DCFAuditor), f"{mode} devrait utiliser DCFAuditor"
        
        # RIM → RIMAuditor
        auditor = AuditorFactory.get_auditor(ValuationMode.RIM)
        assert isinstance(auditor, RIMAuditor)
        
        # Graham → GrahamAuditor
        auditor = AuditorFactory.get_auditor(ValuationMode.GRAHAM)
        assert isinstance(auditor, GrahamAuditor)


class TestAuditSeverityContract:
    """Contrat de stabilité pour AuditSeverity."""
    
    def test_severity_levels_exist(self):
        """Vérifie que les niveaux de sévérité existent."""
        from src.domain.models import AuditSeverity
        
        # Niveaux réels du modèle (pas de ERROR)
        expected = ["INFO", "WARNING", "CRITICAL"]
        actual = [s.name for s in AuditSeverity]
        
        for level in expected:
            assert level in actual, f"Niveau '{level}' manquant dans AuditSeverity"


class TestAuditPillarContract:
    """Contrat de stabilité pour AuditPillar."""
    
    def test_pillars_exist(self):
        """Vérifie que les piliers d'audit existent."""
        from src.domain.models import AuditPillar
        
        expected = [
            "DATA_CONFIDENCE",
            "ASSUMPTION_RISK",
            "MODEL_RISK",
            "METHOD_FIT",
        ]
        actual = [p.name for p in AuditPillar]
        
        for pillar in expected:
            assert pillar in actual, f"Pilier '{pillar}' manquant dans AuditPillar"
