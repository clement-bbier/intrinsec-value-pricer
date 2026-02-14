"""
src/models/market_data.py

MARKET DATA MODELS
==================
Role: Containers for external market data, peer groups, and multiples.
Scope: Used by PeersRunner for relative valuation triangulation.
Architecture: Pydantic V2 DTOs.
Style: Numpy docstrings.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PeerMetric(BaseModel):
    """
    Represents a single peer in the comparative analysis.

    Attributes
    ----------
    ticker : str
        Stock symbol.
    company_name : str | None
        Legal name of the peer company.
    pe_ratio : float | None
        Price to Earnings ratio.
    ev_ebitda : float | None
        Enterprise Value to EBITDA ratio.
    ev_revenue : float | None
        Enterprise Value to Revenue ratio.
    """

    ticker: str
    company_name: str | None = None
    pe_ratio: float | None = None
    ev_ebitda: float | None = None
    ev_revenue: float | None = None


class MultiplesData(BaseModel):
    """
    Aggregated sector multiples and peer cohort data.
    Passed to the PeersRunner to calculate implied prices.

    Attributes
    ----------
    median_pe : float
        Sector median Price-to-Earnings ratio.
    median_ev_ebitda : float
        Sector median EV/EBITDA ratio.
    median_ev_rev : float
        Sector median EV/Revenue ratio.
    peers : List[PeerMetric]
        List of comparable companies used to derive these medians.
    is_valid : bool
        Flag indicating if enough data was collected to trust these multiples.
    """

    median_pe: float = 0.0
    median_ev_ebitda: float = 0.0
    median_ev_rev: float = 0.0
    peers: list[PeerMetric] = Field(default_factory=list)
    is_valid: bool = False
