import logging
from core.models import CompanyFinancials, DCFParameters, DDMValuationResult
from core.valuation.strategies.abstract import ValuationStrategy
from core.exceptions import CalculationError
from core.computation.financial_math import (
    calculate_cost_of_equity_capm,
    calculate_terminal_value_gordon,
    calculate_discount_factors,
    calculate_npv
)

logger = logging.getLogger(__name__)


class DDMBanksStrategy(ValuationStrategy):
    """
    STRATÉGIE 5 : DIVIDEND DISCOUNT MODEL (DDM).
    Spécifique pour les institutions financières (Banques, Assurances).
    Retourne un DDMValuationResult (pas de WACC, pas d'Enterprise Value).
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DDMValuationResult:
        logger.info("[Strategy] Executing DDMBanksStrategy | ticker=%s", financials.ticker)

        # 1. Base : Dividende
        div_base = financials.last_dividend

        # Override manuel
        if params.manual_fcf_base is not None:
            div_base = params.manual_fcf_base

        if div_base is None or div_base <= 0:
            # Pour les banques, un dividende nul rend le modèle DDM standard inopérant
            raise CalculationError("Donnée manquante : Dividende par action requis et positif pour le modèle DDM.")

        # 2. Taux d'Actualisation (Ke uniquement, pas de WACC pour les banques)
        if params.manual_cost_of_equity:
            ke = params.manual_cost_of_equity
        else:
            ke = calculate_cost_of_equity_capm(
                params.risk_free_rate,
                financials.beta,
                params.market_risk_premium
            )

        # 3. Projection des Dividendes
        # Hypothèse simplifiée : Croissance constante (g_growth) puis terminale
        projected_divs = []
        current_div = div_base

        for i in range(1, params.projection_years + 1):
            current_div *= (1.0 + params.fcf_growth_rate)
            projected_divs.append(current_div)

        # 4. Calculs Financiers (Moteur Central)
        factors = calculate_discount_factors(ke, len(projected_divs))
        sum_discounted = calculate_npv(projected_divs, ke)

        # Valeur Terminale
        tv = calculate_terminal_value_gordon(
            final_flow=projected_divs[-1],
            rate=ke,
            g_perp=params.perpetual_growth_rate
        )
        discounted_tv = tv * factors[-1]

        # 5. Equity Value Directe
        # Dans le DDM, on valorise directement les capitaux propres par action.
        equity_value_per_share = sum_discounted + discounted_tv

        # Note : Pour l'objet résultat, on calcule la valo totale pour info
        total_equity_value = equity_value_per_share * financials.shares_outstanding

        return DDMValuationResult(
            request=None,
            financials=financials,
            params=params,
            intrinsic_value_per_share=equity_value_per_share,
            market_price=financials.current_price,
            cost_of_equity=ke,
            projected_dividends=projected_divs,
            discount_factors=factors,
            sum_discounted_dividends=sum_discounted,
            terminal_value=tv,
            discounted_terminal_value=discounted_tv,
            equity_value=total_equity_value
        )