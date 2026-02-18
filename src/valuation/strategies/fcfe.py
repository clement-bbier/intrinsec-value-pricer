"""
src/valuation/strategies/fcfe.py

FREE CASH FLOW TO EQUITY (FCFE) STRATEGY RUNNER
===============================================
Role: Direct Equity Valuation engine.
Academic Reference: Damodaran (Category 2: Leveraged Firms / Banks).
Logic: Discounts flows available to shareholders (after debt service) at Cost of Equity (Ke).
Architecture: IValuationRunner implementation.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
"""

from __future__ import annotations

from typing import cast

import numpy as np

from src.computation.financial_math import calculate_discount_factors

# Config & i18n
from src.i18n import KPITexts, RegistryTexts, StrategyFormulas, StrategyInterpretations, StrategySources
from src.models.company import Company
from src.models.enums import ValuationMethodology, VariableSource
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.strategies import FCFEParameters
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedCapital, ResolvedRates
from src.models.results.options import ExtensionBundleResults
from src.models.results.strategies import FCFEResults

# Models Results
from src.models.valuation import ValuationRequest, ValuationResult

# Libraries
from src.valuation.library.common import CommonLibrary
from src.valuation.library.dcf import DCFLibrary
from src.valuation.strategies.interface import IValuationRunner


