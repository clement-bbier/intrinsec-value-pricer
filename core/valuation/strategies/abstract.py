"""
core/valuation/strategies/abstract.py

Contrat académique et Glass Box des stratégies de valorisation.
Version : V1.2 — Chapitres 3 & 4 conformes (Glass Box Valuation Engine)

Responsabilités :
- Définir le socle commun obligatoire à toutes les méthodes
- Imposer le standard universel de trace Glass Box
- Faire respecter le contrat de sortie
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
    ValuationRequest,
    CalculationStep,
    TraceHypothesis,
    TerminalValueMethod,
    ValuationOutputContract
)

from core.computation.financial_math import (
    calculate_wacc,
    calculate_discount_factors,
    calculate_terminal_value_gordon,
    calculate_terminal_value_exit_multiple,
    calculate_npv,
    calculate_equity_value_bridge
)
from core.computation.growth import project_flows

logger = logging.getLogger(__name__)


# ============================================================
# STRATÉGIE ABSTRAITE — SOCLE GLASS BOX
# ============================================================

class ValuationStrategy(ABC):
    """
    Classe abstraite racine de toutes les stratégies de valorisation.

    Toute stratégie DOIT :
    - produire une trace Glass Box normative
    - exposer chaque hypothèse et chaque calcul
    - retourner un résultat conforme aux contrats Chapitre 3 & 4
    """

    academic_reference: str = "UNSPECIFIED"
    economic_domain: str = "UNSPECIFIED"
    financial_invariants: List[str] = []

    def __init__(self):
        self.trace: List[CalculationStep] = []

    # --------------------------------------------------------
    # GLASS BOX — AJOUT D’ÉTAPE NORMATIVE
    # --------------------------------------------------------

    def add_step(
        self,
        *,
        label: str,
        theoretical_formula: str,
        hypotheses: List[TraceHypothesis],
        numerical_substitution: str,
        result: float,
        unit: str,
        interpretation: str
    ) -> None:
        """
        Ajoute une étape de calcul Glass Box conforme Chapitre 4.

        Toute omission entraîne une non-conformité.
        """

        if not hypotheses:
            raise CalculationError(
                f"Étape '{label}' invalide : hypothèses manquantes."
            )

        self.trace.append(
            CalculationStep(
                label=label,
                theoretical_formula=theoretical_formula,
                hypotheses=hypotheses,
                numerical_substitution=numerical_substitution,
                result=float(result),
                unit=unit,
                interpretation=interpretation
            )
        )

    # --------------------------------------------------------
    # CONTRAT D’EXÉCUTION
    # --------------------------------------------------------

    @abstractmethod
    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> ValuationResult:
        raise NotImplementedError

    # --------------------------------------------------------
    # CONTRAT DE SORTIE — ENFORCEMENT CENTRAL
    # --------------------------------------------------------

    def _finalize_result(
        self,
        result: ValuationResult,
        request_stub: Optional[ValuationRequest] = None
    ) -> ValuationResult:

        if request_stub is not None:
            object.__setattr__(result, "request", request_stub)

        result.calculation_trace = self.trace

        contract: ValuationOutputContract = result.build_output_contract()

        if not contract.is_valid():
            raise CalculationError(
                f"Contrat de sortie invalide pour {self.__class__.__name__}"
            )

        return result

    # --------------------------------------------------------
    # MOTEUR DCF MUTUALISÉ (LOGIQUE INCHANGÉE)
    # --------------------------------------------------------

    def _run_dcf_math(
        self,
        base_flow: float,
        financials: CompanyFinancials,
        params: DCFParameters,
        request_stub: Optional[ValuationRequest] = None
    ) -> DCFValuationResult:

        if params.projection_years <= 0:
            raise CalculationError("Horizon de projection invalide.")

        if base_flow is None:
            raise CalculationError("Flux de trésorerie initial manquant.")

        # 1. Flux initial
        self.add_step(
            label="Flux de trésorerie initial",
            theoretical_formula="FCF₀",
            hypotheses=[
                TraceHypothesis("FCF initial", base_flow, financials.currency)
            ],
            numerical_substitution=f"FCF₀ = {base_flow:,.2f}",
            result=base_flow,
            unit=financials.currency,
            interpretation="Point de départ des projections."
        )

        # 2. WACC
        wacc_ctx = calculate_wacc(financials, params)
        wacc = wacc_ctx.wacc

        self.add_step(
            label="Coût moyen pondéré du capital (WACC)",
            theoretical_formula="Kₑ·Wₑ + K_d·(1−t)·W_d",
            hypotheses=[
                TraceHypothesis("Cost of equity", wacc_ctx.cost_of_equity, "%"),
                TraceHypothesis("Cost of debt (after tax)", wacc_ctx.cost_of_debt_after_tax, "%"),
                TraceHypothesis("Equity weight", wacc_ctx.weight_equity, "%"),
                TraceHypothesis("Debt weight", wacc_ctx.weight_debt, "%"),
            ],
            numerical_substitution=(
                f"({wacc_ctx.cost_of_equity:.2%}×{wacc_ctx.weight_equity:.0%}) + "
                f"({wacc_ctx.cost_of_debt_after_tax:.2%}×{wacc_ctx.weight_debt:.0%})"
            ),
            result=wacc,
            unit="%",
            interpretation="Taux d’actualisation des flux futurs."
        )

        # 3. Projection
        projected_flows = project_flows(
            base_flow=base_flow,
            years=params.projection_years,
            g_start=params.fcf_growth_rate,
            g_term=params.perpetual_growth_rate,
            high_growth_years=params.high_growth_years
        )

        discounted_sum = calculate_npv(projected_flows, wacc)
        discount_factors = calculate_discount_factors(wacc, params.projection_years)

        self.add_step(
            label="Valeur actuelle des flux projetés",
            theoretical_formula="∑ FCFₜ / (1 + WACC)ᵗ",
            hypotheses=[
                TraceHypothesis("Projected FCFs", projected_flows, financials.currency),
                TraceHypothesis("WACC", wacc, "%")
            ],
            numerical_substitution=f"NPV(FCF, {wacc:.2%})",
            result=discounted_sum,
            unit=financials.currency,
            interpretation="Valeur actualisée des flux explicites."
        )

        # 4. Valeur terminale
        final_flow = projected_flows[-1]

        if params.terminal_method == TerminalValueMethod.EXIT_MULTIPLE:
            tv = calculate_terminal_value_exit_multiple(
                final_flow, params.exit_multiple_value
            )
            tv_formula = "FCFₙ × Multiple"
        else:
            tv = calculate_terminal_value_gordon(
                final_flow, wacc, params.perpetual_growth_rate
            )
            tv_formula = "FCFₙ × (1+g) / (WACC − g)"

        discounted_tv = tv * discount_factors[-1]

        self.add_step(
            label="Valeur terminale actualisée",
            theoretical_formula=tv_formula,
            hypotheses=[
                TraceHypothesis("Final FCF", final_flow, financials.currency),
                TraceHypothesis("WACC", wacc, "%"),
                TraceHypothesis("Perpetual growth", params.perpetual_growth_rate, "%")
            ],
            numerical_substitution=f"TV × DFₙ = {tv:,.2f} × {discount_factors[-1]:.4f}",
            result=discounted_tv,
            unit=financials.currency,
            interpretation="Valeur de continuation de l’entreprise."
        )

        # 5. Bridge EV → Equity
        enterprise_value = discounted_sum + discounted_tv
        equity_value = calculate_equity_value_bridge(
            enterprise_value,
            financials.total_debt,
            financials.cash_and_equivalents
        )

        self.add_step(
            label="Valeur des capitaux propres",
            theoretical_formula="EV − Dette + Cash",
            hypotheses=[
                TraceHypothesis("Enterprise Value", enterprise_value, financials.currency),
                TraceHypothesis("Total debt", financials.total_debt, financials.currency),
                TraceHypothesis("Cash", financials.cash_and_equivalents, financials.currency)
            ],
            numerical_substitution=(
                f"{enterprise_value:,.2f} − {financials.total_debt:,.2f} + "
                f"{financials.cash_and_equivalents:,.2f}"
            ),
            result=equity_value,
            unit=financials.currency,
            interpretation="Valeur revenant aux actionnaires."
        )

        if financials.shares_outstanding <= 0:
            raise CalculationError("Nombre d’actions invalide.")

        iv_per_share = equity_value / financials.shares_outstanding

        self.add_step(
            label="Valeur intrinsèque par action",
            theoretical_formula="Equity / Shares outstanding",
            hypotheses=[
                TraceHypothesis("Equity value", equity_value, financials.currency),
                TraceHypothesis("Shares outstanding", financials.shares_outstanding)
            ],
            numerical_substitution=f"{equity_value:,.2f} / {financials.shares_outstanding:,.0f}",
            result=iv_per_share,
            unit=financials.currency,
            interpretation="Valeur intrinsèque estimée par action."
        )

        result = DCFValuationResult(
            request=request_stub,
            financials=financials,
            params=params,
            intrinsic_value_per_share=iv_per_share,
            market_price=financials.current_price,
            wacc=wacc,
            cost_of_equity=wacc_ctx.cost_of_equity,
            cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax,
            projected_fcfs=projected_flows,
            discount_factors=discount_factors,
            sum_discounted_fcf=discounted_sum,
            terminal_value=tv,
            discounted_terminal_value=discounted_tv,
            enterprise_value=enterprise_value,
            equity_value=equity_value
        )

        return self._finalize_result(result, request_stub)
