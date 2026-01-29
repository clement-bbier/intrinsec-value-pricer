"""
tests/contracts/test_audit_contracts.py
Tests de Contrats — API du Moteur d'Audit
"""

from inspect import signature
import pytest

class TestAuditEngineContract:
    """Contrat de stabilité pour AuditEngine."""

    def test_class_exists(self):
        from infra.auditing.audit_engine import AuditEngine
        assert AuditEngine is not None

    def test_compute_audit_method_exists(self):
        from infra.auditing.audit_engine import AuditEngine
        assert hasattr(AuditEngine, "compute_audit")
        assert callable(AuditEngine.compute_audit)

    def test_compute_audit_signature(self):
        from infra.auditing.audit_engine import AuditEngine
        sig = signature(AuditEngine.compute_audit)
        assert "result" in list(sig.parameters.keys())

    def test_compute_audit_returns_audit_report(self, sample_financials, sample_params):
        """Vérifie que compute_audit retourne un AuditReport valide."""
        from infra.auditing.audit_engine import AuditEngine
        from src.models import AuditReport, ValuationRequest, ValuationMode, InputSource
        from src.valuation.strategies.standard_fcff import StandardFCFFStrategy

        # SÉCURISATION : On donne des valeurs minimales pour éviter les TypeError dans le pipeline
        sample_financials.ebit_ttm = 100.0
        sample_financials.interest_expense = 10.0

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
        # Les notations sont maintenant Grade-A (A+, A, B, etc.)
        assert any(r in report.rating for r in ["A", "B", "C", "D", "F"])


class TestAuditorFactoryContract:
    """Contrat de stabilité pour AuditorFactory."""

    def test_returns_correct_auditor_types(self):
        """Vérifie l'instanciation des nouveaux auditeurs refactorisés."""
        from infra.auditing.audit_engine import AuditorFactory
        from infra.auditing.auditors import DCFAuditor, RIMAuditor, GrahamAuditor
        from src.models import ValuationMode

        # DCF modes → DCFAuditor (Le socle commun)
        for mode in [ValuationMode.FCFF_STANDARD, ValuationMode.FCFF_NORMALIZED]:
            auditor = AuditorFactory.get_auditor(mode)
            assert isinstance(auditor, DCFAuditor)

        # RIM & Graham ont maintenant leurs propres classes spécialisées
        assert isinstance(AuditorFactory.get_auditor(ValuationMode.RIM), RIMAuditor)
        assert isinstance(AuditorFactory.get_auditor(ValuationMode.GRAHAM), GrahamAuditor)