class FCFEStrategy(IValuationRunner):
    """
    FCFE Strategy (Direct Equity).
    Ideal for: Financial Services, Highly Leveraged Firms, or Stable Debt Ratio firms.
    """

    def __init__(self) -> None:
        self._glass_box: bool = True

    @property
    def glass_box_enabled(self) -> bool:
        return self._glass_box

    @glass_box_enabled.setter
    def glass_box_enabled(self, value: bool) -> None:
        self._glass_box = value

    def execute(self, financials: Company, params: Parameters) -> ValuationResult:
        """
        Executes FCFE valuation sequence.
        Note: Discounts at Ke, not WACC.
        """
        # Type narrowing for mypy
        strategy_params = cast(FCFEParameters, params.strategy)

        steps: list[CalculationStep] = []

        # --- STEP 1: Rate Resolution (Ke ONLY) ---
        ke, step_ke = CommonLibrary.resolve_discount_rate(
            financials=financials, params=params, use_cost_of_equity_only=True
        )
        if self._glass_box:
            steps.append(step_ke)

        # --- STEP 2: Anchor Selection ---
        fcfe_base = strategy_params.fcfe_anchor or 0.0

        if self._glass_box:
            steps.append(
                CalculationStep(
                    step_key="FCFE_ANCHOR",
                    label=RegistryTexts.FCFE_BASE_L,
                    theoretical_formula=StrategyFormulas.FCFE_RECONSTRUCTION,
                    actual_calculation=f"Starting FCFE: {fcfe_base:,.2f}",
                    result=fcfe_base,
                    interpretation=StrategyInterpretations.FCFE_LOGIC,
                    source=StrategySources.SYSTEM,
                    variables_map={
                        "FCFE_0": VariableInfo(
                            symbol="FCFE_0",
                            value=fcfe_base,
                            source=VariableSource.SYSTEM,
                            description="Base Year Free Cash Flow to Equity",
                        )
                    },
                )
            )

        # --- STEP 3: Projection ---
        manual_vector = getattr(params.strategy, "manual_growth_vector", None)

        if manual_vector and len(manual_vector) > 0:
            flows, step_proj = DCFLibrary.project_flows_manual(fcfe_base, manual_vector)
        else:
            flows, step_proj = DCFLibrary.project_flows_simple(fcfe_base, params)

        if self._glass_box:
            steps.append(step_proj)

        # --- STEP 4: Terminal Value ---
        final_flow = flows[-1] if flows else fcfe_base
        tv, step_tv, tv_diagnostics = DCFLibrary.compute_terminal_value(final_flow, ke, params)
        if self._glass_box:
            steps.append(step_tv)

        # --- STEP 5: Discounting ---
        pv_equity, step_ev = DCFLibrary.compute_discounting(flows, tv, ke)
        if self._glass_box:
            steps.append(step_ev)

        # --- STEP 6: Total Equity Value ---
        cash = params.common.capital.cash_and_equivalents or 0.0
        total_equity_value = pv_equity + cash

        if self._glass_box:
            steps.append(
                CalculationStep(
                    step_key="FCFE_EQUITY_SUM",
                    label=RegistryTexts.FCFE_EQUITY_VALUE,
                    theoretical_formula="Equity = PV(FCFE) + Cash",
                    actual_calculation=f"{pv_equity:,.0f} + {cash:,.0f}",
                    result=total_equity_value,
                    interpretation="Adding non-operating cash to operating equity value.",
                    source=StrategySources.CALCULATED,
                    variables_map={
                        "PV_FCFE": VariableInfo(symbol="PV", value=pv_equity, source=VariableSource.CALCULATED),
                        "Cash": VariableInfo(
                            symbol="Cash",
                            value=cash,
                            source=VariableSource.SYSTEM,
                            description=KPITexts.LABEL_CASH,
                        ),
                    },
                )
            )

        # --- STEP 7: Per Share ---
        iv_per_share, step_iv = DCFLibrary.compute_value_per_share(total_equity_value, params)
        if self._glass_box:
            steps.append(step_iv)

        # --- RESULT CONSTRUCTION ---
        res_rates = ResolvedRates(cost_of_equity=ke, cost_of_debt_after_tax=0.0, wacc=ke)

        debt = params.common.capital.total_debt or 0.0
        implied_ev = total_equity_value + debt - cash

        shares = params.common.capital.shares_outstanding or 1.0
        res_capital = ResolvedCapital(
            market_cap=shares * (financials.current_price or 0.0),
            enterprise_value=implied_ev,
            net_debt_resolved=debt - cash,
            equity_value_total=total_equity_value,
        )

        common_res = CommonResults(
            rates=res_rates,
            capital=res_capital,
            intrinsic_value_per_share=iv_per_share,
            upside_pct=(
                ((iv_per_share - (financials.current_price or 0.0)) / (financials.current_price or 1.0))
                if financials.current_price
                else 0.0
            ),
            bridge_trace=steps if self._glass_box else [],
        )

        discount_factors = calculate_discount_factors(ke, len(flows))
        pv_tv = tv * discount_factors[-1] if discount_factors else 0.0

        strategy_res = FCFEResults(
            projected_flows=flows,
            discount_factors=discount_factors,
            terminal_value=tv,
            discounted_terminal_value=pv_tv,
            tv_weight_pct=(pv_tv / pv_equity) if pv_equity > 0 else 0.0,
            strategy_trace=[],
            projected_net_borrowing=[],
        )

        return ValuationResult(
            request=ValuationRequest(mode=ValuationMethodology.FCFE, parameters=params),
            results=Results(common=common_res, strategy=strategy_res, extensions=ExtensionBundleResults()),
        )

    @staticmethod
    def execute_stochastic(_financials: Company, params: Parameters, vectors: dict[str, np.ndarray]) -> np.ndarray:
        """
        Vectorized FCFE Execution for Monte Carlo.

        Logic: PV(FCFE, Ke) + Non-Operating Cash.
        Note: We do NOT subtract debt here (unlike FCFF), we add Cash.
        """
        # 1. Unpack Vectors
        ke_vec = vectors["wacc"]  # Maps to Ke for FCFE
        g_p1 = vectors["growth"]
        g_n = vectors["terminal_growth"]
        fcfe_0 = vectors["base_flow"]

        # 2. Vectorized Projection
        years = getattr(params.strategy, "projection_years", 5) or 5
        time_exponents = np.arange(1, years + 1)

        # Growth
        growth_factors = (1 + g_p1)[:, np.newaxis] ** time_exponents
        projected_flows = fcfe_0[:, np.newaxis] * growth_factors

        # 3. Discounting (at Ke)
        discount_factors = 1.0 / ((1 + ke_vec)[:, np.newaxis] ** time_exponents)
        pv_explicit = np.sum(projected_flows * discount_factors, axis=1)

        # 4. Terminal Value
        final_flow = projected_flows[:, -1]
        denominator = np.maximum(ke_vec - g_n, 0.001)
        tv_nominal = final_flow * (1 + g_n) / denominator
        pv_tv = tv_nominal / ((1 + ke_vec) ** years)

        # 5. Total Equity Value
        # Equity = PV(FCFE) + Cash
        cash = params.common.capital.cash_and_equivalents or 0.0
        total_equity = pv_explicit + pv_tv + cash

        # 6. Intrinsic Value Per Share
        shares = params.common.capital.shares_outstanding or 1.0
        iv_per_share: np.ndarray = total_equity / shares

        return iv_per_share
