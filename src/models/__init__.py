"""
src/models/
Data layer orchestrator for the valuation engine.

Structure:
- enums.py      : Domain enumerations (Methodology, Sources, etc.)
- company.py    : Static company identity (Pillar 1)
- parameters/   : Input containers (The "Ghost" Objects)
- results/      : Output containers (The "Mirror" Objects)
- valuation.py  : High-level Request/Result envelopes
"""

# 1. Base Enumerations (Enums only)
from .enums import (
    ValuationMethodology,
    ParametersSource,
    TerminalValueMethod,
)

# 2. Domain Identity (Pillar 1)
from .company import Company

# 3. Parameter Containers (Pillar 2, 3, 4 Inputs)
# We export the main Parameters bundle and key sub-structures
from .parameters.base_parameter import Parameters
from .parameters.common import (
    CommonParameters,
    FinancialRatesParameters,
    CapitalStructureParameters
)
from .parameters.options import (
    ExtensionBundleParameters,
    MCParameters,
    ScenariosParameters,
    BacktestParameters,
    PeersParameters,
    SOTPParameters
)

# 4. Results Containers (The calculated Outputs)
from .results.base_result import Results
from .results.common import CommonResults
from .results.options import ExtensionBundleResults

# 5. High-Level Envelopes
# ValuationRequest remains the entry point for the Resolvers
from .valuation import (
    ValuationRequest
)

# 6. Glass Box & Audit (Traceability)
from .glass_box import CalculationStep

__all__ = [
    # Enums
    "ValuationMethodology",
    "ParametersSource",
    "TerminalValueMethod",

    # Pillars & Root Containers
    "Company",
    "Parameters",
    "Results",
    "ValuationRequest",

    # Parameters Sub-structures
    "CommonParameters",
    "FinancialRatesParameters",
    "CapitalStructureParameters",
    "ExtensionBundleParameters",
    "MCParameters",
    "ScenariosParameters",
    "BacktestParameters",
    "PeersParameters",
    "SOTPParameters",

    # Results Sub-structures
    "CommonResults",
    "ExtensionBundleResults",

    # Traceability
    "CalculationStep",
]