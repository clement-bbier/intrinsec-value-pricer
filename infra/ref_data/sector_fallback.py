"""
infra/ref_data/sector_fallback.py

FALLBACK MULTIPLES SECTORIELS — ST-4.1 Resilience Mode

Version : V2.0 — Sprint 4 Enhanced
Rôle : Fournir des multiples de valorisation par défaut si Yahoo échoue.
Pattern : Value Object + Factory
Style : Numpy docstrings

Source des données : Damodaran (NYU Stern) - Moyennes historiques.

ST-4.1 : MODE DÉGRADÉ
=====================
Lorsque Yahoo Finance échoue ou renvoie des données aberrantes,
ce module bascule automatiquement sur les médianes sectorielles
avec traçabilité complète pour l'utilisateur.

Financial Impact:
    Les multiples sectoriels sont des approximations. Ils ne remplacent
    pas une vraie analyse peer-to-peer mais permettent une valorisation
    indicative en cas de panne API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Any

import yaml

from src.domain.models import MultiplesData

logger = logging.getLogger(__name__)

# Chemin vers le fichier de configuration
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "sector_multiples.yaml"

# Cache des multiples sectoriels
_SECTOR_MULTIPLES_CACHE: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SectorFallbackResult:
    """
    Résultat d'une requête de fallback sectoriel avec traçabilité.
    
    Attributes
    ----------
    multiples : MultiplesData
        Les multiples de valorisation.
    is_fallback : bool
        True si les données proviennent du fallback (pas de peers réels).
    sector_key : str
        Clé du secteur utilisé.
    confidence_score : float
        Score de confiance (0-1) des données de fallback.
    source_description : str
        Description textuelle de la source pour l'UI.
    
    Financial Impact
    ----------------
    Le champ is_fallback permet à l'UI d'afficher un bandeau d'avertissement
    pour informer l'utilisateur que les données ne sont pas en temps réel.
    """
    multiples: MultiplesData
    is_fallback: bool
    sector_key: str
    confidence_score: float
    source_description: str


def _load_sector_multiples() -> Dict[str, Any]:
    """Charge les multiples sectoriels depuis le fichier YAML."""
    global _SECTOR_MULTIPLES_CACHE
    
    if _SECTOR_MULTIPLES_CACHE is not None:
        return _SECTOR_MULTIPLES_CACHE
    
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _SECTOR_MULTIPLES_CACHE = yaml.safe_load(f)
            # Exclure les métadonnées du compte
            sector_count = len([k for k in _SECTOR_MULTIPLES_CACHE.keys() if not k.startswith("_")])
            logger.info(f"[SectorFallback] Sectors loaded | count={sector_count}")
            return _SECTOR_MULTIPLES_CACHE
    except Exception as e:
        logger.error(f"[SectorFallback] Loading failed | error={e}")
        return {"default": {
            "pe_ratio": 18.0,
            "ev_ebitda": 12.0,
            "pb_ratio": 3.0,
            "ev_revenue": 2.5,
            "source": "Hardcoded fallback"
        }}


def _normalize_sector_key(sector: str) -> str:
    """
    Normalise le nom du secteur pour correspondre aux clés YAML.
    
    Parameters
    ----------
    sector : str
        Nom du secteur depuis Yahoo Finance.
    
    Returns
    -------
    str
        Clé normalisée pour le fichier YAML.
    """
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
    result = get_sector_fallback_with_metadata(sector)
    return result.multiples


def get_sector_fallback_with_metadata(sector: str) -> SectorFallbackResult:
    """
    Retourne les multiples sectoriels avec métadonnées de traçabilité (ST-4.1).
    
    Parameters
    ----------
    sector : str
        Le nom du secteur (ex: "Technology", "Financial Services").
    
    Returns
    -------
    SectorFallbackResult
        Résultat enrichi avec is_fallback, confidence_score, etc.
    
    Examples
    --------
    >>> result = get_sector_fallback_with_metadata("Technology")
    >>> if result.is_fallback:
    ...     display_degraded_mode_banner()
    >>> multiples = result.multiples
    """
    all_multiples = _load_sector_multiples()
    key = _normalize_sector_key(sector)
    
    data = all_multiples.get(key, all_multiples.get("default", {}))
    source = data.get("source", f"Sector fallback: {sector}")
    
    # Récupérer les métadonnées si disponibles
    metadata = all_multiples.get("_metadata", {})
    confidence = metadata.get("confidence_score", 0.70)
    
    multiples = MultiplesData(
        peers=[],  # Pas de peers réels pour le fallback
        median_pe=data.get("pe_ratio", 0.0) or 0.0,
        median_ev_ebitda=data.get("ev_ebitda", 0.0) or 0.0,
        median_ev_rev=data.get("ev_revenue", 0.0) or 0.0,
        source=source
    )
    
    return SectorFallbackResult(
        multiples=multiples,
        is_fallback=True,
        sector_key=key,
        confidence_score=confidence,
        source_description=f"Mode Dégradé : Données sectorielles moyennes ({source})"
    )


def is_fallback_available() -> bool:
    """Vérifie si le fichier de fallback est disponible."""
    return _CONFIG_PATH.exists()


def get_fallback_metadata() -> Dict[str, Any]:
    """
    Retourne les métadonnées du fichier de fallback.
    
    Returns
    -------
    Dict[str, Any]
        Métadonnées incluant version, source, disclaimer.
    """
    all_multiples = _load_sector_multiples()
    return all_multiples.get("_metadata", {})
