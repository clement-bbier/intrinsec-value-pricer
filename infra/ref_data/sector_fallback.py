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
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Any

import yaml

from src.models import MultiplesData

logger = logging.getLogger(__name__)

# Path to the sectoral configuration repository
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "sector_multiples.yaml"

# Internal cache for performance optimization
_SECTOR_MULTIPLES_CACHE: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SectorFallbackResult:
    """
    Encapsulates a sectoral fallback result with full audit traceability.

    Attributes
    ----------
    multiples : MultiplesData
        The standardized valuation multiples (P/E, EV/EBITDA, etc.).
    is_fallback : bool
        Flag indicating the data comes from the fallback repository (Degraded Mode).
    sector_key : str
        The normalized sector identifier used for lookup.
    confidence_score : float
        A score (0.0 to 1.0) representing the reliability of the fallback data.
    source_description : str
        Human-readable source description for the UI audit trail.
    """
    multiples: MultiplesData
    is_fallback: bool
    sector_key: str
    confidence_score: float
    source_description: str


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


def get_sector_multiples(sector: str) -> MultiplesData:
    """
    Standard accessor for sectoral multiples.
    """
    result = get_sector_fallback_with_metadata(sector)
    return result.multiples


def get_sector_fallback_with_metadata(sector: str) -> SectorFallbackResult:
    """
    Retrieves sectoral multiples enriched with audit metadata for Pillar 3/5.

    Architecture: ST-4.1 Degraded Mode Orchestration.
    """
    all_multiples = _load_sector_multiples()
    key = _normalize_sector_key(sector)

    data = all_multiples.get(key, all_multiples.get("default", {}))
    source = data.get("source", f"Sector fallback: {sector}")

    # Extract metadata for confidence level reporting
    metadata = all_multiples.get("_metadata", {})
    confidence = metadata.get("confidence_score", 0.70)



    multiples = MultiplesData(
        peers=[],  # Fallback mode does not contain individual peer metrics
        median_pe=float(data.get("pe_ratio", 0.0) or 0.0),
        median_ev_ebitda=float(data.get("ev_ebitda", 0.0) or 0.0),
        median_ev_rev=float(data.get("ev_revenue", 0.0) or 0.0),
        source=source
    )

    return SectorFallbackResult(
        multiples=multiples,
        is_fallback=True,
        sector_key=key,
        confidence_score=confidence,
        source_description=f"Mode Dégradé : Multiples sectoriels moyens ({source})"
    )


def is_fallback_available() -> bool:
    """Verifies the availability of the external configuration file."""
    return _CONFIG_PATH.exists()


def get_fallback_metadata() -> Dict[str, Any]:
    """
    Retrieves metadata including versioning and data sources for audit purposes.
    """
    all_multiples = _load_sector_multiples()
    return all_multiples.get("_metadata", {})