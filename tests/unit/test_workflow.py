"""
tests/unit/test_workflow.py
Suite de tests de l'Orchestrateur Logique (DT-016).
Couverture : 100% des branches (Nominal, Erreurs, Scénarios, Backtest).
"""

import pytest
from datetime import date
from unittest.mock import Mock, patch, MagicMock
from app.workflow import (
    run_workflow,
    run_workflow_and_display,
    map_request_to_params,
    compute_scenario_impact,
    _orchestrate_backtesting
)
from src.diagnostics import DiagnosticEvent, SeverityLevel
from src.models import (
    ValuationRequest, ValuationMode, InputSource,
    ValuationResult, DCFParameters
)
from src.exceptions import ValuationException

TARGET = 'app.workflow'

class TestWorkflowCore:
    """Validation du cycle de vie principal et des erreurs."""

    @patch(f'{TARGET}.st')
    @patch(f'{TARGET}.run_valuation')
    @patch(f'{TARGET}._create_data_provider')
    def test_run_workflow_full_success(self, mock_create_provider, mock_run_val, mock_st):
        """Couvre le chemin nominal avec Monte Carlo et Scénarios."""
        # 1. Setup Streamlit Status (Context Manager)
        mock_status = MagicMock()
        mock_st.status.return_value.__enter__.return_value = mock_status

        # 2. Setup Data Provider
        mock_provider = MagicMock()
        mock_create_provider.return_value = mock_provider
        mock_provider.get_company_financials_and_parameters.return_value = (Mock(), Mock())

        # 3. Setup Engine Result with MC data to trigger logging branch
        mock_result = MagicMock(spec=ValuationResult)
        mock_result.simulation_results = [100.0, 110.0, 120.0]
        mock_result.intrinsic_value_per_share = 150.0
        mock_run_val.return_value = mock_result

        request = ValuationRequest(
            ticker="AAPL", projection_years=5,
            mode=ValuationMode.FCFF_STANDARD,
            input_source=InputSource.AUTO,
            options={"enable_backtest": False}
        )

        result, provider = run_workflow(request)

        assert result.intrinsic_value_per_share == 150.0
        mock_status.update.assert_called_with(label=patch.any, state="complete", expanded=False)

    @patch(f'{TARGET}.st')
    @patch(f'{TARGET}._create_data_provider')
    def test_run_workflow_valuation_exception(self, mock_create_provider, mock_st):
        """Couvre la branche ValuationException (Erreur métier)."""
        mock_st.status.return_value.__enter__.return_value = MagicMock()
        diag = DiagnosticEvent(code="ERR", severity=SeverityLevel.ERROR, message="Calcul impossible")
        mock_create_provider.side_effect = ValuationException(diag)

        request = ValuationRequest(ticker="FAIL", mode=ValuationMode.FCFF_STANDARD)
        result, provider = run_workflow(request)

        assert result is None
        mock_st.error.assert_called() # Via _display_diagnostic_message

    @patch(f'{TARGET}.st')
    @patch(f'{TARGET}._create_data_provider')
    def test_run_workflow_system_crash(self, mock_create_provider, mock_st):
        """Couvre la branche Exception générique (Crash système)."""
        mock_st.status.return_value.__enter__.return_value = MagicMock()
        mock_create_provider.side_effect = RuntimeError("Database Offline")

        request = ValuationRequest(ticker="CRASH", mode=ValuationMode.FCFF_STANDARD)
        result, provider = run_workflow(request)

        assert result is None
        # Vérifie que le statut passe en mode erreur
        mock_st.status.return_value.update.assert_called()

class TestSmartMergeLogic:
    """Validation de la fusion auto/manuel (map_request_to_params)."""

    def test_map_manual_source_overrides(self):
        """Vérifie que les saisies EXPERT écrasent les données Yahoo."""
        auto_params = DCFParameters.from_legacy({"projection_years": 5})
        auto_params.rates.risk_free_rate = 0.02

        request = MagicMock(spec=ValuationRequest)
        request.input_source = InputSource.MANUAL
        # Mock du dump Pydantic (simule ce que l'expert a saisi)
        request.manual_params.rates.model_dump.return_value = {"risk_free_rate": 0.045}
        request.manual_params.growth.model_dump.return_value = {"projection_years": 10}

        final = map_request_to_params(request, auto_params)

        assert final.rates.risk_free_rate == 0.045
        assert final.growth.projection_years == 10

class TestAdvancedAnalysis:
    """Validation des Scénarios et du Backtesting."""

    @patch(f'{TARGET}.run_valuation')
    def test_compute_scenario_impact(self, mock_run_val):
        """Vérifie la pondération Bull/Base/Bear."""
        params = DCFParameters.from_legacy({"projection_years": 5})
        params.scenarios.enabled = True
        params.scenarios.bull.probability = 0.25
        params.scenarios.base.probability = 0.50
        params.scenarios.bear.probability = 0.25

        mock_res = MagicMock()
        mock_res.intrinsic_value_per_share = 100.0
        mock_run_val.return_value = mock_res

        synthesis = compute_scenario_impact(Mock(), Mock(), params, mock_res)

        assert synthesis.expected_value == 100.0
        assert len(synthesis.variants) == 3

    @patch(f'{TARGET}.BacktestEngine')
    @patch(f'{TARGET}.run_valuation')
    def test_orchestrate_backtesting_with_failures(self, mock_run_val, mock_bt_engine):
        """Vérifie que le backtest continue même si une année échoue."""
        # Année 1: Succès, Année 2: Crash (doit continuer), Année 3: Succès
        mock_bt_engine.freeze_data_at_fiscal_year.side_effect = [{"data": 1}, None, {"data": 3}]
        mock_bt_engine.get_historical_price_at.return_value = 150.0

        mock_hist_res = MagicMock()
        mock_hist_res.intrinsic_value_per_share = 160.0
        mock_run_val.return_value = mock_hist_res

        mock_provider = MagicMock()

        report = _orchestrate_backtesting(Mock(), Mock(), DCFParameters.from_legacy({}), Mock(), mock_provider)

        # On attend 2 points (l'année None est sautée)
        assert len(report.points) == 2
        assert report.model_accuracy_score > 0

class TestCompatibilityFacade:
    """Validation de run_workflow_and_display."""

    @patch(f'{TARGET}.run_workflow')
    @patch('app.adapters.streamlit_adapters.StreamlitResultRenderer')
    def test_run_workflow_and_display(self, mock_renderer_cls, mock_run_wf):
        """Vérifie le rendu final."""
        mock_res, mock_prov = MagicMock(), MagicMock()
        mock_run_wf.return_value = (mock_res, mock_prov)

        run_workflow_and_display(Mock())

        mock_renderer_cls.return_value.render_results.assert_called_once_with(mock_res, mock_prov)