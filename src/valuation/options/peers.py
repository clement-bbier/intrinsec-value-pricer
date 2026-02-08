"""
src/valuation/options/peers.py

PEERS RUNNER (RELATIVE VALUATION)
=================================
Role: Triangulation of P/E, EV/EBITDA, and EV/Revenue signals.
Architecture: Runner Pattern (Stateless).
Logic: Computes implied share prices based on sector/peer median multiples.

Standard: SOLID, i18n Secured, NumPy Style.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict

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

    This runner applies market multiples to the target company's financial
    metrics to derive an implied intrinsic value from a relative perspective.
    """

    @staticmethod
    def execute(financials: Company, multiples_data: Optional[MultiplesData]) -> Optional[PeersResults]:
        """
        Execute the multiples-based valuation sequence.

        Parameters
        ----------
        financials : Company
            Target company financials (TTM data).
        multiples_data : Optional[MultiplesData]
            The sector or peer multiples collected from providers.

        Returns
        -------
        Optional[PeersResults]
            A result object containing price signals and final triangulated value.
            Returns None if multiples data is invalid or unavailable.
        """
        if not multiples_data or not multiples_data.is_valid:
            logger.warning("[Peers] Invalid or missing multiples data. Skipping extension.")
            return None

        f = financials
        m = multiples_data

        # --- 1. EQUITY BRIDGE PARAMETERS ---
        # Net Debt = Total Debt - Cash
        debt = f.total_debt or 0.0
        cash = f.cash_and_equivalents or 0.0
        net_debt = debt - cash

        shares = f.shares_outstanding or 1.0
        minorities = f.minority_interests or 0.0
        pensions = f.pension_provisions or 0.0

        # --- 2. INDIVIDUAL PRICE SIGNAL COMPUTATION ---
        signals: Dict[str, float] = {}

        # Signal A: P/E (Equity-based)
        if m.median_pe and m.median_pe > 0:
            signals["P/E"] = calculate_price_from_pe_multiple(
                net_income=f.net_income_ttm or 0.0,
                median_pe=m.median_pe,
                shares=shares
            )

        # Signal B: EV/EBITDA (Enterprise-based)
        if m.median_ev_ebitda and m.median_ev_ebitda > 0:
            signals["EV/EBITDA"] = calculate_price_from_ev_multiple(
                metric_value=f.ebitda_ttm or 0.0,
                median_ev_multiple=m.median_ev_ebitda,
                net_debt=net_debt,
                shares=shares,
                minorities=minorities,
                pensions=pensions
            )

        # Signal C: EV/Revenue (Enterprise-based)
        if m.median_ev_rev and m.median_ev_rev > 0:
            signals["EV/Revenue"] = calculate_price_from_ev_multiple(
                metric_value=f.revenue_ttm or 0.0,
                median_ev_multiple=m.median_ev_rev,
                net_debt=net_debt,
                shares=shares,
                minorities=minorities,
                pensions=pensions
            )

        if not signals:
            logger.error("[Peers] No valid signals generated from multiples.")
            return None

        # --- 3. FINAL TRIANGULATION ---
        # Weighted synthesis of all available signals
        final_iv = calculate_triangulated_price(signals)



        # --- 4. PACKAGING RESULTS ---
        return PeersResults(
            median_multiples_used={
                "P/E": m.median_pe,
                "EV/EBITDA": m.median_ev_ebitda,
                "EV/Revenue": m.median_ev_rev
            },
            implied_prices=signals,
            peer_valuations=[],  # Reserved for future peer-by-peer deep analysis
            final_relative_iv=final_iv
        )