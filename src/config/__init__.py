"""
core/config/
Module de configuration centralisée.

Résolution DT-010/011/012/013
Rôle : Centraliser toutes les constantes et seuils du système.

Contenu :
- constants.py : Constantes globales (Monte Carlo, limites, etc.)
- thresholds.py : Seuils d'audit et de validation

Usage :
    from src.config import AuditThresholds, MonteCarloConfig, PeerConfig
"""

from src.config.constants import (
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
    TechnicalDefaults,
)

__all__ = [
    "MonteCarloDefaults",
    "PeerDefaults",
    "AuditThresholds",
    "AuditPenalties",
    "AuditWeights",
    "SystemDefaults",
    "TechnicalDefaults",
]
