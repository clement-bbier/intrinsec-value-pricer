import logging
import pandas as pd
from typing import List, Tuple, Optional
from datetime import datetime

from core.models import CompanyFinancials, DCFParameters, ValuationMode, InputSource
from core.valuation.engines import STRATEGY_REGISTRY
from core.computation.transformations import calculate_total_debt_from_net
from infra.data_providers.base_provider import DataProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

logger = logging.getLogger(__name__)


class YahooMacroHistoricalParamsStrategy:
    """Strategy pour l'historique macro (Proxy)."""

    def __init__(self, macro_provider: YahooMacroProvider, currency: str):
        self.macro_provider = macro_provider
        self.currency = currency

    def get_params_at_date(self, date: datetime, current_params: DCFParameters) -> DCFParameters:
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
    Calcule la série temporelle de Valeur Intrinsèque.
    Mode: Best Effort (ne lève pas d'exception bloquante).
    """
    results = []
    errors = []

    # Force le mode fondamental pour performance
    history_mode = ValuationMode.FUNDAMENTAL_FCFF if mode == ValuationMode.MONTE_CARLO else mode

    for dt in dates:
        try:
            # 1. Fetch Snapshot
            hist_data, logs = provider.get_historical_fundamentals_for_date(ticker, dt)
            if not hist_data:
                continue

            # 2. Build Financials Snapshot
            hist_financials = CompanyFinancials(
                ticker=ticker,
                currency=current_financials.currency,
                sector=current_financials.sector,
                industry=current_financials.industry,
                country=current_financials.country,
                current_price=0.0,
                shares_outstanding=hist_data.get('shares_outstanding', 1.0),
                total_debt=hist_data.get('total_debt', 0.0),
                cash_and_equivalents=hist_data.get('cash_and_equivalents', 0.0),
                interest_expense=0.0,  # Non critique pour historique simplifié
                beta=hist_data.get('beta', 1.0),
                fcf_last=hist_data.get('fcf_last'),
                fcf_fundamental_smoothed=hist_data.get('fcf_last'),  # Proxy
                source_fcf="historical"
            )

            # 3. Get Params Snapshot
            hist_params = macro_strategy.get_params_at_date(dt, current_params)

            # 4. Resolve Strategy
            strategy_cls = STRATEGY_REGISTRY.get(history_mode)
            if not strategy_cls:
                continue

            # 5. Execute
            result = strategy_cls().execute(hist_financials, hist_params)

            results.append({
                "Date": dt,
                "Intrinsic Value": result.intrinsic_value_per_share
            })

        except Exception as e:
            # On ignore les erreurs individuelles de date
            errors.append(f"{dt.date()}: {str(e)}")
            continue

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("Date")

    return df, errors