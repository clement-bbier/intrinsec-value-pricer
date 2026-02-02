"""
src/models/params/strategies.py

SPECIFIC VALUATION STRATEGY Resolvers (ULTRA-CLINICAL & DRY)
============================================================
Role: Captures User Overrides with factored projection logic.
Architecture: Pydantic V2 inheritance. Factors common projection fields
              while keeping accounting anchors specialized per model.
"""

from __future__ import annotations
from typing import Optional, Literal, Union
from pydantic import BaseModel, Field
from src.models.enums import ValuationMethodology, TerminalValueMethod

# ==============================================================================
# 1. REUSABLE COMPONENTS
# ==============================================================================

class TerminalValueResolvers(BaseModel):
    """Resolvers for Step 4: Terminal Value (Exit Logic)."""
    method: Optional[TerminalValueMethod] = None
    perpetual_growth_rate: Optional[float] = None
    exit_multiple: Optional[float] = None

class BaseProjectedResolvers(BaseModel):
    """
    Base Mixin for models requiring a discrete projection period.
    Factors common fields for DCF, DDM, and RIM.
    """
    projection_years: Optional[int] = Field(None, ge=1, le=50)
    terminal_value: TerminalValueResolvers = Field(default_factory=TerminalValueResolvers)

# ==============================================================================
# 2. STRATEGY CLASSES (The Drawers)
# ==============================================================================

class FCFFStandardResolvers(BaseProjectedResolvers):
    """Standard DCF based on Free Cash Flow to Firm."""
    mode: Literal[ValuationMethodology.FCFF_STANDARD] = ValuationMethodology.FCFF_STANDARD

    # --- Accounting Overrides ---
    fcf_anchor: Optional[float] = None
    ebit_ttm: Optional[float] = None
    capex_ttm: Optional[float] = None
    da_ttm: Optional[float] = None

    # --- Specific Lever ---
    growth_rate_p1: Optional[float] = None

class FCFFNormalizedResolvers(BaseProjectedResolvers):
    """DCF based on normalized cycle flows."""
    mode: Literal[ValuationMethodology.FCFF_NORMALIZED] = ValuationMethodology.FCFF_NORMALIZED

    # --- Accounting Overrides ---
    fcf_norm: Optional[float] = None
    ebit_norm: Optional[float] = None

    # --- Specific Lever ---
    cycle_growth_rate: Optional[float] = None

class FCFFGrowthResolvers(BaseProjectedResolvers):
    """DCF starting from Revenue and Margins."""
    mode: Literal[ValuationMethodology.FCFF_GROWTH] = ValuationMethodology.FCFF_GROWTH

    # --- Accounting Overrides ---
    revenue_ttm: Optional[float] = None
    ebitda_ttm: Optional[float] = None
    target_fcf_margin: Optional[float] = None
    capex_ttm: Optional[float] = None

    # --- Specific Lever ---
    revenue_growth_rate: Optional[float] = None

class FCFEResolvers(BaseProjectedResolvers):
    """Free Cash Flow to Equity (Post-Debt)."""
    mode: Literal[ValuationMethodology.FCFE] = ValuationMethodology.FCFE

    # --- Accounting Overrides ---
    fcfe_anchor: Optional[float] = None
    net_income_ttm: Optional[float] = None
    net_borrowing_delta: Optional[float] = None
    capex_ttm: Optional[float] = None

    # --- Specific Lever ---
    growth_rate: Optional[float] = None

class DDMResolvers(BaseProjectedResolvers):
    """Dividend Discount Model."""
    mode: Literal[ValuationMethodology.DDM] = ValuationMethodology.DDM

    # --- Accounting Overrides ---
    dividend_per_share: Optional[float] = None
    net_income_ttm: Optional[float] = None

    # --- Specific Lever ---
    dividend_growth_rate: Optional[float] = None

class RIMResolvers(BaseProjectedResolvers):
    """Residual Income Model (Ohlson)."""
    mode: Literal[ValuationMethodology.RIM] = ValuationMethodology.RIM

    # --- Accounting Overrides ---
    book_value_anchor: Optional[float] = None
    net_income_norm: Optional[float] = None
    total_assets: Optional[float] = None

    # --- Specific Levers ---
    growth_rate: Optional[float] = None
    persistence_factor: Optional[float] = None

class GrahamResolvers(BaseModel):
    """
    Graham Intrinsic Value.
    Note: Does NOT inherit from BaseProjectedResolvers (Static Formula).
    """
    mode: Literal[ValuationMethodology.GRAHAM] = ValuationMethodology.GRAHAM

    # --- Accounting Overrides ---
    eps_normalized: Optional[float] = None
    revenue_ttm: Optional[float] = None

    # --- Method Levers ---
    growth_estimate: Optional[float] = None

# ==============================================================================
# 3. THE ORCHESTRATOR
# ==============================================================================

StrategyUnionResolvers = Union[
    FCFFStandardResolvers,
    FCFFNormalizedResolvers,
    FCFFGrowthResolvers,
    FCFEResolvers,
    DDMResolvers,
    RIMResolvers,
    GrahamResolvers
]