import logging
from abc import ABC, abstractmethod
from typing import Optional

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    ValuationResult,
    DCFValuationResult,
    ValuationRequest
)
from core.computation.financial_math import (
    calculate_wacc,
    calculate_discount_factors,
    calculate_terminal_value_gordon,
    calculate_npv,
    calculate_equity_value_bridge
)
from core.computation.growth import project_flows

logger = logging.getLogger(__name__)


class ValuationStrategy(ABC):
    """
    Contrat d'interface pour toutes les stratégies de valorisation.
    Doit retourner un objet héritant de ValuationResult (DCF, DDM, Graham).
    """

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
        Utilise le nouveau moteur financial_math pour garantir la cohérence (DRY).
        """
        # 1. Validation de base
        years = params.projection_years
        if years <= 0:
            raise CalculationError("L'horizon de projection doit être positif.")

        # 2. Calcul du WACC (Centralisé)
        wacc_ctx = calculate_wacc(financials, params)
        wacc = wacc_ctx.wacc

        # 3. Projection des Flux
        # Note: project_flows est dans core/computation/growth.py (inchangé)
        projected_flows = project_flows(
            base_flow=base_flow,
            years=years,
            g_start=params.fcf_growth_rate,
            g_term=params.perpetual_growth_rate,
            high_growth_years=params.high_growth_years
        )

        # 4. Actualisation (Vectorielle via financial_math)
        # NPV des flux explicites
        sum_discounted = calculate_npv(projected_flows, wacc)
        factors = calculate_discount_factors(wacc, years)

        # 5. Valeur Terminale
        tv = calculate_terminal_value_gordon(
            final_flow=projected_flows[-1],
            rate=wacc,
            g_perp=params.perpetual_growth_rate
        )
        discounted_tv = tv * factors[-1]

        # 6. Aggrégation
        enterprise_value = sum_discounted + discounted_tv
        equity_value = calculate_equity_value_bridge(
            enterprise_value,
            financials.total_debt,
            financials.cash_and_equivalents
        )

        shares = financials.shares_outstanding
        if shares <= 0:
            raise CalculationError("Le nombre d'actions doit être positif.")

        iv_per_share = equity_value / shares

        # 7. Construction du Résultat Typé
        return DCFValuationResult(
            request=request_stub,  # Sera injecté/complété par le workflow
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
            equity_value=equity_value
        )