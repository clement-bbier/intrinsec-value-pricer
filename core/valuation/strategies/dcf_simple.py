import logging
from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)

class SimpleFCFFStrategy(ValuationStrategy):
    """
    STRATÉGIE 1 : DCF "SNAPSHOT" (BASE TTM).
    Utilise fcf_last (Free Cash Flow Trailing 12 Months).
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFValuationResult:
        logger.info(
            "[Strategy] Executing SimpleFCFFStrategy | ticker=%s | currency=%s | years=%s",
            financials.ticker,
            financials.currency,
            params.projection_years,
        )

        # 1. Validation de l'input spécifique
        fcf_base = financials.fcf_last

        # Override manuel prioritaire (géré via params)
        if params.manual_fcf_base is not None:
            fcf_base = params.manual_fcf_base
            logger.info("[Simple] Override FCF Manuel : %s", fcf_base)

        if fcf_base is None:
            msg = (
                "Donnée manquante : FCF TTM (fcf_last) introuvable. "
                "Impossible d'exécuter la méthode Simple sans flux de départ."
            )
            logger.error("%s | ticker=%s", msg, financials.ticker)
            raise CalculationError(msg)

        logger.info(
            "[Simple] FCF start=%s %s | source=%s",
            f"{fcf_base:,.0f}",
            financials.currency,
            "manual" if params.manual_fcf_base else "ttm"
        )

        # 2. Délégation au moteur standard (Abstract)
        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )