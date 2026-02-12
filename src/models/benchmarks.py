"""
src/models/benchmarks.py

MARKET CONTEXT & SECTORAL BENCHMARKS (PILLAR 3)
===============================================
Role: Stores external reference data and Calculate Company Ratios.
Scope: Sector multiples, average margins, growth benchmarks, and Company Stats.
Architecture: Pydantic V2. Includes Factory Logic for Ratio Computation.
Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

# Avoid circular imports at runtime
if TYPE_CHECKING:
    from src.models.company import CompanySnapshot


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


class CompanyStats(BaseModel):
    """
    Computed financial ratios for the target company (The 'Subject').
    Used to compare against the MarketContext.

    Attributes
    ----------
    pe_ratio : float | None
        Price to Earnings ratio (Spot/TTM).
    ev_ebitda : float | None
        Enterprise Value to EBITDA ratio.
    pb_ratio : float | None
        Price to Book ratio.
    fcf_margin : float | None
        Free Cash Flow Margin (FCF / Revenue).
    roe : float | None
        Return on Equity (Net Income / Equity).
    revenue_growth : float | None
        Revenue Growth Rate (Year-over-Year).
    piotroski_score : int
        Financial strength score (0-9).
    """
    # Valuation Multiples (Spot / TTM)
    pe_ratio: float | None = None
    ev_ebitda: float | None = None
    pb_ratio: float | None = None

    # Operational Performance
    fcf_margin: float | None = None
    roe: float | None = None
    revenue_growth: float | None = None

    # Financial Health
    piotroski_score: int = 0

    @classmethod
    def compute(cls, snap: CompanySnapshot) -> CompanyStats:
        """
        Factory Method: Computes financial ratios from a CompanySnapshot.

        Encapsulates all the business logic for ratio calculation (Safe Division,
        Proxy selection, etc.) ensuring the Orchestrator remains clean.

        Parameters
        ----------
        snap : CompanySnapshot
            The raw financial data bag (TTM financials and Price).

        Returns
        -------
        CompanyStats
            A populated statistics object ready for benchmarking.
        """
        stats = cls()

        # Guard clause: We need at least a price to calculate market multiples
        price = snap.current_price
        if not price or price <= 0:
            return stats

        shares = snap.shares_outstanding or 0.0
        market_cap = price * shares

        # --- 1. Valuation Multiples ---

        # P/E Ratio = Price / EPS (TTM)
        if snap.eps_ttm and snap.eps_ttm > 0:
            stats.pe_ratio = price / snap.eps_ttm

        # P/B Ratio = Price / Book Value Per Share
        if snap.book_value_ps and snap.book_value_ps > 0:
            stats.pb_ratio = price / snap.book_value_ps

        # EV/EBITDA Calculation
        # We need Market Enterprise Value = Market Cap + Net Debt
        # Note: We use Snapshot data (Market) not Intrinsic Model data here for consistency.
        net_debt = (snap.total_debt or 0.0) - (snap.cash_and_equivalents or 0.0)
        market_ev = market_cap + net_debt

        # EBITDA Proxy: Usually EBIT + D&A. If EBITDA missing, use EBIT as strict proxy.
        # Ideally, Snapshot should have 'ebitda_ttm'. Using EBIT is a conservative fallback.
        earnings_metric = snap.ebit_ttm
        if earnings_metric and earnings_metric > 0:
            stats.ev_ebitda = market_ev / earnings_metric

        # --- 2. Operational Performance ---

        # FCF Margin = FCF / Revenue
        if snap.revenue_ttm and snap.revenue_ttm > 0 and snap.fcf_ttm:
            stats.fcf_margin = snap.fcf_ttm / snap.revenue_ttm

        # ROE = Net Income / Shareholder Equity
        # Equity approx = Book Value per Share * Shares (Market view of equity book)
        equity_book = (snap.book_value_ps or 0.0) * shares
        if equity_book > 0 and snap.net_income_ttm:
            stats.roe = snap.net_income_ttm / equity_book

        # Revenue Growth (Requires N-1 data, usually pre-calculated in snapshot or provider)
        # Leaving as None if not provided in snapshot directly.

        # Piotroski F-Score (Placeholder logic - requires deep historical accounting)
        # Default to 5 (Average) to avoid alarming users with "0 - Fragile" due to missing data.
        stats.piotroski_score = 5

        return stats


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
        description="Percentile thresholds for key metrics."
    )
