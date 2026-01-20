"""
src/config/constants.py

CONSTANTES CENTRALISÉES — DT-010/011/012/013 Resolution

Version : V1.1 — ST-1.2 Type-Safe Resolution
Pattern : Configuration Object (Single Source of Truth)
Style : Numpy Style docstrings

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
    from src.config import AuditThresholds, MonteCarloDefaults

RISQUES FINANCIERS:
- Ces constantes pilotent les seuils d'audit et les défauts de calcul
- Une modification incorrecte peut impacter toutes les valorisations
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, List
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
# 5. MACRO ÉCONOMIQUE ET SPREADS
# ==============================================================================

@dataclass(frozen=True)
class MacroDefaults:
    """Constantes pour l'analyse macro-économique."""

    # Spread AAA par défaut
    DEFAULT_AAA_SPREAD: float = 0.0070  # 0.70%

    # Taux sans risque par défaut (fallback ultime)
    FALLBACK_RISK_FREE_RATE_USD: float = 0.04  # 4%
    FALLBACK_RISK_FREE_RATE_EUR: float = 0.027  # 2.7%

    # Inflation par défaut
    DEFAULT_INFLATION_RATE: float = 0.02  # 2%

    # MRP par défaut
    DEFAULT_MARKET_RISK_PREMIUM: float = 0.05  # 5%

    # Seuil Large Cap pour sélection des spreads (ST-2.3)
    LARGE_CAP_THRESHOLD: float = 5_000_000_000  # 5 Milliards $


# ==============================================================================
# 6. EXTRACTION DE DONNÉES ET API
# ==============================================================================

@dataclass(frozen=True)
class DataExtractionDefaults:
    """Constantes pour l'extraction et la normalisation des données."""

    # Retry policy
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_BASE: float = 0.5  # secondes
    RETRY_BACKOFF_MULTIPLIER: int = 2

    # Yahoo Raw Fetcher
    YAHOO_RAW_MAX_RETRIES: int = 2

    # CAGR calculation
    HISTORICAL_CAGR_YEARS: int = 3

    # Price format conversion
    PRICE_FORMAT_MULTIPLIER: float = 100.0

    # Normalisation des données financières
    NORMALIZATION_LAST_QUARTERS: int = 4


# ==============================================================================
# 7. MOTEURS DE VALORISATION
# ==============================================================================

@dataclass(frozen=True)
class ValuationEngineDefaults:
    """Constantes pour les moteurs de valorisation."""

    # Convergence
    MAX_ITERATIONS: int = 50
    CONVERGENCE_TOLERANCE: float = 1e-6

    # Stress testing Monte Carlo
    STRESS_GROWTH_RATE: float = 0.0  # Croissance nulle en stress
    STRESS_PERPETUAL_GROWTH: float = 0.01  # 1% perpétuelle en stress
    STRESS_BETA: float = 1.50  # Risque systémique maximum

    # RIM (Residual Income Model) - ST-2.3
    RIM_DEFAULT_OMEGA: float = 0.60  # Facteur de persistance par défaut
    RIM_MAX_PAYOUT_RATIO: float = 0.95  # Plafond du payout ratio

    # Spreads de rating corporate (SPREADS_LARGE_CAP)
    SPREAD_AAA: float = 0.0045
    SPREAD_AA: float = 0.0060
    SPREAD_A: float = 0.0077
    SPREAD_BBB: float = 0.0085
    SPREAD_BB: float = 0.0120
    SPREAD_B: float = 0.0183
    SPREAD_CCC: float = 0.0728

    # Spreads small/mid cap (SPREADS_SMALL_MID_CAP)
    SPREAD_AAA_SMALL: float = 0.0045
    SPREAD_AA_SMALL: float = 0.0060
    SPREAD_A_SMALL: float = 0.0077
    SPREAD_BBB_SMALL: float = 0.0085
    SPREAD_BB_SMALL: float = 0.0120
    SPREAD_B_SMALL: float = 0.0183
    SPREAD_CCC_SMALL: float = 0.0728

    # Tables de spreads complètes (tuples (rating_threshold, spread))
    SPREADS_LARGE_CAP = [
        (8.5, SPREAD_AAA), (6.5, SPREAD_AA), (5.5, SPREAD_A), (4.25, SPREAD_BBB),
        (3.0, 0.0095), (2.5, SPREAD_BB), (2.25, 0.0155), (2.0, SPREAD_B),
        (1.75, 0.0261), (1.5, 0.0300), (1.25, 0.0442), (0.8, SPREAD_CCC),
        (0.65, 0.1010), (0.2, 0.1550), (-999, 0.1900)
    ]

    SPREADS_SMALL_MID_CAP = [
        (12.5, SPREAD_AAA_SMALL), (9.5, SPREAD_AA_SMALL), (7.5, SPREAD_A_SMALL), (6.0, SPREAD_BBB_SMALL),
        (4.5, 0.0095), (4.0, SPREAD_BB_SMALL), (3.5, 0.0155), (3.0, SPREAD_B),
        (2.5, 0.0261), (2.0, 0.0300), (1.5, 0.0442), (1.25, SPREAD_CCC_SMALL),
        (0.8, 0.1010), (0.5, 0.1550), (-999, 0.1900)
    ]


