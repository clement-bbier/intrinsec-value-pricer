"""
src/valuation/strategies/fundamental_fcff.py

FUNDAMENTAL DCF STRATEGY (NORMALIZED)
=====================================
Role: Normalized DCF Engine for cyclical or volatile firms.
Logic: Uses a smoothed 'Cycle-Average' FCF as anchor instead of TTM.
       Useful when current TTM flows are distressed or unrepresentative.
Architecture: IValuationRunner implementation.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
"""

from __future__ import annotations

from typing import cast

import numpy as np

from src.computation.financial_math import calculate_discount_factors

# Config & i18n
from src.i18n import RegistryTexts, StrategyFormulas, StrategyInterpretations, StrategySources
from src.models.company import Company
from src.models.enums import ValuationMethodology, VariableSource
from src.models.glass_box import CalculationStep, VariableInfo
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.strategies import FCFFNormalizedParameters
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedCapital, ResolvedRates
from src.models.results.options import ExtensionBundleResults
from src.models.results.strategies import FCFFNormalizedResults

# Models Results (Nested Architecture)
from src.models.valuation import ValuationRequest, ValuationResult

# Libraries (DRY Logic)
from src.valuation.library.common import CommonLibrary
from src.valuation.library.dcf import DCFLibrary
from src.valuation.strategies.interface import IValuationRunner


