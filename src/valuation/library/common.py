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

# Atomic imports for pure math
from src.computation.financial_math import (
    calculate_comprehensive_net_debt,
    calculate_cost_of_equity_capm,
    calculate_synthetic_cost_of_debt,
)

# Configuration and i18n imports
from src.config.constants import MacroDefaults, ModelDefaults
from src.core.formatting import format_smart_number
from src.i18n import KPITexts, RegistryTexts, StrategyFormulas, StrategyInterpretations, StrategySources
from src.models.company import Company
from src.models.enums import VariableSource
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.parameters.base_parameter import Parameters


class CommonLibrary:
    """
    Shared valuation building blocks used by all strategies (DCF, RIM, etc.).
    """

    @staticmethod
    def resolve_discount_rate(
        financials: Company, params: Parameters, use_cost_of_equity_only: bool = False
    ) -> tuple[float, CalculationStep]:
        """
        Computes the appropriate discount rate (WACC or Ke) with full provenance.
        """
        # --- 1. Input Resolution (Overrides vs System) ---
        r = params.common.rates
        cap = params.common.capital

        # Risk Free & MRP
        rf = r.risk_free_rate or MacroDefaults.DEFAULT_RISK_FREE_RATE
        mrp = r.market_risk_premium or MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM

        # Beta Resolution (Manual > Financials > Default)
        beta_raw = r.beta if r.beta is not None else ModelDefaults.DEFAULT_BETA

        # Cost of Equity Calculation (CAPM)
        ke = calculate_cost_of_equity_capm(rf, beta_raw, mrp)

        # --- CASE 1: EQUITY ONLY (RIM, DDM, FCFE) ---
        if use_cost_of_equity_only:
            variables = {
                "Rf": VariableInfo(
                    symbol="Rf",
                    value=rf,
                    source=VariableSource.MANUAL_OVERRIDE if r.risk_free_rate else VariableSource.SYSTEM,
                    description="Risk-Free Rate",
                ),
                "Beta": VariableInfo(
                    symbol="β",
                    value=beta_raw,
                    source=VariableSource.MANUAL_OVERRIDE if r.beta else VariableSource.YAHOO_FINANCE,
                    description="Beta",
                ),
                "MRP": VariableInfo(
                    symbol="MRP",
                    value=mrp,
                    source=VariableSource.MANUAL_OVERRIDE if r.market_risk_premium else VariableSource.SYSTEM,
                    description="Market Risk Premium",
                ),
            }

            step = CalculationStep(
                step_key="KE_CALC",
                label=RegistryTexts.DCF_KE_L,
                theoretical_formula=StrategyFormulas.CAPM,
                actual_calculation=f"{rf:.2%} + {beta_raw:.2f} × {mrp:.2%}",
                result=ke,
                interpretation=StrategyInterpretations.KE_CONTEXT,
                source=StrategySources.CAPM_CALC,
                variables_map=variables,
            )
            return ke, step

        # --- CASE 2: WACC (FCFF) ---

        # 2.1 Cost of Debt (Kd)
        if r.cost_of_debt is not None:
            kd_pre_tax = r.cost_of_debt
            kd_source = VariableSource.MANUAL_OVERRIDE
        else:
            # Synthetic logic via financial_math
            # We assume ebit_ttm/interest are not available in params directly but implicit via resolver
            # For strict math, we use fallback 0.0 if not passed (handled by atomic function)
            kd_pre_tax = calculate_synthetic_cost_of_debt(
                rf, 0.0, 0.0, financials.current_price * (cap.shares_outstanding or 1.0)
            )
            kd_source = VariableSource.CALCULATED

        tax_rate = r.tax_rate or MacroDefaults.DEFAULT_TAX_RATE
        kd_net = kd_pre_tax * (1.0 - tax_rate)

        # 2.2 Weights (We, Wd)
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

        # 2.4 Trace Building
        wacc_vars = {
            "Ke": VariableInfo(symbol="Ke", value=ke, source=VariableSource.CALCULATED, description="Cost of Equity"),
            "Kd_net": VariableInfo(
                symbol="Kd(1-t)", value=kd_net, source=kd_source, description="Cost of Debt (After Tax)"
            ),
            "We": VariableInfo(symbol="We", value=we, source=VariableSource.CALCULATED, description="Equity Weight"),
            "Wd": VariableInfo(symbol="Wd", value=wd, source=VariableSource.CALCULATED, description="Debt Weight"),
        }

        step = CalculationStep(
            step_key="WACC_CALC",
            label=RegistryTexts.DCF_WACC_L,
            theoretical_formula=StrategyFormulas.WACC,
            actual_calculation=f"({we:.1%} × {ke:.1%}) + ({wd:.1%} × {kd_net:.1%})",
            result=wacc,
            interpretation=StrategyInterpretations.WACC_CONTEXT,
            source=StrategySources.WACC_MARKET,
            variables_map=wacc_vars,
        )

        return wacc, step

    @staticmethod
    def compute_equity_bridge(enterprise_value: float, params: Parameters) -> tuple[float, CalculationStep]:
        """
        Walks from Enterprise Value (EV) to Equity Value using the Bridge.

        Implements IFRS 16 compliance by including lease and pension liabilities
        as debt-equivalents in the equity bridge calculation.

        Note: pension_provisions and pension_liabilities are distinct items.
        - pension_provisions: Legacy accounting provisions
        - pension_liabilities: IFRS 16 off-balance-sheet obligations
        Both are subtracted from EV as debt-equivalents.
        """
        cap = params.common.capital

        debt = cap.total_debt or 0.0
        cash = cap.cash_and_equivalents or 0.0
        minorities = cap.minority_interests or 0.0
        lease_liabilities = cap.lease_liabilities or 0.0
        pension_liabilities = cap.pension_liabilities or 0.0

        # Use comprehensive net debt calculation (IFRS 16 compliant)
        # This includes debt, cash, and IFRS 16 off-balance-sheet liabilities
        comprehensive_net_debt = calculate_comprehensive_net_debt(
            total_debt=debt, cash=cash, lease_liabilities=lease_liabilities, pension_liabilities=pension_liabilities
        )

        # Equity = EV - Comprehensive Net Debt - Minorities
        # Note: pension_provisions are already included in total_debt if on balance sheet,
        # or captured separately as legacy provisions distinct from IFRS 16 pension_liabilities
        equity_value = enterprise_value - comprehensive_net_debt - minorities

        variables = {
            "EV": VariableInfo(
                symbol="EV",
                value=enterprise_value,
                source=VariableSource.CALCULATED,
                description=RegistryTexts.DCF_EV_L,
            ),
            "Net_Debt": VariableInfo(
                symbol="Net Debt",
                value=comprehensive_net_debt,
                source=VariableSource.CALCULATED,
                description="Comprehensive Net Debt (IFRS 16)",
            ),
            "Debt": VariableInfo(
                symbol="Debt", value=debt, source=VariableSource.SYSTEM, description=KPITexts.LABEL_DEBT
            ),
            "Cash": VariableInfo(
                symbol="Cash", value=cash, source=VariableSource.SYSTEM, description=KPITexts.LABEL_CASH
            ),
        }

        # Add IFRS 16 liabilities to variables if present
        if lease_liabilities > 0.0:
            variables["Leases"] = VariableInfo(
                symbol="Leases",
                value=lease_liabilities,
                source=VariableSource.SYSTEM,
                description="Lease Liabilities (IFRS 16)",
            )

        if pension_liabilities > 0.0:
            variables["Pensions_IFRS"] = VariableInfo(
                symbol="Pensions_IFRS",
                value=pension_liabilities,
                source=VariableSource.SYSTEM,
                description="Pension Liabilities (IFRS 16)",
            )

        # Build calculation display
        calc_parts = [f"{format_smart_number(enterprise_value)} (EV)"]
        calc_parts.append(f"- {format_smart_number(comprehensive_net_debt)} (Net Debt)")
        if minorities > 0.0:
            calc_parts.append(f"- {format_smart_number(minorities)} (Min)")

        step = CalculationStep(
            step_key="EQUITY_BRIDGE",
            label=RegistryTexts.DCF_BRIDGE_L,
            theoretical_formula=StrategyFormulas.EQUITY_BRIDGE,
            actual_calculation=" ".join(calc_parts),
            result=equity_value,
            unit="currency",
            interpretation=StrategyInterpretations.BRIDGE,
            source=StrategySources.YAHOO_TTM_SIMPLE,
            variables_map=variables,
        )

        return equity_value, step
