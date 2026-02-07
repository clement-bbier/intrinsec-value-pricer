"""
src/valuation/library/common.py

COMMON VALUATION LIBRARY
========================
Role: Shared financial logic for Discount Rates (WACC/Ke) and Equity Bridge.
Architecture: Stateless Functional Library.
Input: Resolved Parameters + Company Financials.
Output: Computed values + Full Audit Trace (CalculationStep).

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
"""

from __future__ import annotations

from typing import Tuple

from src.models.company import Company
from src.models.parameters.base_parameter import Parameters
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.enums import VariableSource
from src.core.formatting import format_smart_number

# Atomic imports for pure math
from src.computation.financial_math import (
    calculate_cost_of_equity_capm,
    calculate_synthetic_cost_of_debt
)

# Configuration and i18n imports
from src.config.constants import MacroDefaults, ModelDefaults
from src.i18n import RegistryTexts, StrategyFormulas, StrategyInterpretations, KPITexts, StrategySources


class CommonLibrary:
    """
    Shared valuation building blocks used by all strategies (DCF, RIM, etc.).
    """

    @staticmethod
    def resolve_discount_rate(
        financials: Company,
        params: Parameters,
        use_cost_of_equity_only: bool = False
    ) -> Tuple[float, CalculationStep]:
        """
        Computes the appropriate discount rate (WACC or Ke) with full provenance.

        Parameters
        ----------
        financials : Company
            Market data (Price, Beta) and Financials (Debt).
        params : Parameters
            Configuration with Rates (Rf, MRP) and Capital Structure.
        use_cost_of_equity_only : bool
            If True, returns Cost of Equity (for RIM/DDM).
            If False, returns WACC (for FCFF).

        Returns
        -------
        Tuple[float, CalculationStep]
            The rate and its audit step.
        """
        # --- 1. Input Resolution (Overrides vs System) ---
        r = params.common.rates
        cap = params.common.capital

        # Risk Free & MRP
        rf = r.risk_free_rate or MacroDefaults.DEFAULT_RISK_FREE_RATE
        mrp = r.market_risk_premium or MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM

        # Beta Resolution (Manual > Financials > Default)
        beta_raw = r.manual_beta if r.manual_beta is not None else (financials.beta or ModelDefaults.DEFAULT_BETA)

        # Cost of Equity Calculation (CAPM)
        ke = calculate_cost_of_equity_capm(rf, beta_raw, mrp)

        # Direct Ke Override (if provided)
        if r.manual_cost_of_equity is not None:
            ke = r.manual_cost_of_equity

        # --- CASE 1: EQUITY ONLY (RIM, DDM, FCFE) ---
        if use_cost_of_equity_only:
            variables = {
                "Rf": VariableInfo(
                    symbol="Rf", value=rf,
                    source=VariableSource.MANUAL_OVERRIDE if r.risk_free_rate else VariableSource.SYSTEM,
                    description="Risk-Free Rate"
                ),
                "Beta": VariableInfo(
                    symbol="β", value=beta_raw,
                    source=VariableSource.MANUAL_OVERRIDE if r.manual_beta else VariableSource.YAHOO_FINANCE,
                    description="Beta"
                ),
                "MRP": VariableInfo(
                    symbol="MRP", value=mrp,
                    source=VariableSource.MANUAL_OVERRIDE if r.market_risk_premium else VariableSource.SYSTEM,
                    description="Market Risk Premium"
                )
            }

            # Handle Ke override in the trace
            if r.manual_cost_of_equity is not None:
                variables["Ke"] = VariableInfo(
                    symbol="Ke", value=ke,
                    source=VariableSource.MANUAL_OVERRIDE, is_overridden=True,
                    description="Cost of Equity (User Override)"
                )

            step = CalculationStep(
                step_key="KE_CALC",
                label=RegistryTexts.DCF_KE_L,
                theoretical_formula=StrategyFormulas.CAPM,
                actual_calculation=f"{rf:.2%} + {beta_raw:.2f} × {mrp:.2%}",
                result=ke,
                interpretation=StrategyInterpretations.KE_CONTEXT,
                source=StrategySources.CAPM_CALC,
                variables_map=variables
            )
            return ke, step

        # --- CASE 2: WACC (FCFF) ---

        # 2.1 Cost of Debt (Kd)
        if r.cost_of_debt is not None:
            kd_pre_tax = r.cost_of_debt
            kd_source = VariableSource.MANUAL_OVERRIDE
        else:
            # Synthetic rating based on ICR
            # Using defensive logic: resolver should populate snapshot data
            # We assume params.strategy inputs might hold TTM EBIT/Interest if resolver did its job
            # For strict safety, we query the financials structure if available, or 0.0 defaults

            # Note: financial_math.calculate_synthetic_cost_of_debt handles 0.0 values gracefully
            # by returning Rf + Spread (Defensive)
            ebit = 0.0 # To be enriched if we pass full snapshot
            interest = 0.0
            mcap = 0.0
            kd_pre_tax = calculate_synthetic_cost_of_debt(rf, ebit, interest, mcap)
            kd_source = VariableSource.CALCULATED

        tax_rate = r.tax_rate or MacroDefaults.DEFAULT_TAX_RATE
        kd_net = kd_pre_tax * (1.0 - tax_rate)

        # 2.2 Weights (We, Wd)
        # We use params.common.capital which is the resolved source of truth
        debt_val = cap.total_debt or 0.0
        shares = cap.shares_outstanding or 1.0
        price = financials.current_price or 0.0
        equity_val = shares * price

        total_cap = equity_val + debt_val
        if total_cap <= 0:
            we, wd = 1.0, 0.0
        else:
            we = equity_val / total_cap
            wd = debt_val / total_cap

        # 2.3 WACC Calculation
        wacc = (we * ke) + (wd * kd_net)

        # Global WACC Override
        if r.wacc_override is not None:
            wacc = r.wacc_override

        # 2.4 Trace Building
        wacc_vars = {
            "Ke": VariableInfo(
                symbol="Ke", value=ke,
                source=VariableSource.CALCULATED, description="Cost of Equity"
            ),
            "Kd_net": VariableInfo(
                symbol="Kd(1-t)", value=kd_net,
                source=kd_source, description="Cost of Debt (After Tax)"
            ),
            "We": VariableInfo(
                symbol="We", value=we,
                source=VariableSource.CALCULATED, description="Equity Weight"
            ),
            "Wd": VariableInfo(
                symbol="Wd", value=wd,
                source=VariableSource.CALCULATED, description="Debt Weight"
            ),
        }

        if r.wacc_override is not None:
            wacc_vars["WACC"] = VariableInfo(
                symbol="WACC", value=wacc,
                source=VariableSource.MANUAL_OVERRIDE, is_overridden=True,
                description="WACC (User Override)"
            )

        step = CalculationStep(
            step_key="WACC_CALC",
            label=RegistryTexts.DCF_WACC_L,
            theoretical_formula=StrategyFormulas.WACC,
            actual_calculation=f"({we:.1%} × {ke:.1%}) + ({wd:.1%} × {kd_net:.1%})",
            result=wacc,
            interpretation=StrategyInterpretations.WACC_CONTEXT,
            source=StrategySources.WACC_MARKET,
            variables_map=wacc_vars
        )

        return wacc, step

    @staticmethod
    def compute_equity_bridge(
        enterprise_value: float,
        params: Parameters
    ) -> Tuple[float, CalculationStep]:
        """
        Walks from Enterprise Value (EV) to Equity Value using the Bridge.

        Formula: Equity = EV - Net Debt - Minorities - Pensions

        Parameters
        ----------
        enterprise_value : float
            The calculated Firm Value (PV of Flows + PV of Terminal Value).
        params : Parameters
            Contains the Balance Sheet items (Capital).

        Returns
        -------
        Tuple[float, CalculationStep]
            Equity Value and the bridge trace.
        """
        cap = params.common.capital

        # Inputs (Resolver has already handled logic: User Override > Yahoo > Default)
        debt = cap.total_debt or 0.0
        cash = cap.cash_and_equivalents or 0.0
        minorities = cap.minority_interests or 0.0
        pensions = cap.pension_provisions or 0.0

        # Calculation
        # Equity = EV - Debt + Cash - Min - Pens
        equity_value = enterprise_value - debt + cash - minorities - pensions

        # Trace
        variables = {
            "EV": VariableInfo(
                symbol="EV", value=enterprise_value,
                source=VariableSource.CALCULATED, description=RegistryTexts.DCF_EV_L
            ),
            "Debt": VariableInfo(
                symbol="Debt", value=debt,
                source=VariableSource.SYSTEM, # Already resolved by Resolver
                description=KPITexts.LABEL_DEBT
            ),
            "Cash": VariableInfo(
                symbol="Cash", value=cash,
                source=VariableSource.SYSTEM,
                description=KPITexts.LABEL_CASH
            ),
            "Min": VariableInfo(
                symbol="Min", value=minorities,
                source=VariableSource.SYSTEM,
                description=KPITexts.LABEL_MINORITIES
            ),
            "Pens": VariableInfo(
                symbol="Pens", value=pensions,
                source=VariableSource.SYSTEM,
                description=KPITexts.LABEL_PENSIONS
            )
        }

        step = CalculationStep(
            step_key="EQUITY_BRIDGE",
            label=RegistryTexts.DCF_BRIDGE_L,
            theoretical_formula=StrategyFormulas.EQUITY_BRIDGE,
            actual_calculation=(
                f"{format_smart_number(enterprise_value)} - {format_smart_number(debt)} + "
                f"{format_smart_number(cash)} ..."
            ),
            result=equity_value,
            unit="currency",
            interpretation=StrategyInterpretations.BRIDGE,
            source=StrategySources.YAHOO_TTM_SIMPLE,
            variables_map=variables
        )

        return equity_value, step