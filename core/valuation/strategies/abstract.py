"""
core/valuation/strategies/abstract.py

Contrat académique et contractuel des stratégies de valorisation.
Version : V1.1 — Chapitre 3 conforme (Glass Box Valuation Engine)

Responsabilités :
- Définir le socle commun obligatoire à toutes les méthodes
- Garantir la traçabilité (Glass Box)
- Faire respecter le contrat de sortie Chapitre 3
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
# STRATÉGIE ABSTRAITE — SOCLE NORMATIF
# ============================================================

class ValuationStrategy(ABC):
    """
    Classe abstraite racine de toutes les stratégies de valorisation.

    Toute stratégie DOIT :
    - être académiquement référencée
    - produire une trace Glass Box complète
    - retourner un résultat conforme au contrat de sortie Chapitre 3
    """

    academic_reference: str = "UNSPECIFIED"
    economic_domain: str = "UNSPECIFIED"
    financial_invariants: List[str] = []

    def __init__(self):
        self.trace: List[CalculationStep] = []

    # --------------------------------------------------------
    # GLASS BOX — TRACE D’AUDIT
    # --------------------------------------------------------

    def add_step(
        self,
        label: str,
        formula: str,
        values: str,
        result: float,
        unit: str,
        description: str = ""
    ) -> None:
        self.trace.append(
            CalculationStep(
                label=label,
                formula=formula,
                values=values,
                result=float(result),
                unit=unit,
                description=description
            )
        )

    # --------------------------------------------------------
    # CONTRAT D’EXÉCUTION (STRATÉGIE)
    # --------------------------------------------------------

    @abstractmethod
    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> ValuationResult:
        """
        Exécute la stratégie de valorisation.

        Toute implémentation DOIT :
        - valider ses préconditions
        - produire un ValuationResult
        """
        raise NotImplementedError

    # --------------------------------------------------------
    # CONTRAT DE SORTIE — ENFORCEMENT CENTRAL
    # --------------------------------------------------------

    def _finalize_result(
        self,
        result: ValuationResult,
        request_stub: Optional[ValuationRequest] = None
    ) -> ValuationResult:
        """
        Point de sortie UNIQUE de toute stratégie.

        - injecte la requête si nécessaire
        - attache la trace Glass Box
        - vérifie le contrat de sortie Chapitre 3
        - bloque toute sortie invalide
        """

        # Injection requête (traçabilité)
        if request_stub is not None:
            object.__setattr__(result, "request", request_stub)

        # Injection trace
        result.calculation_trace = self.trace

        # Validation contractuelle
        contract: ValuationOutputContract = result.build_output_contract()

        if not contract.is_valid():
            logger.error(
                "[ContractViolation] %s produced an invalid valuation output",
                self.__class__.__name__
            )
            raise CalculationError(
                f"Contrat de sortie invalide pour {self.__class__.__name__} : "
                f"{contract}"
            )

        return result

    # --------------------------------------------------------
    # MOTEUR DCF MUTUALISÉ (DÉTERMINISTE)
    # --------------------------------------------------------

    def _run_dcf_math(
        self,
        base_flow: float,
        financials: CompanyFinancials,
        params: DCFParameters,
        request_stub: Optional[ValuationRequest] = None
    ) -> DCFValuationResult:
        """
        Moteur DCF déterministe partagé (FCFF).

        Conforme :
        - Damodaran
        - CFA Institute
        """

        # 1. Validation
        if params.projection_years <= 0:
            raise CalculationError("Horizon de projection invalide.")

        if base_flow is None:
            raise CalculationError("Flux de trésorerie initial manquant.")

        # 2. Point de départ
        self.add_step(
            "Flux de Trésorerie Initial",
            "FCF_0",
            f"{base_flow:,.2f}",
            base_flow,
            financials.currency,
            "Base des projections."
        )

        # 3. WACC
        wacc_ctx = calculate_wacc(financials, params)
        wacc = wacc_ctx.wacc

        self.add_step(
            "WACC",
            "K_e·W_e + K_d(1−t)·W_d",
            (
                f"({wacc_ctx.cost_of_equity:.2%}×{wacc_ctx.weight_equity:.0%}) + "
                f"({wacc_ctx.cost_of_debt_after_tax:.2%}×{wacc_ctx.weight_debt:.0%})"
            ),
            wacc,
            "%",
            f"Méthode : {wacc_ctx.method}"
        )

        # 4. Projection
        projected_flows = project_flows(
            base_flow=base_flow,
            years=params.projection_years,
            g_start=params.fcf_growth_rate,
            g_term=params.perpetual_growth_rate,
            high_growth_years=params.high_growth_years
        )

        # 5. Actualisation
        discounted_sum = calculate_npv(projected_flows, wacc)
        discount_factors = calculate_discount_factors(wacc, params.projection_years)

        self.add_step(
            "Valeur actuelle des FCF",
            "∑ FCF_t / (1+WACC)^t",
            f"NPV(FCF, {wacc:.2%})",
            discounted_sum,
            financials.currency,
            "Flux explicites."
        )

        # 6. Valeur terminale
        final_flow = projected_flows[-1]

        if params.terminal_method == TerminalValueMethod.EXIT_MULTIPLE:
            if not params.exit_multiple_value:
                raise CalculationError("Exit multiple manquant.")
            tv = calculate_terminal_value_exit_multiple(
                final_flow,
                params.exit_multiple_value
            )
            tv_desc = "Exit Multiple"
        else:
            tv = calculate_terminal_value_gordon(
                final_flow,
                wacc,
                params.perpetual_growth_rate
            )
            tv_desc = "Gordon-Shapiro"

        discounted_tv = tv * discount_factors[-1]

        self.add_step(
            "Valeur Terminale Actualisée",
            tv_desc,
            f"{tv:,.2f}",
            discounted_tv,
            financials.currency,
            "Valeur terminale."
        )

        # 7. Bridge EV → Equity
        enterprise_value = discounted_sum + discounted_tv
        equity_value = calculate_equity_value_bridge(
            enterprise_value,
            financials.total_debt,
            financials.cash_and_equivalents
        )

        self.add_step(
            "Valeur des Capitaux Propres",
            "EV − Dette + Cash",
            f"{enterprise_value:,.2f}",
            equity_value,
            financials.currency,
            "Bridge EV → Equity."
        )

        if financials.shares_outstanding <= 0:
            raise CalculationError("Nombre d’actions invalide.")

        iv_per_share = equity_value / financials.shares_outstanding

        self.add_step(
            "Valeur Intrinsèque par Action",
            "Equity / Shares",
            f"{iv_per_share:,.2f}",
            iv_per_share,
            financials.currency,
            "Résultat final."
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
