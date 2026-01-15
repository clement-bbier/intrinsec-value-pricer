"""
infra/data_providers/financial_normalizer.py

NORMALISATION DES DONNÉES FINANCIÈRES — VERSION V10.0 (Sprint 3)
Rôle : Reconstruction TTM, agrégation D&A, Net Borrowing et standardisation.
Responsabilité : Transformer les données brutes Yahoo en CompanyFinancials.

Paradigme : Honest Data — Propagation stricte des None.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from core.models import CompanyFinancials
from infra.data_providers.yahoo_raw_fetcher import RawFinancialData
from infra.data_providers.extraction_utils import (
    CAPEX_KEYS,
    DA_KEYS,
    DEBT_ISSUANCE_KEYS,
    DEBT_REPAYMENT_KEYS,
    extract_most_recent_value,
    get_simple_annual_fcf,
    normalize_currency_and_price,
)

logger = logging.getLogger(__name__)


class FinancialDataNormalizer:
    """
    Transforme les données brutes Yahoo en CompanyFinancials standardisé.
    Gère désormais l'extraction du Net Borrowing pour le modèle FCFE.
    """

    def normalize(self, raw: RawFinancialData) -> Optional[CompanyFinancials]:
        """
        Orchestrateur de la normalisation.
        """
        if not raw.is_valid:
            logger.warning("[Normalizer] Invalid raw data for %s", raw.ticker)
            return None

        info = raw.info
        currency, current_price = normalize_currency_and_price(info)

        # 1. Reconstruction par segments (Passage des DataFrames requis)
        shares = self._reconstruct_shares(info, raw.balance_sheet, current_price)

        # FIX : On passe explicitement le cash_flow pour le Net Borrowing
        capital_structure = self._reconstruct_capital_structure(
            info, raw.balance_sheet, raw.income_stmt, raw.cash_flow
        )

        profitability = self._reconstruct_profitability(
            info,
            raw.income_stmt,
            raw.cash_flow,
            raw.quarterly_income_stmt,
            raw.quarterly_cash_flow
        )

        return CompanyFinancials(
            ticker=raw.ticker,
            name=str(info.get("shortName", raw.ticker)),
            sector=str(info.get("sector", "Unknown")),
            industry=str(info.get("industry", "Unknown")),
            country=str(info.get("country", "Unknown")),
            currency=currency,
            current_price=float(current_price),
            shares_outstanding=shares,
            **capital_structure,
            **profitability
        )

    # =========================================================================
    # RECONSTRUCTION DES MÉTRIQUES
    # =========================================================================

    def _reconstruct_shares(self, info: Dict[str, Any], bs: Optional[pd.DataFrame], price: float) -> float:
        """Reconstruit le nombre d'actions avec fallback intelligent."""
        shares = info.get("sharesOutstanding")
        if not shares and bs is not None:
            shares = extract_most_recent_value(bs, ["Ordinary Shares Number", "Share Issued"])
        if not shares:
            mcap = info.get("marketCap", 0.0)
            if mcap > 0 and price > 0:
                shares = mcap / price
        return float(shares) if shares else 1.0

    def _reconstruct_capital_structure(
            self,
            info: Dict[str, Any],
            bs: Optional[pd.DataFrame],
            is_: Optional[pd.DataFrame],
            cf: Optional[pd.DataFrame]  # Doit utiliser 'cf' et non 'raw'
    ) -> Dict[str, Any]:
        debt = self._extract_total_debt(info, bs)
        cash = self._extract_cash(info, bs)
        minority = self._extract_minority_interests(bs)
        pensions = self._extract_pension_provisions(bs)
        interest = self._extract_interest_expense(is_)
        net_borrowing = self._extract_net_borrowing(cf)  # Fix reference

        # Calcul de la Book Value totale (Crucial pour le ROE/Audit)
        book_valu_vps = float(info.get("bookValue") or 0.0)
        shares = info.get("sharesOutstanding") or 1.0
        total_bv = book_valu_vps * shares

        return {
            "total_debt": float(debt) if debt is not None else 0.0,
            "cash_and_equivalents": float(cash) if cash is not None else 0.0,
            "minority_interests": float(minority or 0.0),
            "pension_provisions": float(pensions or 0.0),
            "interest_expense": float(abs(interest)) if interest is not None else 0.0,
            "net_borrowing_ttm": float(net_borrowing) if net_borrowing is not None else 0.0,
            "book_value": total_bv  # Injection de la valeur totale
        }

    def _reconstruct_profitability(
            self,
            info: Dict[str, Any],
            is_a: Optional[pd.DataFrame],
            cf_a: Optional[pd.DataFrame],
            is_q: Optional[pd.DataFrame],
            cf_q: Optional[pd.DataFrame]
    ) -> Dict[str, Any]:
        """Extraction TTM via somme trimestrielle avec agrégation D&A."""
        # 1. Tentative TTM (Somme des 4 derniers trimestres)
        rev_ttm = self._sum_last_4_quarters(is_q, ["Total Revenue", "Revenue"])
        ebit_ttm = self._sum_last_4_quarters(is_q, ["EBIT", "Operating Income"])
        ni_ttm = self._sum_last_4_quarters(is_q, ["Net Income Common Stockholders", "Net Income"])

        # 2. Fallbacks sur l'annuel ou l'info
        rev_ttm = rev_ttm or info.get("totalRevenue") or extract_most_recent_value(is_a, ["Total Revenue"])
        ebit_ttm = ebit_ttm or info.get("operatingCashflow") or extract_most_recent_value(is_a, ["EBIT", "Operating Income"])
        ni_ttm = ni_ttm or info.get("netIncomeToCommon") or extract_most_recent_value(is_a, ["Net Income"])

        # 3. FCF, Capex & D&A
        fcf_annuel = get_simple_annual_fcf(cf_a)
        fcf_ttm = self._sum_last_4_quarters(cf_q, ["Free Cash Flow"]) or fcf_annuel
        capex = extract_most_recent_value(cf_a, CAPEX_KEYS)
        da = self._extract_depreciation_amortization(cf_a)

        # 4. Dividendes (Source robuste)
        div_rate = info.get("dividendRate") or (info.get("dividendYield", 0) * info.get("currentPrice", 0))

        return {
            "revenue_ttm": float(rev_ttm) if rev_ttm is not None else None,
            "ebitda_ttm": float(info.get("ebitda") or 0.0),
            "ebit_ttm": float(ebit_ttm) if ebit_ttm is not None else None,
            "net_income_ttm": float(ni_ttm) if ni_ttm is not None else None,
            "eps_ttm": float(info.get("trailingEps") or 0.0),
            "dividend_share": float(div_rate or 0.0),
            "book_value_per_share": float(info.get("bookValue") or 0.0),
            "beta": float(info.get("beta") or 1.0),
            "fcf_last": float(fcf_ttm) if fcf_ttm is not None else None,
            "fcf_fundamental_smoothed": float(fcf_annuel) if fcf_annuel is not None else None,
            "capex": float(capex) if capex is not None else None,
            "depreciation_and_amortization": float(da) if da is not None else None
        }

    # =========================================================================
    # HELPERS D'EXTRACTION (HONEST DATA)
    # =========================================================================

    def _extract_net_borrowing(self, cf: Optional[pd.DataFrame]) -> Optional[float]:
        """
        Calcule le Net Borrowing = Émission - Remboursement de dette.
        Priorité 1 : Clé agrégée Yahoo | Priorité 2 : Calcul manuel.
        """
        if cf is None: return 0.0

        # Tentative Clé agrégée
        net_flow = extract_most_recent_value(cf, ["Net Issuance Payments Of Debt"])
        if net_flow is not None: return net_flow

        # Calcul manuel via extraction_utils
        issuance = extract_most_recent_value(cf, DEBT_ISSUANCE_KEYS) or 0.0
        repayment = extract_most_recent_value(cf, DEBT_REPAYMENT_KEYS) or 0.0

        return issuance + repayment

    def _extract_total_debt(self, info: Dict, bs: Optional[pd.DataFrame]) -> Optional[float]:
        debt = info.get("totalDebt")
        if not debt and bs is not None:
            debt = extract_most_recent_value(bs, ["Total Debt", "Net Debt"])
            if not debt:
                std = extract_most_recent_value(bs, ["Current Debt", "Current Debt And Lease Obligation"]) or 0
                ltd = extract_most_recent_value(bs, ["Long Term Debt", "Long Term Debt And Lease Obligation"]) or 0
                debt = (std + ltd) if (std + ltd) > 0 else None
        return debt

    def _extract_cash(self, info: Dict, bs: Optional[pd.DataFrame]) -> Optional[float]:
        cash = info.get("totalCash")
        if not cash and bs is not None:
            cash = extract_most_recent_value(bs, ["Cash And Cash Equivalents", "Cash Financial"])
        return cash

    def _extract_minority_interests(self, bs: Optional[pd.DataFrame]) -> Optional[float]:
        if bs is None: return 0.0
        return extract_most_recent_value(bs, ["Minority Interest", "Non Controlling Interest"])

    def _extract_pension_provisions(self, bs: Optional[pd.DataFrame]) -> Optional[float]:
        if bs is None: return 0.0
        return extract_most_recent_value(bs, ["Long Term Provisions", "Pension And Other Postretirement Benefit Plans"])

    def _extract_interest_expense(self, is_: Optional[pd.DataFrame]) -> Optional[float]:
        if is_ is None: return None
        return extract_most_recent_value(is_, ["Interest Expense", "Interest Expense Non Operating"])

    def _extract_depreciation_amortization(self, cf_a: Optional[pd.DataFrame]) -> Optional[float]:
        da = extract_most_recent_value(cf_a, DA_KEYS)
        if da is None and cf_a is not None:
            dep = extract_most_recent_value(cf_a, ["Depreciation"]) or 0
            amo = extract_most_recent_value(cf_a, ["Amortization"]) or 0
            da = (dep + amo) if (dep + amo) > 0 else None
        return da

    def _sum_last_4_quarters(self, df: Optional[pd.DataFrame], keys: List[str]) -> Optional[float]:
        if df is None or df.empty: return None
        for key in keys:
            if key in df.index:
                last_4 = df.loc[key].iloc[: 4]
                if len(last_4) == 4 and not last_4.isnull().any():
                    return float(last_4.sum())
        return None