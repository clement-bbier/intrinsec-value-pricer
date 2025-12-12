import logging
from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.valuation.strategies.abstract import ValuationStrategy
from core.exceptions import CalculationError

logger = logging.getLogger(__name__)


class FundamentalFCFFStrategy(ValuationStrategy):
    """
    STRATÉGIE 2 : DCF "FONDAMENTAL" (BASE NORMALISÉE).

    PHILOSOPHIE :
    Au lieu de croire aveuglément les chiffres de l'année passée, cette méthode cherche
    la "capacité bénéficiaire normative" de l'entreprise. Elle utilise un FCF reconstruit
    et lissé sur plusieurs années (généralement Moyenne Pondérée sur 3-5 ans).

    QUAND L'UTILISER ?
    - Entreprises cycliques (Industrie, Matériaux).
    - Entreprises ayant eu une année récente atypique (Covid, amende exceptionnelle).
    - Pour une analyse conservatrice.

    CONTRAINTES & VALIDATION :
    - Cette classe suppose que l'objet `params` a été validé par `FundamentalDCFConfig`.
    - Elle exige la présence de `financials.fcf_fundamental_smoothed`.
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
        logger.info("[Strategy] Mode Fondamental FCFF sélectionné.")

        # 1. Validation de la donnée brute nécessaire
        if financials.fcf_fundamental_smoothed is None:
            msg = (
                "Donnée manquante : FCF Fondamental Lissé. "
                "La méthode 2 nécessite un historique financier complet (EBIT, Capex, BFR sur 5 ans) "
                "pour calculer une moyenne normative. Essayez la méthode 1 (Simple) si l'historique est trop court."
            )
            logger.warning(msg)
            raise CalculationError(msg)

        logger.info(
            f"[Fundamental] Point de départ Normatif (FCF Lissé) : {financials.fcf_fundamental_smoothed:,.0f} {financials.currency}")

        # 2. Exécution via le moteur standard
        return self._compute_standard_dcf(
            fcf_start=financials.fcf_fundamental_smoothed,
            financials=financials,
            params=params
        )