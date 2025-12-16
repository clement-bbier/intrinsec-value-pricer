import logging
from abc import ABC, abstractmethod
from typing import Optional, List

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    ValuationResult,
    DCFValuationResult,
    ValuationRequest,
    CalculationStep,  # <--- NOUVEAU
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


class ValuationStrategy(ABC):
    """
    Classe de base pour toutes les stratégies.
    Intègre désormais le moteur de traçabilité 'Glass Box'.
    """

    def __init__(self):
        # La liste qui contiendra la preuve mathématique étape par étape
        self.trace: List[CalculationStep] = []

    def add_step(self, label: str, formula: str, values: str, result: float, unit: str, description: str = ""):
        """Enregistre une étape de calcul dans l'audit trail."""
        self.trace.append(CalculationStep(
            label=label,
            formula=formula,
            values=values,
            result=float(result),
            unit=unit,
            description=description
        ))

    @abstractmethod
    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
        """Exécute la logique spécifique de la stratégie."""
        raise NotImplementedError

    def _run_dcf_math(
            self,
            base_flow: float,
            financials: CompanyFinancials,
            params: DCFParameters,
            request_stub: Optional[ValuationRequest] = None
    ) -> DCFValuationResult:
        """
        Helper partagé pour les stratégies DCF standard (Simple, Fundamental).
        Génère automatiquement la trace d'audit pour les calculs communs.
        """
        # 1. Validation
        years = params.projection_years
        if years <= 0:
            raise CalculationError("L'horizon de projection doit être positif.")

        # --- TRACE : Point de départ ---
        self.add_step(
            "Flux de Trésorerie Initial (Base FCF)",
            "FCF_{base}",
            f"{base_flow:,.2f}",
            base_flow,
            financials.currency,
            "Point de départ des projections (TTM ou Normatif)."
        )

        # 2. Calcul du WACC
        wacc_ctx = calculate_wacc(financials, params)
        wacc = wacc_ctx.wacc

        self.add_step(
            "Coût Moyen Pondéré du Capital (WACC)",
            "K_e \\times W_e + K_d(1-t) \\times W_d",
            f"({wacc_ctx.cost_of_equity:.1%} x {wacc_ctx.weight_equity:.0%}) + ({wacc_ctx.cost_of_debt_after_tax:.1%} x {wacc_ctx.weight_debt:.0%})",
            wacc,
            "%",
            f"Taux d'actualisation (Méthode: {wacc_ctx.method})"
        )

        # 3. Projection des Flux
        projected_flows = project_flows(
            base_flow=base_flow,
            years=years,
            g_start=params.fcf_growth_rate,
            g_term=params.perpetual_growth_rate,
            high_growth_years=params.high_growth_years
        )

        # 4. Actualisation (NPV)
        sum_discounted = calculate_npv(projected_flows, wacc)
        factors = calculate_discount_factors(wacc, years)

        self.add_step(
            f"Somme des FCF Actualisés ({years} ans)",
            "\\sum \\frac{FCF_t}{(1+WACC)^t}",
            f"NPV(Flows, {wacc:.1%})",
            sum_discounted,
            financials.currency,
            "Valeur actuelle des flux explicites projetés."
        )

        # 5. Valeur Terminale (TV)
        final_flow = projected_flows[-1]

        if params.terminal_method == TerminalValueMethod.EXIT_MULTIPLE and params.exit_multiple_value:
            # Méthode Exit Multiple
            # Note: Pour être puriste, il faudrait projeter l'EBITDA terminal.
            # Ici, par simplification compatible, on applique le multiple au FCF final proxy ou on assume un multiple de FCF.
            # Dans une V2, on projettera l'EBITDA explicitement.
            tv = calculate_terminal_value_exit_multiple(final_flow, params.exit_multiple_value)
            tv_formula = "FCF_n \\times Multiple"
            tv_values = f"{final_flow:,.2f} x {params.exit_multiple_value}x"
            tv_desc = "Valeur de sortie basée sur un multiple comparable."
        else:
            # Méthode Gordon Growth (Défaut)
            tv = calculate_terminal_value_gordon(final_flow, wacc, params.perpetual_growth_rate)
            tv_formula = "\\frac{FCF_n \\times (1+g)}{WACC - g}"
            tv_values = f"({final_flow:,.2f} * (1+{params.perpetual_growth_rate:.1%})) / ({wacc:.1%} - {params.perpetual_growth_rate:.1%})"
            tv_desc = "Modèle de Croissance Perpétuelle (Gordon-Shapiro)."

        discounted_tv = tv * factors[-1]

        self.add_step(
            "Valeur Terminale (TV)",
            tv_formula,
            tv_values,
            tv,
            financials.currency,
            tv_desc
        )

        self.add_step(
            "Valeur Terminale Actualisée",
            "TV \\times (1+WACC)^{-n}",
            f"{tv:,.2f} x {factors[-1]:.4f}",
            discounted_tv,
            financials.currency,
            "Poids de la valeur terminale ramené à aujourd'hui."
        )

        # 6. Aggrégation (Enterprise Value)
        enterprise_value = sum_discounted + discounted_tv

        self.add_step(
            "Valeur d'Entreprise (EV)",
            "\\text{NPV Flux} + \\text{NPV TV}",
            f"{sum_discounted:,.2f} + {discounted_tv:,.2f}",
            enterprise_value,
            financials.currency,
            "Valeur totale opérationnelle de la firme."
        )

        # 7. Pont Equity (Net Debt)
        equity_value = calculate_equity_value_bridge(
            enterprise_value,
            financials.total_debt,
            financials.cash_and_equivalents
        )

        self.add_step(
            "Valeur des Capitaux Propres (Equity Value)",
            "EV - \\text{Dette} + \\text{Cash}",
            f"{enterprise_value:,.2f} - {financials.total_debt:,.2f} + {financials.cash_and_equivalents:,.2f}",
            equity_value,
            financials.currency,
            "Valeur revenant aux actionnaires."
        )

        shares = financials.shares_outstanding
        if shares <= 0:
            raise CalculationError("Le nombre d'actions doit être positif.")

        iv_per_share = equity_value / shares

        self.add_step(
            "Valeur Intrinsèque par Action",
            "\\text{Equity Value} / \\text{Actions}",
            f"{equity_value:,.2f} / {shares:,.0f}",
            iv_per_share,
            financials.currency,
            "FINAL : Juste valeur estimée."
        )

        # 8. Construction du Résultat
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
            discount_factors=factors,
            sum_discounted_fcf=sum_discounted,
            terminal_value=tv,
            discounted_terminal_value=discounted_tv,
            enterprise_value=enterprise_value,
            equity_value=equity_value,
            calculation_trace=self.trace  # Injection de la trace complète
        )