"""
infra/ref_data/sector_fallback.py
FALLBACK MULTIPLES SECTORIELS — DT-023 Resolution

Version : V1.0
Rôle : Fournir des multiples de valorisation par défaut si Yahoo échoue.

Source des données : Damodaran (NYU Stern) - Moyennes historiques.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional, Any

import yaml

from core.models import MultiplesData

logger = logging.getLogger(__name__)

# Chemin vers le fichier de configuration
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "sector_multiples.yaml"

# Cache des multiples sectoriels
_SECTOR_MULTIPLES_CACHE: Optional[Dict[str, Any]] = None


def _load_sector_multiples() -> Dict[str, Any]:
    """Charge les multiples sectoriels depuis le fichier YAML."""
    global _SECTOR_MULTIPLES_CACHE
    
    if _SECTOR_MULTIPLES_CACHE is not None:
        return _SECTOR_MULTIPLES_CACHE
    
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _SECTOR_MULTIPLES_CACHE = yaml.safe_load(f)
            logger.info(f"[SectorFallback] Chargé {len(_SECTOR_MULTIPLES_CACHE)} secteurs.")
            return _SECTOR_MULTIPLES_CACHE
    except Exception as e:
        logger.error(f"[SectorFallback] Erreur de chargement : {e}")
        return {"default": {
            "pe_ratio": 18.0,
            "ev_ebitda": 12.0,
            "pb_ratio": 3.0,
            "ev_revenue": 2.5,
            "source": "Hardcoded fallback"
        }}


def _normalize_sector_key(sector: str) -> str:
    """Normalise le nom du secteur pour correspondre aux clés YAML."""
    # Mapping Yahoo Finance -> nos clés
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
    Retourne les multiples de valorisation pour un secteur donné.
    
    Parameters
    ----------
    sector : str
        Le nom du secteur (ex: "Technology", "Financial Services").
    
    Returns
    -------
    MultiplesData
        Les multiples de valorisation du secteur.
    
    Notes
    -----
    Si le secteur n'est pas trouvé, retourne les multiples par défaut.
    """
    multiples = _load_sector_multiples()
    key = _normalize_sector_key(sector)
    
    data = multiples.get(key, multiples.get("default", {}))
    source = data.get("source", f"Sector fallback: {sector}")
    
    # Utilisation de la vraie structure MultiplesData
    return MultiplesData(
        peers=[],  # Pas de peers réels pour le fallback
        median_pe=data.get("pe_ratio", 0.0) or 0.0,
        median_ev_ebitda=data.get("ev_ebitda", 0.0) or 0.0,
        median_ev_rev=data.get("ev_revenue", 0.0) or 0.0,
        source=source
    )


def is_fallback_available() -> bool:
    """Vérifie si le fichier de fallback est disponible."""
    return _CONFIG_PATH.exists()
