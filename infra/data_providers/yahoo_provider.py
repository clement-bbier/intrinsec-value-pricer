"""
infra/data_providers/yahoo_provider.py

FOURNISSEUR DE DONNÉES — YAHOO FINANCE (OPTIMIZED)
Version : V2.1 — Caching & Robustesse

Responsabilités :
- Interface concrète avec l'API yfinance
- Normalisation des données brutes en objets du domaine (CompanyFinancials)
- Gestion du Caching pour la performance UI (Streamlit)
- Gestion des erreurs réseaux et des données manquantes

Politique de Performance :
- Les données sont mises en cache pour éviter le ban IP et la latence.
- Le cache est invalidé toutes les 2 heures (TTL).
"""

import logging
from datetime import datetime
from typing import Tuple, Optional

import pandas as pd
import yfinance as yf
import streamlit as st  # Import nécessaire pour le caching de performance

# Assurez-vous que core/computation/financial_math.py existe bien
from core.computation.financial_math import calculate_synthetic_cost_of_debt
from core.exceptions import TickerNotFoundError, DataInsufficientError
from core.models import CompanyFinancials, DCFParameters

from infra.data_providers.base_provider import DataProvider
from infra.data_providers.yahoo_helpers import (
    INTEREST_EXPENSE_ALIASES,
    _safe_get_first,
    get_simple_annual_fcf,
    normalize_currency_and_price,
    safe_api_call,
    calculate_historical_cagr
)
from infra.macro.yahoo_macro_provider import YahooMacroProvider

logger = logging.getLogger(__name__)


