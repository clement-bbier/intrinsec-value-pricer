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

    Notes :
    - Le paramètre `mode` est passé tel quel à `run_valuation`, ce qui permet
      d'utiliser aussi bien la Méthode 1 (FCFF simple) que la Méthode 2
      (FCFF fondamental) pour l'historique.
    - Pour la Méthode 2, le champ `fcf_fundamental_smoothed` provient de
      `financials` (calculé sur plusieurs années) et est réutilisé tel quel
      pour chaque date historique (approximation raisonnable pour une V1).
    """

    results: List[Dict[str, object]] = []
    ui_messages: List[str] = []

    # Pré-chargement de l'historique de prix complet pour éviter les appels API en boucle
    try:
        full_price_history = provider.get_price_history(ticker, period="max")
    except Exception as e:
        logger.warning(
            "[HistIV] Impossible de récupérer l'historique complet de prix pour %s: %s",
            ticker,
            e,
        )
        full_price_history = pd.DataFrame()

    logger.info("[HistIV] Démarrage calcul sur %d points pour %s", len(sample_dates), ticker)

    for dt in sample_dates:
        date_str = dt.strftime("%Y-%m")

        # ------------------------------------------------------------------
        # 1. Prix Historique
        # ------------------------------------------------------------------
        price_t = None
        if not full_price_history.empty:
            past_prices = full_price_history[full_price_history.index <= dt]
            if not past_prices.empty:
                # On prend le dernier prix connu à cette date ou avant
                # (Close déjà normalisé dans provider.get_price_history)
                price_t = float(past_prices.iloc[-1]["Close"])

        if price_t is None:
            msg = f"{date_str}: Prix de marché introuvable."
            ui_messages.append(msg)
            logger.warning("[HistIV] %s", msg)
            # Sans prix, on peut quand même calculer une VI, mais pas comparer => on met 0.0
            price_t = 0.0

        # ------------------------------------------------------------------
        # 2. Fondamentaux Historiques (critique)
        # ------------------------------------------------------------------
        # On demande au provider : "Qu'est-ce qu'on savait à cette date ?"
        hist_fund, fund_errors = provider.get_historical_fundamentals_for_date(ticker, dt)

        if not hist_fund:
            # Échec critique : pas de données fondamentales (FCF, Dette...)
            reasons = "; ".join(fund_errors)
            msg = f"{date_str}: Calcul impossible. {reasons}"
            ui_messages.append(msg)
            logger.warning("[HistIV] Skip %s -> %s", dt.date(), reasons)
            continue

        # Construction de l'objet Financials à la date t.
        # On garde:
        #   - fcf_last, total_debt, cash, beta mis à jour avec hist_fund,
        #   - fcf_fundamental_smoothed tel que calculé pour l'entreprise (constant dans le temps),
        #   - shares_outstanding mis à jour si dispo histo.
        fin_t = replace(
            financials,
            current_price=price_t,
            fcf_last=hist_fund.get("fcf_last", financials.fcf_last),
            total_debt=hist_fund.get("total_debt", financials.total_debt),
            cash_and_equivalents=hist_fund.get(
                "cash_and_equivalents", financials.cash_and_equivalents
            ),
            shares_outstanding=hist_fund.get(
                "shares_outstanding", financials.shares_outstanding
            ),
            beta=hist_fund.get("beta", financials.beta),
        )

        # ------------------------------------------------------------------
        # 3. Paramètres Macro Historiques (Rf, MRP, g∞, etc.)
        # ------------------------------------------------------------------
        params_t = params_strategy.get_params_for_date(dt, base_params)

        # ------------------------------------------------------------------
        # 4. Calcul de la VI à la date t
        # ------------------------------------------------------------------
        try:
            dcf_res = run_valuation(fin_t, params_t, mode)
            iv = dcf_res.intrinsic_value_per_share

            results.append(
                {
                    "Date": dt,
                    "Intrinsic Value": iv,
                    "Market Price": price_t if price_t > 0 else None,
                }
            )

        except CalculationError as e:
            msg = f"{date_str}: Erreur mathématique DCF ({str(e)})"
            ui_messages.append(msg)
            logger.warning("[HistIV] %s", msg)

        except Exception as e:
            msg = f"{date_str}: Erreur inattendue ({str(e)})"
            ui_messages.append(msg)
            logger.exception("[HistIV] Exception inattendue lors du calcul DCF historique: %s", e)

    # ----------------------------------------------------------------------
    # 5. Construction du DataFrame final
    # ----------------------------------------------------------------------
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("Date")

    # Filtrer et limiter les messages d'erreur pour éviter le spam (max 5 uniques)
    unique_msgs = sorted(list(set(ui_messages)))
    if len(unique_msgs) > 5:
        unique_msgs = unique_msgs[:5] + ["... et d'autres erreurs similaires."]

    return df, unique_msgs