class FundamentalFCFFStrategy(IValuationRunner):
    """
    Normalized FCFF Strategy.
    Anchors valuation on a 'Cycle-Mid' FCF rather than TTM.
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
        Executes the Normalized DCF sequence.
        """
        # Type narrowing for mypy
        strategy_params = cast(FCFFNormalizedParameters, params.strategy)

        steps: list[CalculationStep] = []

        # --- STEP 1: WACC & Rates ---
        wacc, step_wacc = CommonLibrary.resolve_discount_rate(
            financials=financials, params=params, use_cost_of_equity_only=False
        )
        if self._glass_box:
            steps.append(step_wacc)

        # --- STEP 2: Normalized Anchor Selection ---
        user_norm_fcf = strategy_params.fcf_norm
        fcf_anchor = user_norm_fcf if user_norm_fcf is not None else (getattr(financials, "fcf_ttm", None) or 0.0)

        # Trace the Anchor Selection
        if self._glass_box:
            steps.append(
                CalculationStep(
                    step_key="FCF_NORM_ANCHOR",
                    label=RegistryTexts.DCF_FCF_NORM_L,
                    theoretical_formula=StrategyFormulas.FCF_NORMALIZED,
                    actual_calculation=f"Selected Anchor: {fcf_anchor:,.2f}",
                    result=fcf_anchor,
                    interpretation=StrategyInterpretations.FUND_NORM,
                    source=StrategySources.MANUAL_OVERRIDE if user_norm_fcf else StrategySources.YAHOO_FUNDAMENTAL,
                    variables_map={
                        "FCF_norm": VariableInfo(
                            symbol="FCF_norm",
                            value=fcf_anchor,
                            source=VariableSource.MANUAL_OVERRIDE if user_norm_fcf else VariableSource.YAHOO_FINANCE,
                            description="Normalized Free Cash Flow",
                        )
                    },
                )
            )

        # --- STEP 2.5: Compute Growth from Value Drivers (Damodaran) ---
        roic = strategy_params.roic
        reinvestment_rate = strategy_params.reinvestment_rate
        user_growth = strategy_params.growth_rate
        
        # Calculate g from value drivers if both ROIC and reinvestment rate are provided
        if roic is not None and reinvestment_rate is not None:
            g_derived = roic * reinvestment_rate
            
            # Consistency check if user also provided manual growth override
            if user_growth is not None:
                # Allow 1% tolerance for rounding differences
                tolerance = 0.01
                diff = abs(g_derived - user_growth)
                if diff > tolerance:
                    # Log warning but continue (user override takes precedence)
                    if self._glass_box:
                        steps.append(
                            CalculationStep(
                                step_key="GROWTH_CONSISTENCY_CHECK",
                                label="Vérification de Cohérence (g)",
                                theoretical_formula=r"g = ROIC \times \text{Taux de Réinvestissement}",
                                actual_calculation=f"g_derived={g_derived:.2%} vs g_override={user_growth:.2%} (Δ={diff:.2%})",
                                result=user_growth,
                                interpretation=f"AVERTISSEMENT: Écart détecté entre g calculé ({g_derived:.2%}) et g manuel ({user_growth:.2%}). Utilisation de g manuel.",
                                source=StrategySources.MANUAL_OVERRIDE,
                                variables_map={
                                    "ROIC": VariableInfo(symbol="ROIC", value=roic, formatted_value=f"{roic:.2%}", source=VariableSource.MANUAL_OVERRIDE, description="Return on Invested Capital"),
                                    "RR": VariableInfo(symbol="RR", value=reinvestment_rate, formatted_value=f"{reinvestment_rate:.2%}", source=VariableSource.MANUAL_OVERRIDE, description="Reinvestment Rate"),
                                    "g_derived": VariableInfo(symbol="g_calc", value=g_derived, formatted_value=f"{g_derived:.2%}", source=VariableSource.CALCULATED, description="Calculated Growth Rate"),
                                    "g_override": VariableInfo(symbol="g_override", value=user_growth, formatted_value=f"{user_growth:.2%}", source=VariableSource.MANUAL_OVERRIDE, description="Manual Growth Override"),
                                },
                            )
                        )
                # Use manual override if provided
                growth_to_use = user_growth
            else:
                # Use derived growth
                growth_to_use = g_derived
                
            # Trace the growth calculation
            if self._glass_box and user_growth is None:
                steps.append(
                    CalculationStep(
                        step_key="GROWTH_CALCULATION",
                        label="Calcul de la Croissance (Drivers de Valeur)",
                        theoretical_formula=r"g = ROIC \times \text{Taux de Réinvestissement}",
                        actual_calculation=f"g = {roic:.2%} × {reinvestment_rate:.2%} = {g_derived:.2%}",
                        result=g_derived,
                        interpretation=f"Croissance dérivée des fondamentaux: ROIC de {roic:.1%} multiplié par taux de réinvestissement de {reinvestment_rate:.1%}",
                        source=StrategySources.COMPUTED_VALUE_DRIVERS,
                        variables_map={
                            "ROIC": VariableInfo(symbol="ROIC", value=roic, formatted_value=f"{roic:.2%}", source=VariableSource.MANUAL_OVERRIDE, description="Return on Invested Capital"),
                            "RR": VariableInfo(symbol="RR", value=reinvestment_rate, formatted_value=f"{reinvestment_rate:.2%}", source=VariableSource.MANUAL_OVERRIDE, description="Reinvestment Rate"),
                            "g": VariableInfo(symbol="g", value=g_derived, formatted_value=f"{g_derived:.2%}", source=VariableSource.CALCULATED, description="Derived Growth Rate"),
                        },
                    )
                )
            
            # Temporarily override growth_rate for projection
            strategy_params.growth_rate = growth_to_use

        # --- STEP 3: FCF Projection ---
        manual_vector = getattr(params.strategy, "manual_growth_vector", None)

        if manual_vector and len(manual_vector) > 0:
            flows, step_proj = DCFLibrary.project_flows_manual(fcf_anchor, manual_vector)
        else:
            flows, step_proj = DCFLibrary.project_flows_simple(fcf_anchor, params)

        if self._glass_box:
            steps.append(step_proj)

        # --- STEP 4: Terminal Value ---
        final_flow = flows[-1] if flows else fcf_anchor
        tv, step_tv = DCFLibrary.compute_terminal_value(final_flow, wacc, params)
        if self._glass_box:
            steps.append(step_tv)

        # --- STEP 5: Discounting ---
        ev, step_ev = DCFLibrary.compute_discounting(flows, tv, wacc)
        if self._glass_box:
            steps.append(step_ev)

        # --- STEP 6: Equity Bridge ---
        equity_value, step_bridge = CommonLibrary.compute_equity_bridge(ev, params)
        if self._glass_box:
            steps.append(step_bridge)

        # --- STEP 7: Per Share ---
        iv_per_share, step_iv = DCFLibrary.compute_value_per_share(equity_value, params)
        if self._glass_box:
            steps.append(step_iv)

        # --- RESULT CONSTRUCTION ---
        ke_var = step_wacc.get_variable("Ke")
        kd_var = step_wacc.get_variable("Kd(1-t)")

        res_rates = ResolvedRates(
            cost_of_equity=ke_var.value if ke_var and self._glass_box else 0.0,
            cost_of_debt_after_tax=kd_var.value if kd_var and self._glass_box else 0.0,
            wacc=wacc,
        )

        shares = params.common.capital.shares_outstanding or 1.0
        res_capital = ResolvedCapital(
            market_cap=shares * (financials.current_price or 0.0),
            enterprise_value=ev,
            net_debt_resolved=(
                (params.common.capital.total_debt or 0.0) - (params.common.capital.cash_and_equivalents or 0.0)
            ),
            equity_value_total=equity_value,
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

        discount_factors = calculate_discount_factors(wacc, len(flows))
        pv_tv = tv * discount_factors[-1] if discount_factors else 0.0

        strategy_res = FCFFNormalizedResults(
            projected_flows=flows,
            discount_factors=discount_factors,
            terminal_value=tv,
            discounted_terminal_value=pv_tv,
            tv_weight_pct=(pv_tv / ev) if ev > 0 else 0.0,
            strategy_trace=[],
            normalized_fcf_used=fcf_anchor,
        )

        return ValuationResult(
            request=ValuationRequest(mode=ValuationMethodology.FCFF_NORMALIZED, parameters=params),
            results=Results(common=common_res, strategy=strategy_res, extensions=ExtensionBundleResults()),
        )

    @staticmethod
    def execute_stochastic(_financials: Company, params: Parameters, vectors: dict[str, np.ndarray]) -> np.ndarray:
        """
        High-Performance Vectorized Execution for Monte Carlo (Fundamental DCF).
        Identical math to Standard DCF, just using the shocked 'base_flow' which maps to Normalized FCF.
        """
        # 1. Unpack Vectors
        wacc = vectors["wacc"]
        g_p1 = vectors["growth"]
        g_n = vectors["terminal_growth"]
        fcf_0 = vectors["base_flow"]  # Represents the shocked Normalized FCF

        # 2. Vectorized Projection
        years = getattr(params.strategy, "projection_years", 5) or 5
        time_exponents = np.arange(1, years + 1)

        # Growth factors: (1+g)^t
        growth_factors = (1 + g_p1)[:, np.newaxis] ** time_exponents
        projected_flows = fcf_0[:, np.newaxis] * growth_factors

        # 3. Discounting
        discount_factors = 1.0 / ((1 + wacc)[:, np.newaxis] ** time_exponents)
        pv_explicit = np.sum(projected_flows * discount_factors, axis=1)

        # 4. Terminal Value
        final_flow = projected_flows[:, -1]
        denominator = np.maximum(wacc - g_n, 0.001)
        tv_nominal = final_flow * (1 + g_n) / denominator
        pv_tv = tv_nominal / ((1 + wacc) ** years)

        # 5. Equity Bridge
        ev = pv_explicit + pv_tv

        shares = params.common.capital.shares_outstanding or 1.0
        net_debt = (params.common.capital.total_debt or 0.0) - (params.common.capital.cash_and_equivalents or 0.0)

        equity_value = ev - net_debt
        iv_per_share: np.ndarray = equity_value / shares

        return iv_per_share