class YahooFinanceProvider(DataProvider):
    """
    Implémentation concrète via yfinance.
    Intègre une couche de caching pour optimiser l'expérience utilisateur.
    """

    def __init__(self, macro_provider: YahooMacroProvider):
        self.macro_provider = macro_provider

    # ==========================================================================
    # 1. RÉCUPÉRATION DES DONNÉES FINANCIÈRES (SNAPSHOT)
    # ==========================================================================

    @st.cache_data(ttl=7200, show_spinner=False)
    @safe_api_call(max_retries=3)
    def get_company_financials(_self, ticker: str) -> CompanyFinancials:
        """
        Récupère les états financiers normalisés.

        Optimisation :
        - @st.cache_data : Stocke le résultat 2h pour éviter de rappeler Yahoo.
        - L'argument 'self' est nommé '_self' pour que Streamlit n'essaie pas de hasher l'objet provider.
        """
        logger.info(f"[Yahoo] Fetching financials for {ticker}...")

        ticker_obj = yf.Ticker(ticker)

        try:
            # 1. Info Générale (Métadonnées)
            info = ticker_obj.info
            if not info or "regularMarketPrice" not in info:
                # Parfois info est vide mais l'historique existe, mais pour le DCF on a besoin d'info
                raise TickerNotFoundError(f"Ticker '{ticker}' introuvable ou incomplet via Yahoo.")

            currency = info.get("currency", "USD")
            current_price = info.get("regularMarketPrice", 0.0)

            # Normalisation (ex: GBp -> GBP)
            current_price, currency = normalize_currency_and_price(current_price, currency)

            shares = info.get("sharesOutstanding")
            if not shares:
                # Fallback sur la market cap
                mcap = info.get("marketCap", 0.0)
                if mcap > 0 and current_price > 0:
                    shares = mcap / current_price
                else:
                    raise DataInsufficientError(f"Nombre d'actions introuvable pour {ticker}.")

            # 2. États Financiers (DataFrames)
            # On force le chargement explicite
            balance_sheet = ticker_obj.balance_sheet
            income_stmt = ticker_obj.financials
            cashflow = ticker_obj.cashflow

            if balance_sheet.empty or income_stmt.empty:
                raise DataInsufficientError(f"États financiers vides pour {ticker}.")

            # 3. Extraction des données clés (Helpers robustes)

            # Dette Totale
            total_debt = _safe_get_first(
                balance_sheet,
                ["Total Debt", "Long Term Debt And Capital Lease Obligation", "Long Term Debt"]
            )
            if total_debt is None:
                # Fallback : Short Term + Long Term
                std = _safe_get_first(balance_sheet, ["Current Debt", "Commercial Paper"]) or 0.0
                ltd = _safe_get_first(balance_sheet, ["Long Term Debt"]) or 0.0
                total_debt = std + ltd

            # Cash
            cash = _safe_get_first(
                balance_sheet,
                ["Cash And Cash Equivalents", "Cash Financial"]
            ) or 0.0

            # Interest Expense (souvent positif dans Yahoo, on veut la valeur absolue)
            interest_expense = _safe_get_first(income_stmt, INTEREST_EXPENSE_ALIASES)
            if interest_expense:
                interest_expense = abs(interest_expense)
            else:
                interest_expense = 0.0
                logger.warning(f"Charges d'intérêts introuvables pour {ticker}. WACC approximatif.")

            # Free Cash Flow (Last TTM or Year)
            fcf = get_simple_annual_fcf(cashflow)

            # Dividendes (pour RIM / Graham)
            div_rate = info.get("dividendRate", 0.0)
            div_yield = info.get("dividendYield", 0.0)
            div = div_rate if div_rate else (div_yield * current_price if div_yield else 0.0)

            # Beta (Brut Yahoo)
            beta = info.get("beta", 1.0)
            if beta is None:
                beta = 1.0  # Fallback neutre

            # Book Value (pour RIM)
            book_value = _safe_get_first(balance_sheet, ["Total Equity Gross Minority Interest", "Stockholders Equity"])
            if not book_value:
                book_value = info.get("bookValue") * shares if info.get("bookValue") else 0.0

            # Industrie / Pays (pour Macro)
            industry = info.get("industry", "Unknown")
            country = info.get("country", "United States")

            logger.info(f"[Yahoo] Success {ticker} | Price={current_price} {currency} | Debt={total_debt:,.0f}")

            return CompanyFinancials(
                ticker=ticker.upper(),
                name=info.get("shortName", ticker),
                currency=currency,
                current_price=current_price,
                shares_outstanding=shares,
                total_debt=total_debt,
                cash_and_equivalents=cash,
                interest_expense=interest_expense,
                beta=beta,
                industry=industry,
                country=country,
                dividend_share=float(div) if div else None,
                revenue_ttm=info.get("totalRevenue"),
                book_value=book_value,
                fcf_last=fcf,
                fcf_fundamental_smoothed=fcf,  # Par défaut identique, sauf si stratégie fondamentale
                source_fcf="yahoo_api"
            )

        except Exception as e:
            logger.error(f"[Yahoo] Failed to fetch {ticker}: {e}")
            raise e

    # ==========================================================================
    # 2. HISTORIQUE DE PRIX (GRAPHIQUES)
    # ==========================================================================

    @st.cache_data(ttl=3600 * 4)  # Cache long (4h) pour l'historique
    def get_price_history(_self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """
        Récupère l'historique de prix (Close).
        """
        try:
            df = yf.Ticker(ticker).history(period=period)
            return df
        except Exception:
            return pd.DataFrame()

    # ==========================================================================
    # 3. WORKFLOW COMPLET (AUTO MODE)
    # ==========================================================================

    def get_company_financials_and_parameters(
            self, ticker: str, projection_years: int
    ) -> Tuple[CompanyFinancials, DCFParameters]:
        """
        Méthode orchestrateur pour le mode AUTO.
        Récupère les données ET construit les paramètres macro par défaut.
        """

        # 1. Données Entreprise (Cachées)
        financials = self.get_company_financials(ticker)

        # 2. Données Macro (Live)
        macro_ctx = self.macro_provider.get_macro_context(
            date=datetime.now(),
            currency=financials.currency
        )

        # 3. Calcul du Coût de la dette synthétique
        # (Car Yahoo ne donne pas le Kd explicite)
        kd_synthetic = calculate_synthetic_cost_of_debt(
            rf=macro_ctx.risk_free_rate,
            ebit=financials.fcf_last or 1.0,  # Proxy EBIT
            interest_expense=financials.interest_expense,
            market_cap=financials.current_price * financials.shares_outstanding
        )

        # 4. Estimation de la croissance (Basée sur l'historique CA)
        # Note : On ne cache pas cette étape car elle est rapide si financials est déjà là
        historical_cagr = None
        try:
            # On accède directement à l'objet yfinance sans refaire une requête réseau complète
            # car get_company_financials ne retourne que le DTO.
            # Pour bien faire, on peut faire une estimation prudente par défaut
            # ou rappeler yf.Ticker(ticker).financials (qui sera cachée par yfinance interne)
            pass
        except:
            pass

        # Valeur normative par défaut (Conservative)
        growth_assumption = 0.03

        # 5. Construction des Paramètres DCF
        params = DCFParameters(
            risk_free_rate=macro_ctx.risk_free_rate,
            market_risk_premium=macro_ctx.market_risk_premium,
            corporate_aaa_yield=macro_ctx.corporate_aaa_yield,
            cost_of_debt=kd_synthetic,
            tax_rate=0.25,  # TODO: Affiner via Country Matrix

            fcf_growth_rate=growth_assumption,
            perpetual_growth_rate=min(growth_assumption, 0.025),  # Caped at 2.5%

            projection_years=projection_years,
            target_equity_weight=0.80,  # Structure cible par défaut si inconnue
            target_debt_weight=0.20
        )

        return financials, params