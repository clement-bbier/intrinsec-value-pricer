"""
tests/contracts/test_engines_contracts.py
Tests de Contrats — API du Moteur de Valorisation
"""

class TestRunValuationContract:
    def test_return_type_is_valuation_result(self, sample_financials, sample_params):
        from src.valuation.engines import run_valuation
        from src.models import ValuationRequest, ValuationMode, InputSource, ValuationResult

        # Rigueur des données pour le pipeline
        sample_financials.ebit_ttm = 500.0
        sample_financials.interest_expense = 50.0

        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
        )

        result = run_valuation(request, sample_financials, sample_params)
        assert isinstance(result, ValuationResult)
        assert result.audit_report is not None


class TestCentralizedRegistryContract:
    """Contrat de stabilité pour le registre centralisé."""

    def test_get_auditor_returns_instance(self):
        """Vérifie que le registre retourne un auditeur fonctionnel."""
        from src.valuation.registry import get_auditor
        from src.models import ValuationMode
        from infra.auditing.auditors import IValuationAuditor

        auditor = get_auditor(ValuationMode.FCFF_STANDARD)
        assert auditor is not None
        assert isinstance(auditor, IValuationAuditor)
        assert hasattr(auditor, "audit_pillars")