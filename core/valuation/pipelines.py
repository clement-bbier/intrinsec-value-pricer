"""
core/valuation/pipelines.py
PIPELINE DE CALCUL UNIFIÉ (DRY ARCHITECTURE) — VERSION V1.0
Rôle : Moteur universel pour les modèles DCF (FCFF).
Architecture : Orchestration WACC -> Projections -> TV -> NPV -> Bridge.
Standards : SOLID, Pydantic, Glass Box, i18n.
"""

from __future__ import annotations
import logging
from typing import List, Optional, Dict, Any

from core.models import (
    CalculationStep, CompanyFinancials, DCFParameters,
    DCFValuationResult, TerminalValueMethod, TraceHypothesis
)
from core.computation.financial_math import (
    calculate_discount_factors,
    calculate_terminal_value_exit_multiple,
    calculate_terminal_value_gordon,
    calculate_wacc,
)
from core.computation.growth import FlowProjector, ProjectionOutput
from core.exceptions import CalculationError, ModelDivergenceError
from app.ui_components.ui_texts import (
    RegistryTexts, StrategyInterpretations, CalculationErrors, StrategySources, KPITexts
)

logger = logging.getLogger(__name__)


class DCFCalculationPipeline:
    """
    Pipeline de calcul standardisé pour toutes les variantes DCF.
    Élimine la duplication de code entre les stratégies Standard, Fundamental et Growth.
    """

    def __init__(self, projector: FlowProjector, glass_box_enabled: bool = True):
        self.projector = projector
        self.glass_box_enabled = glass_box_enabled
        self.calculation_trace: List[CalculationStep] = []

    def run(
            self,
            base_value: float,
            financials: CompanyFinancials,
            params: DCFParameters,
            wacc_override: Optional[float] = None
    ) -> DCFValuationResult:
        """Exécute la séquence complète de valorisation DCF."""

        # 1. Calcul du Coût du Capital (WACC)
        wacc, wacc_ctx = self._compute_wacc(financials, params, wacc_override)

        # 2. Phase de Projection (via le Projecteur injecté)
        proj_output = self.projector.project(base_value, financials, params)
        self._add_projection_step(proj_output)
        flows = proj_output.flows

        # 3. Valeur Terminale (TV)
        tv, key_tv = self._compute_terminal_value(flows, wacc, params)

        # 4. Valeur d'Entreprise (NPV / EV)
        factors, sum_pv, pv_tv, ev = self._compute_enterprise_value(flows, tv, wacc, params)

        # 5. Equity Bridge (EV -> Valeur des Fonds Propres)
        equity_val, bridge = self._compute_equity_bridge(ev, financials, params)

        # 6. Valeur Intrinsèque par Action
        iv_share = self._compute_value_per_share(equity_val, bridge["shares"], financials)

        # 7. Collecte des métriques pour l'audit institutionnel
        audit_metrics = self._extract_audit_metrics(financials, pv_tv, ev)

        return DCFValuationResult(
            request=None,
            financials=financials,
            params=params,
            intrinsic_value_per_share=iv_share,
            market_price=financials.current_price,
            wacc=wacc,
            cost_of_equity=wacc_ctx.cost_of_equity,
            cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax,
            projected_fcfs=flows,
            discount_factors=factors,
            sum_discounted_fcf=sum_pv,
            terminal_value=tv,
            discounted_terminal_value=pv_tv,
            enterprise_value=ev,
            equity_value=equity_val,
            calculation_trace=self.calculation_trace,
            # Métriques d'audit requises par infra/auditing/auditors.py
            icr_observed=audit_metrics["icr"],
            capex_to_da_ratio=audit_metrics["capex_ratio"],
            terminal_value_weight=audit_metrics["tv_weight"],
            payout_ratio_observed=audit_metrics["payout"],
            leverage_observed=audit_metrics["leverage"]
        )

    # ==========================================================================
    # ÉTAPES DE CALCUL (LOGIQUE GLASS BOX & I18N)
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

    def _compute_wacc(self, financials, params, wacc_override) -> tuple:
        r = params.rates
        wacc_ctx = calculate_wacc(financials, params)
        wacc = wacc_override if wacc_override is not None else wacc_ctx.wacc
        beta_used = r.manual_beta if r.manual_beta is not None else financials.beta

        sub_wacc = (f"{wacc_ctx.weight_equity:.2f} × [{r.risk_free_rate or 0:.4f} + "
                    f"{beta_used:.2f} × ({r.market_risk_premium or 0:.4f})] + "
                    f"{wacc_ctx.weight_debt:.2f} × [{r.cost_of_debt or 0:.4f} × (1 - {r.tax_rate or 0:.2f})]")

        self._add_step("WACC_CALC", wacc, sub_wacc, RegistryTexts.DCF_WACC_L, r"WACC",
                       StrategyInterpretations.WACC.format(wacc=wacc))
        return wacc, wacc_ctx

    def _add_projection_step(self, output: ProjectionOutput) -> None:
        """Intègre le rendu du projecteur (Simple ou Convergence) dans la trace."""
        self._add_step(
            step_key="FCF_PROJ",
            result=sum(output.flows),
            numerical_substitution=output.numerical_substitution,
            label=output.method_label,
            theoretical_formula=output.theoretical_formula,
            interpretation=output.interpretation
        )

    def _compute_terminal_value(self, flows, wacc, params) -> tuple:
        g = params.growth
        if g.terminal_method == TerminalValueMethod.GORDON_GROWTH:
            p_growth = g.perpetual_growth_rate or 0.0
            if p_growth >= wacc:
                raise ModelDivergenceError(p_growth, wacc)
            tv = calculate_terminal_value_gordon(flows[-1], wacc, p_growth)
            key_tv, sub_tv, label_tv = "TV_GORDON", f"({flows[-1]:,.0f} × {1 + p_growth:.3f}) / ({wacc:.4f} - {p_growth:.4f})", RegistryTexts.DCF_TV_GORDON_L
        else:
            exit_m = g.exit_multiple_value or 12.0
            tv = calculate_terminal_value_exit_multiple(flows[-1], exit_m)
            key_tv, sub_tv, label_tv = "TV_MULTIPLE", f"{flows[-1]:,.0f} × {exit_m:.1f}", RegistryTexts.DCF_TV_MULT_L

        self._add_step(key_tv, tv, sub_tv, label_tv, interpretation=StrategyInterpretations.TV)
        return tv, key_tv

    def _compute_enterprise_value(self, flows, tv, wacc, params) -> tuple:
        factors = calculate_discount_factors(wacc, params.growth.projection_years)
        sum_pv, pv_tv = sum(f * d for f, d in zip(flows, factors)), tv * factors[-1]
        ev = sum_pv + pv_tv
        self._add_step("NPV_CALC", ev, f"{sum_pv:,.0f} + ({tv:,.0f} × {factors[-1]:.4f})", RegistryTexts.DCF_EV_L,
                       interpretation=StrategyInterpretations.EV)
        return factors, sum_pv, pv_tv, ev

    def _compute_equity_bridge(self, ev: float, financials: CompanyFinancials, params: DCFParameters) -> tuple:
        g = params.growth
        debt = g.manual_total_debt if g.manual_total_debt is not None else financials.total_debt
        cash = g.manual_cash if g.manual_cash is not None else financials.cash_and_equivalents
        shares = g.manual_shares_outstanding if g.manual_shares_outstanding is not None else financials.shares_outstanding
        minorities = g.manual_minority_interests if g.manual_minority_interests is not None else financials.minority_interests
        pensions = g.manual_pension_provisions if g.manual_pension_provisions is not None else financials.pension_provisions

        equity_val = ev - debt + cash - minorities - pensions

        self._add_step(
            step_key="EQUITY_BRIDGE",
            label=RegistryTexts.DCF_BRIDGE_L,
            theoretical_formula=r"Equity = EV - Debt + Cash - Minorities - Provisions",
            result=equity_val,
            numerical_substitution=f"{ev:,.0f} - {debt:,.0f} + {cash:,.0f} - {minorities:,.0f} - {pensions:,.0f}",
            interpretation=StrategyInterpretations.BRIDGE
        )

        return equity_val, {"shares": shares}

    def _compute_value_per_share(self, equity_val, shares, financials) -> float:
        if shares <= 0:
            raise CalculationError(CalculationErrors.INVALID_SHARES)
        iv_share = equity_val / shares
        self._add_step("VALUE_PER_SHARE", iv_share, f"{equity_val:,.0f} / {shares:,.0f}", RegistryTexts.DCF_IV_L,
                       interpretation=StrategyInterpretations.IV.format(ticker=financials.ticker))
        return iv_share

    def _extract_audit_metrics(self, financials: CompanyFinancials, pv_tv: float, ev: float) -> dict:
        """Extrait les ratios nécessaires au moteur d'audit."""
        icr = financials.ebit_ttm / financials.interest_expense if financials.interest_expense > 0 and financials.ebit_ttm is not None else None
        capex_ratio = abs(
            financials.capex / financials.depreciation_and_amortization) if financials.capex and financials.depreciation_and_amortization else None
        tv_weight = (pv_tv / ev) if ev > 0 else None
        payout = financials.dividends_total_calculated / financials.net_income_ttm if financials.net_income_ttm and financials.net_income_ttm > 0 else None
        leverage = financials.total_debt / financials.ebit_ttm if financials.ebit_ttm and financials.ebit_ttm > 0 else None

        return {
            "icr": icr, "capex_ratio": capex_ratio, "tv_weight": tv_weight,
            "payout": payout, "leverage": leverage
        }