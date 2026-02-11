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
from .benchmarks import MarketContext, SectorMultiples, SectorPerformance

# 2. Domain Identity (Pillar 1)
from .company import Company, CompanySnapshot
from .enums import (
    CompanySector,
    DiagnosticLevel,
    DiscountRateMethod,
    ParametersSource,
    SOTPMethod,
    TerminalValueMethod,
    ValuationMethodology,
    VariableSource,
)

# 6. Glass Box & Audit (Traceability)
from .glass_box import CalculationStep, TraceHypothesis, VariableInfo

# 7. Market & Benchmarks
from .market_data import MultiplesData, PeerMetric

# 3. Parameter Containers (Pillar 2, 3, 4 Inputs)
from .parameters.base_parameter import Parameters
from .parameters.common import CapitalStructureParameters, CommonParameters, FinancialRatesParameters
from .parameters.input_metadata import UIKey
from .parameters.options import (
    BacktestParameters,
    ExtensionBundleParameters,
    MCParameters,
    PeersParameters,
    ScenariosParameters,
    SOTPParameters,
)

# 4. Results Containers (We export what is available, assuming results module exists)
# Note: Ensure src.models.results is populated in the next steps if not already.
from .results.base_result import Results

# 5. High-Level Envelopes
from .valuation import AuditReport, ValuationRequest, ValuationResult, ValuationRunMetadata

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
    "ValuationRunMetadata",
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
