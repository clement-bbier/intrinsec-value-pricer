"""
core/valuation/strategies/abstract.py

Socle abstrait pour toutes les stratégies de valorisation (Glass Box Pattern).
Gère la traçabilité (Audit), le contrat de sortie et les mathématiques communes.
Version : V2.2 — Pydantic Compatibility Fix (Keyword Arguments)
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
    """
    Socle abstrait pour toutes les stratégies de valorisation (Glass Box Pattern).
    Gère la traçabilité (Audit), le contrat de sortie et les mathématiques communes.
    """

    # Metadonnées par défaut
    academic_reference: str = "Standard Valuation"
    economic_domain: str = "General"

    def __init__(self, glass_box_enabled: bool = True):
        self.glass_box_enabled = glass_box_enabled
        self.calculation_trace: List[CalculationStep] = []

    # --------------------------------------------------------------------------
    # 1. GLASS BOX ENGINE (Traçabilité)
    # --------------------------------------------------------------------------
    def add_step(self, label: str, theoretical_formula: str, hypotheses: List[TraceHypothesis],
                 numerical_substitution: str, result: float, unit: str, interpretation: str) -> None:
        """Enregistre une étape de calcul si le mode Glass Box est actif."""
        if not self.glass_box_enabled:
            return

        # [CORRECTIF PYDANTIC] : Arguments nommés obligatoires
        self.calculation_trace.append(CalculationStep(
            step_id=len(self.calculation_trace) + 1,
            label=label,
            theoretical_formula=theoretical_formula,
            hypotheses=hypotheses,
            numerical_substitution=numerical_substitution,
            result=result,
            unit=unit,
            interpretation=interpretation
        ))

    # --------------------------------------------------------------------------
    # 2. CONTRAT (Interface)
    # --------------------------------------------------------------------------
    @abstractmethod
    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
        """Méthode principale à implémenter par les stratégies concrètes."""
        pass

    def verify_output_contract(self, result: ValuationResult) -> None:
        """Valide l'intégrité des données avant le retour au client."""
        contract = result.build_output_contract()

        if not contract.has_intrinsic_value:
            raise CalculationError("Contrat violé : Valeur intrinsèque manquante.")

        if self.glass_box_enabled and not contract.has_calculation_trace:
            raise CalculationError("Contrat violé : Trace Glass Box manquante.")

    # --------------------------------------------------------------------------
    # 3. HELPER MATHÉMATIQUE (Moteur DCF partagé)
    # --------------------------------------------------------------------------
    def _run_dcf_math(self, base_flow: float, financials: CompanyFinancials,
                      params: DCFParameters, wacc_override: Optional[float] = None) -> DCFValuationResult:
        """
        Exécute la séquence mathématique standard DCF :
        WACC -> Projections -> TV -> Actualisation -> Bridge -> Equity.
        """

        # --- A. WACC ---
        if wacc_override is not None:
            wacc = wacc_override
            wacc_ctx = None
            self.add_step(
                label="WACC (Manuel)",
                theoretical_formula="Input",
                hypotheses=[],
                numerical_substitution=f"{wacc:.2%}",
                result=wacc,
                unit="%",
                interpretation="Surcharge manuelle."
            )
        else:
            wacc_ctx = calculate_wacc(financials, params)
            wacc = wacc_ctx.wacc

            # [CORRECTIF PYDANTIC] : Arguments nommés pour TraceHypothesis
            self.add_step(
                label="Calcul du WACC",
                theoretical_formula="Ke*We + Kd*(1-t)*Wd",
                hypotheses=[
                    TraceHypothesis(name="Risk-free", value=params.risk_free_rate, unit="%"),
                    TraceHypothesis(name="Beta", value=financials.beta, unit="")
                ],
                numerical_substitution=f"Ke: {wacc_ctx.cost_of_equity:.2%} | Kd_net: {wacc_ctx.cost_of_debt_after_tax:.2%}",
                result=wacc,
                unit="%",
                interpretation="Coût Moyen Pondéré du Capital."
            )

        # --- B. Projections ---
        flows = project_flows(base_flow, params.projection_years, params.fcf_growth_rate,
                              params.perpetual_growth_rate, params.high_growth_years)

        # [CORRECTIF PYDANTIC]
        self.add_step(
            label="Projections FCF",
            theoretical_formula="FCF(t-1) * (1+g)",
            hypotheses=[
                TraceHypothesis(name="Base FCF", value=base_flow, unit=financials.currency)
            ],
            numerical_substitution=f"Projection sur {len(flows)} ans",
            result=sum(flows),
            unit=financials.currency,
            interpretation="Flux futurs cumulés (non actualisés)."
        )

        # --- C. Valeur Terminale ---
        if params.terminal_method == TerminalValueMethod.GORDON_SHAPIRO:
            if wacc <= params.perpetual_growth_rate:
                logger.warning("WACC <= g_perp : risque mathématique.")

            tv = calculate_terminal_value_gordon(flows[-1], wacc, params.perpetual_growth_rate)
            formula_tv = "FCF_n * (1+g) / (WACC - g)"
        else:
            tv = calculate_terminal_value_exit_multiple(flows[-1], 12.0)
            formula_tv = "Metric_n * Multiple (12x)"

        self.add_step(
            label="Valeur Terminale",
            theoretical_formula=formula_tv,
            hypotheses=[],
            numerical_substitution="Voir détail",
            result=tv,
            unit=financials.currency,
            interpretation="Valeur à l'infini."
        )

        # --- D. Actualisation & Bridge ---
        factors = calculate_discount_factors(wacc, params.projection_years)
        sum_pv = sum(f * d for f, d in zip(flows, factors))

        pv_tv = tv * factors[-1]
        ev = sum_pv + pv_tv

        # [CORRECTIF PYDANTIC]
        self.add_step(
            label="Actualisation (NPV)",
            theoretical_formula="Sum(FCF * Factors) + TV * Factor_n",
            hypotheses=[
                TraceHypothesis(name="Discounted FCF Sum", value=sum_pv, unit="M"),
                TraceHypothesis(name="Discounted TV", value=pv_tv, unit="M")
            ],
            numerical_substitution=f"{sum_pv:,.0f} + {pv_tv:,.0f}",
            result=ev,
            unit=financials.currency,
            interpretation="Valeur d'Entreprise (EV)."
        )

        bridge_res = calculate_equity_value_bridge(ev, financials.total_debt, financials.cash_and_equivalents)
        if isinstance(bridge_res, dict):
            equity_val = bridge_res.get("equity_value", 0.0)
        else:
            equity_val = bridge_res

        # --- E. Résultat par action ---
        if financials.shares_outstanding <= 0:
            raise CalculationError("Nombre d'actions invalide.")

        iv_share = equity_val / financials.shares_outstanding

        # [CORRECTIF PYDANTIC]
        self.add_step(
            label="Valeur par action",
            theoretical_formula="Equity / Shares",
            hypotheses=[
                TraceHypothesis(name="Equity", value=equity_val, unit="M"),
                TraceHypothesis(name="Shares", value=financials.shares_outstanding, unit="#")
            ],
            numerical_substitution=f"{equity_val:,.0f} / {financials.shares_outstanding:,.0f}",
            result=iv_share,
            unit=financials.currency,
            interpretation="Valeur Intrinsèque."
        )

        return DCFValuationResult(
            request=None, financials=financials, params=params,
            intrinsic_value_per_share=iv_share, market_price=financials.current_price,
            wacc=wacc,
            cost_of_equity=wacc_ctx.cost_of_equity if wacc_ctx else 0.0,
            cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax if wacc_ctx else 0.0,
            projected_fcfs=flows, discount_factors=factors,
            sum_discounted_fcf=sum_pv, terminal_value=tv, discounted_terminal_value=pv_tv,
            enterprise_value=ev, equity_value=equity_val,
            calculation_trace=self.calculation_trace
        )