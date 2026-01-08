"""
infra/data_providers/yahoo_provider.py

FOURNISSEUR DE DONNÉES — YAHOO FINANCE (ULTIMATE V3.8)
Version : V3.8 — Audit-Grade Inputs & Dynamic Assumptions

Changelog :
- Amélioration : Croissance g calculée dynamiquement via CAGR historique.
- Amélioration : Taux d'imposition (tax_rate) extrait du contexte pays/macro.
- Nettoyage : Suppression des imports inutilisés.
- Maintien du Deep Fetch et de la robustesse Pydantic.
"""

import logging
from datetime import datetime
from typing import Tuple, Optional

import pandas as pd
import yfinance as yf
import streamlit as st
from pydantic import ValidationError

# --- CORE IMPORTS ---
from core.computation.financial_math import calculate_synthetic_cost_of_debt
from core.exceptions import (
    TickerNotFoundError,
    ExternalServiceError
)
from core.models import CompanyFinancials, DCFParameters

# --- INFRA IMPORTS ---
from infra.data_providers.base_provider import DataProvider
from infra.data_providers.yahoo_helpers import (
    safe_api_call,
    get_simple_annual_fcf,
    normalize_currency_and_price,
    extract_most_recent_value,
    calculate_historical_cagr
)
from infra.macro.yahoo_macro_provider import YahooMacroProvider
from infra.ref_data.country_matrix import COUNTRY_CONTEXT, DEFAULT_COUNTRY

logger = logging.getLogger(__name__)


