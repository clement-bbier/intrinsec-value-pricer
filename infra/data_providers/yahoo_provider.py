import logging
from typing import Optional, Dict, Tuple, Any, List
from datetime import datetime

import pandas as pd
import yfinance as yf

from core.models import CompanyFinancials, DCFParameters
from core.exceptions import DataProviderError
from infra.data_providers.base_provider import DataProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider

logger = logging.getLogger(__name__)


def _safe_get_first(df: Optional[pd.DataFrame], row_names: List[str]) -> Optional[float]:
    """Cherche la première ligne correspondante dans une liste d'alias et retourne sa première valeur."""
    if df is None or df.empty:
        return None

    # Normalisation de l'index pour la recherche
    normalized_df = df.copy()
    normalized_df.index = normalized_df.index.astype(str).str.strip().str.lower()

    for name in row_names:
        clean_name = str(name).strip().lower()
        if clean_name in normalized_df.index:
            try:
                # Prend la première colonne (la donnée la plus récente)
                val = normalized_df.loc[clean_name].iloc[0]
                return float(val)
            except Exception:
                continue
    return None


def _get_historical_fundamental(
    df_annual: Optional[pd.DataFrame],
    df_quarterly: Optional[pd.DataFrame],
    date: datetime,
    row_names: List[str],
    is_ttm: bool = False,
) -> Tuple[Optional[float], Optional[datetime]]:
    """
    Récupère la donnée fondamentale (le plus souvent) de la dernière publication
    avant ou égale à la date demandée.

    Utilise en priorité les états annuels, puis les trimestriels en fallback.
    """
    # 1. Recherche dans les rapports Annuels (pour Dette, Cash, Shares, etc.)
    if df_annual is not None and not df_annual.empty:
        try:
            # On cherche l'ensemble des rapports publiés avant ou à la date demandée
            valid_reports = df_annual.columns[df_annual.columns <= date]

            if len(valid_reports) > 0:
                # On prend le rapport le plus récent
                latest_report_date = valid_reports[-1]

                # Extraction de la valeur pour cette date
                report_df = df_annual[[latest_report_date]]
                value = _safe_get_first(report_df, row_names)

                if value is not None:
                    return value, latest_report_date
        except Exception:
            pass

    # 2. Recherche dans les rapports Trimestriels (fallback si pas trouvé en annuel)
    if df_quarterly is not None and not df_quarterly.empty:
        try:
            valid_reports = df_quarterly.columns[df_quarterly.columns <= date]

            if len(valid_reports) > 0:
                latest_report_date = valid_reports[-1]
                report_df = df_quarterly[[latest_report_date]]
                value = _safe_get_first(report_df, row_names)

                if value is not None:
                    return value, latest_report_date
        except Exception:
            pass

    return None, None


def _get_ttm_fcf_historical(
        cashflow_quarterly: pd.DataFrame,
        date: datetime
) -> Optional[Tuple[float, datetime]]:
    """
    Calcule le FCF TTM (Trailing Twelve Months) en sommant les 4 derniers
    rapports trimestriels publiés avant ou à la date donnée.
    Gère proprement les histoires de timezone pour éviter les erreurs
    « Invalid comparison between dtype=datetime64[ns] and datetime ».
    """
    if cashflow_quarterly is None or cashflow_quarterly.empty:
        return None, None

    # Alias pour les lignes de FCF (Flux de trésorerie d'exploitation - Dépenses en capital)
    CFO_ALIASES = [
        "Operating Cash Flow",
        "Cash Flow From Continuing Operating Activities",
        "Cash Flow From Operating Activities",
        "Total Cash From Operating Activities",
    ]
    CAPEX_ALIASES = [
        "Capital Expenditure",
        "Net PPE Purchase And Sale",
        "Purchase Of PPE",
        "Capital Expenditures",
    ]

    try:
        # 1) Colonnes converties en Timestamp
        cols_ts = pd.to_datetime(cashflow_quarterly.columns)

        # 2) Version pour comparaison : toujours tz-naive
        if getattr(cols_ts, "tz", None) is not None:
            cols_cmp = cols_ts.tz_convert(None)
        else:
            cols_cmp = cols_ts

        date_ts = pd.Timestamp(date)
        if date_ts.tzinfo is not None:
            date_cmp = date_ts.tz_convert(None)
        else:
            date_cmp = date_ts

        # 3) Filtre des colonnes <= date (sur la version “comparaison”)
        mask = cols_cmp <= date_cmp
        valid_cols = list(cashflow_quarterly.columns[mask])

        if len(valid_cols) < 4:
            logger.warning(
                f"[Hist] Pas assez de données trimestrielles (< 4) avant {date.date()} pour le FCF TTM."
            )
            return None, None

        # 4) On prend les 4 dernières colonnes (labels originaux)
        valid_cols_sorted = sorted(valid_cols, reverse=True)
        ttm_cols = valid_cols_sorted[:4]

        ttm_fcf = 0.0
        cfo_found = True
        capex_found = True

        for col in ttm_cols:
            report_df = cashflow_quarterly[[col]]

            cfo = _safe_get_first(report_df, CFO_ALIASES)
            if cfo is None:
                cfo_found = False
                logger.warning(
                    f"[Hist] FCF TTM: CFO manquant pour le trimestre {col}."
                )
                break

            capex = _safe_get_first(report_df, CAPEX_ALIASES)
            if capex is None:
                capex_found = False
                logger.warning(
                    f"[Hist] FCF TTM: CAPEX manquant pour le trimestre {col}."
                )
                break

            # FCFF simple: CFO + CAPEX (Capex est généralement négatif)
            ttm_fcf += cfo + capex

        if not cfo_found or not capex_found:
            logger.warning(
                f"[Hist] FCF TTM: CFO ou CAPEX manquant dans les 4 derniers rapports avant {date.date()}."
            )
            return None, None

        # La date de publication TTM est la plus récente des 4
        ttm_report_date = pd.to_datetime(ttm_cols[0]).to_pydatetime()

        return float(ttm_fcf), ttm_report_date

    except Exception as e:
        logger.error(f"[Hist] Erreur lors du calcul du FCF TTM pour {date.date()}: {e}")
        return None, None


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

                # Charger toutes les données pour l'historique
                data = {
                    "ticker_obj": yt,
                    "balance_sheet": yt.balance_sheet,
                    "quarterly_balance_sheet": yt.quarterly_balance_sheet,
                    "cashflow": yt.cashflow,
                    "quarterly_cashflow": yt.quarterly_cashflow,
                    "info": yt.info,
                }

                if data["balance_sheet"] is None or data["balance_sheet"].empty:
                    logger.warning("[Provider] Bilan annuel manquant pour %s.", ticker)
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
        info = data["info"] or {}

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

        # 3. FCF TTM (calculé ici) - TTM est le standard pour le DCF
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

        # 4. Beta
        beta = info.get("beta", 1.0)

        logger.info(
            "[Provider] Financials ACTUELS pour %s: Price=%.2f, Shares=%.0f, FCF=%.2f",
            ticker,
            price,
            shares,
            fcf_ttm,
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
