"""
infra/ref_data/sector_fallback.py

SECTORIAL FALLBACK MULTIPLES — Resiliency Mode (ST-4.1)
=======================================================
Role: Provides curated valuation multiples by sector when live peer data fails.
Pattern: Adapter Pattern (Config -> Provider).
Data Source: src.config.sector_multiples (Single Source of Truth).

Architecture: Fallback Infrastructure Layer.
Style: Numpy docstrings.
"""

from __future__ import annotations

import logging

# Import the new typed configuration (No more YAML reading)
from src.config.sector_multiples import SECTORS, SectorBenchmarks

logger = logging.getLogger(__name__)


def _normalize_sector_key(sector: str) -> str:
    """
    Maps Yahoo Finance sector nomenclature to internal canonical keys.
    
    Implements fuzzy matching with synonym support for robust sector resolution.
    Handles all 11 official Yahoo Finance sectors plus common variations.
    
    Parameters
    ----------
    sector : str
        Raw sector name from Yahoo Finance API.
    
    Returns
    -------
    str
        Normalized sector key matching configuration.
    
    Notes
    -----
    Yahoo Finance Standard Sectors (2026):
    - Technology
    - Financial Services
    - Healthcare
    - Consumer Cyclical
    - Consumer Defensive
    - Industrials
    - Energy
    - Basic Materials
    - Real Estate
    - Utilities
    - Communication Services
    """
    # Comprehensive mapping with synonym support
    mapping = {
        # Technology
        "technology": "technology",
        "tech": "technology",
        
        # Financial Services
        "financial services": "financial_services",
        "financials": "financial_services",
        "finance": "financial_services",
        
        # Healthcare
        "healthcare": "healthcare",
        "health care": "healthcare",
        "medical": "healthcare",
        
        # Consumer Cyclical
        "consumer cyclical": "consumer_cyclical",
        "consumer discretionary": "consumer_cyclical",  # Synonym
        "cyclical": "consumer_cyclical",
        
        # Consumer Defensive
        "consumer defensive": "consumer_defensive",
        "consumer staples": "consumer_defensive",  # Synonym
        "defensive": "consumer_defensive",
        
        # Industrials
        "industrials": "industrials",
        "industrial": "industrials",
        
        # Energy
        "energy": "energy",
        
        # Basic Materials
        "basic materials": "basic_materials",
        "materials": "basic_materials",
        "chemicals": "basic_materials",
        
        # Real Estate
        "real estate": "real_estate",
        "realty": "real_estate",
        "reit": "real_estate",
        
        # Utilities
        "utilities": "utilities",
        "utility": "utilities",
        
        # Communication Services
        "communication services": "communication_services",
        "communications": "communication_services",
        "telecom": "communication_services",
    }

    # Fuzzy matching: case-insensitive, strip whitespace
    normalized = sector.lower().strip()
    return mapping.get(normalized, "default")


def _slugify(text: str | None) -> str:
    """
    Normalizes raw API strings into canonical configuration keys.
    """
    if not text or not isinstance(text, str):
        return ""

    return (
        text.lower()
        .replace("—", "_")
        .replace("-", "_")
        .replace(" ", "_")
        .replace("__", "_")
        .strip("_")
    )


def get_sector_data(industry: str | None, sector: str | None) -> SectorBenchmarks:
    """
    Retrieves valuation benchmarks using a hierarchical fallback strategy.

    The logic enforces a 'Granular-to-Broad' search order:
    1. Specific Industry match (e.g., 'semiconductors').
    2. Macro Sector match (e.g., 'technology').
    3. Global 'default' fallback if no matches are found.

    Parameters
    ----------
    industry : str, optional
        The specific industry name provided by the data source.
    sector : str, optional
        The broad macro-sector name provided by the data source.

    Returns
    -------
    SectorBenchmarks
        The typed configuration object containing PE, EV/EBITDA, etc.
    """
    # 1. Primary Attempt: Granular Industry
    industry_key = _slugify(industry)
    if industry_key and industry_key in SECTORS:
        return SECTORS[industry_key]

    # 2. Secondary Attempt: Broad Macro Sector
    sector_key = _slugify(sector)
    if sector_key not in SECTORS:
        sector_key = _normalize_sector_key(sector or "")

    if sector_key and sector_key in SECTORS:
        logger.debug(f"[SectorFallback] Industry '{industry}' not found. Falling back to sector '{sector_key}'.")
        return SECTORS[sector_key]

    # 3. Last Resort: Global Market Default
    logger.warning(f"[SectorFallback] No match for '{industry}/{sector}'. Using global default.")
    return SECTORS["default"]
