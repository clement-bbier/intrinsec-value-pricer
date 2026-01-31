"""
infra/data_providers/financial_normalizer.py

FINANCIAL DATA NORMALIZER
=========================
Role: TTM (Trailing Twelve Months) reconstruction and peer normalization.
Responsibility: Transforms raw Yahoo data into validated models (CompanyFinancials & MultiplesData).

Paradigm: Honest Data — Strict filtering of outliers for accurate triangulation.
Architecture: Data Infrastructure Layer.
"""

from __future__ import annotations

import logging
import statistics
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import ValidationError

from src.models import Company, PeerMetric, MultiplesData
from src.i18n import DiagnosticTexts
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
    Orchestrates the transformation of raw API payloads into standardized
    financial structures. Enforces Pydantic-based validation and economic
    robustness filters for sector comparison.
    """

    # =========================================================================
    # 1. TARGET COMPANY NORMALIZATION
    # =========================================================================

    def normalize(self, raw: RawFinancialData) -> Optional[Company]:
        """
        Main orchestrator for company data normalization.
        Reconstructs the capital structure and TTM profitability.
        """
        if not raw.is_valid:
            logger.warning("[Normalizer] Invalid raw data for %s", raw.ticker)
            return None

        info = raw.info
        currency, current_price = normalize_currency_and_price(info)

        # Segmented reconstruction logic
        shares = self._reconstruct_shares(info, raw.balance_sheet, current_price)
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

        return Company(
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
    # 2. PEER NORMALIZATION (PILLAR 5)
    # =========================================================================

    def normalize_peers(self, raw_peers: List[Dict[str, Any]]) -> MultiplesData:
        """
        Converts raw peer lists into a summary of validated valuation multiples.
        Filters extreme economic outliers (e.g., P/E > 100) to protect triangulation.
        """
        valid_peers: List[PeerMetric] = []

        for p_info in raw_peers:
            ticker = p_info.get("symbol", "N/A")
            try:
                # 1. Type validation via Pydantic model
                peer = PeerMetric(
                    ticker=ticker,
                    name=p_info.get("shortName", ticker),
                    pe_ratio=p_info.get("trailingPE"),
                    ev_ebitda=p_info.get("enterpriseToEbitda"),
                    ev_revenue=p_info.get("enterpriseToRevenue"),
                    market_cap=p_info.get("marketCap", 0.0)
                )

                # 2. Economic Robustness Filtering
                if self._is_peer_robust(peer):
                    valid_peers.append(peer)
                else:
                    logger.info(DiagnosticTexts.DATA_PEER_SKIP_MSG.format(ticker=ticker))

            except (ValidationError, TypeError, ValueError):
                continue

        # 3. Robust statistics calculation (Median-based)
        return self._build_multiples_summary(valid_peers)

    @staticmethod
    def _is_peer_robust(peer: PeerMetric) -> bool:
        """
        Applies safety thresholds on valuation multiples.
        Filters out money-losing firms (Negative P/E) or absurd valuations.
        """
        # P/E Filtering (Trailing)
        if peer.pe_ratio is not None:
            if not (0.1 < peer.pe_ratio < 100.0):
                return False

        # EV/EBITDA Filtering
        if peer.ev_ebitda is not None:
            if not (0.1 < peer.ev_ebitda < 60.0):
                return False

        return True

    @staticmethod
    def _build_multiples_summary(peers: List[PeerMetric]) -> MultiplesData:
        """Calculates sectoral medians for the Football Field visualization."""
        if not peers:
            return MultiplesData()

        # Extract lists for statistical processing
        pes = [p.pe_ratio for p in peers if p.pe_ratio is not None]
        ebitda_list = [p.ev_ebitda for p in peers if p.ev_ebitda is not None]
        revs = [p.ev_revenue for p in peers if p.ev_revenue is not None]

        return MultiplesData(
            peers=peers,
            median_pe=statistics.median(pes) if pes else 0.0,
            median_ev_ebitda=statistics.median(ebitda_list) if ebitda_list else 0.0,
            median_ev_rev=statistics.median(revs) if revs else 0.0
        )

    # =========================================================================
    # RECONSTRUCTION HELPERS (STRICT AUDIT)
    # =========================================================================

    @staticmethod
    def _reconstruct_shares(info: Dict[str, Any], bs: Optional[pd.DataFrame], price: float) -> float:
        """Extracts current share count using fallback hierarchy."""
        shares = info.get("sharesOutstanding")
        if not shares and bs is not None:
            shares = extract_most_recent_value(bs, ["Ordinary Shares Number", "Share Issued"])
        if not shares:
            mcap = info.get("marketCap", 0.0)
            if mcap > 0 and price > 0:
                shares = mcap / price
        return float(shares) if shares else 1.0

    @staticmethod
    def extract_shares_history(bs: Optional[pd.DataFrame]) -> List[float]:
        """Extracts chronological share count series (Oldest to Newest)."""
        if bs is None or bs.empty:
            return []

        keys = ["Ordinary Shares Number", "Share Issued"]
        for key in keys:
            if key in bs.index:
                # Reverse Yahoo's New-to-Old delivery
                series = bs.loc[key].dropna().iloc[::-1].tolist()
                if len(series) >= 2:
                    return [float(v) for v in series]
        return []

    def _reconstruct_capital_structure(
            self,
            info: Dict[str, Any],
            bs: Optional[pd.DataFrame],
            is_: Optional[pd.DataFrame],
            cf: Optional[pd.DataFrame]
    ) -> Dict[str, Any]:
        """Reconstructs the Equity Bridge components (Debt, Cash, Provisions)."""
        debt = self._extract_total_debt(info, bs)
        cash = self._extract_cash(info, bs)
        minority = self._extract_minority_interests(bs)
        pensions = self._extract_pension_provisions(bs)
        interest = self._extract_interest_expense(is_)
        net_borrowing = self._extract_net_borrowing(cf)

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
            "book_value": total_bv
        }

    def _reconstruct_profitability(self, info: Dict[str, Any], is_a: Optional[pd.DataFrame], cf_a: Optional[pd.DataFrame],
                                 is_q: Optional[pd.DataFrame], cf_q: Optional[pd.DataFrame]) -> Dict[str, Any]:
        """Aggregates TTM (Trailing Twelve Months) and smoothed profitability metrics."""
        rev_ttm = self._sum_last_4_quarters(is_q, ["Total Revenue", "Revenue"])
        ebit_ttm = self._sum_last_4_quarters(is_q, ["EBIT", "Operating Income"])
        ni_ttm = self._sum_last_4_quarters(is_q, ["Net Income Common Stockholders", "Net Income"])

        # TTM Fallback logic
        rev_ttm = rev_ttm or info.get("totalRevenue") or extract_most_recent_value(is_a, ["Total Revenue"])
        ebit_ttm = ebit_ttm or info.get("operatingCashflow") or extract_most_recent_value(is_a, ["EBIT", "Operating Income"])
        ni_ttm = ni_ttm or info.get("netIncomeToCommon") or extract_most_recent_value(is_a, ["Net Income"])

        fcf_annuel = get_simple_annual_fcf(cf_a)
        fcf_ttm = self._sum_last_4_quarters(cf_q, ["Free Cash Flow"]) or fcf_annuel
        capex = extract_most_recent_value(cf_a, CAPEX_KEYS)
        da = self._extract_depreciation_amortization(cf_a)
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

    @staticmethod
    def _extract_net_borrowing(cf: Optional[pd.DataFrame]) -> Optional[float]:
        """Extracts net change in debt (Net Borrowing)."""
        if cf is None:
            return 0.0
        net_flow = extract_most_recent_value(cf, ["Net Issuance Payments Of Debt"])
        if net_flow is not None:
            return net_flow
        issuance = extract_most_recent_value(cf, DEBT_ISSUANCE_KEYS) or 0.0
        repayment = extract_most_recent_value(cf, DEBT_REPAYMENT_KEYS) or 0.0
        return issuance + repayment

    @staticmethod
    def _extract_total_debt(info: Dict, bs: Optional[pd.DataFrame]) -> Optional[float]:
        """Extracts gross total debt."""
        debt = info.get("totalDebt")
        if not debt and bs is not None:
            debt = extract_most_recent_value(bs, ["Total Debt", "Net Debt"])
            if not debt:
                std = extract_most_recent_value(bs, ["Current Debt", "Current Debt And Lease Obligation"]) or 0
                ltd = extract_most_recent_value(bs, ["Long Term Debt", "Long Term Debt And Lease Obligation"]) or 0
                debt = (std + ltd) if (std + ltd) > 0 else None
        return debt

    @staticmethod
    def _extract_cash(info: Dict, bs: Optional[pd.DataFrame]) -> Optional[float]:
        """Extracts total cash and equivalents."""
        cash = info.get("totalCash")
        if not cash and bs is not None:
            cash = extract_most_recent_value(bs, ["Cash And Cash Equivalents", "Cash Financial"])
        return cash

    @staticmethod
    def _extract_minority_interests(bs: Optional[pd.DataFrame]) -> Optional[float]:
        """Extracts minority interests (non-controlling)."""
        if bs is None:
            return 0.0
        return extract_most_recent_value(bs, ["Minority Interest", "Non Controlling Interest"])

    @staticmethod
    def _extract_pension_provisions(bs: Optional[pd.DataFrame]) -> Optional[float]:
        """Extracts pension and post-retirement provisions."""
        if bs is None:
            return 0.0
        return extract_most_recent_value(bs, ["Long Term Provisions", "Pension And Other Postretirement Benefit Plans"])

    @staticmethod
    def _extract_interest_expense(is_: Optional[pd.DataFrame]) -> Optional[float]:
        """Extracts interest expense."""
        if is_ is None:
            return None
        return extract_most_recent_value(is_, ["Interest Expense", "Interest Expense Non Operating"])

    @staticmethod
    def _extract_depreciation_amortization(cf_a: Optional[pd.DataFrame]) -> Optional[float]:
        """Extracts depreciation and amortization charges."""
        da = extract_most_recent_value(cf_a, DA_KEYS)
        if da is None and cf_a is not None:
            dep = extract_most_recent_value(cf_a, ["Depreciation"]) or 0
            amo = extract_most_recent_value(cf_a, ["Amortization"]) or 0
            da = (dep + amo) if (dep + amo) > 0 else None
        return da

    @staticmethod
    def _sum_last_4_quarters(df: Optional[pd.DataFrame], keys: List[str]) -> Optional[float]:
        """Aggregates the last 4 quarters for a given metric to build TTM values."""
        if df is None or df.empty:
            return None
        for key in keys:
            if key in df.index:
                last_4 = df.loc[key].iloc[: 4]
                # Ensure we have exactly 4 quarters for a robust TTM reconstruction
                if len(last_4) == 4 and not last_4.isnull().any():
                    return float(last_4.sum())
        return None