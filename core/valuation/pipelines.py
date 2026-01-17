"""
core/valuation/pipelines.py
PIPELINE DE CALCUL UNIFIÉ (DRY ARCHITECTURE) — VERSION V1.2 (Sync V11.0)
Rôle : Moteur universel pour les modèles de flux (FCFF, FCFE, DDM).
Architecture : Orchestration bifurquée Firm-Level (EV) vs Equity-Level (IV).
Note : Alignement strict sur ui_glass_box_registry.py V11.0 pour éviter les KeyError.
"""

from __future__ import annotations
import logging
from typing import List, Optional, Dict, Any

from core.models import (
    CalculationStep, CompanyFinancials, DCFParameters,
    ValuationResult, DCFValuationResult, EquityDCFValuationResult,
    TerminalValueMethod, TraceHypothesis, ValuationMode
)
from core.computation.financial_math import (
    calculate_discount_factors,
    calculate_terminal_value_exit_multiple,
    calculate_terminal_value_gordon,
    calculate_wacc,
    calculate_cost_of_equity
)
from core.computation.growth import FlowProjector, ProjectionOutput
from core.exceptions import CalculationError, ModelDivergenceError
# DT-001/002: Import depuis core.i18n
from core.i18n import RegistryTexts, StrategyInterpretations, CalculationErrors, KPITexts

logger = logging.getLogger(__name__)


