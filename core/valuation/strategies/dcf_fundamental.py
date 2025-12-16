import logging
from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)

class FundamentalFCFFStrategy(ValuationStrategy):
    """
    STRATÉGIE 2 : NORMALIZED FCFF (CYCLICAL/FUNDAMENTAL).
    Utilise le Free Cash Flow normatif.
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFValuationResult:
        logger.info(
            "[Strategy] Executing FundamentalFCFFStrategy | ticker=%s",
            financials.ticker
        )

        fcf_base = financials.fcf_fundamental_smoothed

        if params.manual_fcf_base is not None:
            fcf_base = params.manual_fcf_base
            logger.info("[Fundamental] Override FCF Manuel : %s", fcf_base)

        if fcf_base is None:
            msg = "Donnée manquante : FCF Fondamental Lissé non disponible."
            logger.warning("%s | ticker=%s", msg, financials.ticker)
            raise CalculationError(msg)

        # Délégation au moteur standard (Abstract)
        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )