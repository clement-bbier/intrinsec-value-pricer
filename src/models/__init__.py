"""
src/models/__init__.py

MODELS LAYER EXPORTS
====================
Single entry point for all data structures in the Domain Layer.

Structure:
- enums.py      : Domain enumerations (Methodology, Sources, etc.)
- company.py    : Static company identity (Pillar 1)
- parameters/   : Input containers (The "Ghost" Objects)
- results/      : Output containers (The "Mirror" Objects)
- valuation.py  : High-level Request/Result envelopes
- market_data.py: Peer analysis containers
- benchmarks.py : Sector reference data
- glass_box.py  : Traceability logic
"""

# 1. Base Enumerations (Enums only)
from .enums import (
    ValuationMethodology,
    ParametersSource,
    TerminalValueMethod,
    CompanySector,
    DiscountRateMethod,
    VariableSource,
    SOTPMethod,
    DiagnosticLevel
)

# 2. Domain Identity (Pillar 1)
from .company import Company, CompanySnapshot

# 3. Parameter Containers (Pillar 2, 3, 4 Inputs)
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
from .parameters.input_metadata import UIKey

# 4. Results Containers (We export what is available, assuming results module exists)
# Note: Ensure src.models.results is populated in the next steps if not already.
from .results.base_result import Results

# 5. High-Level Envelopes
from .valuation import (
    ValuationRequest,
    ValuationResult,
    AuditReport
)

# 6. Glass Box & Audit (Traceability)
from .glass_box import CalculationStep, VariableInfo, TraceHypothesis

# 7. Market & Benchmarks
from .market_data import MultiplesData, PeerMetric
from .benchmarks import MarketContext, SectorMultiples, SectorPerformance

__all__ = [
    # Enums
    "ValuationMethodology",
    "ParametersSource",
    "TerminalValueMethod",
    "CompanySector",
    "DiscountRateMethod",
    "VariableSource",
    "SOTPMethod",
    "DiagnosticLevel",

    # Pillars & Root Containers
    "Company",
    "CompanySnapshot",
    "Parameters",
    "Results",
    "ValuationRequest",
    "ValuationResult",
    "AuditReport",

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
    "UIKey",

    # Market & Traceability
    "MarketContext",
    "SectorMultiples",
    "SectorPerformance",
    "MultiplesData",
    "PeerMetric",
    "CalculationStep",
    "VariableInfo",
    "TraceHypothesis"
]