# ==============================================================================
# 8. MODÈLES DE DONNÉES PAR DÉFAUT
# ==============================================================================

@dataclass(frozen=True)
class ModelDefaults:
    """Valeurs par défaut pour les modèles de données."""

    # CompanyFinancials
    DEFAULT_BETA: float = 1.0
    DEFAULT_TOTAL_DEBT: float = 0.0
    DEFAULT_CASH_EQUIVALENTS: float = 0.0
    DEFAULT_MINORITY_INTERESTS: float = 0.0
    DEFAULT_PENSION_PROVISIONS: float = 0.0
    DEFAULT_BOOK_VALUE: float = 0.0
    DEFAULT_INTEREST_EXPENSE: float = 0.0

    # Audit metrics
    DEFAULT_MEAN_ABSOLUTE_ERROR: float = 0.0
    DEFAULT_ALPHA_VS_MARKET: float = 0.0
    DEFAULT_MODEL_ACCURACY_SCORE: float = 0.0

    # Multiples data
    DEFAULT_MEDIAN_PE: float = 0.0
    DEFAULT_MEDIAN_EV_EBITDA: float = 0.0
    DEFAULT_MEDIAN_EV_EBIT: float = 0.0
    DEFAULT_MEDIAN_PB: float = 0.0
    DEFAULT_MEDIAN_EV_REV: float = 0.0
    DEFAULT_IMPLIED_VALUE_EV_EBITDA: float = 0.0
    DEFAULT_IMPLIED_VALUE_PE: float = 0.0
    DEFAULT_PE_BASED_PRICE: float = 0.0
    DEFAULT_EBITDA_BASED_PRICE: float = 0.0
    DEFAULT_REV_BASED_PRICE: float = 0.0

    # Scenarios
    DEFAULT_PROBABILITY: float = 0.333
    DEFAULT_EXPECTED_VALUE: float = 0.0
    DEFAULT_MAX_UPSIDE: float = 0.0
    DEFAULT_MAX_DOWNSIDE: float = 0.0

    # SOTP
    DEFAULT_CONGLOMERATE_DISCOUNT: float = 0.0

    # Glass box
    DEFAULT_STEP_ID: int = 0
    DEFAULT_RESULT_VALUE: float = 0.0
    DEFAULT_INDICATOR_VALUE: float = 0.0

    # Projection
    DEFAULT_PROJECTION_YEARS: int = 5
    DEFAULT_HIGH_GROWTH_YEARS: int = 0


# ==============================================================================
# 9. WIDGETS UI ET PARAMÈTRES D'INTERFACE
# ==============================================================================

@dataclass(frozen=True)
class UIWidgetDefaults:
    """Constantes pour les widgets d'interface utilisateur."""

    # Projection years
    DEFAULT_PROJECTION_YEARS: int = 5
    MIN_PROJECTION_YEARS: int = 3
    MAX_PROJECTION_YEARS: int = 15

    # Growth rates
    MIN_GROWTH_RATE: float = -0.50
    MAX_GROWTH_RATE: float = 1.0

    # Terminal growth
    MAX_TERMINAL_GROWTH: float = 0.05

    # Discount rates
    MAX_DISCOUNT_RATE: float = 0.20

    # Beta
    MAX_BETA: float = 5.0

    # Tax rate
    MAX_TAX_RATE: float = 0.60

    # Cost of debt
    MAX_COST_OF_DEBT: float = 0.20

    # Exit multiple
    MAX_EXIT_MULTIPLE: float = 100.0

    # Manual price
    MAX_MANUAL_PRICE: float = 10000.0

    # Base flow volatility
    DEFAULT_BASE_FLOW_VOLATILITY: float = 0.05


# ==============================================================================
# 10. CROISSANCE ET CALCULS FINANCIERS
# ==============================================================================

