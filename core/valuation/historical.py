import logging
import pandas as pd
from typing import List, Tuple, Optional
from datetime import datetime

from core.models import CompanyFinancials, DCFParameters, ValuationMode, InputSource
# [CORRECTION] On importe le registre au lieu de l'ancienne fonction supprimée
from core.valuation.engines import STRATEGY_REGISTRY
from core.computation.transformations import calculate_total_debt_from_net
from infra.data_providers.base_provider import DataProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

logger = logging.getLogger(__name__)


class YahooMacroHistoricalParamsStrategy:
    """
    Stratégie pour récupérer les paramètres macro (Rf, MRP) historiques.
    """

    def __init__(self, macro_provider: YahooMacroProvider, currency: str):
        self.macro_provider = macro_provider
        self.currency = currency

    def get_params_at_date(self, date: datetime, current_params: DCFParameters) -> DCFParameters:
        """
        Reconstruit un objet DCFParameters approximatif pour une date passée.
        Note: C'est une approximation 'Best Effort'.
        """
        # Pour cette version, on garde les paramètres actuels comme proxy,
        # sauf si on connecte une API macro historique complète.
        return current_params


def build_intrinsic_value_time_series(
        ticker: str,
        current_financials: CompanyFinancials,
        current_params: DCFParameters,
        mode: ValuationMode,
        provider: DataProvider,
        macro_strategy: YahooMacroHistoricalParamsStrategy,
        dates: List[datetime]
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Calcule la Valeur Intrinsèque (VI) historique sur une série de dates.

    LOGIQUE SÉNIOR :
    - Si Mode == MONTE_CARLO -> On force le mode FUNDAMENTAL pour l'historique (Performance).
    - Utilise le STRATEGY_REGISTRY pour instancier le moteur correct.
    """

    results = []
    errors = []

    # Force le mode déterministe pour l'historique pour éviter l'explosion du temps de calcul
    history_mode = mode
    if mode == ValuationMode.MONTE_CARLO:
        history_mode = ValuationMode.FUNDAMENTAL_FCFF
        # On loggue une seule fois pour éviter le spam
        logger.info("[Historical] Switch Monte Carlo -> Fondamental pour le backtesting (Perf).")

    for dt in dates:
        try:
            # 1. Récupération des fondamentaux à la date T (Snapshot)
            hist_data, logs = provider.get_historical_fundamentals_for_date(ticker, dt)

            if hist_data is None:
                continue  # Pas de données pour cette date

            # 2. Reconstruction de l'objet Financials à la date T
            hist_financials = CompanyFinancials(
                ticker=ticker,
                currency=current_financials.currency,
                sector=current_financials.sector,
                industry=current_financials.industry,
                current_price=0.0,  # Sera ignoré par le DCF fondamental
                shares_outstanding=hist_data.get('shares_outstanding', current_financials.shares_outstanding),
                total_debt=hist_data.get('total_debt', current_financials.total_debt),
                cash_and_equivalents=hist_data.get('cash_and_equivalents', current_financials.cash_and_equivalents),
                beta=hist_data.get('beta', current_financials.beta),
                fcf_last=hist_data.get('fcf_last'),
                fcf_fundamental_smoothed=hist_data.get('fcf_last'),  # Proxy si pas d'historique lissé complet
                source_fcf="historical_proxy"
            )

            # 3. Paramètres à la date T
            hist_params = macro_strategy.get_params_at_date(dt, current_params)

            # [CORRECTION IMPORTANTE] Instanciation via Registre
            strategy_cls = STRATEGY_REGISTRY.get(history_mode)
            if not strategy_cls:
                errors.append(f"Mode non supporté: {history_mode}")
                continue

            # 4. Exécution
            strategy = strategy_cls()
            result = strategy.execute(hist_financials, hist_params)

            results.append({
                "Date": dt,
                "Intrinsic Value": result.intrinsic_value_per_share,
                "WACC": result.wacc
            })

        except Exception as e:
            # On ne casse pas toute la boucle pour une date erronée
            errors.append(str(e))
            continue

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("Date")

    return df, errors