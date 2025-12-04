import logging
from abc import ABC, abstractmethod
from dataclasses import replace
from datetime import datetime

from core.models import DCFParameters
from infra.macro.yahoo_macro_provider import YahooMacroProvider

logger = logging.getLogger(__name__)


class HistoricalParamsStrategy(ABC):
    """
    Interface de stratégie pour les paramètres DCF dépendants du temps.

    Étant donné les DCFParameters de base (d'aujourd'hui) et une date passée,
    retourne les paramètres ajustés pour cette date (ex: taux sans risque historique).
    """

    @abstractmethod
    def get_params_for_date(self, date: datetime, base_params: DCFParameters) -> DCFParameters:
        """Retourne les paramètres ajustés pour la date donnée."""
        pass


class YahooMacroHistoricalParamsStrategy(HistoricalParamsStrategy):
    """
    Ajuste Rf (Taux sans risque) et Rd (Coût de la dette) basés sur l'historique macro.
    Hypothèse : Le spread de crédit de l'entreprise (Rd - Rf) reste constant par rapport à aujourd'hui.
    """

    def __init__(self, macro_provider: YahooMacroProvider, currency: str):
        self.macro_provider = macro_provider
        self.currency = currency
        self._initial_credit_spread: Optional[float] = None

    def get_params_for_date(self, date: datetime, base_params: DCFParameters) -> DCFParameters:
        """
        Calcule les DCFParameters historiques en ajustant le Taux sans Risque (Rf)
        et le Coût de la Dette (Rd).
        """
        # 1. Calculer le spread de crédit actuel une seule fois
        if self._initial_credit_spread is None:
            self._initial_credit_spread = base_params.cost_of_debt - base_params.risk_free_rate
            logger.info(
                "[HistParams] Spread de crédit initial (Rd - Rf) calculé : %.4f",
                self._initial_credit_spread,
            )

        # 2. Récupérer le contexte macro historique (Rf à la date t)
        macro = self.macro_provider.get_macro_context(date, self.currency)

        if not macro:
            # Fallback : on garde les paramètres actuels si pas de macro historique
            logger.warning(
                "[HistParams] Pas de contexte macro pour %s. Utilisation des paramètres de base.",
                date.date()
            )
            return base_params

        hist_rf = macro.risk_free_rate

        # 3. Reconstruire le Rd historique
        # Rd_t = Rf_t + Spread_constant
        hist_rd = hist_rf + self._initial_credit_spread

        # 4. Retourner les nouveaux paramètres (avec les hypothèses de croissance/impôts constantes)
        params_t = replace(
            base_params,
            risk_free_rate=hist_rf,
            cost_of_debt=hist_rd,
            # Le MRP, g, g∞, TaxRate restent constants pour la version simple
        )

        logger.info(
            "[HistParams] %s | Rf_t=%.4f | Rd_t=%.4f (Spread=%.4f)",
            date.date(),
            params_t.risk_free_rate,
            params_t.cost_of_debt,
            self._initial_credit_spread,
        )

        return params_t