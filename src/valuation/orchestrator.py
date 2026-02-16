"""
src/valuation/orchestrator.py

CENTRAL VALUATION ORCHESTRATOR
==============================
Role: The entry point for the backend calculation pipeline.
Process:
  1. Hydrate Parameters (Ghost -> Solid).
  2. Run Economic Guardrails (Validation).
  3. Execute Core Strategy (IValuationRunner).
  4. Execute Extensions (Monte Carlo, Sensitivity, etc.).
  5. Package Final Envelope.

Architecture: Pipeline Pattern.
Standard: SOLID, institutional-grade error handling.
"""

from __future__ import annotations

import hashlib
import logging
import time

from src.computation.financial_math import calculate_wacc
from src.core.diagnostics import DiagnosticDomain, DiagnosticEvent, SeverityLevel
from src.core.exceptions import CalculationError, ValuationError
from src.core.quant_logger import QuantLogger
from src.models import Parameters
from src.models.benchmarks import CompanyStats, MarketContext, SectorMultiples, SectorPerformance
from src.models.company import CompanySnapshot
from src.models.valuation import AuditReport, ValuationRequest, ValuationResult, ValuationRunMetadata

# Guardrails
from src.valuation.guardrails import (
    GuardrailCheckResult,
    validate_capital_structure,
    validate_roic_spread,
    validate_scenario_probabilities,
    validate_terminal_growth,
)

# Options/Extensions Runners
from src.valuation.options.monte_carlo import MonteCarloRunner
from src.valuation.options.scenarios import ScenariosRunner
from src.valuation.options.sensitivity import SensitivityRunner
from src.valuation.options.sotp import SOTPRunner

# Registry & Interface
from src.valuation.registry import get_strategy

