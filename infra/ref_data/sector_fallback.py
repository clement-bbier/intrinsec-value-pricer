"""
infra/ref_data/sector_fallback.py

SECTORIAL FALLBACK MULTIPLES — Resiliency Mode (ST-4.1)
======================================================
Role: Provides curated valuation multiples by sector when live peer data fails.
Pattern: Value Object + Provider Factory.
Data Source: Damodaran (NYU Stern) & Institutional Historical Averages.

Architecture: Fallback Infrastructure Layer.
Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional, Any

import yaml

logger = logging.getLogger(__name__)

# Path to the sectoral configuration repository
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "sector_multiples.yaml"

# Internal cache for performance optimization
_SECTOR_MULTIPLES_CACHE: Optional[Dict[str, Any]] = None

def _load_sector_multiples() -> Dict[str, Any]:
    """
    Loads the sectoral multiples from the YAML configuration file.
    Implements a fail-safe mechanism with hardcoded baseline constants.
    """
    global _SECTOR_MULTIPLES_CACHE

    if _SECTOR_MULTIPLES_CACHE is not None:
        return _SECTOR_MULTIPLES_CACHE

    try:
        if not _CONFIG_PATH.exists():
            raise FileNotFoundError(f"Config file missing at {_CONFIG_PATH}")

        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _SECTOR_MULTIPLES_CACHE = yaml.safe_load(f)
            # Exclude metadata keys for logging accuracy
            sector_count = len([k for k in _SECTOR_MULTIPLES_CACHE.keys() if not k.startswith("_")])
            logger.info(f"[SectorFallback] Repository loaded | count={sector_count}")
            return _SECTOR_MULTIPLES_CACHE

    except Exception as e:
        logger.error(f"[SectorFallback] Loading failed, using critical defaults | error={e}")
        # Global market averages as a last-resort safety net
        return {"default": {
            "pe_ratio": 18.0,
            "ev_ebitda": 12.0,
            "pb_ratio": 3.0,
            "ev_revenue": 2.5,
            "source": "Critical hardcoded fallback"
        }}


def _normalize_sector_key(sector: str) -> str:
    """
    Maps Yahoo Finance sector nomenclature to internal canonical keys.
    """
    mapping = {
        "technology": "technology",
        "financial services": "financial_services",
        "healthcare": "healthcare",
        "consumer cyclical": "consumer_cyclical",
        "consumer defensive": "consumer_defensive",
        "industrials": "industrials",
        "energy": "energy",
        "basic materials": "basic_materials",
        "real estate": "real_estate",
        "utilities": "utilities",
        "communication services": "communication_services",
    }

    normalized = sector.lower().strip()
    return mapping.get(normalized, "default")


def _slugify(text: Optional[str]) -> str:
    """
    Normalizes raw API strings into canonical configuration keys.

    Converts characters like em-dashes, spaces, and hyphens into underscores
    to match the YAML structure (e.g., 'Software—Infrastructure' -> 'software_infrastructure').

    Parameters
    ----------
    text : str, optional
        The raw string to be normalized.

    Returns
    -------
    str
        The normalized, lowercase, snake_case string. Returns empty string if input is None.
    """
    if not text or not isinstance(text, str):
        return ""

    # Handle common separators found in financial APIs
    return (
        text.lower()
        .replace("—", "_")  # Long dash
        .replace("-", "_")  # Hyphen
        .replace(" ", "_")  # Space
        .replace("__", "_")  # Clean up double underscores
        .strip("_")
    )


def get_sector_data(industry: Optional[str], sector: Optional[str]) -> Dict[str, Any]:
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
    Dict[str, Any]
        A dictionary containing valuation multiples (pe_ratio, ev_ebitda, etc.)
        and the source metadata.
    """
    all_data = _load_sector_multiples()

    # 1. Primary Attempt: Granular Industry
    industry_key = _slugify(industry)
    if industry_key and industry_key in all_data:
        return all_data[industry_key]

    # 2. Secondary Attempt: Broad Macro Sector
    sector_key = _slugify(sector)
    if sector_key and sector_key in all_data:
        logger.debug(f"[SectorFallback] Industry '{industry}' not found. Falling back to sector '{sector}'.")
        return all_data[sector_key]

    # 3. Last Resort: Global Market Default
    logger.warning(f"[SectorFallback] No match for '{industry}/{sector}'. Using global default.")
    return all_data.get("default", {})