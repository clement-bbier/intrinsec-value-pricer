"""
core/config/constants.py
CONSTANTES CENTRALISÉES — DT-010/011/012/013 Resolution

Version : V1.0
Pattern : Configuration Object (Single Source of Truth)

AVANT (Hardcoding dispersé) :
- app/main.py : _MIN_MC_SIMULATIONS, _MAX_MC_SIMULATIONS, etc.
- yahoo_provider.py : _MAX_PEERS_ANALYSIS = 5
- auditors.py : PENALTY_CRITICAL = 100.0, etc.
- audit_engine.py : MODE_WEIGHTS, seuils gap < 0.05, etc.

APRÈS (Centralisation) :
- Toutes les constantes dans ce fichier
- Imports depuis core.config
- Modification en un seul endroit

Usage :
    from core.config import AuditThresholds, MonteCarloDefaults
    
    if icr < AuditThresholds.ICR_MIN:
        ...
"""

from dataclasses import dataclass
from typing import Dict
from enum import Enum


# ==============================================================================
# 1. MONTE CARLO SIMULATION
# ==============================================================================

@dataclass(frozen=True)
class MonteCarloDefaults:
    """Constantes pour les simulations Monte Carlo."""
    
    # Nombre de simulations
    MIN_SIMULATIONS: int = 100
    MAX_SIMULATIONS: int = 20_000
    DEFAULT_SIMULATIONS: int = 5_000
    STEP_SIMULATIONS: int = 200
    
    # Corrélation par défaut (rho)
    DEFAULT_RHO: float = -0.30
    
    # Seuils de validité
    MIN_VALID_RATIO: float = 0.80  # 80% des simulations doivent être valides
    CLAMPING_THRESHOLD: float = 0.10  # 10% de simulations clampées = warning


# ==============================================================================
# 2. PEERS / MULTIPLES
# ==============================================================================

@dataclass(frozen=True)
class PeerDefaults:
    """Constantes pour l'analyse de comparables."""
    
    # Limites de pairs
    MAX_PEERS_ANALYSIS: int = 5
    MIN_PEERS_REQUIRED: int = 2
    
    # Timeout API (Sprint 6)
    API_TIMEOUT_SECONDS: float = 12.0
    
    # Retry policy
    MAX_RETRY_ATTEMPTS: int = 1


# ==============================================================================
# 3. AUDIT - SEUILS DE VALIDATION
# ==============================================================================

@dataclass(frozen=True)
class AuditThresholds:
    """Seuils pour les tests d'audit."""
    
    # Solvabilité
    ICR_MIN: float = 1.5  # Interest Coverage Ratio minimum
    
    # Beta
    BETA_MIN: float = 0.4
    BETA_MAX: float = 3.0
    
    # Liquidité
    LIQUIDITY_RATIO_MIN: float = 1.0
    
    # SOTP
    SOTP_REVENUE_GAP_WARNING: float = 0.05  # 5%
    SOTP_REVENUE_GAP_ERROR: float = 0.15  # 15%
    SOTP_DISCOUNT_MAX: float = 0.25  # 25%
    
    # Spread WACC vs g
    WACC_G_SPREAD_MIN: float = 0.01  # 1% minimum
    WACC_G_SPREAD_WARNING: float = 0.02  # 2% pour être confortable
    
    # FCF
    FCF_GROWTH_MAX: float = 0.25  # 25% max avant warning
    FCF_MARGIN_MIN: float = 0.05  # 5% minimum
    
    # Réinvestissement
    REINVESTMENT_RATE_MAX: float = 1.0  # 100% max


# ==============================================================================
# 4. AUDIT - PÉNALITÉS
# ==============================================================================

@dataclass(frozen=True)
class AuditPenalties:
    """Pénalités appliquées lors des échecs d'audit."""
    
    CRITICAL: float = 100.0  # Bloquant
    HIGH: float = 35.0
    MEDIUM: float = 15.0
    LOW: float = 5.0
    INFO: float = 0.0  # Informatif uniquement


# ==============================================================================
# 5. AUDIT - PONDÉRATIONS PAR MODE
# ==============================================================================

class AuditWeights:
    """
    Pondérations des piliers d'audit selon le mode d'input.
    
    AUTO : Plus de poids sur la confiance des données (30%)
    MANUAL : Plus de poids sur les hypothèses (50%)
    """
    
    # Mode AUTO (données Yahoo Finance)
    AUTO = {
        "DATA_CONFIDENCE": 0.30,
        "ASSUMPTION_RISK": 0.30,
        "MODEL_RISK": 0.25,
        "METHOD_FIT": 0.15,
    }
    
    # Mode MANUAL (Expert)
    MANUAL = {
        "DATA_CONFIDENCE": 0.10,  # Réduit car l'expert valide
        "ASSUMPTION_RISK": 0.50,  # Augmenté car hypothèses critiques
        "MODEL_RISK": 0.20,
        "METHOD_FIT": 0.20,
    }
    
    @classmethod
    def get_weights(cls, is_manual: bool) -> Dict[str, float]:
        """Retourne les pondérations selon le mode."""
        return cls.MANUAL if is_manual else cls.AUTO


# ==============================================================================
# 6. CONSTANTES SYSTÈME
# ==============================================================================

@dataclass(frozen=True)
class SystemDefaults:
    """Constantes système générales."""
    
    # Horizon de projection par défaut
    DEFAULT_PROJECTION_YEARS: int = 5
    MIN_PROJECTION_YEARS: int = 1
    MAX_PROJECTION_YEARS: int = 15
    
    # Taux par défaut (fallback)
    DEFAULT_RISK_FREE_RATE: float = 0.04  # 4%
    DEFAULT_MARKET_RISK_PREMIUM: float = 0.05  # 5%
    DEFAULT_TAX_RATE: float = 0.25  # 25%
    
    # Croissance terminale par défaut
    DEFAULT_PERPETUAL_GROWTH: float = 0.02  # 2%
    MAX_PERPETUAL_GROWTH: float = 0.04  # 4% (inflation long terme)
    
    # Cache TTL (en secondes)
    CACHE_TTL_SHORT: int = 3600  # 1 heure
    CACHE_TTL_LONG: int = 14400  # 4 heures


# ==============================================================================
# 7. VALIDATION AU CHARGEMENT
# ==============================================================================

def _validate_constants():
    """Valide la cohérence des constantes au chargement du module."""
    # Monte Carlo
    assert MonteCarloDefaults.MIN_SIMULATIONS < MonteCarloDefaults.MAX_SIMULATIONS
    assert MonteCarloDefaults.DEFAULT_SIMULATIONS >= MonteCarloDefaults.MIN_SIMULATIONS
    
    # Audit
    assert AuditThresholds.BETA_MIN < AuditThresholds.BETA_MAX
    assert AuditThresholds.SOTP_REVENUE_GAP_WARNING < AuditThresholds.SOTP_REVENUE_GAP_ERROR
    
    # Pondérations
    assert abs(sum(AuditWeights.AUTO.values()) - 1.0) < 0.001
    assert abs(sum(AuditWeights.MANUAL.values()) - 1.0) < 0.001


# Validation au chargement
_validate_constants()
