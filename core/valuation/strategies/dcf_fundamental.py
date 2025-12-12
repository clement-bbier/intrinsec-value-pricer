import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class FundamentalFCFFStrategy(ValuationStrategy):
    """
    STRATÉGIE 2 : DCF "FONDAMENTAL" (BASE NORMALISÉE).

    Philosophie :
    - Utilise un FCF reconstruit/lissé (normatif) pour réduire la sensibilité aux années atypiques.

    Préconditions :
    - `financials.fcf_fundamental_smoothed` doit être disponible.
    - Les paramètres `params` sont supposés valides (validation en amont).
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
        logger.info(
            "[Strategy] Executing FundamentalFCFFStrategy | ticker=%s | currency=%s | years=%s",
            financials.ticker,
            financials.currency,
            params.projection_years,
        )

        if financials.fcf_fundamental_smoothed is None:
            msg = (
                "Missing data: smoothed fundamental FCF is unavailable. "
                "Fundamental method requires sufficient financial history (e.g., EBIT/Capex/NWC over multiple years). "
                "Use Simple method if history is too short."
            )
            logger.warning(
                "%s | ticker=%s | field=fcf_fundamental_smoothed | method=FundamentalFCFFStrategy",
                msg,
                financials.ticker,
            )
            raise CalculationError(msg)

        logger.info(
            "[Fundamental] FCF start=%s %s | source=smoothed",
            f"{financials.fcf_fundamental_smoothed:,.0f}",
            financials.currency,
        )

        return self._compute_standard_dcf(
            fcf_start=financials.fcf_fundamental_smoothed,
            financials=financials,
            params=params,
        )
