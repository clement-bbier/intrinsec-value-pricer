import logging
from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.valuation.strategies.abstract import ValuationStrategy
from core.exceptions import CalculationError

logger = logging.getLogger(__name__)


class SimpleFCFFStrategy(ValuationStrategy):
    """
    STRATÉGIE 1 : DCF "SNAPSHOT" (BASE TTM).

    PHILOSOPHIE :
    Cette méthode prend une "photo instantanée" de l'entreprise. Elle part du principe que
    les résultats des 12 derniers mois (TTM - Trailing Twelve Months) sont le meilleur
    proxy disponible pour prédire la performance future.

    QUAND L'UTILISER ?
    - Entreprises matures et stables (ex: Coca-Cola, Air Liquide).
    - Première estimation rapide ("Back of the envelope calculation").

    CONTRAINTES & VALIDATION :
    - Cette classe suppose que l'objet `params` a été validé par `SimpleDCFConfig`.
    - Elle exige la présence de `financials.fcf_last`.
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
        logger.info("[Strategy] Mode Simple FCFF sélectionné.")

        # 1. Validation de la donnée brute nécessaire
        if financials.fcf_last is None:
            # C'est une erreur de donnée (Data), pas de config (User)
            logger.error(f"Donnée manquante pour {financials.ticker}: FCF TTM (fcf_last) est None.")
            raise CalculationError(
                "Donnée manquante : FCF TTM (fcf_last). "
                "Impossible d'exécuter la méthode Simple sans un flux de référence récent. "
                "Vérifiez que le ticker est correct et que les données financières sont disponibles."
            )

        logger.info(f"[Simple] Point de départ (FCF TTM) : {financials.fcf_last:,.0f} {financials.currency}")

        # 2. Exécution via le moteur standard (hérité de ValuationStrategy)
        # Note: Le moteur standard s'occupe de la projection et de l'actualisation
        return self._compute_standard_dcf(
            fcf_start=financials.fcf_last,
            financials=financials,
            params=params
        )