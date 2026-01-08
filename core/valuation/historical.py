"""
core/valuation/historical.py
MOTEUR DE SÉRIES TEMPORELLES — VERSION V3.2
Rôle : Reconstruction de la valeur intrinsèque historique (Honest Snapshot).
Note : Suppression des "zéro-fill" automatiques pour préserver l'intégrité graphique.
"""

import logging
import pandas as pd
from typing import List, Tuple, Optional
from datetime import datetime

from core.models import CompanyFinancials, DCFParameters, ValuationMode, InputSource
from core.valuation.engines import STRATEGY_REGISTRY
from infra.data_providers.base_provider import DataProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

logger = logging.getLogger(__name__)


class YahooMacroHistoricalParamsStrategy:
    """Strategy pour l'historique macro (Proxy)."""

    def __init__(self, macro_provider: YahooMacroProvider, currency: str):
        self.macro_provider = macro_provider
        self.currency = currency

    def get_params_at_date(self, date: datetime, current_params: DCFParameters) -> DCFParameters:
        """
        Pour l'instant, conserve les paramètres de croissance/risque actuels
        sur l'axe historique (ajustement macro dynamique en V4).
        """
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
    Standard : 'Honest Data' — Si une donnée manque, la date est sautée.
    """
    results = []
    errors = []

    # On utilise le mode fondamental pour la stabilité historique si Monte Carlo est demandé
    history_mode = ValuationMode.FCFF_NORMALIZED if mode == ValuationMode.FCFF_REVENUE_DRIVEN else mode
    if mode == ValuationMode.RESIDUAL_INCOME_MODEL:
        history_mode = ValuationMode.RESIDUAL_INCOME_MODEL

    for dt in dates:
        try:
            # 1. Fetch Snapshot (Données brutes de la date T)
            hist_data, _ = provider.get_historical_fundamentals_for_date(ticker, dt)
            if not hist_data:
                continue

            # 2. Build Financials Snapshot (Souveraineté des données réelles)
            # On ne met plus de valeurs par défaut (0.0 ou 1.0) qui faussent l'analyse
            hist_financials = CompanyFinancials(
                ticker=ticker,
                currency=current_financials.currency,
                name=current_financials.name,
                sector=current_financials.sector,
                industry=current_financials.industry,
                country=current_financials.country,
                current_price=0.0,  # Le prix n'impacte pas la valeur intrinsèque pure

                # Extraction sans fallbacks "menteurs"
                shares_outstanding=hist_data.get('shares_outstanding'),
                total_debt=hist_data.get('total_debt'),
                cash_and_equivalents=hist_data.get('cash_and_equivalents'),
                minority_interests=hist_data.get('minority_interests', 0.0),
                pension_provisions=hist_data.get('pension_provisions', 0.0),

                interest_expense=hist_data.get('interest_expense', 0.0),
                beta=hist_data.get('beta'),

                fcf_last=hist_data.get('fcf_last'),
                fcf_fundamental_smoothed=hist_data.get('fcf_last'),

                revenue_ttm=hist_data.get('revenue_ttm'),
                ebitda_ttm=hist_data.get('ebitda_ttm'),
                net_income_ttm=hist_data.get('net_income_ttm'),
                book_value_per_share=hist_data.get('book_value_per_share'),

                source_fcf="historical_reconstruction"
            )

            # 3. Get Params Snapshot
            hist_params = macro_strategy.get_params_at_date(dt, current_params)

            # 4. Resolve Strategy & Execution
            strategy_cls = STRATEGY_REGISTRY.get(history_mode)
            if not strategy_cls:
                continue

            # Exécution du moteur de calcul (sera rejeté par Pydantic/Engine si données None critiques)
            result = strategy_cls().execute(hist_financials, hist_params)

            results.append({
                "Date": dt,
                "Intrinsic Value": result.intrinsic_value_per_share
            })

        except Exception as e:
            # Enregistrement de l'erreur pour diagnostic technique expander
            errors.append(f"{dt.date()}: {str(e)}")
            continue

    # 5. Finalisation du DataFrame
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("Date")

    return df, errors