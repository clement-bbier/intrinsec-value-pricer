"""
src/models/benchmarks.py

MARKET CONTEXT & SECTORAL BENCHMARKS (PILLAR 3)
===============================================
Role: Stores external reference data from ETFs and Sectoral Indices.
Scope: Sector multiples, average margins, and growth benchmarks.
Architecture: Pydantic V2. Used by the Engine to position the company vs its peers.
Style: Numpy docstrings.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SectorMultiples(BaseModel):
    """
    Average valuation multiples for the sector (ETF-based).

    Attributes
    ----------
    pe_ratio : float | None
        Price to Earnings ratio (P/E).
    ev_ebitda : float | None
        Enterprise Value to EBITDA ratio.
    ev_revenue : float | None
        Enterprise Value to Revenue ratio.
    pb_ratio : float | None
        Price to Book ratio (P/B).
    """
    pe_ratio: float | None = None
    ev_ebitda: float | None = None
    ev_revenue: float | None = None
    pb_ratio: float | None = None


class SectorPerformance(BaseModel):
    """
    Average operational metrics for the sector.

    Attributes
    ----------
    fcf_margin : float | None
        Average Free Cash Flow margin of the sector.
    revenue_growth : float | None
        Average revenue growth (3Y/5Y CAGR).
    roe : float | None
        Average Return on Equity.
    net_margin : float | None
        Average Net Income margin.
    """
    fcf_margin: float | None = Field(None, description="Average FCF margin of the sector.")
    revenue_growth: float | None = Field(None, description="Average revenue growth (3Y/5Y).")
    roe: float | None = Field(None, description="Average Return on Equity.")
    net_margin: float | None = None


class MarketContext(BaseModel):
    """
    The 'Yardstick' for Pillar 3 Benchmarking.
    Contains data from the most relevant Sectoral ETF or Index.

    Attributes
    ----------
    reference_ticker : str
        The ETF or Index used as benchmark (e.g., XLK).
    sector_name : str
        Human-readable name of the sector.
    multiples : SectorMultiples
        Aggregated valuation multiples.
    performance : SectorPerformance
        Aggregated operational metrics.
    risk_free_rate : float
        The foundational risk-free rate used for the market data snapshot.
    equity_risk_premium : float
        The market risk premium used for the market data snapshot.
    percentiles : Dict[str, Dict[str, float]]
        Percentile thresholds for key metrics (e.g., {'fcf_margin': {'p75': 0.18}}).
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
    percentiles: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Percentile thresholds for key metrics (e.g., {'fcf_margin': {'p75': 0.18}})."
    )