class YahooFinanceProvider(DataProvider):
    """
    Implémentation robuste via yfinance avec stratégies de repli (Fallback).
    """

    def __init__(self, macro_provider: YahooMacroProvider):
        self.macro_provider = macro_provider

    # ==========================================================================
    # 1. RÉCUPÉRATION DES DONNÉES FINANCIÈRES (SNAPSHOT)
    # ==========================================================================

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_company_financials(_self, ticker: str) -> CompanyFinancials:
        """
        Récupère les états financiers normalisés.
        Utilise le 'Deep Fetch' pour reconstruire les données manquantes.
        """
        ticker = ticker.upper().strip()
        logger.info(f"[Yahoo] Fetching financials for {ticker}...")

        try:
            yt = yf.Ticker(ticker)

            # --- A. Info Générale (Métadonnées) ---
            info = safe_api_call(lambda: yt.info, "Info")

            # Diagnostic : Ticker inconnu ou sans prix
            if not info or ("currentPrice" not in info and "regularMarketPrice" not in info):
                suffixes = [".PA", ".US", ".L", ".DE"]
                if not any(ticker.endswith(s) for s in suffixes):
                    logger.info(f"Tentative de suffixe automatique .PA pour {ticker}")
                    return _self.get_company_financials(f"{ticker}.PA")

                raise TickerNotFoundError(ticker=ticker)

            currency, current_price = normalize_currency_and_price(info)

            # --- B. États Financiers ---
            balance_sheet = safe_api_call(lambda: yt.balance_sheet, "Balance Sheet")
            income_stmt = safe_api_call(lambda: yt.income_stmt, "Income Stmt")
            cash_flow = safe_api_call(lambda: yt.cash_flow, "Cash Flow")

            # --- C. Extraction & Reconstruction (Deep Fetch) ---

            # 1. Shares Outstanding
            shares = info.get("sharesOutstanding")
            if not shares and balance_sheet is not None:
                shares = extract_most_recent_value(balance_sheet, ["Ordinary Shares Number", "Share Issued"])

            if not shares:
                mcap = info.get("marketCap", 0.0)
                if mcap > 0 and current_price > 0:
                    shares = mcap / current_price

            shares = float(shares) if shares else 1.0

            # 2. Book Value
            book_value_total = None
            if balance_sheet is not None:
                book_value_total = extract_most_recent_value(balance_sheet, [
                    "Total Stockholder Equity",
                    "Stockholders Equity",
                    "Total Equity Gross Minority Interest"
                ])

            if book_value_total and shares > 0:
                book_value_per_share = float(book_value_total) / shares
            else:
                book_value_per_share = float(info.get("bookValue", 0.0))

            # 3. Dette Totale
            total_debt = info.get("totalDebt")
            if (not total_debt or total_debt == 0) and balance_sheet is not None:
                total_debt = extract_most_recent_value(balance_sheet, ["Total Debt", "Net Debt"])
                if not total_debt:
                    std = extract_most_recent_value(balance_sheet, ["Current Debt", "Current Debt And Capital Lease Obligation"]) or 0
                    ltd = extract_most_recent_value(balance_sheet, ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"]) or 0
                    total_debt = std + ltd

            total_debt = float(total_debt) if total_debt else 0.0

            # 4. Cash
            total_cash = info.get("totalCash")
            if (not total_cash or total_cash == 0) and balance_sheet is not None:
                total_cash = extract_most_recent_value(balance_sheet, ["Cash And Cash Equivalents", "Cash Financial"])

            total_cash = float(total_cash) if total_cash else 0.0

            minority_interests = 0.0
            pension_provisions = 0.0

            if balance_sheet is not None:
                # Recherche des intérêts minoritaires (Non-controlling interests)
                minority_interests = extract_most_recent_value(balance_sheet, [
                    "Minority Interest",
                    "Non Controlling Interest",
                    "Total Equity Gross Minority Interest"
                ]) or 0.0

                # Recherche des provisions pour pensions et risques long terme
                pension_provisions = extract_most_recent_value(balance_sheet, [
                    "Pension And Other Postretirement Benefit Plans",
                    "Long Term Provisions",
                    "Other Provisions"
                ]) or 0.0

            # 5. Interest Expense
            interest_expense = 0.0
            if income_stmt is not None:
                val = extract_most_recent_value(income_stmt, ["Interest Expense", "Interest Expense Non Operating"])
                interest_expense = float(abs(val)) if val else 0.0

            # 6. FCF
            fcf = get_simple_annual_fcf(cash_flow)
            if fcf is None:
                fcf = 0.0
            else:
                fcf = float(fcf)

            # Dividendes
            div_rate = info.get("dividendRate")
            if div_rate is None:
                # Fallback : Yield * Price
                dy = info.get("dividendYield", 0.0)
                if dy:
                    div_rate = dy * current_price
                else:
                    div_rate = 0.0

            div_rate = float(div_rate)

            # Beta
            beta = info.get("beta", 1.0)
            beta = float(beta) if beta is not None else 1.0

            # Instanciation Pydantic (CompanyFinancials)
            return CompanyFinancials(
                ticker=ticker,
                name=str(info.get("shortName", ticker)),
                sector=str(info.get("sector", "Unknown")),
                industry=str(info.get("industry", "Unknown")),
                country=str(info.get("country", "Unknown")),
                currency=currency,
                current_price=float(current_price),
                shares_outstanding=shares,

                total_debt=total_debt,
                cash_and_equivalents=total_cash,
                minority_interests=float(minority_interests),
                pension_provisions=float(pension_provisions),
                interest_expense=interest_expense,
                book_value_per_share=book_value_per_share,

                beta=beta,
                revenue_ttm=float(info.get("totalRevenue") or 0.0),
                ebitda_ttm=float(info.get("ebitda") or 0.0),
                net_income_ttm=float(info.get("netIncomeToCommon") or 0.0),
                eps_ttm=float(info.get("trailingEps") or 0.0),

                last_dividend=info.get("lastDividendValue"), # Peut être None
                dividend_share=div_rate,

                fcf_last=fcf,
                fcf_fundamental_smoothed=fcf,
                source_fcf="yahoo_deep_fetch"
            )

        except TickerNotFoundError:
            raise
        except ValidationError as ve:
            logger.error(f"[Yahoo] Validation Error for {ticker}: {ve}")
            raise ExternalServiceError(provider="Yahoo/Pydantic", error_detail=str(ve))
        except Exception as e:
            logger.error(f"[Yahoo] Unexpected error for {ticker}: {str(e)}")
            raise ExternalServiceError(provider="Yahoo Finance", error_detail=str(e))

    # ==========================================================================
    # 2. HISTORIQUE DE PRIX
    # ==========================================================================

    @st.cache_data(ttl=3600 * 4)
    def get_price_history(_self, ticker: str, period: str = "5y") -> pd.DataFrame:
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
        Instancie DCFParameters avec validation stricte.
        """
        # 1. Données Entreprise
        financials = self.get_company_financials(ticker)

        # 2. Données Macro & Pays (Fallback)
        country_data = COUNTRY_CONTEXT.get(financials.country, DEFAULT_COUNTRY)
        try:
            macro_ctx = self.macro_provider.get_macro_context(
                date=datetime.now(),
                currency=financials.currency
            )
        except Exception as e:
            logger.error(f"Macro failure: {e}. Switching to country fallback.")
            from infra.macro.yahoo_macro_provider import MacroContext
            macro_ctx = MacroContext(
                date=datetime.now(),
                currency=financials.currency,
                risk_free_rate=float(country_data["risk_free_rate"]),
                market_risk_premium=float(country_data["market_risk_premium"]),
                perpetual_growth_rate=float(country_data["inflation_rate"]),
                corporate_aaa_yield=float(country_data["risk_free_rate"] + 0.01)
            )

        # 3. Calcul des paramètres implicites dynamiques

        # --- Fiscalité dynamique ---
        # On privilégie le taux du contexte pays (Standard OCDE/Local)
        effective_tax_rate = float(country_data.get("tax_rate", 0.25))

        # --- Croissance dynamique (CAGR) ---
        # On tente de justifier g par l'historique des flux (Deep Fetch)
        try:
            yt = yf.Ticker(ticker)
            hist_cf = safe_api_call(lambda: yt.cash_flow, "Cash Flow History")
            # Justification mathématique de la croissance attendue
            growth_assumption = calculate_historical_cagr(hist_cf, "Free Cash Flow")

            # Prudence : on borne la croissance automatique entre 1% et 10%
            growth_assumption = max(0.01, min(growth_assumption, 0.10))
        except Exception:
            growth_assumption = 0.03 # Fallback standard 3% si historique corrompu

        kd_synthetic = calculate_synthetic_cost_of_debt(
            rf=macro_ctx.risk_free_rate,
            ebit=financials.fcf_last or 1.0,
            interest_expense=financials.interest_expense,
            market_cap=financials.current_price * financials.shares_outstanding
        )

        # 4. Création SÉCURISÉE des paramètres
        try:
            params = DCFParameters(
                risk_free_rate=macro_ctx.risk_free_rate,
                market_risk_premium=macro_ctx.market_risk_premium,
                corporate_aaa_yield=macro_ctx.corporate_aaa_yield,
                cost_of_debt=kd_synthetic,
                tax_rate=effective_tax_rate,
                fcf_growth_rate=growth_assumption,
                perpetual_growth_rate=macro_ctx.perpetual_growth_rate,
                projection_years=projection_years,
                target_equity_weight=financials.market_cap,
                target_debt_weight=financials.total_debt,

                # --- AJOUT DES STANDARDS INSTITUTIONNELS (Prudence AUTO) ---
                # On définit ici la "volatilité par défaut" pour le mode AUTO
                beta_volatility=0.10,  # ± 10% sur le Beta
                growth_volatility=0.015,  # ± 1.5% sur la croissance g
                terminal_growth_volatility=0.005,  # ± 0.5% sur la croissance perpétuelle
                correlation_beta_growth=-0.30  # Corrélation standard risque/croissance
            )

            params.normalize_weights()
            return financials, params

        except ValidationError as ve:
            logger.critical(f"[Param Build] Erreur de validation Pydantic : {ve}")
            raise ExternalServiceError(
                provider="Parameters Engine",
                error_detail=f"Données incohérentes détectées : {ve}"
            )