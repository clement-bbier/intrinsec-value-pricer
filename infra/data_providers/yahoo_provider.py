import logging
from typing import Optional, Dict, Tuple, Any, List
from datetime import datetime

import pandas as pd
import yfinance as yf

from core.models import CompanyFinancials, DCFParameters
from core.exceptions import DataProviderError
from infra.data_providers.base_provider import DataProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

# Import des helpers déplacés
from infra.data_providers.yahoo_helpers import (
    _safe_get_first,
    _get_historical_fundamental,
    _get_ttm_fcf_historical,
    get_fundamental_fcf_historical,
)

logger = logging.getLogger(__name__)


class YahooFinanceProvider(DataProvider):
    def __init__(self, macro_provider: Optional[YahooMacroProvider] = None):
        # Utilisation de l'injection de dépendance pour le macro provider si non fourni
        self.macro_provider = macro_provider if macro_provider is not None else YahooMacroProvider()
        # Cache pour l'objet Ticker et les données financières complètes (pour l'historique)
        self._ticker_cache: Dict[str, Any] = {}

    def _get_ticker_data(self, ticker: str) -> Dict[str, Any]:
        """Récupère l'objet Ticker et toutes ses données, puis le met en cache."""
        if ticker not in self._ticker_cache:
            try:
                yt = yf.Ticker(ticker)

                # Charger toutes les données nécessaires (annuel + trimestriel)
                data = {
                    "ticker_obj": yt,
                    # États financiers annuels
                    "balance_sheet": yt.balance_sheet,
                    "cashflow": yt.cashflow,
                    "income_statement": yt.financials,
                    # États financiers trimestriels
                    "quarterly_balance_sheet": yt.quarterly_balance_sheet,
                    "quarterly_cashflow": yt.quarterly_cashflow,
                    "quarterly_income_statement": yt.quarterly_financials,
                    # Métadonnées
                    "info": yt.info,
                }

                if data["balance_sheet"] is None or data["balance_sheet"].empty:
                    logger.warning("[Provider] Bilan annuel manquant pour %s.", ticker)
                if data["cashflow"] is None or data["cashflow"].empty:
                    logger.warning("[Provider] Flux de trésorerie annuels manquants pour %s.", ticker)
                if data["income_statement"] is None or data["income_statement"].empty:
                    logger.warning("[Provider] Compte de résultat annuel manquant pour %s.", ticker)
                if data["quarterly_cashflow"] is None or data["quarterly_cashflow"].empty:
                    logger.warning(
                        "[Provider] Flux de trésorerie trimestriels manquants pour %s. FCF TTM pourrait échouer.",
                        ticker,
                    )

                self._ticker_cache[ticker] = data
            except Exception as e:
                logger.error("[Provider] Échec de la récupération des données Yahoo pour %s: %s", ticker, e)
                raise DataProviderError(f"Échec de la récupération des données de base pour {ticker}.")

        return self._ticker_cache[ticker]

    # --------------------------------------------------------------------------
    # 1. Données Actuelles (Pour la valorisation UI principale)
    # --------------------------------------------------------------------------
    def get_company_financials(self, ticker: str) -> CompanyFinancials:
        """Récupère et normalise les données financières actuelles."""
        data = self._get_ticker_data(ticker)
        yt = data["ticker_obj"]
        bs = data["balance_sheet"]
        qcf = data["quarterly_cashflow"]
        info = data.get("info") or {}

        income_annual = data.get("income_statement")
        cashflow_annual = data.get("cashflow")
        balance_annual = data.get("balance_sheet")

        if "regularMarketPrice" not in info:
            raise DataProviderError(f"Prix de marché actuel manquant pour {ticker}.")

        warnings: List[str] = []

        # 1. Prix, Devise, Actions
        price = info.get("regularMarketPrice")
        currency = info.get("currency", "USD")
        shares = info.get("sharesOutstanding") or info.get("floatShares")  # Parfois floatShares est plus fiable

        if not shares or shares <= 0:
            raise DataProviderError(f"Nombre d'actions en circulation manquant pour {ticker}.")

        # 2. Bilan (Dette et Cash) – en distinguant valeur manquante et vrai zéro
        raw_debt = _safe_get_first(bs, ["Total Debt", "Long Term Debt"])
        if raw_debt is None:
            debt = 0.0
            warnings.append(
                "Dette totale manquante dans le dernier bilan disponible : utilisation de 0 comme approximation."
            )
        else:
            debt = float(raw_debt)

        raw_cash = _safe_get_first(bs, ["Cash And Cash Equivalents", "Cash"])
        if raw_cash is None:
            cash = 0.0
            warnings.append(
                "Trésorerie et équivalents de trésorerie manquants dans le dernier bilan disponible : utilisation de 0."
            )
        else:
            cash = float(raw_cash)

        # 3. FCF TTM (Méthode 1) - standard pour un DCF simple
        fcf_ttm, _ = _get_ttm_fcf_historical(qcf, datetime.now())
        if fcf_ttm is None:
            logger.warning(
                "[Provider] FCF TTM calculé pour AUJOURD'HUI est manquant pour %s. Utilisation de 0.", ticker
            )
            warnings.append(
                "FCF TTM (flux de trésorerie libres sur 12 mois) incomplet ou manquant : "
                "utilisation de 0 comme proxy. Interprétez la valeur intrinsèque avec prudence."
            )
            fcf_ttm = 0.0

        # 4. FCFF fondamental lissé (Méthode 2 – 3-Statement Light)
        fcf_fundamental_smoothed: Optional[float] = None
        try:
            if (
                income_annual is not None
                and not income_annual.empty
                and cashflow_annual is not None
                and not cashflow_annual.empty
                and balance_annual is not None
                and not balance_annual.empty
            ):
                fundamental_fcf_list = get_fundamental_fcf_historical(
                    income_annual=income_annual,
                    cashflow_annual=cashflow_annual,
                    balance_annual=balance_annual,
                    tax_rate_default=0.25,  # même ordre de grandeur que le tax_rate par défaut du DCFParameters
                    nb_years=3,
                )

                if fundamental_fcf_list:
                    fcf_fundamental_smoothed = float(
                        sum(fundamental_fcf_list) / len(fundamental_fcf_list)
                    )
                else:
                    warnings.append(
                        "FCFF fondamental (NOPAT + D&A - Capex - ΔNWC) non disponible : "
                        "données historiques insuffisantes ou incomplètes."
                    )
            else:
                warnings.append(
                    "États financiers annuels incomplets (compte de résultat / cashflow / bilan) : "
                    "FCFF fondamental non calculable."
                )
        except Exception as e:
            logger.warning(
                "[Provider] Erreur lors du calcul du FCFF fondamental pour %s : %s", ticker, e
            )
            warnings.append(
                "Erreur lors du calcul du FCFF fondamental : la Méthode 2 peut être indisponible pour ce ticker."
            )
            fcf_fundamental_smoothed = None

        # 5. Beta
        beta = info.get("beta", 1.0)

        logger.info(
            "[Provider] Financials ACTUELS pour %s: Price=%.2f, Shares=%.0f, FCF_TTM=%.2f, FCFF_fondamental=%s",
            ticker,
            price,
            shares,
            fcf_ttm,
            f"{fcf_fundamental_smoothed:.2f}" if fcf_fundamental_smoothed is not None else "None",
        )

        return CompanyFinancials(
            ticker=ticker,
            currency=currency,
            current_price=float(price),
            shares_outstanding=float(shares),
            total_debt=float(debt),
            cash_and_equivalents=float(cash),
            fcf_last=float(fcf_ttm),
            beta=float(beta),
            fcf_fundamental_smoothed=fcf_fundamental_smoothed,
            warnings=warnings,
        )

    # --------------------------------------------------------------------------
    # 2. Historique de prix (pour graphique + VI historique)
    # --------------------------------------------------------------------------
    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """Récupère l'historique de prix (Close) sous forme de DataFrame."""
        try:
            yt = yf.Ticker(ticker)
            history = yt.history(period=period, interval="1d", auto_adjust=False)

            if history.empty:
                raise DataProviderError(f"Historique de prix vide pour {ticker}.")

            # S'assurer que 'Close' est utilisé (ou 'Adj Close')
            if "Adj Close" in history.columns:
                history = history[["Adj Close"]].rename(columns={"Adj Close": "Close"})
            elif "Close" in history.columns:
                history = history[["Close"]]
            else:
                raise DataProviderError(f"Colonnes de prix manquantes pour {ticker}.")

            return history

        except Exception as e:
            logger.error("[Provider] Erreur de récupération de l'historique de prix pour %s: %s", ticker, e)
            raise DataProviderError(f"Échec de l'accès à l'historique de prix pour {ticker}.")

    # --------------------------------------------------------------------------
    # 3. Données Historiques (Pour la Valorisation Intrinsèque Historique - VIH)
    # --------------------------------------------------------------------------
    def get_historical_fundamentals_for_date(
        self,
        ticker: str,
        date: datetime,
    ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Récupère les fondamentaux pour le calcul de la VI à une date historique.
        (Actuellement basé sur le FCF TTM simple ; pourra être étendu pour la Méthode 2.)
        """
        logger.info("[Hist] Récupération des fondamentaux pour %s à la date %s", ticker, date.date())
        data = self._get_ticker_data(ticker)

        # Données yfinance mises en cache
        info = data.get("info", {})
        bs_annual = data.get("balance_sheet")
        bs_quarterly = data.get("quarterly_balance_sheet")
        cf_quarterly = data.get("quarterly_cashflow")

        # Dictionnaire de sortie et messages d'erreur/avertissement
        fundamentals_t: Dict[str, Any] = {}
        errors: List[str] = []

        # --- FCF TTM (le plus critique) ---
        fcf_ttm, fcf_date = _get_ttm_fcf_historical(cf_quarterly, date)
        if fcf_ttm is not None:
            fundamentals_t["fcf_last"] = fcf_ttm
        else:
            errors.append(
                "FCF TTM introuvable (manque < 4 trimestres de cashflow avant la date ou labels incompatibles)."
            )

        # --- Dette (Total Debt) ---
        debt, debt_date = _get_historical_fundamental(
            bs_annual,
            bs_quarterly,
            date,
            ["Total Debt", "Long Term Debt"],
        )
        if debt is not None:
            fundamentals_t["total_debt"] = debt
        else:
            errors.append("Dette totale introuvable.")

        # --- Cash (Cash and Equivalents) ---
        cash, cash_date = _get_historical_fundamental(
            bs_annual,
            bs_quarterly,
            date,
            ["Cash And Cash Equivalents", "Cash"],
        )
        if cash is not None:
            fundamentals_t["cash_and_equivalents"] = cash
        else:
            errors.append("Trésorerie introuvable.")

        # --- Actions en Circulation (Shares Outstanding) ---
        shares, shares_date = _get_historical_fundamental(
            bs_annual,
            bs_quarterly,
            date,
            ["Common Stock Shares Outstanding", "Share Issued"],
        )

        if shares is not None and shares > 0:
            fundamentals_t["shares_outstanding"] = shares
        elif info.get("sharesOutstanding"):
            fundamentals_t["shares_outstanding"] = info["sharesOutstanding"]
            errors.append(
                f"Actions en circulation: Historique manquant. Utilisation du nombre actuel ({info['sharesOutstanding']})."
            )
        else:
            errors.append("Actions en circulation introuvables (ni historique, ni actuel).")

        # --- Beta ---
        fundamentals_t["beta"] = info.get("beta", 1.0)

        if not fundamentals_t:
            return None, errors

        return fundamentals_t, errors

    # --------------------------------------------------------------------------
    # 4. Paramètres DCF (Point d'entrée de l'UI)
    # --------------------------------------------------------------------------
    def get_company_financials_and_parameters(
        self,
        ticker: str,
        projection_years: int,
    ) -> Tuple[CompanyFinancials, DCFParameters]:
        """Récupère les données financières actuelles et les paramètres DCF correspondants."""

        # 1. Données Financières
        financials = self.get_company_financials(ticker)

        # 2. Paramètres Macro Actuels
        macro = self.macro_provider.get_macro_context(datetime.now(), financials.currency)

        # Valeurs par défaut si le macro provider échoue
        rf = macro.risk_free_rate if macro else 0.04
        mrp = macro.market_risk_premium if macro else 0.05
        g_inf = macro.perpetual_growth_rate if macro else 0.02

        # 3. Définition des Paramètres DCF
        params = DCFParameters(
            risk_free_rate=rf,
            market_risk_premium=mrp,
            cost_of_debt=rf + 0.02,      # Spread de crédit par défaut de 2%
            tax_rate=0.25,               # Taux d'imposition par défaut
            fcf_growth_rate=0.05,        # Taux de croissance de FCF par défaut (5%)
            perpetual_growth_rate=g_inf,
            projection_years=int(projection_years),
        )

        logger.info("[DCFParams] Paramètres initiaux construits.")
        return financials, params
