import logging
from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)

class StandardFCFFStrategy(ValuationStrategy):
    """
    STRATÉGIE 1 : STANDARD TWO-STAGE FCFF.
    (Anciennement Simple DCF)
    Utilise le FCF TTM comme point de départ (Snapshot).
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFValuationResult:
        logger.info(
            "[Strategy] Executing StandardFCFFStrategy | ticker=%s | years=%s",
            financials.ticker,
            params.projection_years,
        )

        # 1. Validation de l'input spécifique
        fcf_base = financials.fcf_last

        # Override manuel prioritaire (géré via params)
        if params.manual_fcf_base is not None:
            fcf_base = params.manual_fcf_base
            logger.info("[Standard] Override FCF Manuel : %s", fcf_base)

        if fcf_base is None:
            msg = (
                "Donnée manquante : FCF TTM (fcf_last) introuvable. "
                "Impossible d'exécuter la méthode Standard sans flux de départ."
            )
            logger.error("%s | ticker=%s", msg, financials.ticker)
            raise CalculationError(msg)

        # 2. Délégation au moteur standard (Abstract) qui gère la Trace d'Audit
        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )