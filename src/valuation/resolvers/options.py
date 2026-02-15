"""
src/valuation/resolvers/options.py

EXTENSION RESOLVER — LOGIC LAYER
================================
Role: Applies system defaults and fallback logic to optional modules.
Scope: Logic Only. Consumes 'Parameters' objects.
Architecture: Service Class pattern (Stateless).
Style: Numpy docstrings.
"""

from __future__ import annotations

import logging

from src.config.constants import (
    BacktestDefaults,
    MonteCarloDefaults,
    PeerDefaults,
    ScenarioDefaults,
    SensitivityDefaults,
    SOTPDefaults,
)
from src.models.parameters.options import (
    BacktestParameters,
    ExtensionBundleParameters,
    MCParameters,
    PeersParameters,
    ScenarioParameters,
    ScenariosParameters,
    SensitivityParameters,
    SOTPParameters,
)

logger = logging.getLogger(__name__)


class ExtensionResolver:
    """
    Service class responsible for hydrating optional module parameters.
    Ensures that if a module is enabled, it has valid configuration values.
    """

    def resolve(self, bundle: ExtensionBundleParameters) -> ExtensionBundleParameters:
        """
        Orchestrates the resolution of all extensions.

        Parameters
        ----------
        bundle : ExtensionBundleParameters
            The raw input bundle.

        Returns
        -------
        ExtensionBundleParameters
            The hydrated bundle with defaults applied.
        """
        self._resolve_monte_carlo(bundle.monte_carlo)
        self._resolve_sensitivity(bundle.sensitivity)
        self._resolve_scenarios(bundle.scenarios)
        self._resolve_backtest(bundle.backtest)
        self._resolve_peers(bundle.peers)
        self._resolve_sotp(bundle.sotp)

        return bundle

    @staticmethod
    def _resolve_monte_carlo(params: MCParameters) -> None:
        """Applies defaults to Monte Carlo simulation settings."""
        if not params.enabled:
            return

        if params.iterations is None:
            params.iterations = MonteCarloDefaults.DEFAULT_SIMULATIONS

    @staticmethod
    def _resolve_sensitivity(params: SensitivityParameters) -> None:
        """Applies defaults to Sensitivity Analysis (Heatmap) settings."""
        if not params.enabled:
            return

        if params.steps is None:
            params.steps = SensitivityDefaults.DEFAULT_STEPS

        if params.wacc_span is None:
            params.wacc_span = SensitivityDefaults.DEFAULT_WACC_SPAN

        if params.growth_span is None:
            params.growth_span = SensitivityDefaults.DEFAULT_GROWTH_SPAN

    @staticmethod
    def _resolve_scenarios(params: ScenariosParameters) -> None:
        """
        Validates scenario configurations.
        Injects a neutral 'Base Case' if enabled but the list is empty (Safety Net).
        """
        if not params.enabled:
            return

        # Fallback: If enabled but list is empty -> Inject neutral Base Case
        if not params.cases:
            logger.info("[Resolver] Scenarios enabled but empty. Injecting default Base Case.")
            default_case = ScenarioParameters(
                name=ScenarioDefaults.DEFAULT_CASE_NAME,
                probability=ScenarioDefaults.DEFAULT_PROBABILITY,
                growth_override=None,  # None respects the base model value
                margin_override=None,
            )
            params.cases.append(default_case)

    @staticmethod
    def _resolve_backtest(params: BacktestParameters) -> None:
        """Applies defaults to Historical Backtesting."""
        if not params.enabled:
            return

        if params.lookback_years is None:
            params.lookback_years = BacktestDefaults.DEFAULT_LOOKBACK_YEARS

    @staticmethod
    def _resolve_peers(params: PeersParameters) -> None:
        """Validates Peer Group settings."""
        if not params.enabled:
            return

        if not params.tickers:
            logger.warning("[Resolver] Peer module enabled but no tickers provided.")
        elif len(params.tickers) < PeerDefaults.MIN_PEERS_REQUIRED:
            logger.debug(
                "[Resolver] Peer list size (%d) below recommended minimum (%d).",
                len(params.tickers),
                PeerDefaults.MIN_PEERS_REQUIRED,
            )

    @staticmethod
    def _resolve_sotp(params: SOTPParameters) -> None:
        """Applies defaults to Sum-of-the-Parts (Conglomerate) settings."""
        if not params.enabled:
            return

        # Log the segments to verify they are being received
        segment_count = len(params.segments) if params.segments else 0
        logger.info(f"[Resolver] SOTP enabled with {segment_count} segment(s)")

        if segment_count > 0:
            for idx, seg in enumerate(params.segments):
                logger.debug(f"[Resolver] SOTP Segment {idx + 1}: {seg.name} = {seg.value}")
        else:
            logger.warning("[Resolver] SOTP enabled but no segments provided")

        if params.conglomerate_discount is None:
            params.conglomerate_discount = SOTPDefaults.DEFAULT_CONGLOMERATE_DISCOUNT
