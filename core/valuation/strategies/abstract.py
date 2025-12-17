"""
core/valuation/strategies/abstract.py

Contrat académique des stratégies de valorisation.
Version : V1 Normative (CFA / Damodaran / Buy-Side)

Rôle :
- Définir le socle commun obligatoire à toutes les méthodes
- Garantir la traçabilité (Glass Box)
- Encadrer les invariants financiers
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    ValuationResult,
    DCFValuationResult,
    ValuationRequest,
    CalculationStep,
    TerminalValueMethod
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
# CONTRAT ABSTRAIT — STRATÉGIE DE VALORISATION
# ============================================================

class ValuationStrategy(ABC):
    """
    Classe abstraite racine de toutes les stratégies de valorisation.

    Toute stratégie DOIT :
    - être académiquement référencée
    - déclarer explicitement son domaine de validité
    - respecter les invariants financiers
    - produire une preuve de calcul complète (Glass Box)
    """

    #: Référence académique principale (ex: "Damodaran", "Penman", "Graham")
    academic_reference: str = "UNSPECIFIED"

    #: Domaine économique de validité (ex: "Mature firms", "Banks", "High growth")
    economic_domain: str = "UNSPECIFIED"

    #: Invariants financiers obligatoires
    financial_invariants: List[str] = []

    def __init__(self):
        # Trace complète du raisonnement financier (preuve mathématique)
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
        """Enregistre une étape atomique du calcul."""
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
    # CONTRAT D’EXÉCUTION
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
        - respecter les invariants financiers
        - produire une ValuationResult cohérente
        """
        raise NotImplementedError

    # --------------------------------------------------------
    # OUTIL MUTUALISÉ — DCF DÉTERMINISTE STANDARD
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

        Invariants imposés :
        - WACC > g_terminal
        - Horizon de projection > 0
        """

        # ====================================================
        # 1. VALIDATION PRÉLIMINAIRE
        # ====================================================

        years = params.projection_years
        if years <= 0:
            raise CalculationError("Horizon de projection invalide (<= 0).")

        if base_flow is None:
            raise CalculationError("Flux de trésorerie initial manquant.")

        # ====================================================
        # 2. POINT DE DÉPART
        # ====================================================

        self.add_step(
            "Flux de Trésorerie Initial",
            "FCF_0",
            f"{base_flow:,.2f}",
            base_flow,
            financials.currency,
            "Base des projections (TTM ou normalisée)."
        )

        # ====================================================
        # 3. COÛT DU CAPITAL (WACC)
        # ====================================================

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

        # ====================================================
        # 4. PROJECTION DES FLUX
        # ====================================================

        projected_flows = project_flows(
            base_flow=base_flow,
            years=years,
            g_start=params.fcf_growth_rate,
            g_term=params.perpetual_growth_rate,
            high_growth_years=params.high_growth_years
        )

        # ====================================================
        # 5. ACTUALISATION DES FLUX
        # ====================================================

        discounted_sum = calculate_npv(projected_flows, wacc)
        discount_factors = calculate_discount_factors(wacc, years)

        self.add_step(
            f"Valeur actuelle des FCF ({years} ans)",
            "∑ FCF_t / (1+WACC)^t",
            f"NPV(FCF, {wacc:.2%})",
            discounted_sum,
            financials.currency,
            "Valeur des flux explicites."
        )

        # ====================================================
        # 6. VALEUR TERMINALE
        # ====================================================

        final_flow = projected_flows[-1]

        if params.terminal_method == TerminalValueMethod.EXIT_MULTIPLE:
            if not params.exit_multiple_value:
                raise CalculationError("Exit multiple manquant.")
            tv = calculate_terminal_value_exit_multiple(
                final_flow,
                params.exit_multiple_value
            )
            tv_formula = "FCF_n × Multiple"
            tv_desc = "Approche par multiple de marché."
        else:
            tv = calculate_terminal_value_gordon(
                final_flow,
                wacc,
                params.perpetual_growth_rate
            )
            tv_formula = "FCF_n·(1+g)/(WACC−g)"
            tv_desc = "Modèle Gordon-Shapiro."

        discounted_tv = tv * discount_factors[-1]

        self.add_step(
            "Valeur Terminale Actualisée",
            tv_formula,
            f"{tv:,.2f} × {discount_factors[-1]:.4f}",
            discounted_tv,
            financials.currency,
            tv_desc
        )

        # ====================================================
        # 7. ENTERPRISE VALUE → EQUITY VALUE
        # ====================================================

        enterprise_value = discounted_sum + discounted_tv

        equity_value = calculate_equity_value_bridge(
            enterprise_value,
            financials.total_debt,
            financials.cash_and_equivalents
        )

        self.add_step(
            "Valeur des Capitaux Propres",
            "EV − Dette + Cash",
            (
                f"{enterprise_value:,.2f} − "
                f"{financials.total_debt:,.2f} + "
                f"{financials.cash_and_equivalents:,.2f}"
            ),
            equity_value,
            financials.currency,
            "Valeur revenant aux actionnaires."
        )

        # ====================================================
        # 8. VALEUR PAR ACTION
        # ====================================================

        if financials.shares_outstanding <= 0:
            raise CalculationError("Nombre d’actions invalide.")

        iv_per_share = equity_value / financials.shares_outstanding

        self.add_step(
            "Valeur Intrinsèque par Action",
            "Equity Value / Shares",
            (
                f"{equity_value:,.2f} / "
                f"{financials.shares_outstanding:,.0f}"
            ),
            iv_per_share,
            financials.currency,
            "Résultat final du modèle."
        )

        # ====================================================
        # 9. CONSTRUCTION DU RÉSULTAT
        # ====================================================

        return DCFValuationResult(
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
            equity_value=equity_value,
            calculation_trace=self.trace
        )
