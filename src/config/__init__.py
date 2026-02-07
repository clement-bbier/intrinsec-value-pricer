"""
src/config/__init__.py

CONFIGURATION MODULE EXPORTS
============================
Exposes centralized constants, system defaults, and validation thresholds.
"""

from src.config.constants import (
    MonteCarloDefaults,
    SensitivityDefaults,
    ScenarioDefaults,
    BacktestDefaults,
    PeerDefaults,
    SOTPDefaults,
    ValidationThresholds,
    MacroDefaults,
    ModelDefaults,
    ValuationEngineDefaults,
    UIWidgetDefaults,
    SystemDefaults,
)

from src.config.settings import (
    SIMULATION_CONFIG,
    VALIDATION_CONFIG,
    SYSTEM_CONFIG,
    VALUATION_CONFIG,
    get_config,
)

from src.config.sector_multiples import (
    SECTORS,
    SECTOR_METADATA,
)

__all__ = [
    # Constants & Defaults
    "MonteCarloDefaults",
    "SensitivityDefaults",
    "ScenarioDefaults",
    "BacktestDefaults",
    "PeerDefaults",
    "SOTPDefaults",
    "ValidationThresholds",
    "MacroDefaults",
    "ModelDefaults",
    "ValuationEngineDefaults",
    "UIWidgetDefaults",
    "SystemDefaults",

    # Config Objects
    "SIMULATION_CONFIG",
    "VALIDATION_CONFIG",
    "SYSTEM_CONFIG",
    "VALUATION_CONFIG",
    "get_config",

    # Sector multiples
    "SECTORS",
    "SECTOR_METADATA"
]