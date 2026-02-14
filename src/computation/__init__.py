"""
src/computation/__init__.py

COMPUTATION LAYER EXPORTS
=========================
Role: Exposes stateless mathematical engines and logic strategies.
Scope: Financial formulas, Flow projections, and Statistical simulations.
Architecture: Facade Pattern.
"""

from src.computation.financial_math import (
    WACCBreakdown,
    apply_dilution_adjustment,
    calculate_cost_of_equity,
    calculate_dilution_factor,
    calculate_discount_factors,
    calculate_fcfe_base,
    calculate_fcfe_reconstruction,
    calculate_graham_1974_value,
    calculate_historical_share_growth,
    calculate_npv,
    calculate_price_from_ev_multiple,
    calculate_price_from_pe_multiple,
    calculate_rim_vectors,
    calculate_synthetic_cost_of_debt,
    calculate_terminal_value_exit_multiple,
    calculate_terminal_value_gordon,
    calculate_terminal_value_pe,
    calculate_triangulated_price,
    calculate_wacc,
    compute_diluted_shares,
)
from src.computation.flow_projector import (
    FlowProjector,
    MarginConvergenceProjector,
    ProjectionOutput,
    SimpleFlowProjector,
)
from src.computation.statistics import (
    MonteCarloEngine,
    StochasticOutput,
    generate_independent_samples,
    generate_multivariate_samples,
)

__all__ = [
    # Financial Mathematics (Atomic)
    "WACCBreakdown",
    "calculate_wacc",
    "calculate_cost_of_equity",
    "calculate_synthetic_cost_of_debt",
    "calculate_npv",
    "calculate_discount_factors",
    "calculate_terminal_value_gordon",
    "calculate_terminal_value_exit_multiple",
    "calculate_terminal_value_pe",
    "calculate_historical_share_growth",
    "calculate_dilution_factor",
    "apply_dilution_adjustment",
    "compute_diluted_shares",
    "calculate_fcfe_base",
    "calculate_fcfe_reconstruction",
    "calculate_graham_1974_value",
    "calculate_rim_vectors",
    "calculate_price_from_pe_multiple",
    "calculate_price_from_ev_multiple",
    "calculate_triangulated_price",
    # Flow Projections (Strategy)
    "FlowProjector",
    "SimpleFlowProjector",
    "MarginConvergenceProjector",
    "ProjectionOutput",
    # Statistics & Monte Carlo (Vectorized)
    "MonteCarloEngine",
    "StochasticOutput",
    "generate_multivariate_samples",
    "generate_independent_samples",
]
