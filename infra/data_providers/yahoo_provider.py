import logging
from typing import Optional, Dict, Tuple, Any, List
from datetime import datetime

import pandas as pd
import yfinance as yf
import numpy as np

from core.models import CompanyFinancials, DCFParameters
from core.exceptions import DataProviderError
from infra.data_providers.base_provider import DataProvider
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.ref_data.country_matrix import get_country_context

# --- IMPORTS HELPERS (Calculs et Waterfalls) ---
from infra.data_providers.yahoo_helpers import (
    _safe_get_first,
    _get_ttm_fcf_historical,
    get_fundamental_fcf_historical_weighted,
    get_simple_annual_fcf,
    calculate_historical_cagr,
    calculate_sustainable_growth,
    _get_historical_fundamental,
    EBIT_ALIASES,
    INTEREST_EXPENSE_ALIASES
)

from core.dcf.wacc import compute_synthetic_cost_of_debt
from core.dcf.reverse_engine import run_reverse_dcf

# --- IMPORT AUDIT (Le Moteur de Notation) ---
from infra.data_providers.audit import audit_valuation_model

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# CONSTANTES DE SECOURS (FALLBACKS)
# -----------------------------------------------------------------------------
SECTOR_DEFAULTS = {
    "Technology": {"beta": 1.2, "cost_of_debt": 0.05},
    "Communication Services": {"beta": 1.0, "cost_of_debt": 0.055},
    "Consumer Cyclical": {"beta": 1.1, "cost_of_debt": 0.06},
    "Healthcare": {"beta": 0.8, "cost_of_debt": 0.04},
    "Consumer Defensive": {"beta": 0.7, "cost_of_debt": 0.045},
    "Utilities": {"beta": 0.5, "cost_of_debt": 0.05},
    "Energy": {"beta": 1.1, "cost_of_debt": 0.065},
    "Basic Materials": {"beta": 1.2, "cost_of_debt": 0.06},
    "Industrials": {"beta": 1.0, "cost_of_debt": 0.055},
    "Financial Services": {"beta": 1.0, "cost_of_debt": 0.05},
    "Real Estate": {"beta": 0.9, "cost_of_debt": 0.06},
}
DEFAULT_SECTOR_VALS = {"beta": 1.0, "cost_of_debt": 0.06}

SECTOR_RISK_PROFILE = {
    "Technology": {"beta_vol": 0.15, "g_vol": 0.020},
    "Healthcare": {"beta_vol": 0.08, "g_vol": 0.010},
    "Energy": {"beta_vol": 0.20, "g_vol": 0.025},
    # Les autres secteurs utilisent le profil par défaut
}
DEFAULT_RISK_PROFILE = {"beta_vol": 0.10, "g_vol": 0.010}


