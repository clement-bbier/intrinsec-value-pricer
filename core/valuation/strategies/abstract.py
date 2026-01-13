"""
core/valuation/strategies/abstract.py

SOCLE ABSTRAIT — VERSION V8.2
Rôle : Moteur de calcul DCF avec détection de divergence et transparence totale.
Architecture : Audit-Grade avec respect de la souveraineté du zéro.
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
from core. models import (
    CalculationStep,
    CompanyFinancials,
    DCFParameters,
    DCFValuationResult,
    TerminalValueMethod,
    TraceHypothesis,
    ValuationResult,
)

# Import des constantes de texte pour i18n
from app.ui_components.ui_texts import (
    RegistryTexts,
    StrategyInterpretations,
    CalculationErrors,
    StrategySources
)

logger = logging.getLogger(__name__)


class ValuationStrategy(ABC):
    """Socle abstrait standardisé pour toutes les stratégies de valorisation."""

    def __init__(self, glass_box_enabled: bool = True):
        self.glass_box_enabled = glass_box_enabled
        self.calculation_trace: List[CalculationStep] = []

    # ==========================================================================
    # 1. INTERFACE PUBLIQUE
    # ==========================================================================

    @abstractmethod
    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> ValuationResult:
        """Exécute la stratégie de valorisation."""
        pass

    def add_step(
        self,
        step_key: str,
        result: float,
        numerical_substitution: str,
        label:  str = "",
        theoretical_formula: str = "",
        interpretation:  str = "",
        hypotheses:  Optional[List[TraceHypothesis]] = None
    ) -> None:
        """Enregistre une étape enrichie pour l'audit buy-side."""
        if not self.glass_box_enabled:
            return

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

    def verify_output_contract(self, result: ValuationResult) -> None:
        """Vérifie que le résultat respecte le contrat de sortie attendu."""
        contract = result.build_output_contract()
        if not contract.is_valid():
            raise CalculationError(
                CalculationErrors.CONTRACT_VIOLATION.format(cls=self.__class__.__name__)
            )

    # ==========================================================================
    # 2. MOTEUR DCF COMMUN (AUDIT-GRADE)
    # ==========================================================================

    def _run_dcf_math(
        self,
        base_flow: float,
        financials: CompanyFinancials,
        params: DCFParameters,
        wacc_override: Optional[float] = None
    ) -> DCFValuationResult:
        """
        Exécute le calcul DCF complet avec traçabilité Glass Box.
        """
        # A. WACC
        wacc, wacc_ctx = self._compute_wacc(financials, params, wacc_override)

        # B.  Projections FCF
        flows = self._compute_projections(base_flow, params)

        # C. Valeur Terminale
        tv, key_tv = self._compute_terminal_value(flows, wacc, params)

        # D. NPV et Enterprise Value
        factors, sum_pv, pv_tv, ev = self._compute_enterprise_value(flows, tv, wacc, params)

        # E.  Equity Bridge
        equity_val, bridge_components = self._compute_equity_bridge(ev, financials, params)

        # F. Valeur par action
        iv_share = self._compute_value_per_share(equity_val, bridge_components["shares"], financials)

        # G. Métriques d'audit
        audit_metrics = self._compute_audit_metrics(financials, pv_tv, ev)

        return DCFValuationResult(
            request=None,
            financials=financials,
            params=params,
            intrinsic_value_per_share=iv_share,
            market_price=financials.current_price,
            wacc=wacc,
            cost_of_equity=wacc_ctx.cost_of_equity if wacc_ctx else 0.0,
            cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax if wacc_ctx else 0.0,
            projected_fcfs=flows,
            discount_factors=factors,
            sum_discounted_fcf=sum_pv,
            terminal_value=tv,
            discounted_terminal_value=pv_tv,
            enterprise_value=ev,
            equity_value=equity_val,
            calculation_trace=self.calculation_trace,
            icr_observed=audit_metrics["icr"],
            capex_to_da_ratio=audit_metrics["capex_ratio"],
            terminal_value_weight=audit_metrics["tv_weight"],
            payout_ratio_observed=audit_metrics["payout"],
            leverage_observed=audit_metrics["leverage"]
        )

    # ==========================================================================
    # 3. ÉTAPES DE CALCUL (PRIVATE)
    # ==========================================================================

    def _compute_wacc(
        self,
        financials:  CompanyFinancials,
        params: DCFParameters,
        wacc_override: Optional[float]
    ) -> tuple:
        """Calcule le WACC avec traçabilité."""
        if wacc_override is not None:
            wacc = wacc_override
            wacc_ctx = None
            sub_wacc = StrategySources.WACC_MANUAL.format(wacc=wacc)
        else:
            wacc_ctx = calculate_wacc(financials, params)
            wacc = wacc_ctx.wacc
            beta_used = params.manual_beta if params.manual_beta is not None else financials.beta

            sub_wacc = (
                f"{wacc_ctx. weight_equity:.2f} × [{params.risk_free_rate or 0:.4f} + "
                f"{beta_used:.2f} × ({params.market_risk_premium or 0:.4f})] + "
                f"{wacc_ctx.weight_debt:.2f} × [{params.cost_of_debt or 0:.4f} × "
                f"(1 - {params.tax_rate or 0:.2f})]"
            )

        self.add_step(
            step_key="WACC_CALC",
            label=RegistryTexts.DCF_WACC_L,
            theoretical_formula=r"WACC = w_e \cdot [R_f + \beta \cdot (ERP)] + w_d \cdot [K_d \cdot (1 - \tau)]",
            result=wacc,
            numerical_substitution=sub_wacc,
            interpretation=StrategyInterpretations.WACC.format(wacc=wacc)
        )

        return wacc, wacc_ctx

    def _compute_projections(
        self,
        base_flow: float,
        params:  DCFParameters
    ) -> List[float]:
        """Projette les flux de trésorerie."""
        flows = project_flows(
            base_flow,
            params.projection_years,
            params.fcf_growth_rate,
            params.perpetual_growth_rate,
            params.high_growth_years
        )

        self.add_step(
            step_key="FCF_PROJ",
            label=RegistryTexts.DCF_PROJ_L,
            theoretical_formula=r"\sum FCF_t",
            result=sum(flows),
            numerical_substitution=f"{base_flow: ,.0f} × (1 + {params.fcf_growth_rate or 0:.3f})^{params.projection_years}",
            interpretation=StrategyInterpretations.PROJ.format(
                years=params.projection_years,
                g=params.fcf_growth_rate or 0
            )
        )

        return flows

    def _compute_terminal_value(
        self,
        flows: List[float],
        wacc: float,
        params: DCFParameters
    ) -> tuple:
        """Calcule la valeur terminale avec contrôle de divergence."""
        if params.terminal_method == TerminalValueMethod.GORDON_GROWTH:
            p_growth = params.perpetual_growth_rate or 0.0

            if p_growth >= wacc:
                raise ModelDivergenceError(p_growth, wacc)

            tv = calculate_terminal_value_gordon(flows[-1], wacc, p_growth)
            key_tv = "TV_GORDON"
            sub_tv = f"({flows[-1]:,.0f} × {1 + p_growth:.3f}) / ({wacc:.4f} - {p_growth:.4f})"
            formula_tv = r"TV = \frac{FCF_n \cdot (1 + g)}{WACC - g}"
            label_tv = RegistryTexts.DCF_TV_GORDON_L
        else:
            exit_m = params.exit_multiple_value or 12.0
            tv = calculate_terminal_value_exit_multiple(flows[-1], exit_m)
            key_tv = "TV_MULTIPLE"
            sub_tv = f"{flows[-1]:,.0f} × {exit_m:.1f}"
            formula_tv = r"TV = EBITDA_n \cdot Exit\_Multiple"
            label_tv = RegistryTexts.DCF_TV_MULT_L

        self.add_step(
            step_key=key_tv,
            label=label_tv,
            theoretical_formula=formula_tv,
            result=tv,
            numerical_substitution=sub_tv,
            interpretation=StrategyInterpretations.TV
        )

        return tv, key_tv

    def _compute_enterprise_value(
        self,
        flows: List[float],
        tv: float,
        wacc: float,
        params: DCFParameters
    ) -> tuple:
        """Calcule la valeur d'entreprise (EV)."""
        factors = calculate_discount_factors(wacc, params.projection_years)
        sum_pv = sum(f * d for f, d in zip(flows, factors))
        pv_tv = tv * factors[-1]
        ev = sum_pv + pv_tv

        self.add_step(
            step_key="NPV_CALC",
            label=RegistryTexts.DCF_EV_L,
            theoretical_formula=r"EV = \sum \frac{FCF_t}{(1+r)^t} + \frac{TV}{(1+r)^n}",
            result=ev,
            numerical_substitution=f"{sum_pv:,.0f} + ({tv:,.0f} × {factors[-1]:.4f})",
            interpretation=StrategyInterpretations.EV
        )

        return factors, sum_pv, pv_tv, ev

    def _compute_equity_bridge(
        self,
        ev: float,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> tuple:
        """Calcule le passage EV → Equity Value."""
        debt = params.manual_total_debt if params.manual_total_debt is not None else financials.total_debt
        cash = params.manual_cash if params.manual_cash is not None else financials.cash_and_equivalents
        shares = params.manual_shares_outstanding if params.manual_shares_outstanding is not None else financials. shares_outstanding
        minorities = params.manual_minority_interests if params.manual_minority_interests is not None else financials.minority_interests
        pensions = params.manual_pension_provisions if params.manual_pension_provisions is not None else financials.pension_provisions

        equity_val = ev - debt + cash - minorities - pensions

        self.add_step(
            step_key="EQUITY_BRIDGE",
            label=RegistryTexts.DCF_BRIDGE_L,
            theoretical_formula=r"Equity = EV - Debt + Cash - Minority\_Interests - Provisions",
            result=equity_val,
            numerical_substitution=f"{ev:,.0f} - {debt:,.0f} + {cash:,.0f} - {minorities:,.0f} - {pensions:,.0f}",
            interpretation=StrategyInterpretations.BRIDGE
        )

        bridge_components = {
            "debt": debt,
            "cash":  cash,
            "shares": shares,
            "minorities":  minorities,
            "pensions":  pensions
        }

        return equity_val, bridge_components

    def _compute_value_per_share(
        self,
        equity_val: float,
        shares: float,
        financials:  CompanyFinancials
    ) -> float:
        """Calcule la valeur intrinsèque par action."""
        if shares <= 0:
            raise CalculationError(CalculationErrors.INVALID_SHARES)

        iv_share = equity_val / shares

        self.add_step(
            step_key="VALUE_PER_SHARE",
            label=RegistryTexts.DCF_IV_L,
            theoretical_formula=r"Price = \frac{Equity\_Value}{Shares\_Outstanding}",
            result=iv_share,
            numerical_substitution=f"{equity_val: ,.0f} / {shares:,.0f}",
            interpretation=StrategyInterpretations.IV.format(ticker=financials.ticker)
        )

        return iv_share

    def _compute_audit_metrics(
        self,
        financials: CompanyFinancials,
        pv_tv: float,
        ev:  float
    ) -> dict:
        """Calcule les métriques d'audit pour injection dans le résultat."""
        # ICR (Interest Coverage Ratio)
        icr = None
        if financials.interest_expense and financials.interest_expense > 0:
            icr = financials.ebit_ttm / financials.interest_expense

        # Capex / D&A ratio
        capex_ratio = None
        if financials.capex and financials.depreciation_and_amortization:
            capex_ratio = abs(financials.capex) / financials.depreciation_and_amortization

        # Terminal Value weight
        tv_weight = pv_tv / ev if ev > 0 else None

        # Payout ratio
        payout = None
        if financials.net_income_ttm and financials.net_income_ttm > 0:
            payout = financials.dividends_total_calculated / financials.net_income_ttm

        # Leverage
        leverage = None
        if financials.ebit_ttm and financials.ebit_ttm > 0:
            leverage = financials.total_debt / financials.ebit_ttm

        return {
            "icr": icr,
            "capex_ratio":  capex_ratio,
            "tv_weight": tv_weight,
            "payout": payout,
            "leverage": leverage
        }