"""
core/valuation/strategies/abstract.py
SOCLE ABSTRAIT V6.8 — AUDIT-GRADE & MODEL RISK CONTROL
Rôle : Moteur de calcul DCF avec détection de divergence et transparence totale.
Note : Correction syntaxique et respect de la souveraineté du zéro.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from core.exceptions import CalculationError, ModelDivergenceError
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
    calculate_terminal_value_exit_multiple
)
from core.computation.growth import project_flows

logger = logging.getLogger(__name__)

class ValuationStrategy(ABC):
    """Socle abstrait standardisé pour toutes les stratégies de valorisation."""

    def __init__(self, glass_box_enabled: bool = True):
        self.glass_box_enabled = glass_box_enabled
        self.calculation_trace: List[CalculationStep] = []

    def add_step(self, step_key: str, result: float, numerical_substitution: str,
                 label: str = "", theoretical_formula: str = "",
                 interpretation: str = "", hypotheses: List[TraceHypothesis] = None) -> None:
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
                f"Le contrat de sortie n'est pas respecté pour {self.__class__.__name__}."
            )

    @abstractmethod
    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
        pass

    # ==========================================================================
    # LOGIQUE MATHÉMATIQUE (AUDIT-GRADE V6.8)
    # ==========================================================================
    def _run_dcf_math(self, base_flow: float, financials: CompanyFinancials,
                      params: DCFParameters, wacc_override: Optional[float] = None) -> DCFValuationResult:

        # --- A. WACC : Coût Moyen Pondéré du Capital ---
        if wacc_override is not None:
            wacc = wacc_override
            wacc_ctx = None
            sub_wacc = f"WACC = {wacc:.4f} (Manual Override)"
        else:
            wacc_ctx = calculate_wacc(financials, params)
            wacc = wacc_ctx.wacc

            # Respect de la souveraineté du 0.0 pour le Beta
            beta_used = params.manual_beta if params.manual_beta is not None else financials.beta

            sub_wacc = (
                f"{wacc_ctx.weight_equity:.2f} × [{params.risk_free_rate or 0:.4f} + {beta_used:.2f} × ({params.market_risk_premium or 0:.4f})] + "
                f"{wacc_ctx.weight_debt:.2f} × [{params.cost_of_debt or 0:.4f} × (1 - {params.tax_rate or 0:.2f})]"
            )

        self.add_step(
            step_key="WACC_CALC",
            label="Calcul du WACC",
            theoretical_formula=r"WACC = w_e \cdot [R_f + \beta \cdot (ERP)] + w_d \cdot [K_d \cdot (1 - \tau)]",
            result=wacc,
            numerical_substitution=sub_wacc,
            interpretation=f"Taux d'actualisation cible (WACC) de {wacc:.2%}, basé sur la structure de capital actuelle."
        )

        # --- B. PROJECTIONS : Flux de Trésorerie Disponibles ---
        flows = project_flows(base_flow, params.projection_years, params.fcf_growth_rate,
                              params.perpetual_growth_rate, params.high_growth_years)

        self.add_step(
            step_key="FCF_PROJ",
            label="Projections des Flux (Somme)",
            theoretical_formula=r"\sum FCF_t",
            result=sum(flows),
            numerical_substitution=f"{base_flow:,.0f} × (1 + {params.fcf_growth_rate or 0:.3f})^{params.projection_years}",
            interpretation=f"Projection sur {params.projection_years} ans à un taux de croissance annuel moyen de {params.fcf_growth_rate or 0:.2%}"
        )

        # --- C. VALEUR TERMINALE : Contrôle de Risque de Modèle ---
        if params.terminal_method == TerminalValueMethod.GORDON_GROWTH:
            p_growth = params.perpetual_growth_rate or 0.0
            if p_growth >= wacc:
                raise ModelDivergenceError(p_growth, wacc)

            tv = calculate_terminal_value_gordon(flows[-1], wacc, p_growth)
            key_tv = "TV_GORDON"
            sub_tv = f"({flows[-1]:,.0f} × {1 + p_growth:.3f}) / ({wacc:.4f} - {p_growth:.4f})"
            formula_tv = r"TV = \frac{FCF_n \cdot (1 + g)}{WACC - g}"
        else:
            exit_m = params.exit_multiple_value or 12.0
            tv = calculate_terminal_value_exit_multiple(flows[-1], exit_m)
            key_tv = "TV_MULTIPLE"
            sub_tv = f"{flows[-1]:,.0f} × {exit_m:.1f}"
            formula_tv = r"TV = EBITDA_n \cdot Exit\_Multiple"

        self.add_step(
            step_key=key_tv,
            label="Valeur Terminale (TV)",
            theoretical_formula=formula_tv,
            result=tv,
            numerical_substitution=sub_tv,
            interpretation="Estimation de la valeur de l'entreprise au-delà de la période explicite."
        )

        # --- D. NPV : Valeur Actuelle de l'Entreprise (EV) ---
        factors = calculate_discount_factors(wacc, params.projection_years)
        sum_pv = sum(f * d for f, d in zip(flows, factors))
        pv_tv = tv * factors[-1]
        ev = sum_pv + pv_tv

        self.add_step(
            step_key="NPV_CALC",
            label="Valeur d'Entreprise (Enterprise Value)",
            theoretical_formula=r"EV = \sum \frac{FCF_t}{(1+r)^t} + \frac{TV}{(1+r)^n}",
            result=ev,
            numerical_substitution=f"{sum_pv:,.0f} + ({tv:,.0f} × {factors[-1]:.4f})",
            interpretation="Valeur totale de l'outil de production actualisée."
        )

        # --- E. BRIDGE : Passage à la Valeur des Fonds Propres ---
        debt = params.manual_total_debt if params.manual_total_debt is not None else financials.total_debt
        cash = params.manual_cash if params.manual_cash is not None else financials.cash_and_equivalents
        shares = params.manual_shares_outstanding if params.manual_shares_outstanding is not None else financials.shares_outstanding
        minorities = params.manual_minority_interests if params.manual_minority_interests is not None else financials.minority_interests
        pensions = params.manual_pension_provisions if params.manual_pension_provisions is not None else financials.pension_provisions

        equity_val = ev - debt + cash - minorities - pensions

        self.add_step(
            step_key="EQUITY_BRIDGE",
            label="Pont de Valeur (Equity Bridge)",
            theoretical_formula=r"Equity = EV - Debt + Cash - Minority\_Interests - Provisions",
            result=equity_val,
            numerical_substitution=f"{ev:,.0f} - {debt:,.0f} + {cash:,.0f} - {minorities:,.0f} - {pensions:,.0f}",
            interpretation="Ajustement de la structure financière."
        )

        # --- F. VALEUR FINALE PAR ACTION ---
        if shares <= 0:
            raise CalculationError("Nombre d'actions en circulation invalide (<= 0).")
        iv_share = equity_val / shares

        self.add_step(
            step_key="VALUE_PER_SHARE",
            label="Valeur Intrinsèque par Action",
            theoretical_formula=r"Price = \frac{Equity\_Value}{Shares\_Outstanding}",
            result=iv_share,
            numerical_substitution=f"{equity_val:,.0f} / {shares:,.0f}",
            interpretation=f"Estimation de la valeur réelle d'une action pour {financials.ticker}."
        )

        # --- G. CALCUL DES MÉTRIQUES D'AUDIT (INJECTION) ---
        icr = financials.ebit_ttm / financials.interest_expense if financials.interest_expense > 0 else None

        capex_ratio = None
        if financials.capex and financials.depreciation_and_amortization:
            capex_ratio = abs(financials.capex) / financials.depreciation_and_amortization

        tv_weight = pv_tv / ev if ev > 0 else None

        # Utilisation de la nouvelle propriété calculée dans models.py
        payout = financials.dividends_total_calculated / financials.net_income_ttm if (
                    financials.net_income_ttm and financials.net_income_ttm > 0) else None

        leverage = financials.total_debt / financials.ebit_ttm if (
                    financials.ebit_ttm and financials.ebit_ttm > 0) else None

        return DCFValuationResult(
            request=None, financials=financials, params=params,
            intrinsic_value_per_share=iv_share, market_price=financials.current_price,
            wacc=wacc, cost_of_equity=wacc_ctx.cost_of_equity if wacc_ctx else 0.0,
            cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax if wacc_ctx else 0.0,
            projected_fcfs=flows, discount_factors=factors,
            sum_discounted_fcf=sum_pv, terminal_value=tv, discounted_terminal_value=pv_tv,
            enterprise_value=ev, equity_value=equity_val, calculation_trace=self.calculation_trace,
            icr_observed=icr, capex_to_da_ratio=capex_ratio, terminal_value_weight=tv_weight,
            payout_ratio_observed=payout, leverage_observed=leverage
        )