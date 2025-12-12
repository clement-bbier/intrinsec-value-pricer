import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class SimpleFCFFStrategy(ValuationStrategy):
    """
    STRATÉGIE 1 : DCF "SNAPSHOT" (BASE TTM).
    Utilise fcf_last.
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
        logger.info(
            "[Strategy] Executing SimpleFCFFStrategy | ticker=%s | currency=%s | years=%s",
            financials.ticker,
            financials.currency,
            params.projection_years,
        )

        # 1. Validation de l'input spécifique
        fcf_base = financials.fcf_last

        # Override manuel prioritaire
        if params.manual_fcf_base is not None:
            fcf_base = params.manual_fcf_base
            logger.info("[Simple] Override FCF Manuel : %s", fcf_base)

        if fcf_base is None:
            msg = (
                "Donnée manquante : FCF TTM (fcf_last) introuvable. "
                "Impossible d'exécuter la méthode Simple."
            )
            logger.error(
                "%s | ticker=%s",
                msg,
                financials.ticker,
            )
            raise CalculationError(msg)

        logger.info(
            "[Simple] FCF start=%s %s | source=%s",
            f"{fcf_base:,.0f}",
            financials.currency,
            "manual" if params.manual_fcf_base else "ttm"
        )

        # 2. Exécution du moteur standard
        return self._compute_standard_dcf(
            fcf_start=fcf_base,
            financials=financials,
            params=params,
        )