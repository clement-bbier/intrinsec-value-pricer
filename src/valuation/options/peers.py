"""
src/valuation/options/peers.py

PEERS RUNNER (RELATIVE VALUATION)
=================================
Role: Triangulation of P/E, EV/EBITDA, and EV/Revenue signals.
Architecture: Runner Pattern (Stateless).
Input: Target Company + Sector Multiples Data.
Output: PeersResults (with Implied Prices).

Standard: SOLID, i18n Secured.
Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.models.company import Company
from src.models.results.options import PeersResults
from src.models.market_data import MultiplesData

from src.computation.financial_math import (
    calculate_price_from_pe_multiple,
    calculate_price_from_ev_multiple,
    calculate_triangulated_price
)

logger = logging.getLogger(__name__)


class PeersRunner:
    """
    Orchestrates Relative Valuation via peer-group triangulation.
    """

    @staticmethod
    def execute(financials: Company, multiples_data: Optional[MultiplesData]) -> Optional[PeersResults]:
        """
        Executes the multiples-based valuation sequence.

        Parameters
        ----------
        financials : Company
            Target company financials (TTM).
        multiples_data : Optional[MultiplesData]
            The sector multiples collected from data providers.
            If None (provider failure), returns None.

        Returns
        -------
        Optional[PeersResults]
            A result object containing the three signals and the final triangulated value.
        """
        if not multiples_data or not multiples_data.is_valid:
            return None

        f = financials
        m = multiples_data

        # --- PREPARATION: EQUITY BRIDGE COMPONENTS ---
        # Net Debt = Total Debt - Cash
        total_debt = f.total_debt or 0.0
        cash = f.cash_and_equivalents or 0.0
        net_debt = total_debt - cash

        shares = f.shares_outstanding or 1.0
        minorities = f.minority_interests or 0.0
        pensions = f.pension_provisions or 0.0

        # --- 1. INDIVIDUAL PRICE SIGNAL COMPUTATION ---

        # Signal A: Equity-based (P/E)
        # Formula: (NI * P/E) / Shares
        price_pe = calculate_price_from_pe_multiple(
            net_income=f.net_income_ttm or 0.0,
            median_pe=m.median_pe,
            shares=shares
        )

        # Signal B: Enterprise-based (EV/EBITDA)
        # Formula: (EBITDA * Multiple - NetDebt - Min - Pens) / Shares
        price_ebitda = calculate_price_from_ev_multiple(
            metric_value=f.ebitda_ttm or 0.0,
            median_ev_multiple=m.median_ev_ebitda,
            net_debt=net_debt,
            shares=shares,
            minorities=minorities,
            pensions=pensions
        )

        # Signal C: Enterprise-based (EV/Revenue)
        # Formula: (Rev * Multiple - NetDebt - Min - Pens) / Shares
        price_rev = calculate_price_from_ev_multiple(
            metric_value=f.revenue_ttm or 0.0,
            median_ev_multiple=m.median_ev_rev,
            net_debt=net_debt,
            shares=shares,
            minorities=minorities,
            pensions=pensions
        )

        # --- 2. FINAL TRIANGULATION ---
        signals = {
            "P/E": price_pe,
            "EV/EBITDA": price_ebitda,
            "EV/Revenue": price_rev
        }

        # Weighted synthesis (Average of valid positive signals)
        final_iv = calculate_triangulated_price(signals)

        # --- 3. PACKAGING RESULTS ---
        return PeersResults(
            median_multiples_used={
                "P/E": m.median_pe,
                "EV/EBITDA": m.median_ev_ebitda,
                "EV/Revenue": m.median_ev_rev
            },
            implied_prices=signals,
            peer_valuations=[], # Can be enriched if we run batch valuation on peers
            final_relative_iv=final_iv
        )