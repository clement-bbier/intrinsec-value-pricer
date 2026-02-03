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

class ValuationMethodology(str, Enum):
    """Supported valuation methodologies."""
    FCFF_STANDARD = "Free Cash Flow to Firm"
    FCFF_NORMALIZED = "Normalized Free Cash Flow to Firm"
    FCFF_GROWTH = "Top-Down Free Cash Flow to Firm"
    FCFE = "Free Cash Flow to Equity"
    DDM = "Dividend Discount Model"
    RIM = "Residual Income Model"
    GRAHAM = "Graham Intrinsic Value"

    @property
    def is_direct_equity(self) -> bool:
        """True if the model values equity directly (DDM, RIM, FCFE)."""
        return self in [ValuationMethodology.DDM, ValuationMethodology.RIM, ValuationMethodology.FCFE]

class TerminalValueMethod(str, Enum):
    """Calculation logic for the residual value beyond the forecast horizon."""
    GORDON_GROWTH = "GORDON_GROWTH"
    EXIT_MULTIPLE = "EXIT_MULTIPLE"

class ParametersSource(str, Enum):
    """
    Provenance of a specific parameter value.
    Used for the 'Glass Box' resolution dance.
    """
    MANUAL = "USER_INPUT"        # Expert override
    AUTO = "PROVIDER_INPUT"      # Market data provider (Yahoo)
    SYSTEM = "SYSTEM_INPUT"      # Internal fallback or sector benchmark
    EMPTY = None

class SOTPMethod(str, Enum):
    """Valuation techniques for segment-based analysis."""
    DCF = "DCF"
    MULTIPLES = "MULTIPLES"
    ASSET_VALUE = "ASSET_VALUE"

class DiagnosticLevel(str, Enum):
    """Classification levels for trace findings."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"