@dataclass(frozen=True)
class GrowthCalculationDefaults:
    """Constantes pour les calculs de croissance."""

    # Margins
    DEFAULT_MARGIN: float = 0.0
    DEFAULT_FCF_MARGIN_TARGET: float = 0.20  # Marge FCF cible par défaut

    # Years
    DEFAULT_HIGH_GROWTH_YEARS: int = 0

    # High growth period
    DEFAULT_HIGH_GROWTH_PERIOD: Optional[int] = 0

    # Sustainable growth rate calculation
    MIN_RETENTION_RATE: float = 0.0
    MAX_RETENTION_RATE: float = 1.0


# ==============================================================================
# 11. CONSTANTES TECHNIQUES ET VALIDATION
# ==============================================================================

@dataclass(frozen=True)
class TechnicalDefaults:
    """Constantes techniques pour calculs et validations."""

    # Tolérances numériques
    NUMERICAL_TOLERANCE: float = 0.001  # Tolérance pour comparaisons flottantes
    PROBABILITY_TOLERANCE: float = 0.001  # Tolérance pour validation des probabilités

    # Seuils de validation
    BACKTEST_ERROR_THRESHOLD: float = 0.20  # 20% seuil d'erreur acceptable
    VALUATION_CONVERGENCE_THRESHOLD: float = 0.5  # 0.5 unité monétaire pour convergence

    # Reverse DCF - Bornes de recherche (ST-2.3)
    REVERSE_DCF_LOW_BOUND: float = -0.20  # -20% croissance minimale
    REVERSE_DCF_HIGH_BOUND: float = 0.50  # +50% croissance maximale

    # Ratios d'audit
    BORROWING_RATIO_MAX: float = 0.5  # Ratio emprunt/NI maximum
    GROWTH_AUDIT_THRESHOLD: float = 0.20  # Seuil d'audit pour croissance

    # Conversions
    PERCENTAGE_MULTIPLIER: float = 100.0  # Pour conversions % ↔ décimales

    # Yield AAA par défaut (Graham)
    DEFAULT_AAA_YIELD: float = 0.044  # 4.4% yield AAA par défaut


# ==============================================================================
# 12. CONFIGURATION DE RAPPORT
# ==============================================================================

@dataclass(frozen=True)
class ReportingConfig:
    """Configuration pour la génération de rapports PDF."""

    # Dimensions A4 (en points pour PDF)
    PAGE_WIDTH_A4: float = 595.28  # Largeur A4 en points (210mm)
    PAGE_HEIGHT_A4: float = 841.89  # Hauteur A4 en points (297mm)

    # Marges par défaut (en points)
    MARGIN_LEFT: float = 50.0
    MARGIN_RIGHT: float = 50.0
    MARGIN_TOP: float = 50.0
    MARGIN_BOTTOM: float = 50.0

    # Largeur et hauteur utilisables (après marges)
    @property
    def usable_width(self) -> float:
        """Largeur utilisable après marges."""
        return self.PAGE_WIDTH_A4 - self.MARGIN_LEFT - self.MARGIN_RIGHT

    @property
    def usable_height(self) -> float:
        """Hauteur utilisable après marges."""
        return self.PAGE_HEIGHT_A4 - self.MARGIN_TOP - self.MARGIN_BOTTOM


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

    # UI Widgets
    assert UIWidgetDefaults.MIN_PROJECTION_YEARS <= UIWidgetDefaults.DEFAULT_PROJECTION_YEARS
    assert UIWidgetDefaults.DEFAULT_PROJECTION_YEARS <= UIWidgetDefaults.MAX_PROJECTION_YEARS

    # Growth
    assert GrowthCalculationDefaults.MIN_RETENTION_RATE <= GrowthCalculationDefaults.MAX_RETENTION_RATE

    # Valuation Engine
    assert ValuationEngineDefaults.MAX_ITERATIONS > 0
    assert ValuationEngineDefaults.CONVERGENCE_TOLERANCE > 0


# Validation au chargement
_validate_constants()


# ==============================================================================
# EXPORTS POUR FACILITER LES IMPORTS
# ==============================================================================

__all__ = [
    "MonteCarloDefaults",
    "PeerDefaults",
    "AuditThresholds",
    "AuditPenalties",
    "AuditWeights",
    "SystemDefaults",
    "MacroDefaults",
    "DataExtractionDefaults",
    "ValuationEngineDefaults",
    "ModelDefaults",
    "UIWidgetDefaults",
    "GrowthCalculationDefaults",
    "TechnicalDefaults",
    "ReportingConfig",
]