# Resolvers
from src.valuation.resolvers.base_resolver import Resolver
from src.valuation.resolvers.options import ExtensionResolver
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

    @staticmethod
    def _run_guardrails(params: Parameters) -> tuple[list[DiagnosticEvent], bool]:
        """
        Executes all economic guardrails and collects results.

        Parameters
        ----------
        params : Parameters
            The hydrated parameters to validate.

        Returns
        -------
        tuple[List[DiagnosticEvent], bool]
            A tuple of (diagnostic_events, has_blocking_errors).
        """
        financials = params.structure
        events: list[DiagnosticEvent] = []
        has_errors = False

        # Calculate WACC for guardrails that need it
        try:
            wacc_breakdown = calculate_wacc(financials, params)
            wacc = wacc_breakdown.wacc
        except Exception as e:
            logger.warning(f"Could not calculate WACC for guardrails: {e}. Using default.")
            wacc = 0.10  # Fallback default

        # Run each guardrail
        guardrail_checks: list[GuardrailCheckResult] = [
            validate_terminal_growth(params, wacc),
            validate_roic_spread(financials, params, wacc),
            validate_capital_structure(financials, params),
            validate_scenario_probabilities(params),
        ]

        # Convert guardrail results to DiagnosticEvents
        for check in guardrail_checks:
            if check.type == "error":
                severity = SeverityLevel.ERROR
                has_errors = True
            elif check.type == "warning":
                severity = SeverityLevel.WARNING
            else:
                severity = SeverityLevel.INFO

            event = DiagnosticEvent(
                code=check.code,
                severity=severity,
                domain=DiagnosticDomain.MODEL,
                message=check.message,
                technical_detail=str(check.extra) if check.extra else None,
            )
            events.append(event)

            if check.type == "error":
                logger.error(f"[Guardrail] {check.code}: {check.message}")
            elif check.type == "warning":
                logger.warning(f"[Guardrail] {check.code}: {check.message}")
            else:
                logger.info(f"[Guardrail] {check.code}: {check.message}")

        return events, has_errors

    @staticmethod
    def _build_market_context(snapshot: CompanySnapshot) -> MarketContext | None:
        """
        Constructs the MarketContext object from the flat CompanySnapshot data.

        Parameters
        ----------
        snapshot : CompanySnapshot
            The raw data bag containing sector fallbacks and identifiers.

        Returns
        -------
        MarketContext | None
            The structured benchmark context or None if sector data is missing.
        """
        if not snapshot.sector:
            return None

        # 1. Build Multiples from Snapshot fallbacks
        multiples = SectorMultiples(
            pe_ratio=snapshot.sector_pe_fallback,
            ev_ebitda=snapshot.sector_ev_ebitda_fallback,
            ev_revenue=snapshot.sector_ev_rev_fallback,
            pb_ratio=None,  # Not currently fetched in snapshot fallbacks
        )

        # 2. Build Performance (Placeholder logic for now)
        performance = SectorPerformance(fcf_margin=None, revenue_growth=None, roe=None)

        return MarketContext(
            reference_ticker=snapshot.industry or "Unknown Index",
            sector_name=snapshot.sector,
            multiples=multiples,
            performance=performance,
            risk_free_rate=snapshot.risk_free_rate or 0.04,
            equity_risk_premium=snapshot.market_risk_premium or 0.05,
        )

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
        QuantLogger.log_stage_start(ticker, "HYDRATION")

        # --- PHASE 1: HYDRATION (Ghost -> Solid) ---
        # Arbitrate between User Overrides, Snapshot Data, and Defaults.
        params = self.resolver.resolve(request.parameters, snapshot)

        # Hydrate Extension configurations (Monte Carlo, Sensitivity, etc.).
        params.extensions = self.extension_resolver.resolve(params.extensions)

        # Compute input hash for provenance
        input_hash = hashlib.sha256(params.model_dump_json().encode()).hexdigest()
        hydration_ms = int((time.time() - start_time) * 1000)
        QuantLogger.log_stage_complete(ticker, "HYDRATION", duration_ms=hydration_ms)

        # --- PHASE 1.5: DATA FETCHING LOG ---
        QuantLogger.log_data_fetching(ticker)

        # --- PHASE 1.6: PARAMETER RESOLUTION LOG ---
        QuantLogger.log_parameter_resolution(ticker, request.mode.value)

        # --- PHASE 1.6b: CRITICAL PARAMETER RESOLUTION LOG ---
        logger.info(
            "[RESOLVER] Risk-Free Rate resolved to %.4f for %s",
            params.common.rates.risk_free_rate,
            ticker,
        )
        logger.info(
            "[RESOLVER] Beta resolved to %.2f for %s",
            params.common.rates.beta,
            ticker,
        )
        logger.info(
            "[RESOLVER] WACC components: MRP=%.4f | Kd=%.4f | Tax=%.4f for %s",
            params.common.rates.market_risk_premium,
            params.common.rates.cost_of_debt or 0.0,
            params.common.rates.tax_rate or 0.0,
            ticker,
        )
        logger.info(
            "[RESOLVER] Capital: Debt=%.2fM | Cash=%.2fM | Shares=%.2fM for %s",
            (params.common.capital.total_debt or 0.0) / 1e6,
            (params.common.capital.cash_and_equivalents or 0.0) / 1e6,
            (params.common.capital.shares_outstanding or 0.0) / 1e6,
            ticker,
        )

        # --- PHASE 1.7: ECONOMIC GUARDRAILS ---
        logger.info(f"[Orchestrator] Running economic guardrails for {ticker}")
        guardrail_events, has_blocking_errors = self._run_guardrails(params)

        if has_blocking_errors:
            error_messages = [e.message for e in guardrail_events if e.severity == SeverityLevel.ERROR]
            raise CalculationError(f"Valuation blocked by economic guardrails: {'; '.join(error_messages)}")

        # --- PHASE 2: CORE STRATEGY EXECUTION ---
        strategy_cls = get_strategy(request.mode)
        if not strategy_cls:
            raise CalculationError(f"Methodology {request.mode} not found in registry.")

        strategy_runner = strategy_cls()
        QuantLogger.log_strategy_execution(ticker, type(strategy_runner).__name__)

        try:
            # Execute the core deterministic valuation logic.
            strategy_start = time.time()
            valuation_output = strategy_runner.execute(params.structure, params)
            strategy_ms = int((time.time() - strategy_start) * 1000)
            QuantLogger.log_stage_complete(ticker, "STRATEGY_EXECUTION", duration_ms=strategy_ms)

            # --- PHASE 3: EXTENSIONS (The Risk & Market Pillars) ---
            self._process_extensions(valuation_output, strategy_runner, params, ticker)

            # Post-calculation metadata (Upside/Downside).
            valuation_output.compute_upside()

            # --- PHASE 3.5: ATTACH GUARDRAIL RESULTS TO AUDIT ---
            if valuation_output.audit_report is None:
                valuation_output.audit_report = AuditReport()

            valuation_output.audit_report.events.extend(guardrail_events)
            valuation_output.audit_report.critical_warnings += sum(
                1 for event in guardrail_events if event.severity == SeverityLevel.WARNING
            )

            # --- PHASE 3.6: CONTEXT & STATS (Clean Architecture) ---
            # 1. Attach Financial Snapshot (Source of Truth for UI Display)
            valuation_output.financials = snapshot

            # 2. Build Market Context (Benchmark) from Snapshot
            valuation_output.market_context = self._build_market_context(snapshot)

            # 3. Compute Company Stats via Factory Method (The "Pro" way)
            # Delegates logic to the model itself
            valuation_output.company_stats = CompanyStats.compute(snapshot)

            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"[Orchestrator] Execution successful for {ticker} in {execution_time}ms")

            # --- PHASE 4: METADATA ATTACHMENT ---
            random_seed = None
            if params.extensions.monte_carlo and params.extensions.monte_carlo.enabled:
                random_seed = params.extensions.monte_carlo.random_seed

            metadata = ValuationRunMetadata(
                model_name=request.mode.value,
                ticker=ticker,
                random_seed=random_seed,
                input_hash=input_hash,
                execution_time_ms=execution_time,
            )
            valuation_output.metadata = metadata

            # --- PHASE 5: FINAL PACKAGING & STRUCTURED JSON LOGGING ---
            QuantLogger.log_final_packaging(
                ticker,
                intrinsic_value=valuation_output.results.common.intrinsic_value_per_share,
                execution_time_ms=execution_time,
            )
            QuantLogger.log_json(event="valuation_completed", **metadata.model_dump(mode="json"))

            return valuation_output

        except ValuationError as e:
            logger.error(f"[Orchestrator] Known valuation failure: {e}")
            raise e
        except Exception as e:
            logger.critical(f"[Orchestrator] Unexpected system failure: {e}")
            raise CalculationError(f"Internal Engine Failure: {str(e)}")

    @staticmethod
    def _process_extensions(
        base_result: ValuationResult,
        strategy_runner: IValuationRunner,
        params: Parameters,
        ticker: str = "N/A",
    ) -> None:
        """
        Executes enabled analytical modules and attaches results to the envelope.
        """
        ext_params = params.extensions
        ext_results = base_result.results.extensions
        financials = params.structure

        # 1. Monte Carlo Simulation (Stochastic Analysis).
        if ext_params.monte_carlo.enabled:
            ext_start = time.time()
            mc_runner = MonteCarloRunner(strategy_runner)
            ext_results.monte_carlo = mc_runner.execute(params, financials)
            ext_ms = int((time.time() - ext_start) * 1000)
            QuantLogger.log_extension_processing(ticker, "MONTE_CARLO", duration_ms=ext_ms)

        # 2. Sensitivity Analysis (Deterministic 2D Heatmap).
        if ext_params.sensitivity.enabled:
            ext_start = time.time()
            sensi_runner = SensitivityRunner(strategy_runner)
            ext_results.sensitivity = sensi_runner.execute(params, financials)
            ext_ms = int((time.time() - ext_start) * 1000)
            QuantLogger.log_extension_processing(ticker, "SENSITIVITY", duration_ms=ext_ms)

        # 3. Scenario Analysis (Weighted deterministic cases).
        if ext_params.scenarios.enabled:
            ext_start = time.time()
            scenario_runner = ScenariosRunner(strategy_runner)
            ext_results.scenarios = scenario_runner.execute(params, financials)
            ext_ms = int((time.time() - ext_start) * 1000)
            QuantLogger.log_extension_processing(ticker, "SCENARIOS", duration_ms=ext_ms)

        # 4. Sum-of-the-parts (SOTP / Conglomerate Bridge).
        if ext_params.sotp.enabled:
            ext_start = time.time()
            ext_results.sotp = SOTPRunner.execute(params)
            ext_ms = int((time.time() - ext_start) * 1000)
            QuantLogger.log_extension_processing(ticker, "SOTP", duration_ms=ext_ms)
