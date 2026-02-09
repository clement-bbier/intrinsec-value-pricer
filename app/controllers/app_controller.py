"""
app/controllers/app_controller.py

APP CONTROLLER — ORCHESTRATION LOGIC
====================================
Role: Central handler for the "Run Analysis" action.
Flow:
  1. Trigger Spinner.
  2. Use InputFactory to build the Request.
  3. Call Backend Orchestrator.
  4. Update State with Result.
  5. Handle Errors/Exceptions.
"""

import logging
import streamlit as st

from src.valuation.orchestrator import ValuationOrchestrator
from infra.data_providers.yahoo_financial_provider import YahooFinancialProvider
from infra.macro.default_macro_provider import DefaultMacroProvider
from app.state.store import get_state
from app.state.session_manager import SessionManager
from app.controllers.input_factory import InputFactory
from src.i18n import CommonTexts

logger = logging.getLogger(__name__)


class AppController:
    """
    Controller for the main valuation workflow.
    Decouples View (Buttons) from Model (Calculation).
    """

    @staticmethod
    def handle_run_analysis():
        """
        Executed when the user clicks 'Run Valuation'.
        """
        state = get_state()

        # 1. UI Feedback: Spinner
        with st.spinner(CommonTexts.STATUS_CALCULATED):
            try:
                # 2. Infrastructure Setup (DI)
                # We instantiate providers here (Controller scope)
                macro = DefaultMacroProvider()
                provider = YahooFinancialProvider(macro_provider=macro)

                # 3. Input Assembly
                # Extracts data from the UI widgets into a clean Pydantic object
                request = InputFactory.build_request()

                # 4. Backend Execution
                # The heavy lifting happens here
                engine = ValuationOrchestrator()
                # Note: The Orchestrator expects a CompanySnapshot, which it usually fetches itself
                # But here we pass the provider to the orchestrator implicitly or explicitly?
                # Looking at src.valuation.orchestrator.run signature:
                # run(request: ValuationRequest, snapshot: Optional[CompanySnapshot] = None)

                # We need to fetch the snapshot first to pass it, OR let the orchestrator do it.
                # Since the orchestrator is "pure", we usually fetch data in the infra layer.

                # Let's fetch the data first (Controller responsibility)
                snapshot = provider.get_company_snapshot(request.parameters.structure.ticker)

                if not snapshot:
                    SessionManager.set_error(f"Data unavailable for ticker: {request.parameters.structure.ticker}")
                    return

                # 5. Run Engine
                result = engine.run(request, snapshot)

                # 6. Success State Update
                state.last_result = result
                state.should_run_valuation = False  # Reset flag
                state.error_message = None  # Clear errors

                # Force re-render to show results
                st.rerun()

            except Exception as e:
                logger.error(f"Controller Error: {e}", exc_info=True)
                SessionManager.set_error(f"Analysis Failed: {str(e)}")