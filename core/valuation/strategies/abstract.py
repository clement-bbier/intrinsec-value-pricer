"""
core/valuation/strategies/abstract.py

SOCLE ABSTRAIT — VERSION V9.0 (Segmenté & i18n Secured)
Rôle : Moteur de calcul DCF avec transparence totale via segments Rates & Growth.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from core.computation.financial_math import (
    calculate_discount_factors,
    calculate_terminal_value_exit_multiple,
    calculate_terminal_value_gordon,
    calculate_wacc,
)
from core.computation.growth import project_flows
from core.exceptions import CalculationError, ModelDivergenceError
from core.models import (
    CalculationStep, CompanyFinancials, DCFParameters,
    DCFValuationResult, TerminalValueMethod, TraceHypothesis, ValuationResult
)
from app.ui_components.ui_texts import (
    RegistryTexts, StrategyInterpretations, CalculationErrors, StrategySources
)

logger = logging.getLogger(__name__)

class ValuationStrategy(ABC):
    def __init__(self, glass_box_enabled: bool = True):
        self.glass_box_enabled = glass_box_enabled
        self.calculation_trace: List[CalculationStep] = []

    @abstractmethod
    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
        pass

    def add_step(self, step_key: str, result: float, numerical_substitution: str,
                 label: str = "", theoretical_formula: str = "", interpretation: str = "",
                 hypotheses: Optional[List[TraceHypothesis]] = None) -> None:
        if not self.glass_box_enabled: return
        self.calculation_trace.append(CalculationStep(
            step_id=len(self.calculation_trace) + 1, step_key=step_key,
            label=label or step_key, theoretical_formula=theoretical_formula,
            hypotheses=hypotheses or [], numerical_substitution=numerical_substitution,
            result=result, interpretation=interpretation
        ))
    def verify_output_contract(self, result: ValuationResult) -> None:
        contract = result.build_output_contract()
        if not contract.is_valid():
            raise CalculationError(CalculationErrors.CONTRACT_VIOLATION.format(cls=self.__class__.__name__))

    # ==========================================================================
    # 2. MOTEUR DCF COMMUN (AUDIT-GRADE)
    # ==========================================================================

    def _run_dcf_math(self, base_flow: float, financials: CompanyFinancials,
                      params: DCFParameters, wacc_override: Optional[float] = None) -> DCFValuationResult:
        """Pipeline DCF standardisé (V9 Segmented)."""
        wacc, wacc_ctx = self._compute_wacc(financials, params, wacc_override)
        flows = self._compute_projections(base_flow, params)
        tv, key_tv = self._compute_terminal_value(flows, wacc, params)
        factors, sum_pv, pv_tv, ev = self._compute_enterprise_value(flows, tv, wacc, params)
        equity_val, bridge = self._compute_equity_bridge(ev, financials, params)
        iv_share = self._compute_value_per_share(equity_val, bridge["shares"], financials)
        audit_metrics = self._compute_audit_metrics(financials, pv_tv, ev)

        return DCFValuationResult(
            request=None, financials=financials, params=params, intrinsic_value_per_share=iv_share,
            market_price=financials.current_price, wacc=wacc,
            cost_of_equity=wacc_ctx.cost_of_equity if wacc_ctx else 0.0,
            cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax if wacc_ctx else 0.0,
            projected_fcfs=flows, discount_factors=factors, sum_discounted_fcf=sum_pv,
            terminal_value=tv, discounted_terminal_value=pv_tv, enterprise_value=ev,
            equity_value=equity_val, calculation_trace=self.calculation_trace,
            icr_observed=audit_metrics["icr"], capex_to_da_ratio=audit_metrics["capex_ratio"],
            terminal_value_weight=audit_metrics["tv_weight"], payout_ratio_observed=audit_metrics["payout"],
            leverage_observed=audit_metrics["leverage"]
        )

    # ==========================================================================
    # 3. ÉTAPES DE CALCUL (PRIVATE)
    # ==========================================================================

    def _compute_wacc(self, financials, params, wacc_override) -> tuple:
        r = params.rates
        wacc_ctx = calculate_wacc(financials, params)
        wacc = wacc_override if wacc_override is not None else wacc_ctx.wacc
        beta_used = r.manual_beta if r.manual_beta is not None else financials.beta

        sub_wacc = (f"{wacc_ctx.weight_equity:.2f} × [{r.risk_free_rate or 0:.4f} + "
                    f"{beta_used:.2f} × ({r.market_risk_premium or 0:.4f})] + "
                    f"{wacc_ctx.weight_debt:.2f} × [{r.cost_of_debt or 0:.4f} × (1 - {r.tax_rate or 0:.2f})]")

        self.add_step("WACC_CALC", wacc, sub_wacc, RegistryTexts.DCF_WACC_L, r"WACC",
                      StrategyInterpretations.WACC.format(wacc=wacc))
        return wacc, wacc_ctx

    def _compute_projections(self, base_flow, params) -> List[float]:
        g = params.growth
        flows = project_flows(base_flow, g.projection_years, g.fcf_growth_rate, g.perpetual_growth_rate, g.high_growth_years)
        self.add_step("FCF_PROJ", sum(flows), f"{base_flow:,.0f} × (1 + {g.fcf_growth_rate or 0:.3f})^{g.projection_years}",
                      RegistryTexts.DCF_PROJ_L, interpretation=StrategyInterpretations.PROJ.format(years=g.projection_years, g=g.fcf_growth_rate or 0))
        return flows

    def _compute_terminal_value(self, flows, wacc, params) -> tuple:
        g = params.growth
        if g.terminal_method == TerminalValueMethod.GORDON_GROWTH:
            p_growth = g.perpetual_growth_rate or 0.0
            if p_growth >= wacc: raise ModelDivergenceError(p_growth, wacc)
            tv = calculate_terminal_value_gordon(flows[-1], wacc, p_growth)
            key_tv, sub_tv, label_tv = "TV_GORDON", f"({flows[-1]:,.0f} × {1+p_growth:.3f}) / ({wacc:.4f} - {p_growth:.4f})", RegistryTexts.DCF_TV_GORDON_L
        else:
            exit_m = g.exit_multiple_value or 12.0
            tv = calculate_terminal_value_exit_multiple(flows[-1], exit_m)
            key_tv, sub_tv, label_tv = "TV_MULTIPLE", f"{flows[-1]:,.0f} × {exit_m:.1f}", RegistryTexts.DCF_TV_MULT_L
        self.add_step(key_tv, tv, sub_tv, label_tv, interpretation=StrategyInterpretations.TV)
        return tv, key_tv

    def _compute_enterprise_value(self, flows, tv, wacc, params) -> tuple:
        factors = calculate_discount_factors(wacc, params.growth.projection_years)
        sum_pv, pv_tv = sum(f * d for f, d in zip(flows, factors)), tv * factors[-1]
        ev = sum_pv + pv_tv
        self.add_step("NPV_CALC", ev, f"{sum_pv:,.0f} + ({tv:,.0f} × {factors[-1]:.4f})", RegistryTexts.DCF_EV_L, interpretation=StrategyInterpretations.EV)
        return factors, sum_pv, pv_tv, ev

    def _compute_equity_bridge(
            self,
            ev: float,
            financials: CompanyFinancials,
            params: DCFParameters
    ) -> tuple:
        """Calcule le passage EV → Equity Value via le segment growth (V9 Secured)."""
        g = params.growth

        debt = g.manual_total_debt if g.manual_total_debt is not None else financials.total_debt
        cash = g.manual_cash if g.manual_cash is not None else financials.cash_and_equivalents
        shares = g.manual_shares_outstanding if g.manual_shares_outstanding is not None else financials.shares_outstanding
        minorities = g.manual_minority_interests if g.manual_minority_interests is not None else financials.minority_interests
        pensions = g.manual_pension_provisions if g.manual_pension_provisions is not None else financials.pension_provisions

        equity_val = ev - debt + cash - minorities - pensions

        self.add_step(
            step_key="EQUITY_BRIDGE",
            label=RegistryTexts.DCF_BRIDGE_L,
            theoretical_formula=r"Equity = EV - Debt + Cash - Minorities - Provisions",
            result=equity_val,
            numerical_substitution=f"{ev:,.0f} - {debt:,.0f} + {cash:,.0f} - {minorities:,.0f} - {pensions:,.0f}",
            interpretation=StrategyInterpretations.BRIDGE
        )

        # RECOUPEMENT : On renvoie l'intégralité des composants pour la traçabilité
        bridge_components = {
            "debt": debt,
            "cash": cash,
            "shares": shares,
            "minorities": minorities,
            "pensions": pensions
        }

        return equity_val, bridge_components

    def _compute_value_per_share(self, equity_val, shares, financials) -> float:
        if shares <= 0: raise CalculationError(CalculationErrors.INVALID_SHARES)
        iv_share = equity_val / shares
        self.add_step("VALUE_PER_SHARE", iv_share, f"{equity_val:,.0f} / {shares:,.0f}", RegistryTexts.DCF_IV_L, interpretation=StrategyInterpretations.IV.format(ticker=financials.ticker))
        return iv_share

    def _compute_audit_metrics(self, financials: CompanyFinancials, pv_tv: float, ev: float) -> dict:
        """Calcule les métriques d'audit avec une sécurité totale contre les Nones."""
        # 1. ICR (Interest Coverage Ratio)
        icr = None
        if financials.ebit_ttm is not None and financials.interest_expense > 0:
            icr = financials.ebit_ttm / financials.interest_expense

        # 2. Capex / D&A ratio
        capex_ratio = None
        if financials.capex is not None and financials.depreciation_and_amortization:
            capex_ratio = abs(financials.capex) / financials.depreciation_and_amortization

        # 3. Terminal Value weight
        tv_weight = (pv_tv / ev) if (ev and ev > 0) else None

        # 4. Payout ratio
        payout = None
        if financials.net_income_ttm is not None and financials.net_income_ttm > 0:
            payout = financials.dividends_total_calculated / financials.net_income_ttm

        # 5. Levier (Debt / EBIT)
        leverage = None
        if financials.ebit_ttm is not None and financials.ebit_ttm > 0:
            leverage = financials.total_debt / financials.ebit_ttm

        return {
            "icr": icr,
            "capex_ratio": capex_ratio,
            "tv_weight": tv_weight,
            "payout": payout,
            "leverage": leverage
        }