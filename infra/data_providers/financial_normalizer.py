"""
infra/data_providers/financial_normalizer.py

NORMALISATION DES DONNÉES FINANCIÈRES — VERSION V11.0 (Sprint 4)
Rôle : Reconstruction TTM et normalisation des pairs (Multiples sectoriels).
Responsabilité : Transformer les données brutes Yahoo en modèles validés (CompanyFinancials & MultiplesData).

Paradigme : Honest Data — Filtrage strict des aberrations pour la triangulation.
"""

from __future__ import annotations

import logging
import statistics
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import ValidationError

from core.models import CompanyFinancials, PeerMetric, MultiplesData
from app.ui_components.ui_texts import DiagnosticTexts
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
    Transforme les données brutes Yahoo en structures financières standardisées.
    Gère la validation Pydantic des multiples pour éliminer les outliers sectoriels.
    """

    # =========================================================================
    # 1. NORMALISATION DE L'ENTREPRISE CIBLE (SPRINT 3)
    # =========================================================================

    def normalize(self, raw: RawFinancialData) -> Optional[CompanyFinancials]:
        """Orchestrateur de la normalisation pour l'entreprise principale."""
        if not raw.is_valid:
            logger.warning("[Normalizer] Invalid raw data for %s", raw.ticker)
            return None

        info = raw.info
        currency, current_price = normalize_currency_and_price(info)

        # Reconstruction par segments
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
    # 2. NORMALISATION DES PAIRS (SPRINT 4 - PHASE 3)
    # =========================================================================

    def normalize_peers(self, raw_peers: List[Dict[str, Any]]) -> MultiplesData:
        """
        Transforme une liste de dictionnaires bruts en synthèse de multiples validés.
        Filtre les données aberrantes (ex: P/E > 100) pour protéger la triangulation.
        """
        valid_peers: List[PeerMetric] = []

        for p_info in raw_peers:
            ticker = p_info.get("symbol", "N/A")
            try:
                # 1. Instanciation via Pydantic pour validation de type
                peer = PeerMetric(
                    ticker=ticker,
                    name=p_info.get("shortName", ticker),
                    pe_ratio=p_info.get("trailingPE"),
                    ev_ebitda=p_info.get("enterpriseToEbitda"),
                    ev_revenue=p_info.get("enterpriseToRevenue"),
                    market_cap=p_info.get("marketCap", 0.0)
                )

                # 2. Filtrage des aberrations économiques (Robustesse)
                if self._is_peer_robust(peer):
                    valid_peers.append(peer)
                else:
                    logger.info(DiagnosticTexts.DATA_PEER_SKIP_MSG.format(ticker=ticker))

            except (ValidationError, TypeError, ValueError):
                logger.debug(f"[Normalizer] Données illisibles pour le pair {ticker}, passage.")
                continue

        # 3. Calcul des médianes robustes
        return self._build_multiples_summary(valid_peers)

    def _is_peer_robust(self, peer: PeerMetric) -> bool:
        """
        Applique des filtres de sécurité sur les multiples.
        On écarte les entreprises en perte (P/E négatif) ou les valorisations absurdes.
        """
        # Filtrage P/E (Trailing)
        if peer.pe_ratio is not None:
            if not (0.1 < peer.pe_ratio < 100.0):
                return False

        # Filtrage EV/EBITDA
        if peer.ev_ebitda is not None:
            if not (0.1 < peer.ev_ebitda < 60.0):
                return False

        return True

    def _build_multiples_summary(self, peers: List[PeerMetric]) -> MultiplesData:
        """Calcule les médianes sectorielles pour les colonnes du Football Field."""
        if not peers:
            return MultiplesData()

        # Extraction des listes pour calcul statistique (uniquement valeurs non nulles)
        pes = [p.pe_ratio for p in peers if p.pe_ratio is not None]
        ebitdas = [p.ev_ebitda for p in peers if p.ev_ebitda is not None]
        revs = [p.ev_revenue for p in peers if p.ev_revenue is not None]

        return MultiplesData(
            peers=peers,
            median_pe=statistics.median(pes) if pes else 0.0,
            median_ev_ebitda=statistics.median(ebitdas) if ebitdas else 0.0,
            median_ev_rev=statistics.median(revs) if revs else 0.0
        )

    # =========================================================================
    # HELPERS DE RECONSTRUCTION (SPRINT 3 - MAINTENANCE)
    # =========================================================================

    def _reconstruct_shares(self, info: Dict[str, Any], bs: Optional[pd.DataFrame], price: float) -> float:
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
            cf: Optional[pd.DataFrame]
    ) -> Dict[str, Any]:
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
        rev_ttm = self._sum_last_4_quarters(is_q, ["Total Revenue", "Revenue"])
        ebit_ttm = self._sum_last_4_quarters(is_q, ["EBIT", "Operating Income"])
        ni_ttm = self._sum_last_4_quarters(is_q, ["Net Income Common Stockholders", "Net Income"])

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

    def _extract_net_borrowing(self, cf: Optional[pd.DataFrame]) -> Optional[float]:
        if cf is None: return 0.0
        net_flow = extract_most_recent_value(cf, ["Net Issuance Payments Of Debt"])
        if net_flow is not None: return net_flow
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