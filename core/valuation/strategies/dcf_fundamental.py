import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class FundamentalFCFFStrategy(ValuationStrategy):
    """
    STRATÉGIE 2 : DCF "FONDAMENTAL" (BASE NORMALISÉE).
    Utilise fcf_fundamental_smoothed.
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
        logger.info(
            "[Strategy] Executing FundamentalFCFFStrategy | ticker=%s | currency=%s | years=%s",
            financials.ticker,
            financials.currency,
            params.projection_years,
        )

        # 1. Validation de l'input spécifique à la stratégie
        fcf_base = financials.fcf_fundamental_smoothed

        # Override manuel prioritaire (géré au niveau global params, mais appliqué ici)
        if params.manual_fcf_base is not None:
            fcf_base = params.manual_fcf_base
            logger.info("[Fundamental] Override FCF Manuel : %s", fcf_base)

        if fcf_base is None:
            msg = (
                "Donnée manquante : FCF Fondamental Lissé non disponible. "
                "Impossible d'exécuter la méthode Analytique sans historique suffisant."
            )
            logger.warning(
                "%s | ticker=%s",
                msg,
                financials.ticker,
            )
            raise CalculationError(msg)

        logger.info(
            "[Fundamental] FCF start=%s %s | source=%s",
            f"{fcf_base:,.0f}",
            financials.currency,
            "manual" if params.manual_fcf_base else "smoothed"
        )

        # 2. Exécution du moteur standard
        return self._compute_standard_dcf(
            fcf_start=fcf_base,
            financials=financials,
            params=params,
        )