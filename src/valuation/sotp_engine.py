"""
src/valuation/sotp_engine.py

SUM-OF-THE-PARTS (SOTP) VALUATION ENGINE
========================================
Role: Aggregation of segment-level EVs and application of the Global Equity Bridge.
Architecture: Pipeline Pattern / Glass Box Compliant (ST-2.3).
Scope: Conglomerates and Multi-divisional entities.

Standard: SOLID, i18n Secured.
Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import List, Tuple
from src.models.parameters import SOTPParameters
from src.models.company import CompanyFinancials
from src.models.glass_box import CalculationStep, TraceHypothesis

# Centralized i18n imports (Aligned with src/i18n/fr/backend/)
from src.i18n import SOTPTexts, RegistryTexts, KPITexts


def run_sotp_valuation(
    params: SOTPParameters,
    financials: CompanyFinancials
) -> Tuple[float, List[CalculationStep]]:
    """
    Orchestrates the complete SOTP valuation lifecycle.

    1. Consolidation of segment Enterprise Values (EV).
    2. Application of the Conglomerate (Holding) Discount.
    3. Execution of the global Equity Bridge to resolve shareholder value.

    Parameters
    ----------
    params : SOTPParameters
        Configuration containing segment data and discount rates.
    financials : CompanyFinancials
        Consolidated balance sheet data for the equity bridge.

    Returns
    -------
    Tuple[float, List[CalculationStep]]
        A tuple containing the total Equity Value and the Glass Box trace steps.
    """
    steps: List[CalculationStep] = []

    # --- PILLAR 1: EV CONSOLIDATION & DISCOUNTING ---
    if not params.enabled or not params.segments:
        return 0.0, []

    # Summing individual segment Enterprise Values
    raw_ev_sum = sum(seg.enterprise_value for seg in params.segments)
    discount_factor = (1.0 - params.conglomerate_discount)
    consolidated_ev = raw_ev_sum * discount_factor

    ev_step = CalculationStep(
        step_id=1,
        step_key="SOTP_EV_CONSOLIDATION",
        label=SOTPTexts.STEP_LABEL_CONSOLIDATION,
        theoretical_formula=r"EV_{Total} = \left( \sum EV_{segments} \right) \times (1 - \text{Discount})",
        hypotheses=[
            TraceHypothesis(name=SOTPTexts.LBL_SEGMENT_COUNT, value=len(params.segments), source="Expert"),
            TraceHypothesis(name=SOTPTexts.LBL_RAW_EV_SUM, value=raw_ev_sum, unit="currency"),
            TraceHypothesis(name=SOTPTexts.LBL_DISCOUNT, value=params.conglomerate_discount, unit="%")
        ],
        actual_calculation=f"{raw_ev_sum:,.2f} × (1 - {params.conglomerate_discount:.2%})",
        result=consolidated_ev,
        unit="currency",
        interpretation=SOTPTexts.INTERP_CONSOLIDATION.format(count=len(params.segments))
    )
    steps.append(ev_step)

    # --- PILLAR 2: CONSOLIDATED EQUITY BRIDGE (ST-2.3) ---
    # Global adjustments from the consolidated balance sheet
    debt = financials.total_debt or 0.0
    cash = financials.cash_and_equivalents or 0.0
    minorities = financials.minority_interests or 0.0
    pensions = financials.pension_provisions or 0.0

    # Formula: Equity Value = EV - Debt + Cash - Minorities - Pensions
    equity_value = consolidated_ev - debt + cash - minorities - pensions

    bridge_step = CalculationStep(
        step_id=2,
        step_key="SOTP_EQUITY_BRIDGE",
        label=RegistryTexts.DCF_BRIDGE_L,  # Reusing standard label for consistency
        theoretical_formula=r"Equity Value = EV - Debt + Cash - Minorities - Pensions",
        hypotheses=[
            TraceHypothesis(name=KPITexts.LABEL_DEBT, value=debt, unit="currency", source="Yahoo"),
            TraceHypothesis(name=KPITexts.LABEL_CASH, value=cash, unit="currency", source="Yahoo"),
            TraceHypothesis(name=KPITexts.LABEL_MINORITIES, value=minorities, unit="currency", source="Yahoo"),
            TraceHypothesis(name=KPITexts.LABEL_PENSIONS, value=pensions, unit="currency", source="Yahoo")
        ],
        actual_calculation=(
            f"{consolidated_ev:,.2f} - {debt:,.2f} + {cash:,.2f} "
            f"- {minorities:,.2f} - {pensions:,.2f}"
        ),
        result=equity_value,
        unit="currency",
        interpretation=RegistryTexts.DCF_BRIDGE_D
    )
    steps.append(bridge_step)

    return equity_value, steps