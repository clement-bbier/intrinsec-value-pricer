import logging
import pandas as pd
from typing import List, Tuple, Optional
from datetime import datetime

from core.models import CompanyFinancials, DCFParameters, ValuationMode, InputSource
from core.valuation.engines import run_deterministic_dcf
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
        Note: C'est une approximation 'Best Effort' car l'historique macro précis est coûteux.
        On garde les inputs structurels (Croissance, Taxe) constants pour voir l'impact du Prix/WACC.
        """
        # Idéalement, on récupérerait le Rf historique ici.
        # Pour cette version, on garde les paramètres actuels comme proxy,
        # sauf si on connecte une API macro historique.
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
    - On tente de récupérer les fondamentaux (Dette, Cash, Shares) à la date T.
    """

    results = []
    errors = []

    # Force le mode déterministe pour l'historique pour éviter l'explosion du temps de calcul
    history_mode = mode
    if mode == ValuationMode.MONTE_CARLO:
        history_mode = ValuationMode.FUNDAMENTAL_FCFF
        logger.info("[Historical] Switch Monte Carlo -> Fondamental pour le backtesting (Perf).")

    for dt in dates:
        try:
            # 1. Récupération des fondamentaux à la date T (Snapshot)
            hist_data, logs = provider.get_historical_fundamentals_for_date(ticker, dt)

            if hist_data is None:
                continue  # Pas de données pour cette date

            # 2. Reconstruction de l'objet Financials à la date T
            # On clone l'actuel et on remplace les valeurs changeantes
            hist_financials = CompanyFinancials(
                ticker=ticker,
                currency=current_financials.currency,
                sector=current_financials.sector,
                industry=current_financials.industry,
                current_price=0.0,  # Sera ignoré par le DCF fondamental, mais propre
                shares_outstanding=hist_data.get('shares_outstanding', current_financials.shares_outstanding),
                total_debt=hist_data.get('total_debt', current_financials.total_debt),
                cash_and_equivalents=hist_data.get('cash_and_equivalents', current_financials.cash_and_equivalents),
                beta=hist_data.get('beta', current_financials.beta),
                fcf_last=hist_data.get('fcf_last'),  # Important pour méthode Simple
                # On suppose que le lissage fondamental reste valide structurellement,
                # ou on utilise le FCF TTM historique comme proxy du fondamental
                fcf_fundamental_smoothed=hist_data.get('fcf_last')
            )

            # 3. Paramètres à la date T
            hist_params = macro_strategy.get_params_at_date(dt, current_params)

            # 4. Calcul
            result = run_deterministic_dcf(hist_financials, hist_params, history_mode)

            results.append({
                "Date": dt,
                "Intrinsic Value": result.intrinsic_value_per_share,
                "WACC": result.wacc
            })

        except Exception as e:
            # On ne casse pas toute la boucle pour une date erronée
            # logger.debug(f"Skip date {dt}: {e}")
            errors.append(str(e))
            continue

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("Date")

    return df, errors