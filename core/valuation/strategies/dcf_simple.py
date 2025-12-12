import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class SimpleFCFFStrategy(ValuationStrategy):
    """
    STRATÉGIE 1 : DCF "SNAPSHOT" (BASE TTM).

    Philosophie :
    - Approche "photo" : le FCF des 12 derniers mois (TTM) sert de base de projection.
    - Méthode rapide pour une première estimation.

    Préconditions :
    - `financials.fcf_last` doit être disponible.
    - Les paramètres `params` sont supposés valides (ex: cohérence WACC vs g∞, horizon, etc.).
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
        """
        Execute the Simple FCFF valuation.

        Notes (observabilité) :
        - Cette stratégie peut être appelée comme moteur interne (ex: Monte Carlo).
        - Les logs doivent donc rester neutres (pas d’assertion "mode sélectionné").
        """
        logger.info(
            "[Strategy] Executing SimpleFCFFStrategy | ticker=%s | currency=%s | years=%s",
            financials.ticker,
            financials.currency,
            params.projection_years,
        )

        if financials.fcf_last is None:
            logger.error(
                "Missing required data | ticker=%s | field=fcf_last | method=SimpleFCFFStrategy",
                financials.ticker,
            )
            raise CalculationError(
                "Donnée manquante : FCF TTM (fcf_last). "
                "Impossible d'exécuter la méthode Simple sans un flux de référence récent. "
                "Vérifiez que le ticker est correct et que les données financières sont disponibles."
            )

        logger.info(
            "[Simple] FCF start=%s %s | source=ttm",
            f"{financials.fcf_last:,.0f}",
            financials.currency,
        )

        return self._compute_standard_dcf(
            fcf_start=financials.fcf_last,
            financials=financials,
            params=params,
        )
