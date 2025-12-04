import logging
from dataclasses import replace
from datetime import datetime
from typing import List, Tuple, Dict
import pandas as pd

from core.models import CompanyFinancials, DCFParameters, ValuationMode
from core.dcf.valuation_service import run_valuation
from core.dcf.historical_params import HistoricalParamsStrategy
from core.exceptions import CalculationError
from infra.data_providers.yahoo_provider import YahooFinanceProvider

logger = logging.getLogger(__name__)


def build_intrinsic_value_time_series(
        ticker: str,
        financials: CompanyFinancials,
        base_params: DCFParameters,
        mode: ValuationMode,
        provider: YahooFinanceProvider,
        params_strategy: HistoricalParamsStrategy,
        sample_dates: List[datetime],
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Calcule la Valeur Intrinsèque Historique (VIH) pour une liste de dates.

    Retourne:
      1. DataFrame [Date, Intrinsic Value, Market Price]
      2. Liste de messages d'erreurs/warnings pour l'UI (ex: "2021-05: Pas de bilan dispo")
    """

    results = []
    ui_messages = []

    # Pré-chargement de l'historique de prix complet pour éviter les appels API en boucle
    try:
        full_price_history = provider.get_price_history(ticker, period="max")
    except Exception:
        full_price_history = pd.DataFrame()

    logger.info(f"[HistIV] Démarrage calcul sur {len(sample_dates)} points pour {ticker}")

    for dt in sample_dates:
        date_str = dt.strftime('%Y-%m')

        # --- 1. Prix Historique ---
        # On cherche le prix dans notre dataframe complet
        price_t = None
        if not full_price_history.empty:
            # Slicing jusqu'à la date
            past_prices = full_price_history[full_price_history.index <= dt]
            if not past_prices.empty:
                # On prend le dernier prix connu
                price_t = float(past_prices.iloc[-1]["Close"])

        if price_t is None:
            msg = f"{date_str}: Prix de marché introuvable."
            ui_messages.append(msg)
            logger.warning(f"[HistIV] {msg}")
            # Sans prix, on peut quand même calculer la VI, mais on ne pourra pas comparer.
            # On continue, mais c'est un point faible.
            price_t = 0.0

            # --- 2. Fondamentaux Historiques (Le plus critique) ---
        # On demande au provider : "Qu'est-ce qu'on savait à cette date ?"
        hist_fund, fund_errors = provider.get_historical_fundamentals_for_date(ticker, dt)

        if not hist_fund:
            # Échec critique : pas de données fondamentales (FCF, Dette...)
            # On ne peut PAS calculer une VI fiable. On saute ce point.
            reasons = "; ".join(fund_errors)
            msg = f"{date_str}: Calcul impossible. {reasons}"
            ui_messages.append(msg)
            logger.warning(f"[HistIV] Skip {dt.date()} -> {reasons}")
            continue

        # Construction de l'objet Financials à la date t
        # On garde les shares constants si pas trouvés (souvent acceptable)
        fin_t = replace(
            financials,
            current_price=price_t,
            fcf_last=hist_fund.get('fcf_last', financials.fcf_last),
            total_debt=hist_fund.get('total_debt', financials.total_debt),
            cash_and_equivalents=hist_fund.get('cash_and_equivalents', financials.cash_and_equivalents),
            beta=hist_fund.get('beta', financials.beta)
        )

        # --- 3. Paramètres Macro Historiques ---
        params_t = params_strategy.get_params_for_date(dt, base_params)

        # --- 4. Calcul de la VI ---
        try:
            dcf_res = run_valuation(fin_t, params_t, mode)
            iv = dcf_res.intrinsic_value_per_share

            # Succès !
            results.append({
                "Date": dt,
                "Intrinsic Value": iv,
                "Market Price": price_t if price_t > 0 else None
            })

        except CalculationError as e:
            msg = f"{date_str}: Erreur mathématique DCF ({str(e)})"
            ui_messages.append(msg)
        except Exception as e:
            msg = f"{date_str}: Erreur inattendue ({str(e)})"
            ui_messages.append(msg)

    # Création du DF final
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("Date")

    # Filtrage des messages d'erreur pour éviter le spam (max 5 erreurs uniques affichées)
    unique_msgs = sorted(list(set(ui_messages)))
    if len(unique_msgs) > 5:
        unique_msgs = unique_msgs[:5] + ["... et d'autres erreurs similaires."]

    return df, unique_msgs