class DCFCalculationPipeline:
    """
    Pipeline de calcul standardisé.
    Les clés (step_key) sont alignées sur le registre Glass Box V11.0.
    """

    def __init__(self, projector: FlowProjector, mode: ValuationMode, glass_box_enabled: bool = True):
        self.projector = projector
        self.mode = mode
        self.glass_box_enabled = glass_box_enabled
        self.calculation_trace: List[CalculationStep] = []

    def run(
            self,
            base_value: float,
            financials: CompanyFinancials,
            params: DCFParameters,
            wacc_override: Optional[float] = None
    ) -> ValuationResult:
        """Exécute la séquence de valorisation avec synchronisation des clés registre."""

        # 1. Détermination du taux d'actualisation (Sync: WACC_CALC / KE_CALC)
        is_equity_level = self.mode.is_direct_equity

        if is_equity_level:
            discount_rate = calculate_cost_of_equity(financials, params)
            rate_key = "KE_CALC"
            rate_label = RegistryTexts.DCF_KE_L
            interp_rate = KPITexts.SUB_KE_LABEL.format(val=discount_rate)
            wacc_ctx = None
        else:
            wacc_breakdown = calculate_wacc(financials, params)
            discount_rate = wacc_override if wacc_override is not None else wacc_breakdown.wacc
            rate_key = "WACC_CALC"
            rate_label = RegistryTexts.DCF_WACC_L
            interp_rate = StrategyInterpretations.WACC.format(wacc=discount_rate)
            wacc_ctx = wacc_breakdown

        self._add_step(rate_key, discount_rate, interp_rate, label=rate_label, theoretical_formula=r"r")

        # 2. Phase de Projection (Sync: FCF_PROJ)
        proj_output = self.projector.project(base_value, financials, params)
        self._add_projection_step(proj_output)
        flows = proj_output.flows

        # 3. Valeur Terminale (Sync: TV_GORDON / TV_MULTIPLE)
        tv, key_tv = self._compute_terminal_value(flows, discount_rate, params)

        # 4. NPV (Sync: NPV_CALC)
        factors, sum_pv, pv_tv, final_value = self._compute_npv_logic(flows, tv, discount_rate, params)

        # 5. Equity Bridge (Sync: EQUITY_BRIDGE / EQUITY_DIRECT)
        equity_val, bridge_shares = self._compute_bridge_by_level(final_value, financials, params, is_equity_level)

        # 6. Valeur Intrinsèque par Action (Sync: VALUE_PER_SHARE)
        iv_share = self._compute_value_per_share(equity_val, bridge_shares, financials)

        # 7. Collecte des métriques d'audit
        audit_metrics = self._extract_audit_metrics(financials, pv_tv, final_value)

        # 8. Dispatch du contrat de résultat
        if is_equity_level:
            return EquityDCFValuationResult(
                financials=financials, params=params, intrinsic_value_per_share=iv_share,
                market_price=financials.current_price, cost_of_equity=discount_rate,
                projected_equity_flows=flows, equity_value=equity_val,
                discounted_terminal_value=pv_tv, calculation_trace=self.calculation_trace
            )

        return DCFValuationResult(
            financials=financials, params=params, intrinsic_value_per_share=iv_share,
            market_price=financials.current_price, wacc=discount_rate,
            cost_of_equity=wacc_ctx.cost_of_equity, cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax,
            projected_fcfs=flows, discount_factors=factors, sum_discounted_fcf=sum_pv,
            terminal_value=tv, discounted_terminal_value=pv_tv, enterprise_value=final_value,
            equity_value=equity_val, calculation_trace=self.calculation_trace,
            icr_observed=audit_metrics["icr"], capex_to_da_ratio=audit_metrics["capex_ratio"],
            terminal_value_weight=audit_metrics["tv_weight"], payout_ratio_observed=audit_metrics["payout"],
            leverage_observed=audit_metrics["leverage"]
        )

    # ==========================================================================
    # LOGIQUE DE TRACE (SYNC RÉGISTRE V11.0)
    # ==========================================================================

    def _add_step(self, step_key: str, result: float, numerical_substitution: str,
                  label: str = "", theoretical_formula: str = "", interpretation: str = "",
                  hypotheses: Optional[List[TraceHypothesis]] = None) -> None:
        if not self.glass_box_enabled: return
        self.calculation_trace.append(CalculationStep(
            step_id=len(self.calculation_trace) + 1,
            step_key=step_key,
            label=label or step_key,
            theoretical_formula=theoretical_formula,
            hypotheses=hypotheses or [],
            numerical_substitution=numerical_substitution,
            result=result,
            interpretation=interpretation
        ))

    def _add_projection_step(self, output: ProjectionOutput) -> None:
        """Utilise la clé FCF_PROJ synchronisée."""
        self._add_step(
            step_key="FCF_PROJ",
            result=sum(output.flows),
            numerical_substitution=output.numerical_substitution,
            label=output.method_label,
            theoretical_formula=output.theoretical_formula,
            interpretation=output.interpretation
        )

    def _compute_terminal_value(self, flows, discount_rate, params) -> tuple:
        """Bifurcation TV_GORDON ou TV_MULTIPLE."""
        g = params.growth
        if g.terminal_method == TerminalValueMethod.GORDON_GROWTH:
            p_growth = g.perpetual_growth_rate or 0.0
            if p_growth >= discount_rate:
                raise ModelDivergenceError(p_growth, discount_rate)
            tv = calculate_terminal_value_gordon(flows[-1], discount_rate, p_growth)
            key_tv = "TV_GORDON"
            sub_tv = f"({flows[-1]:,.0f} × {1 + p_growth:.3f}) / ({discount_rate:.4f} - {p_growth:.4f})"
            label_tv = RegistryTexts.DCF_TV_GORDON_L
        else:
            exit_m = g.exit_multiple_value or 12.0
            tv = calculate_terminal_value_exit_multiple(flows[-1], exit_m)
            key_tv = "TV_MULTIPLE"
            sub_tv = f"{flows[-1]:,.0f} × {exit_m:.1f}"
            label_tv = RegistryTexts.DCF_TV_MULT_L

        self._add_step(key_tv, tv, sub_tv, label_tv, interpretation=StrategyInterpretations.TV)
        return tv, key_tv

    def _compute_npv_logic(self, flows, tv, rate, params) -> tuple:
        """Actualisation des flux (Sync: NPV_CALC)."""
        factors = calculate_discount_factors(rate, params.growth.projection_years)
        sum_pv = sum(f * d for f, d in zip(flows, factors))
        pv_tv = tv * factors[-1]
        final_value = sum_pv + pv_tv

        # Distinction EV (Entity) vs Total Equity (Direct)
        label = RegistryTexts.DCF_EV_L if not self.mode.is_direct_equity else "Total Equity Value"
        self._add_step("NPV_CALC", final_value, f"{sum_pv:,.0f} + {pv_tv:,.0f}", label=label, theoretical_formula=r"PV = \sum PV(Flows) + PV(TV)")
        return factors, sum_pv, pv_tv, final_value

    def _compute_bridge_by_level(self, val: float, financials: CompanyFinancials, params: DCFParameters, is_equity_level: bool) -> tuple:
        """Bifurcation EQUITY_BRIDGE ou EQUITY_DIRECT."""
        g = params.growth
        shares = g.manual_shares_outstanding if g.manual_shares_outstanding is not None else financials.shares_outstanding

        if is_equity_level:
            self._add_step("EQUITY_DIRECT", val, KPITexts.SUB_EQUITY_NPV.format(val=val), label=RegistryTexts.DCF_BRIDGE_L)
            return val, shares

        debt = g.manual_total_debt if g.manual_total_debt is not None else financials.total_debt
        cash = g.manual_cash if g.manual_cash is not None else financials.cash_and_equivalents
        minorities = g.manual_minority_interests if g.manual_minority_interests is not None else financials.minority_interests
        pensions = g.manual_pension_provisions if g.manual_pension_provisions is not None else financials.pension_provisions

        equity_val = val - debt + cash - minorities - pensions

        self._add_step(
            step_key="EQUITY_BRIDGE",
            label=RegistryTexts.DCF_BRIDGE_L,
            theoretical_formula=r"Equity = EV - Debt + Cash - Min - Prov",
            result=equity_val,
            numerical_substitution=f"{val:,.0f} - {debt:,.0f} + {cash:,.0f} - {minorities:,.0f} - {pensions:,.0f}",
            interpretation=StrategyInterpretations.BRIDGE
        )
        return equity_val, shares

    def _compute_value_per_share(self, equity_val, shares, financials) -> float:
        """Etape finale (Sync: VALUE_PER_SHARE)."""
        if shares <= 0:
            raise CalculationError(CalculationErrors.INVALID_SHARES)
        iv_share = equity_val / shares
        self._add_step("VALUE_PER_SHARE", iv_share, f"{equity_val:,.0f} / {shares:,.0f}", RegistryTexts.DCF_IV_L,
                       interpretation=StrategyInterpretations.IV.format(ticker=financials.ticker))
        return iv_share

    def _extract_audit_metrics(self, financials: CompanyFinancials, pv_tv: float, ev: float) -> dict:
        icr = financials.ebit_ttm / financials.interest_expense if financials.interest_expense > 0 and financials.ebit_ttm is not None else None
        capex_ratio = abs(financials.capex / (financials.depreciation_and_amortization or 1.0)) if financials.capex else None
        tv_weight = (pv_tv / ev) if ev > 0 else None
        payout = financials.dividends_total_calculated / financials.net_income_ttm if financials.net_income_ttm and financials.net_income_ttm > 0 else None
        leverage = financials.total_debt / financials.ebit_ttm if financials.ebit_ttm and financials.ebit_ttm > 0 else None

        return {"icr": icr, "capex_ratio": capex_ratio, "tv_weight": tv_weight, "payout": payout, "leverage": leverage}