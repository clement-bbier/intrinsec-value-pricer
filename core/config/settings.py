"""
core/config/settings.py
PARAMÈTRES DE CONFIGURATION CENTRALISÉS — Sprint 4

Version : V1.0 — ST 4.1 Resolution
Pattern : Configuration Object (Single Source of Truth)

AVANT : Constantes éparpillées dans le code
APRÈS : Centralisation complète dans ce fichier

Usage :
    from core.config.settings import SIMULATION_CONFIG, AUDIT_CONFIG
"""

from dataclasses import dataclass
from typing import Dict, Any


# ==============================================================================
# 1. CONFIGURATION SIMULATION MONTE CARLO
# ==============================================================================

@dataclass(frozen=True)
class MonteCarloSimulationConfig:
    """Configuration complète des simulations Monte Carlo."""

    # Import depuis constants.py pour éviter la duplication
    from core.config.constants import MonteCarloDefaults

    # Paramètres de base (migration depuis constants.py)
    default_simulations: int = MonteCarloDefaults.DEFAULT_SIMULATIONS
    min_simulations: int = MonteCarloDefaults.MIN_SIMULATIONS
    max_simulations: int = MonteCarloDefaults.MAX_SIMULATIONS

    # Paramètres de corrélation
    default_rho: float = -0.30
    rho_bounds: tuple[float, float] = (-1.0, 1.0)

    # Paramètres de volatilité par défaut
    default_volatility_beta: float = 0.10
    default_volatility_growth: float = 0.02
    default_volatility_terminal: float = 0.01

    # Seuils de validité
    min_valid_ratio: float = 0.80
    max_clamping_ratio: float = 0.10

    # Paramètres de sécurité
    growth_safety_margin: float = 0.015
    sensitivity_simulations: int = 1000
    max_iv_filter: float = 100_000.0
    default_wacc_fallback: float = 0.08

    # Timeout
    timeout_seconds: int = 30


# ==============================================================================
# 2. CONFIGURATION AUDIT ET VALIDATION
# ==============================================================================

@dataclass(frozen=True)
class AuditValidationConfig:
    """Configuration des seuils d'audit et validation."""

    # Seuils financiers
    icr_minimum: float = 1.5
    beta_minimum: float = 0.4
    beta_maximum: float = 3.0
    liquidity_ratio_minimum: float = 1.0

    # Seuils SOTP
    sotp_revenue_gap_warning: float = 0.05
    sotp_revenue_gap_error: float = 0.15
    sotp_discount_maximum: float = 0.25

    # Seuils de convergence
    wacc_growth_spread_minimum: float = 0.01
    wacc_growth_spread_warning: float = 0.02

    # Seuils FCF
    fcf_growth_maximum: float = 0.25
    fcf_margin_minimum: float = 0.05

    # Seuils réinvestissement
    reinvestment_rate_maximum: float = 1.0


# ==============================================================================
# 3. CONFIGURATION SYSTÈME ET PERFORMANCE
# ==============================================================================

@dataclass(frozen=True)
class SystemPerformanceConfig:
    """Configuration système et paramètres de performance."""

    # Cache
    cache_ttl_short: int = 3600   # 1 heure
    cache_ttl_medium: int = 14400 # 4 heures
    cache_ttl_long: int = 86400   # 24 heures

    # API Timeouts
    yahoo_api_timeout: float = 12.0
    retry_attempts: int = 3
    retry_delay_base: float = 0.5

    # UI
    max_display_rows: int = 100
    chart_height: int = 400

    # Logs
    max_log_file_size: int = 10_000_000  # 10MB
    max_log_backup_files: int = 5


# ==============================================================================
# 4. CONFIGURATION VALORISATION
# ==============================================================================

@dataclass(frozen=True)
class ValuationModelConfig:
    """Configuration des modèles de valorisation."""

    # Horizon par défaut
    default_projection_years: int = 5
    minimum_projection_years: int = 1
    maximum_projection_years: int = 15

    # Taux par défaut (fallback)
    default_risk_free_rate: float = 0.04
    default_market_risk_premium: float = 0.05
    default_tax_rate: float = 0.25

    # Croissance terminale
    default_terminal_growth: float = 0.02
    maximum_terminal_growth: float = 0.04

    # Limites de convergence
    maximum_iterations: int = 1000
    convergence_tolerance: float = 1e-6


# ==============================================================================
# INSTANCES GLOBALES DE CONFIGURATION
# ==============================================================================

# Configurations principales
SIMULATION_CONFIG = MonteCarloSimulationConfig()
AUDIT_CONFIG = AuditValidationConfig()
SYSTEM_CONFIG = SystemPerformanceConfig()
VALUATION_CONFIG = ValuationModelConfig()

# Dictionnaire pour accès programmatique
CONFIG_REGISTRY: Dict[str, Any] = {
    "simulation": SIMULATION_CONFIG,
    "audit": AUDIT_CONFIG,
    "system": SYSTEM_CONFIG,
    "valuation": VALUATION_CONFIG,
}


def get_config(section: str) -> Any:
    """
    Récupère une section de configuration.

    Parameters
    ----------
    section : str
        Nom de la section ('simulation', 'audit', 'system', 'valuation')

    Returns
    -------
    Configuration object

    Raises
    ------
    KeyError
        Si la section n'existe pas
    """
    if section not in CONFIG_REGISTRY:
        available = ", ".join(CONFIG_REGISTRY.keys())
        raise KeyError(f"Section '{section}' inconnue. Disponible: {available}")
    return CONFIG_REGISTRY[section]


# ==============================================================================
# VALIDATION AU CHARGEMENT
# ==============================================================================

def _validate_configurations():
    """Valide la cohérence des configurations au chargement."""

    # Validation Monte Carlo
    assert SIMULATION_CONFIG.min_simulations < SIMULATION_CONFIG.default_simulations
    assert SIMULATION_CONFIG.default_simulations <= SIMULATION_CONFIG.max_simulations

    # Validation Audit
    assert AUDIT_CONFIG.beta_minimum < AUDIT_CONFIG.beta_maximum
    assert AUDIT_CONFIG.sotp_revenue_gap_warning < AUDIT_CONFIG.sotp_revenue_gap_error

    # Validation Valorisation
    assert VALUATION_CONFIG.minimum_projection_years <= VALUATION_CONFIG.default_projection_years
    assert VALUATION_CONFIG.default_projection_years <= VALUATION_CONFIG.maximum_projection_years


# Validation au chargement du module
_validate_configurations()
