"""
src/valuation/orchestrator.py

CENTRAL VALUATION ORCHESTRATOR
==============================
Role: The entry point for the backend calculation pipeline.
Process:
  1. Hydrate Parameters (Ghost -> Solid).
  2. Execute Core Strategy (IValuationRunner).
  3. Execute Extensions (Monte Carlo, Sensitivity, etc.).
  4. Package Final Envelope.

Architecture: Pipeline Pattern.
Standard: SOLID, institutional-grade error handling.
"""

from __future__ import annotations
import logging
import time
import hashlib

from src.models import Parameters
from src.models.valuation import ValuationRequest, ValuationResult, ValuationRunMetadata
from src.models.company import CompanySnapshot
from src.core.quant_logger import QuantLogger

# Resolvers
from src.valuation.resolvers.base_resolver import Resolver
from src.valuation.resolvers.options import ExtensionResolver

# Registry & Interface
from src.valuation.registry import get_strategy
from src.core.exceptions import CalculationError, ValuationException

# Options/Extensions Runners
from src.valuation.options.monte_carlo import MonteCarloRunner
from src.valuation.options.sensitivity import SensitivityRunner
from src.valuation.options.scenarios import ScenariosRunner
from src.valuation.options.sotp import SOTPRunner
from src.valuation.strategies import IValuationRunner

logger = logging.getLogger(__name__)

class ValuationOrchestrator:
    """
    Coordinates the full lifecycle of a valuation session.

    This class acts as the single point of contact for the application
    layer to trigger complex financial simulations.
    """

    def __init__(self):
        """Initializes the required resolvers for hydration."""
        self.resolver = Resolver()
        self.extension_resolver = ExtensionResolver()

    def run(self, request: ValuationRequest, snapshot: CompanySnapshot) -> ValuationResult:
        """
        Executes the full valuation pipeline.

        Parameters
        ----------
        request : ValuationRequest
            The raw request containing ghost parameters and selected mode.
        snapshot : CompanySnapshot
            The raw financial data used for hydration.

        Returns
        -------
        ValuationResult
            The complete result envelope with core results and extensions.
        """
        start_time = time.time()
        ticker = request.parameters.structure.ticker
        logger.info(f"[Orchestrator] Starting pipeline for {ticker}")

        # --- PHASE 1: HYDRATION (Ghost -> Solid) ---
        # Arbitrate between User Overrides, Snapshot Data, and Defaults.
        params = self.resolver.resolve(request.parameters, snapshot) #

        # Hydrate Extension configurations (Monte Carlo, Sensitivity, etc.).
        params.extensions = self.extension_resolver.resolve(params.extensions) #

        # Compute input hash for provenance
        input_hash = hashlib.sha256(params.model_dump_json().encode()).hexdigest()

        # --- PHASE 2: CORE STRATEGY EXECUTION ---
        # Retrieve the strategy class from the registry via the selected mode.
        strategy_cls = get_strategy(request.mode) #
        if not strategy_cls:
            raise CalculationError(f"Methodology {request.mode} not found in registry.") #

        strategy_runner = strategy_cls() #

        try:
            # Execute the core deterministic valuation logic.
            # financials (Pillar 1) + params (Pillars 2,3).
            valuation_output = strategy_runner.execute(params.structure, params) #

            # --- PHASE 3: EXTENSIONS (The Risk & Market Pillars) ---
            # Process optional analytical modules based on hydrated extension settings.
            self._process_extensions(valuation_output, strategy_runner, params)

            # Post-calculation metadata (Upside/Downside).
            valuation_output.compute_upside() #

            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"[Orchestrator] Execution successful for {ticker} in {execution_time}ms")

            # --- PHASE 4: METADATA ATTACHMENT ---
            # Capture random seed if MC is enabled
            random_seed = None
            if params.extensions.monte_carlo and params.extensions.monte_carlo.enabled:
                random_seed = params.extensions.monte_carlo.random_seed

            metadata = ValuationRunMetadata(
                model_name=request.mode.value,
                ticker=ticker,
                random_seed=random_seed,
                input_hash=input_hash,
                execution_time_ms=execution_time
            )
            valuation_output.metadata = metadata

            # --- PHASE 5: STRUCTURED JSON LOGGING ---
            QuantLogger.log_json(
                event="valuation_completed",
                **metadata.model_dump(mode="json")
            )

            return valuation_output

        except ValuationException as e:
            logger.error(f"[Orchestrator] Known valuation failure: {e}")
            raise e #
        except Exception as e:
            logger.critical(f"[Orchestrator] Unexpected system failure: {e}")
            raise CalculationError(f"Internal Engine Failure: {str(e)}") #

    @staticmethod
    def _process_extensions(
            base_result: ValuationResult,
            strategy_runner: IValuationRunner,
            params: Parameters
    ) -> None:
        """
        Executes enabled analytical modules and attaches results to the envelope.
        """
        ext_params = params.extensions
        ext_results = base_result.results.extensions
        financials = params.structure

        # 1. Monte Carlo Simulation (Stochastic Analysis).
        if ext_params.monte_carlo.enabled:
            mc_runner = MonteCarloRunner(strategy_runner) #
            ext_results.monte_carlo = mc_runner.execute(params, financials) #

        # 2. Sensitivity Analysis (Deterministic 2D Heatmap).
        if ext_params.sensitivity.enabled:
            sensi_runner = SensitivityRunner(strategy_runner) #
            ext_results.sensitivity = sensi_runner.execute(params, financials) #

        # 3. Scenario Analysis (Weighted deterministic cases).
        if ext_params.scenarios.enabled:
            scenario_runner = ScenariosRunner(strategy_runner) #
            ext_results.scenarios = scenario_runner.execute(params, financials) #

        # 4. Sum-of-the-parts (SOTP / Conglomerate Bridge).
        if ext_params.sotp.enabled:
            ext_results.sotp = SOTPRunner.execute(params) #