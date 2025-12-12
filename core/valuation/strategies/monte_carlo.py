import logging
from dataclasses import replace
from typing import Optional

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class MonteCarloDCFStrategy(ValuationStrategy):
    """
    STRATÉGIE 3 : DCF PROBABILISTE (MONTE CARLO).

    Positionnement (important) :
    - Cette Strategy est maintenue pour compatibilité/évolution (registry).
    - La source de vérité du Monte Carlo runtime est le moteur `run_monte_carlo_dcf`
      (core.valuation.engines) afin d'éviter une duplication divergente.

    Préconditions :
    - Les volatilités doivent être définies dans `params` :
      beta_volatility, growth_volatility, terminal_growth_volatility.
    - Un FCF de départ doit exister (TTM ou fondamental lissé).
    """

    N_SIMULATIONS = 5000

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
        """
        Executes Monte Carlo DCF via the engine-level implementation (single source of truth).
        """
        sims = int(getattr(params, "num_simulations", 0) or self.N_SIMULATIONS)

        logger.info(
            "[Strategy] Executing MonteCarloDCFStrategy | ticker=%s | currency=%s | years=%s | sims=%s",
            financials.ticker,
            financials.currency,
            params.projection_years,
            sims,
        )

        base_fcf = financials.fcf_fundamental_smoothed
        if base_fcf is None or base_fcf == 0:
            base_fcf = financials.fcf_last
            logger.info("[MonteCarlo] FCF start source=ttm (smoothed unavailable).")
        else:
            logger.info("[MonteCarlo] FCF start source=smoothed.")

        if base_fcf is None:
            raise CalculationError(
                f"Missing data: no FCF available (neither TTM nor smoothed) | ticker={financials.ticker}"
            )

        # Note:
        # - We DO NOT set a global NumPy seed here (side-effects across app).
        # - Reproducibility is handled at engine level/tests if needed.

        # We call the engine Monte Carlo implementation to avoid divergence.
        try:
            from core.valuation.engines import run_monte_carlo_dcf
        except Exception as exc:
            raise CalculationError("Monte Carlo engine is unavailable") from exc

        # Ensure we pass a params instance that has the same projection_years, weights normalized, etc.
        # We do not mutate the original params object here (clean functional behavior).
        safe_params = replace(params)
        try:
            safe_params.normalize_weights()
        except Exception:
            # normalize_weights may not exist in older versions; ignore silently (non-breaking).
            pass

        result = run_monte_carlo_dcf(financials, safe_params, num_simulations=sims)

        # Ensure the median/central value is well-defined:
        # engine returns a deterministic DCFResult + attaches simulation_results
        if not result.simulation_results:
            raise CalculationError(
                f"Monte Carlo produced no valid scenarios (empty distribution) | ticker={financials.ticker}"
            )

        logger.info(
            "[MonteCarlo] Completed | ticker=%s | valid_scenarios=%s/%s",
            financials.ticker,
            len(result.simulation_results),
            sims,
        )
        return result
