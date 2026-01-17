"""
core/config/
Module de configuration centralisée.

Version : V1.0 — DT-010/011/012/013 Resolution
Rôle : Centraliser toutes les constantes et seuils du système.

Contenu :
- constants.py : Constantes globales (Monte Carlo, limites, etc.)
- thresholds.py : Seuils d'audit et de validation

Usage :
    from core.config import AuditThresholds, MonteCarloConfig, PeerConfig
"""

from core.config.constants import (
    # Monte Carlo
    MonteCarloDefaults,
    
    # Peers / Multiples
    PeerDefaults,
    
    # Audit
    AuditThresholds,
    AuditPenalties,
    AuditWeights,
    
    # Général
    SystemDefaults,
)

__all__ = [
    "MonteCarloDefaults",
    "PeerDefaults",
    "AuditThresholds",
    "AuditPenalties",
    "AuditWeights",
    "SystemDefaults",
]
