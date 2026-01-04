"""
core/valuation/strategies/abstract.py
SOCLE ABSTRAIT V5.2 — RÉFÉRENTIEL D'AUDIT INSTITUTIONNEL
Rôle : Rigueur mathématique et traçabilité granulaire des flux (Standard CFA).
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    ValuationResult,
    DCFValuationResult,
    CalculationStep,
    TraceHypothesis,
    TerminalValueMethod
)
from core.computation.financial_math import (
    calculate_wacc,
    calculate_discount_factors,
    calculate_terminal_value_gordon,
    calculate_terminal_value_exit_multiple,
    calculate_equity_value_bridge
)
from core.computation.growth import project_flows

logger = logging.getLogger(__name__)

class ValuationStrategy(ABC):
    """Socle abstrait standardisé pour toutes les stratégies de valorisation."""

    def __init__(self, glass_box_enabled: bool = True):
        self.glass_box_enabled = glass_box_enabled
        self.calculation_trace: List[CalculationStep] = []

    def add_step(self, step_key: str, result: float, numerical_substitution: str,
                 hypotheses: List[TraceHypothesis] = None) -> None:
        """Enregistre une étape via une clé de registre pour lookup UI."""
        if not self.glass_box_enabled:
            return

        self.calculation_trace.append(CalculationStep(
            step_id=len(self.calculation_trace) + 1,
            label=step_key,
            hypotheses=hypotheses or [],
            numerical_substitution=numerical_substitution,
            result=result
        ))

    def verify_output_contract(self, result: ValuationResult) -> bool:
        """Indispensable pour la validation par le moteur d'audit."""
        if result is None: return False
        contract = result.build_output_contract()
        return contract.is_valid()

    @abstractmethod
    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
        pass

    # ==========================================================================
    # LOGIQUE MATHÉMATIQUE (AUDIT CFA READY)
    # ==========================================================================
    def _run_dcf_math(self, base_flow: float, financials: CompanyFinancials,
                      params: DCFParameters, wacc_override: Optional[float] = None) -> DCFValuationResult:

        # --- A. WACC (Structure de capital et CAPM) ---
        if wacc_override is not None:
            wacc = wacc_override
            wacc_ctx = None
            sub_wacc = f"WACC = {wacc:.4f} (Surcharge Analyste)"
        else:
            wacc_ctx = calculate_wacc(financials, params)
            wacc = wacc_ctx.wacc
            beta_used = params.manual_beta or financials.beta
            sub_wacc = (
                f"{wacc_ctx.weight_equity:.2f} × [{params.risk_free_rate:.4f} + {beta_used:.2f} × ({params.market_risk_premium:.4f})] + "
                f"{wacc_ctx.weight_debt:.2f} × [{params.cost_of_debt:.4f} × (1 - {params.tax_rate:.2f})]"
            )

        self.add_step(step_key="WACC_CALC", result=wacc, numerical_substitution=sub_wacc)

        # --- B. PROJECTIONS (Flux Final FCF_n) ---
        # Correction Audit : On montre le flux de l'année n, pas la somme cumulée.
        flows = project_flows(base_flow, params.projection_years, params.fcf_growth_rate,
                              params.perpetual_growth_rate, params.high_growth_years)

        self.add_step(
            step_key="FCF_PROJ",
            result=flows[-1], # On affiche FCF_5 (ex: 114 Md), pas la somme
            numerical_substitution=f"{base_flow:,.0f} × (1 + {params.fcf_growth_rate:.3f})^{params.projection_years}"
        )

        # --- C. VALEUR TERMINALE (TV) ---
        if params.terminal_method == TerminalValueMethod.GORDON_GROWTH:
            tv = calculate_terminal_value_gordon(flows[-1], wacc, params.perpetual_growth_rate)
            key_tv = "TV_GORDON"
            sub_tv = f"({flows[-1]:,.0f} × {1 + params.perpetual_growth_rate:.3f}) / ({wacc:.4f} - {params.perpetual_growth_rate:.3f})"
        else:
            tv = calculate_terminal_value_exit_multiple(flows[-1], params.exit_multiple_value or 12.0)
            key_tv = "TV_MULTIPLE"
            sub_tv = f"{flows[-1]:,.0f} × {params.exit_multiple_value:.1f}"

        self.add_step(step_key=key_tv, result=tv, numerical_substitution=sub_tv)

        # --- D. ACTUALISATION (Somme PV des flux + PV de la TV) ---
        # Correction Audit : Séparation pour garantir la cohérence temporelle.
        factors = calculate_discount_factors(wacc, params.projection_years)
        sum_pv_flows = sum(f * d for f, d in zip(flows, factors))
        pv_tv = tv * factors[-1]
        ev = sum_pv_flows + pv_tv

        # Nouvelle étape pour la somme des flux actualisés (Audit Requirement)
        self.add_step(
            step_key="NPV_SUM_FLOWS",
            result=sum_pv_flows,
            numerical_substitution=" + ".join([f"({f:,.0f} × {d:.4f})" for f, d in zip(flows[:2], factors[:2])]) + " + ..."
        )

        self.add_step(
            step_key="NPV_CALC",
            result=ev,
            numerical_substitution=f"{sum_pv_flows:,.0f} (Sum PV Flows) + ({tv:,.0f} × {factors[-1]:.4f}) (PV TV)"
        )

        # --- E. BRIDGE (EV -> Equity Value) ---
        debt = params.manual_total_debt if params.manual_total_debt is not None else financials.total_debt
        cash = params.manual_cash if params.manual_cash is not None else financials.cash_and_equivalents
        shares = params.manual_shares_outstanding if params.manual_shares_outstanding is not None else financials.shares_outstanding

        equity_val = calculate_equity_value_bridge(ev, debt, cash)
        if isinstance(equity_val, dict): equity_val = equity_val.get("equity_value", 0.0)

        self.add_step(
            step_key="EQUITY_BRIDGE",
            result=equity_val,
            numerical_substitution=f"{ev:,.0f} - {debt:,.0f} + {cash:,.0f}"
        )

        # --- F. VALEUR FINALE (Prix par action) ---
        if shares <= 0: raise CalculationError("Actions invalides.")
        iv_share = equity_val / shares

        self.add_step(
            step_key="VALUE_PER_SHARE",
            result=iv_share,
            numerical_substitution=f"{equity_val:,.0f} / {shares:,.0f}"
        )

        return DCFValuationResult(
            request=None, financials=financials, params=params,
            intrinsic_value_per_share=iv_share, market_price=financials.current_price,
            wacc=wacc, cost_of_equity=wacc_ctx.cost_of_equity if wacc_ctx else 0.0,
            cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax if wacc_ctx else 0.0,
            projected_fcfs=flows, discount_factors=factors,
            sum_discounted_fcf=sum_pv_flows, terminal_value=tv, discounted_terminal_value=pv_tv,
            enterprise_value=ev, equity_value=equity_val, calculation_trace=self.calculation_trace
        )