"""
src/valuation/options/sotp.py

SUM-OF-THE-PARTS (SOTP) RUNNER
==============================
Role: Aggregation of segment-level EVs and application of the Global Equity Bridge.
Architecture: Runner Pattern / Glass Box Compliant.
Scope: Conglomerates and Multi-divisional entities.

Standard: SOLID, i18n Secured.
Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from src.models.parameters.base_parameter import Parameters
from src.models.results.options import SOTPResults
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.enums import ParametersSource
from src.utilities.formatting import format_smart_number

# Centralized i18n imports
from src.i18n import SOTPTexts, RegistryTexts, KPITexts

logger = logging.getLogger(__name__)


class SOTPRunner:
    """
    Orchestrates the complete SOTP valuation lifecycle as an Extension.

    1. Consolidation of segment Enterprise Values (EV).
    2. Application of the Conglomerate (Holding) Discount.
    3. Execution of the global Equity Bridge to resolve shareholder value.
    """

    @staticmethod
    def execute(params: Parameters) -> Optional[SOTPResults]:
        """
        Runs the SOTP logic using fully hydrated parameters.

        Parameters
        ----------
        params : Parameters
            The full parameter bundle. Used to access:
            - extensions.sotp: Segment data and discount.
            - common.capital: Bridge items (Debt, Cash, etc.) resolved by the Resolver.

        Returns
        -------
        Optional[SOTPResults]
            The SOTP valuation results if enabled and segments exist, else None.
        """
        sotp_cfg = params.extensions.sotp

        if not sotp_cfg.enabled or not sotp_cfg.segments:
            return None

        steps: List[CalculationStep] = []

        # --- STEP 1: EV CONSOLIDATION & DISCOUNTING ---
        # Sum individual segment values (handling potential Nones as 0.0)
        raw_ev_sum = sum((seg.value or 0.0) for seg in sotp_cfg.segments)
        discount_rate = sotp_cfg.conglomerate_discount or 0.0
        consolidated_ev = raw_ev_sum * (1.0 - discount_rate)

        # Build Variable Map for Glass Box
        step1_vars = {
            "Σ_EV": VariableInfo(
                symbol="Σ_EV",
                value=raw_ev_sum,
                formatted_value=format_smart_number(raw_ev_sum),
                source=ParametersSource.MANUAL,  # Segments are user inputs
                description=SOTPTexts.LBL_RAW_EV_SUM
            ),
            "Disc": VariableInfo(
                symbol="Disc",
                value=discount_rate,
                formatted_value=f"{discount_rate:.1%}",
                source=ParametersSource.MANUAL,
                description=SOTPTexts.LBL_DISCOUNT
            )
        }

        steps.append(CalculationStep(
            step_id=1,
            step_key="SOTP_EV_CONSOLIDATION",
            label=SOTPTexts.STEP_LABEL_CONSOLIDATION,
            theoretical_formula=r"EV_{Total} = \left( \sum EV_{segments} \right) \times (1 - \text{Discount})",
            actual_calculation=f"{format_smart_number(raw_ev_sum)} × (1 - {discount_rate:.1%})",
            result=consolidated_ev,
            unit="currency",
            interpretation=SOTPTexts.INTERP_CONSOLIDATION.format(count=len(sotp_cfg.segments)),
            variables_map=step1_vars
        ))

        # --- STEP 2: CONSOLIDATED EQUITY BRIDGE ---
        # Global adjustments from the consolidated balance sheet.
        # We strictly use 'params.common.capital' because the Resolver has already
        # arbitrated between User Overrides and Yahoo Data.

        cap = params.common.capital

        debt = cap.total_debt or 0.0
        cash = cap.cash_and_equivalents or 0.0
        minorities = cap.minority_interests or 0.0
        pensions = cap.pension_provisions or 0.0
        shares = cap.shares_outstanding or 1.0

        equity_value = consolidated_ev - debt + cash - minorities - pensions
        per_share_value = equity_value / shares if shares > 0 else 0.0

        # Note: For source tracking, we assume SYSTEM (Resolver result) unless we want to trace deeper.
        # Using ParametersSource.AUTO/SYSTEM is safer than hardcoding "Yahoo".
        step2_vars = {
            "EV": VariableInfo(
                symbol="EV",
                value=consolidated_ev,
                formatted_value=format_smart_number(consolidated_ev),
                source=ParametersSource.SYSTEM,
                description=RegistryTexts.DCF_EV_L
            ),
            "Debt": VariableInfo(
                symbol="Debt",
                value=debt,
                formatted_value=format_smart_number(debt),
                source=ParametersSource.SYSTEM,
                description=KPITexts.LABEL_DEBT
            ),
            "Cash": VariableInfo(
                symbol="Cash",
                value=cash,
                formatted_value=format_smart_number(cash),
                source=ParametersSource.SYSTEM,
                description=KPITexts.LABEL_CASH
            ),
            "Min": VariableInfo(
                symbol="Min",
                value=minorities,
                formatted_value=format_smart_number(minorities),
                source=ParametersSource.SYSTEM,
                description=KPITexts.LABEL_MINORITIES
            ),
            "Pens": VariableInfo(
                symbol="Pens",
                value=pensions,
                formatted_value=format_smart_number(pensions),
                source=ParametersSource.SYSTEM,
                description=KPITexts.LABEL_PENSIONS
            )
        }

        steps.append(CalculationStep(
            step_id=2,
            step_key="SOTP_EQUITY_BRIDGE",
            label=RegistryTexts.DCF_BRIDGE_L,
            theoretical_formula=r"Equity = EV - Debt + Cash - Min - Pens",
            actual_calculation=(
                f"{format_smart_number(consolidated_ev)} - {format_smart_number(debt)} + "
                f"{format_smart_number(cash)} ..."
            ),
            result=equity_value,
            unit="currency",
            interpretation=RegistryTexts.DCF_BRIDGE_D,
            variables_map=step2_vars
        ))

        # --- STEP 3: PACKAGING ---
        segment_map = {s.name: (s.value or 0.0) for s in sotp_cfg.segments}

        return SOTPResults(
            total_enterprise_value=consolidated_ev,
            segment_values=segment_map,
            implied_equity_value=equity_value,
            equity_value_per_share=per_share_value,
            sotp_trace=steps
        )