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

from app.controllers.input_factory import InputFactory
from app.state.session_manager import SessionManager
from app.state.store import get_state
from infra.data_providers.yahoo_financial_provider import YahooFinancialProvider
from infra.macro.default_macro_provider import DefaultMacroProvider
from src.core.exceptions import ExternalServiceError, TickerNotFoundError, ValuationError
from src.i18n import CommonTexts
from src.valuation.orchestrator import ValuationOrchestrator

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
                macro = DefaultMacroProvider()
                provider = YahooFinancialProvider(macro_provider=macro)

                # 3. Input Assembly
                request = InputFactory.build_request()
                ticker = request.parameters.structure.ticker

                # 4. Fetch Financial Data
                snapshot = provider.get_company_snapshot(ticker)

                if not snapshot:
                    SessionManager.set_error(f"Data unavailable for ticker: {ticker}")
                    return

                # 5. Run Engine
                engine = ValuationOrchestrator()
                result = engine.run(request, snapshot)

                # 6. Success State Update
                state.last_result = result
                state.should_run_valuation = False
                state.error_message = ""

                # Force re-render to show results
                st.rerun()

            except TickerNotFoundError as e:
                logger.warning(f"Ticker not found: {e}")
                SessionManager.set_error(f"Ticker not found: {e.diagnostic.message}")

            except ExternalServiceError as e:
                logger.error(f"Provider failure: {e}")
                SessionManager.set_error(f"Data provider error: {e.diagnostic.message}")

            except ValuationError as e:
                logger.error(f"Valuation error: {e}", exc_info=True)
                SessionManager.set_error(f"Calculation error: {e.diagnostic.message}")

            except Exception as e:
                logger.critical(f"Unexpected error: {e}", exc_info=True)
                SessionManager.set_error(f"Unexpected error: {str(e)}")
