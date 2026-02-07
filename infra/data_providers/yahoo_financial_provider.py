"""
infra/data_providers/yahoo_financial_provider.py

YAHOO FINANCE FINANCIAL PROVIDER — Unified Infrastructure Pipe
==============================================================
Role: Implementation of FinancialDataProvider for Yahoo Finance.
Responsibility: Acquire raw data, map to Micro, and enrich with Macro.
Standards: SOLID, Clean Code, No IDE warnings.
"""

from __future__ import annotations
import logging
from typing import Optional

import streamlit as st
from .base_provider import FinancialDataProvider
from src.models.company import CompanySnapshot
from infra.macro.base_macro_provider import MacroDataProvider
from .yahoo_raw_fetcher import YahooRawFetcher
from .yahoo_snapshot_mapper import YahooSnapshotMapper
from infra.ref_data.sector_fallback import get_sector_data

logger = logging.getLogger(__name__)


@st.cache_data(ttl=3600, show_spinner=False)
def _get_cached_snapshot(
    ticker: str,
    _fetcher: YahooRawFetcher,
    _mapper: YahooSnapshotMapper,
    _macro_provider: MacroDataProvider
) -> Optional[CompanySnapshot]:
    """
    Module-level private function to handle Streamlit caching.

    Arguments prefixed with '_' are ignored by Streamlit's hash engine,
    preventing errors with non-hashable objects like API fetchers.
    """
    try:
        # 1. API Fetching
        raw_data = _fetcher.fetch_ttm_snapshot(ticker)
        if not raw_data or not raw_data.is_valid:
            return None

        # 2. Technical Mapping
        snapshot = _mapper.map_to_snapshot(raw_data)

        # 3. Sector Fallback Enrichment (Knowledge Base)
        # Note: s_data is now a strongly typed SectorBenchmarks object (not a dict)
        s_data = get_sector_data(snapshot.industry, snapshot.sector)

        snapshot.sector_pe_fallback = s_data.pe_ratio
        snapshot.sector_ev_ebitda_fallback = s_data.ev_ebitda
        snapshot.sector_ev_rev_fallback = s_data.ev_revenue

        # 4. Macro Hydration
        return _macro_provider.hydrate_macro_data(snapshot)

    except Exception as e:
        logger.error(f"[YahooProvider] Internal pipeline failed for {ticker}: {e}")
        return None


class YahooFinancialProvider(FinancialDataProvider):
    """
    Orchestrates the data acquisition pipeline.
    """

    def __init__(self, macro_provider: MacroDataProvider):
        self.fetcher = YahooRawFetcher()
        self.mapper = YahooSnapshotMapper()
        self.macro_provider = macro_provider

    def get_company_snapshot(self, ticker: str) -> Optional[CompanySnapshot]:
        """
        Public entry point. Delegates to a cached module function.
        """
        return _get_cached_snapshot(
            ticker,
            self.fetcher,
            self.mapper,
            self.macro_provider
        )