class YahooFinanceProvider(DataProvider):
    """
    Fournisseur Intelligent avec TRIPLE WATERFALL et AUDIT INTÉGRÉ.
    Gère la récupération des données, les stratégies de repli (Waterfalls)
    et l'audit de fiabilité des résultats.
    """

    def __init__(self, macro_provider: Optional[YahooMacroProvider] = None):
        self.macro_provider = macro_provider if macro_provider is not None else YahooMacroProvider()
        self._ticker_cache: Dict[str, Any] = {}

    def _get_ticker_data(self, ticker: str) -> Dict[str, Any]:
        """Récupère les données brutes Yahoo et les met en cache."""
        if ticker not in self._ticker_cache:
            try:
                yt = yf.Ticker(ticker)
                # On force le chargement de certaines propriétés pour éviter le lazy loading lent
                data = {
                    "ticker_obj": yt,
                    "balance_sheet": yt.balance_sheet,
                    "cashflow": yt.cashflow,
                    "income_statement": yt.financials,
                    "quarterly_balance_sheet": yt.quarterly_balance_sheet,
                    "quarterly_cashflow": yt.quarterly_cashflow,
                    "info": yt.info,
                }
                self._ticker_cache[ticker] = data
            except Exception as e:
                logger.error("[Provider] Échec connexion Yahoo pour %s: %s", ticker, e)
                raise DataProviderError(f"Impossible de récupérer les données pour {ticker}.")
        return self._ticker_cache[ticker]

    # -------------------------------------------------------------------------
    # WATERFALL 1 : FREE CASH FLOW (FCF)
    # -------------------------------------------------------------------------
    def _resolve_fcf_strategy(self, ticker: str, data: Dict[str, Any], warnings: List[str]) -> float:
        """Cascade de calcul du FCF : TTM -> Pondéré -> Annuel Simple."""
        inc = data["income_statement"]
        cf = data["cashflow"]
        qcf = data["quarterly_cashflow"]

        # 1. TTM (Précision Max - 12 derniers mois)
        fcf_ttm, ttm_date = _get_ttm_fcf_historical(qcf, datetime.now())
        if fcf_ttm is not None:
            date_str = ttm_date.strftime('%Y-%m') if ttm_date else "N/A"
            warnings.append(f"✅ FCF Source : TTM (12 mois glissants au {date_str}).")
            return float(fcf_ttm)
        else:
            warnings.append("ℹ️ FCF : Données trimestrielles insuffisantes pour TTM.")

        # 2. Pondéré (Normatif - Lissés sur 5 ans)
        fcf_weighted = get_fundamental_fcf_historical_weighted(inc, cf, tax_rate_default=0.25, nb_years=5)
        if fcf_weighted is not None:
            warnings.append(f"✅ FCF Source : Moyenne Pondérée (5 ans).")
            return float(fcf_weighted)

        # 3. Dernier Annuel (Secours - Donnée brute)
        fcf_simple = get_simple_annual_fcf(cf)
        if fcf_simple is not None:
            warnings.append(f"⚠️ FCF Source : Dernier Bilan Annuel (Donnée brute).")
            return float(fcf_simple)

        # 4. Échec
        warnings.append("❌ FCF CRITIQUE : Impossible de calculer un flux valide. (Mis à 0).")
        return 0.0

    # -------------------------------------------------------------------------
    # WATERFALL 2 : GROWTH RATE (g)
    # -------------------------------------------------------------------------
    def _resolve_growth_strategy(self, data: Dict[str, Any], warnings: List[str]) -> float:
        """Cascade de croissance : Analystes -> Historique -> Fondamentale -> Macro."""
        info = data.get("info", {})
        inc = data.get("income_statement")
        bs = data.get("balance_sheet")

        # 1. Estimations Analystes (Le "Gold Standard")
        analyst_g = info.get("earningsGrowth") or info.get("revenueGrowth")
        if analyst_g is not None:
            g_val = float(analyst_g)
            # Bornage réaliste (-50% à +50%)
            if -0.5 < g_val < 0.5:
                warnings.append(f"✅ Croissance : Basée sur estimations analystes ({g_val:.1%}).")
                return g_val

        # 2. Historique CAGR (3 ans)
        cagr_3y = calculate_historical_cagr(inc, years=3)
        if cagr_3y is not None:
            # Facteur de prudence (0.8) car le passé ne prédit pas le futur parfaitement
            g_val = max(0.0, min(0.20, cagr_3y * 0.8))
            warnings.append(f"✅ Croissance : Basée sur l'historique 3 ans ajusté ({g_val:.1%}).")
            return g_val

        # 3. Croissance Fondamentale (ROE * Retention)
        sust_g = calculate_sustainable_growth(inc, bs)
        if sust_g is not None:
            g_val = max(0.01, min(0.15, sust_g))
            warnings.append(f"✅ Croissance : Basée sur les fondamentaux (ROE * Retention = {g_val:.1%}).")
            return g_val

        # 4. Fallback Macro (PIB/Inflation)
        warnings.append("⚠️ Croissance : Aucune donnée spécifique. Fallback sur 2.5%.")
        return 0.025

    # -------------------------------------------------------------------------
    # WATERFALL 3 : COST OF DEBT (Kd)
    # -------------------------------------------------------------------------
    def _resolve_cost_of_debt_strategy(self, interest_expense: float, total_debt: float,
                                       risk_free_rate: float, sector: str, warnings: List[str]) -> float:
        """Cascade dette : Synthétique (Réel) -> Sectoriel (Moyenne)."""
        sector_defaults = SECTOR_DEFAULTS.get(sector, DEFAULT_SECTOR_VALS)

        # 1. Synthétique (Réel)
        if total_debt > 0 and interest_expense > 0:
            synthetic_kd = interest_expense / total_debt

            # Sanity Check : Est-ce raisonnable ? (Entre RiskFree et 20%)
            if risk_free_rate < synthetic_kd < 0.20:
                return synthetic_kd
            else:
                warnings.append(f"⚠️ Coût dette calculé aberrant ({synthetic_kd:.1%}). Rejeté.")

        # 2. Fallback Sectoriel
        fallback_kd = sector_defaults["cost_of_debt"]
        warnings.append(f"ℹ️ Coût dette : Utilisation de la moyenne sectorielle ({fallback_kd:.1%}).")
        return fallback_kd

    # -------------------------------------------------------------------------
    # RÉCUPÉRATION FINANCES DE BASE
    # -------------------------------------------------------------------------
    def get_company_financials(self, ticker: str) -> CompanyFinancials:
        """Extrait les données brutes et lance les premiers calculs."""
        data = self._get_ticker_data(ticker)
        info = data.get("info") or {}
        bs = data["balance_sheet"]
        inc = data["income_statement"]

        if "regularMarketPrice" not in info:
            raise DataProviderError(f"Prix introuvable pour {ticker}. Ticker invalide ou délisté ?")

        warnings: List[str] = []

        # Données de base
        price = float(info.get("regularMarketPrice", 0.0))
        shares = float(info.get("sharesOutstanding") or info.get("floatShares") or 0.0)
        currency = info.get("currency", "USD")
        if shares <= 0:
            raise DataProviderError(f"Nombre d'actions invalide (0) pour {ticker}.")

        # Dette et Cash (Extraction sécurisée)
        raw_debt = _safe_get_first(bs, ["Total Debt", "Long Term Debt"])
        debt = float(raw_debt) if raw_debt is not None else 0.0

        raw_cash = _safe_get_first(bs, ["Cash And Cash Equivalents", "Cash"])
        cash = float(raw_cash) if raw_cash is not None else 0.0

        # Intérêts
        interest_exp = 0.0
        if inc is not None and not inc.empty:
            recent_inc = inc.iloc[:, 0:1]
            val = _safe_get_first(recent_inc, INTEREST_EXPENSE_ALIASES)
            if val is not None: interest_exp = abs(float(val))

        # --- WATERFALL 1 : APPEL DU FCF ---
        final_fcf = self._resolve_fcf_strategy(ticker, data, warnings)

        # Calcul optionnel du FCF Smoothed (pour affichage UI uniquement)
        fcf_fundamental_smoothed = get_fundamental_fcf_historical_weighted(
            inc, data["cashflow"], tax_rate_default=0.25, nb_years=5
        )

        # Beta (avec fallback)
        raw_beta = info.get("beta")
        sector = info.get("sector", "Unknown")
        beta = float(raw_beta) if raw_beta is not None else 1.0
        if raw_beta is None:
            defaults = SECTOR_DEFAULTS.get(sector, DEFAULT_SECTOR_VALS)
            beta = defaults["beta"]
            warnings.append(f"ℹ️ Beta : Donnée manquante, utilisation moyenne sectorielle ({beta}).")

        if interest_exp > 0:
            warnings.append(f"💳 Dette : Charge d'intérêts ({interest_exp / 1e6:,.0f} M{currency}).")

        return CompanyFinancials(
            ticker=ticker,
            currency=currency,
            sector=sector,
            industry=info.get("industry", "Unknown"),
            current_price=price,
            shares_outstanding=shares,
            total_debt=debt,
            cash_and_equivalents=cash,
            interest_expense=interest_exp,
            fcf_last=final_fcf,
            beta=beta,
            fcf_fundamental_smoothed=fcf_fundamental_smoothed,
            warnings=warnings,
        )

    def get_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        try:
            yt = yf.Ticker(ticker)
            hist = yt.history(period=period, interval="1d", auto_adjust=False)
            if hist.empty: return pd.DataFrame()

            if "Adj Close" in hist.columns:
                return hist[["Adj Close"]].rename(columns={"Adj Close": "Close"})
            return hist[["Close"]] if "Close" in hist.columns else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    # -------------------------------------------------------------------------
    # ORCHESTRATEUR PRINCIPAL + AUDIT
    # -------------------------------------------------------------------------
    def get_company_financials_and_parameters(self, ticker: str, projection_years: int):
        """
        Cerveau de l'Auto-Pilote :
        1. Récupère les données (via Waterfalls).
        2. Calcule les paramètres DCF (WACC, Growth).
        3. Exécute l'AUDIT DE FIABILITÉ.
        4. Loggue le rapport détaillé.
        """
        # 1. & 2. Récupération Finances de base & Macro
        financials = self.get_company_financials(ticker)
        data = self._get_ticker_data(ticker)
        info = data.get("info", {})
        ctx = get_country_context(info.get("country", "United States"))

        # 3. --- WATERFALL 3 : COST OF DEBT ---
        final_cost_of_debt = self._resolve_cost_of_debt_strategy(
            financials.interest_expense, financials.total_debt, ctx["risk_free_rate"],
            financials.sector, financials.warnings
        )

        # 4. --- WATERFALL 2 : GROWTH ---
        base_growth = self._resolve_growth_strategy(data, financials.warnings)

        # Ajustement intelligent du "High Growth Period"
        auto_high_growth_years = 0
        if base_growth > 0.15:
            base_growth = 0.15  # Hard Cap pour éviter l'infini
            auto_high_growth_years = 3
        elif base_growth > 0.08:
            auto_high_growth_years = 2

        # 5. Volatilité (Monte Carlo)
        risk_profile = SECTOR_RISK_PROFILE.get(financials.sector, DEFAULT_RISK_PROFILE)

        # 6. Construction des Paramètres Finaux
        params = DCFParameters(
            risk_free_rate=ctx["risk_free_rate"],
            market_risk_premium=ctx["market_risk_premium"],
            cost_of_debt=final_cost_of_debt,
            tax_rate=ctx["tax_rate"],
            fcf_growth_rate=base_growth,
            perpetual_growth_rate=ctx["inflation_rate"],
            projection_years=int(projection_years),
            high_growth_years=auto_high_growth_years,
            beta_volatility=risk_profile["beta_vol"],
            growth_volatility=risk_profile["g_vol"]
        )

        # 7. Reverse DCF (Contrôle final)
        try:
            implied_g = run_reverse_dcf(financials, params, financials.current_price)
            financials.implied_growth_rate = implied_g
            if implied_g is not None:
                spread = implied_g - base_growth
                if abs(spread) > 0.05:
                    trend = "Optimiste" if spread > 0 else "Pessimiste"
                    financials.warnings.append(f"👀 Marché {trend} : Price {implied_g:.1%} vs Modèle {base_growth:.1%}.")
        except Exception:
            pass

        # =================================================================
        # 8. LANCEMENT AUDIT DÉTAILLÉ (Le Bulletin de Notes)
        # =================================================================
        audit_res = audit_valuation_model(financials, params)

        # Injection des résultats dans l'objet pour utilisation UI
        financials.audit_score = audit_res.score
        financials.audit_rating = audit_res.rating
        financials.audit_details = audit_res.ui_details
        financials.audit_logs = audit_res.terminal_logs

        # =================================================================
        # 9. LOGGING TERMINAL RICHE (Le Rapport)
        # =================================================================
        logger.info(f"")
        logger.info(f"📊 [AUDIT REPORT] {ticker} | Score: {audit_res.score}/100 ({audit_res.rating})")
        logger.info(f"----------------------------------------------------------------")

        if audit_res.score == 100.0:
            logger.info(f"   ✅ Aucune pénalité détectée. Données 'Gold Standard'.")
        else:
            for log_line in audit_res.terminal_logs:
                logger.info(log_line)

        logger.info(f"----------------------------------------------------------------")
        logger.info(f"")

        return financials, params

    # -------------------------------------------------------------------------
    # MÉTHODES HISTORIQUES (Backtest)
    # -------------------------------------------------------------------------
    def get_historical_fundamentals_for_date(self, ticker: str, date: datetime) -> Tuple[
        Optional[Dict[str, Any]], List[str]]:
        """
        Reconstruit les fondamentaux pour une date passée.
        """
        data = self._get_ticker_data(ticker)

        bs_annual = data.get("balance_sheet")
        bs_quarterly = data.get("quarterly_balance_sheet")

        DEBT_KEYS = ["Total Debt", "Long Term Debt"]
        CASH_KEYS = ["Cash And Cash Equivalents", "Cash"]
        SHARE_KEYS = ["Share Issued", "Ordinary Shares Number"]

        debt_val, _ = _get_historical_fundamental(bs_annual, bs_quarterly, date, DEBT_KEYS)
        cash_val, _ = _get_historical_fundamental(bs_annual, bs_quarterly, date, CASH_KEYS)
        shares_val, _ = _get_historical_fundamental(bs_annual, bs_quarterly, date, SHARE_KEYS)

        if shares_val is None:
            shares_val = data.get("info", {}).get("sharesOutstanding")

        if shares_val is None or debt_val is None:
            return None, ["Données Bilan (Dette/Actions) introuvables."]

        qcf = data.get("quarterly_cashflow")
        fcf_ttm, _ = _get_ttm_fcf_historical(qcf, date)

        if fcf_ttm is None:
            return None, ["Flux trimestriels insuffisants pour TTM historique."]

        beta_val = data.get("info", {}).get("beta", 1.0)

        result = {
            "fcf_last": fcf_ttm,
            "total_debt": debt_val,
            "cash_and_equivalents": cash_val,
            "shares_outstanding": shares_val,
            "beta": beta_val
        }
        return result, []