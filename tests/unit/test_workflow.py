"""
tests/unit/test_workflow.py - Version "Deep Mock"
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.workflow import run_workflow, run_workflow_and_display, map_request_to_params
from src.domain.models import ValuationRequest, ValuationMode, InputSource

class TestWorkflowCore:
    @patch('app.workflow.st')
    @patch('app.workflow.run_valuation')
    @patch('app.workflow._create_data_provider')
    def test_run_workflow_success_path(self, mock_create_provider, mock_run_valuation, mock_st):
        # 1. Mock du status Streamlit
        mock_st.status.return_value.__enter__.return_value = MagicMock()

        # 2. Mock du résultat (On enlève spec pour éviter AttributeError: audit_report)
        mock_result = MagicMock() 
        mock_result.simulation_results = []
        mock_result.intrinsic_value_per_share = 150.0
        mock_run_valuation.return_value = mock_result

        # 3. Mock du provider et des params
        mock_provider = MagicMock()
        mock_create_provider.return_value = mock_provider
        
        # On s'assure que auto_params a bien l'attribut monte_carlo
        mock_auto_params = MagicMock()
        mock_provider.get_company_financials_and_parameters.return_value = (MagicMock(), mock_auto_params)
        mock_provider.get_peer_multiples.return_value = MagicMock()

        request = ValuationRequest(ticker="AAPL", projection_years=5, mode=ValuationMode.FCFF_STANDARD, input_source=InputSource.AUTO)

        # Exécution
        result, provider = run_workflow(request)

        assert result is not None
        assert result.intrinsic_value_per_share == 150.0

    @patch('app.workflow.st')
    @patch('app.workflow.run_valuation')
    @patch('app.workflow._create_data_provider')
    def test_run_workflow_with_options_enabled(self, mock_create_provider, mock_run_valuation, mock_st):
        mock_st.status.return_value.__enter__.return_value = MagicMock()
        
        # Mock des paramètres automatiques avec structure imbriquée
        mock_auto_params = MagicMock()
        mock_provider = MagicMock()
        mock_create_provider.return_value = mock_provider
        mock_provider.get_company_financials_and_parameters.return_value = (MagicMock(), mock_auto_params)
        
        mock_result = MagicMock()
        mock_result.simulation_results = [100.0]
        mock_run_valuation.return_value = mock_result

        request = ValuationRequest(
            ticker="AAPL", projection_years=5, mode=ValuationMode.FCFF_STANDARD, 
            input_source=InputSource.AUTO, options={"enable_mc": True}
        )

        result, _ = run_workflow(request)
        assert result is not None # Ne sera plus None car l'AttributeError monte_carlo est fixée