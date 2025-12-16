import logging
from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)

class FundamentalFCFFStrategy(ValuationStrategy):
    """
    STRATÉGIE 2 : DCF "FONDAMENTAL".
    Utilise le Free Cash Flow normatif (lissé sur plusieurs années ou ajusté).
    Idéal pour les entreprises industrielles cycliques.
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFValuationResult:
        logger.info(
            "[Strategy] Executing FundamentalFCFFStrategy | ticker=%s",
            financials.ticker
        )

        # 1. Validation de l'input spécifique
        fcf_base = financials.fcf_fundamental_smoothed

        # Override manuel prioritaire
        if params.manual_fcf_base is not None:
            fcf_base = params.manual_fcf_base
            logger.info("[Fundamental] Override FCF Manuel : %s", fcf_base)

        if fcf_base is None:
            msg = (
                "Donnée manquante : FCF Fondamental Lissé non disponible. "
                "Impossible d'exécuter la méthode Analytique sans historique suffisant pour lisser les cycles."
            )
            logger.warning("%s | ticker=%s", msg, financials.ticker)
            raise CalculationError(msg)

        logger.info(
            "[Fundamental] FCF start=%s %s | source=%s",
            f"{fcf_base:,.0f}",
            financials.currency,
            "manual" if params.manual_fcf_base else "smoothed"
        )

        # 2. Délégation au moteur standard (Abstract)
        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )