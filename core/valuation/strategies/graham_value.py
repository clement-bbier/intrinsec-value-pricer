import logging
from math import sqrt
from core.models import CompanyFinancials, DCFParameters, GrahamValuationResult
from core.valuation.strategies.abstract import ValuationStrategy
from core.exceptions import CalculationError

logger = logging.getLogger(__name__)


class GrahamNumberStrategy(ValuationStrategy):
    """
    STRATÉGIE 6 : FORMULE DE BENJAMIN GRAHAM.
    V = Sqrt(22.5 * EPS * BVPS).
    Approche "Deep Value" classique.
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> GrahamValuationResult:
        logger.info("[Strategy] Executing GrahamNumberStrategy")

        eps = financials.eps_ttm
        bvps = financials.book_value_per_share

        # Override manuel : agit sur l'EPS
        if params.manual_fcf_base:
            eps = params.manual_fcf_base

        if eps is None or bvps is None:
            raise CalculationError("Données manquantes : EPS et Book Value requis pour la formule de Graham.")

        # La formule de Graham requiert des valeurs positives
        intrinsic_value = 0.0

        if eps > 0 and bvps > 0:
            intrinsic_value = sqrt(22.5 * eps * bvps)
        else:
            logger.warning(
                "Graham impossible : EPS (%.2f) ou BVPS (%.2f) négatif ou nul. Retourne 0.",
                eps, bvps
            )
            # On retourne 0 mais proprement

        return GrahamValuationResult(
            request=None,
            financials=financials,
            params=params,
            intrinsic_value_per_share=intrinsic_value,
            market_price=financials.current_price,
            eps_used=eps,
            book_value_used=bvps,
            graham_multiplier=22.5
        )