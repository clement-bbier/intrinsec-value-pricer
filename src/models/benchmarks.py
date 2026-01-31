"""
src/models/market.py

MARKET CONTEXT & SECTORAL BENCHMARKS (PILLAR 3)
==============================================
Role: Stores external reference data from ETFs and Sectoral Indices.
Scope: Sector multiples, average margins, and growth benchmarks.
Architecture: Pydantic V2. Used by the Engine to position the company vs its peers.
"""

from __future__ import annotations
from typing import Optional, Dict
from pydantic import BaseModel, Field


class SectorMultiples(BaseModel):
    """Average valuation multiples for the sector (ETF-based)."""
    pe_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    ev_revenue: Optional[float] = None
    pb_ratio: Optional[float] = None


class SectorPerformance(BaseModel):
    """Average operational metrics for the sector."""
    fcf_margin: Optional[float] = Field(None, description="Average FCF margin of the sector.")
    revenue_growth: Optional[float] = Field(None, description="Average revenue growth (3Y/5Y).")
    roe: Optional[float] = Field(None, description="Average Return on Equity.")
    net_margin: Optional[float] = None


class MarketContext(BaseModel):
    """
    The 'Yardstick' for Pillar 3 Benchmarking.
    Contains data from the most relevant Sectoral ETF or Index.
    """
    # --- Reference Identity ---
    reference_ticker: str = Field(..., description="The ETF or Index used as benchmark (e.g., XLK).")
    sector_name: str

    # --- Benchmark Data ---
    multiples: SectorMultiples = Field(default_factory=SectorMultiples)
    performance: SectorPerformance = Field(default_factory=SectorPerformance)

    # --- Macro Rates ---
    risk_free_rate: float
    equity_risk_premium: float

    # --- Statistical Distribution (Optional) ---
    # Permet de savoir si l'entreprise est dans le top 10% ou 25%
    percentiles: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Percentile thresholds for key metrics (e.g., {'fcf_margin': {'p75': 0.18}})."
    )