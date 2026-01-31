"""
src/models/enums.py

DOMAIN ENUMERATIONS AND TYPE ALIASES
====================================
Role: Centralized type definitions and constants for the valuation domain.
Scope: Ensures consistent naming conventions across the engine and UI handlers.
Architecture: Static type aliases and String-based Enums.

Style: Numpy docstrings.
"""

from __future__ import annotations

from enum import Enum
from typing import TypeAlias


# ==============================================================================
# 1. FINANCIAL TYPE ALIASES (TYPE-SAFE)
# ==============================================================================

Rate: TypeAlias = float
"""Financial rate (WACC, growth, discount). Example: 0.08 for 8%."""

Currency: TypeAlias = float
"""Monetary amount in base currency. Example: 1_500_000.00 for 1.5M."""

Percentage: TypeAlias = float
"""Normalized percentage between 0.0 and 1.0. Example: 0.15 for 15%."""

Multiple: TypeAlias = float
"""Valuation multiple (P/E, EV/EBITDA). Example: 15.5 for a 15.5x P/E ratio."""

ShareCount: TypeAlias = int
"""Number of shares outstanding. Example: 1_000_000_000."""

Years: TypeAlias = int
"""Duration in years for projection horizons. Example: 5."""

Ratio: TypeAlias = float
"""Generic financial ratio. Example: 0.35 for a 35% Debt-to-Equity ratio."""


# ==============================================================================
# 2. VALUATION & STRATEGY ENUMS
# ==============================================================================

class ValuationMode(str, Enum):
    """
    Supported valuation methodologies.
    Defines the specific analytical engine to be invoked by the orchestrator.
    """
    FCFF_STANDARD = "Free Cash Flow to Firm"
    FCFF_NORMALIZED = "Normalized Free Cash Flow to Firm"
    FCFF_GROWTH = "Top-Down Free Cash Flow to Firm"
    FCFE = "Free Cash Flow to Equity"
    DDM = "Dividend Discount Model"
    RIM = "Residual Income Model"
    GRAHAM = "Graham Intrinsic Value"

class TerminalValueMethod(str, Enum):
    """
    Calculation logic for the residual value beyond the forecast horizon.
    """
    GORDON_GROWTH = "GORDON_GROWTH"
    EXIT_MULTIPLE = "EXIT_MULTIPLE"

class InputSource(str, Enum):
    """
    Source of the calculation parameters.
    Used to drive audit weighting and data lineage tracking.
    """
    AUTO = "AUTO"      # Automated acquisition via providers
    MANUAL = "MANUAL"  # Expert overrides provided by the user
    SYSTEM = "SYSTEM"  # Internal fallback or calculated constants





class AuditSeverity(str, Enum):
    """
    Classification levels for audit check findings.
    """
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class SOTPMethod(str, Enum):
    """
    Valuation techniques for segment-based analysis (Sum-of-the-Parts).
    """
    DCF = "DCF"
    MULTIPLES = "MULTIPLES"
    ASSET_VALUE = "ASSET_VALUE"


class AuditPillar(str, Enum):
    """
    Core dimensions evaluated during the valuation reliability audit.
    """
    DATA_CONFIDENCE = "Data Confidence"
    ASSUMPTION_RISK = "Assumption Risk"
    MODEL_RISK = "Model Risk"
    METHOD_FIT = "Method Fit"