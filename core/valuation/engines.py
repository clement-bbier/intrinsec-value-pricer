import logging
from typing import Dict, Type, Optional

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    ValuationResult,  # REMPLACEMENT CRITIQUE : DCFResult -> ValuationResult
    ValuationMode,
    ValuationRequest
)
from core.valuation.strategies.abstract import ValuationStrategy

# --- IMPORT DES STRATÉGIES ---
from core.valuation.strategies.dcf_simple import SimpleFCFFStrategy
from core.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy
from core.valuation.strategies.dcf_growth import RevenueBasedStrategy
from core.valuation.strategies.ddm_banks import DDMBanksStrategy
from core.valuation.strategies.graham_value import GrahamNumberStrategy
from core.valuation.strategies.monte_carlo import MonteCarloDCFStrategy

logger = logging.getLogger(__name__)

# --- REGISTRE DES STRATÉGIES ---
# Mappe l'Enum ValuationMode vers la classe de stratégie correspondante
STRATEGY_REGISTRY: Dict[ValuationMode, Type[ValuationStrategy]] = {
    ValuationMode.SIMPLE_FCFF: SimpleFCFFStrategy,
    ValuationMode.FUNDAMENTAL_FCFF: FundamentalFCFFStrategy,
    ValuationMode.GROWTH_TECH: RevenueBasedStrategy,
    ValuationMode.DDM_BANKS: DDMBanksStrategy,
    ValuationMode.GRAHAM_VALUE: GrahamNumberStrategy,
    ValuationMode.MONTE_CARLO: MonteCarloDCFStrategy,
}


def run_valuation(request: ValuationRequest, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
    """
    Fonction principale d'exécution.
    Instancie la bonne stratégie et retourne un résultat typé (Polymorphique).
    """
    logger.info(f"Engine requested: {request.mode} for {request.ticker}")

    strategy_cls = STRATEGY_REGISTRY.get(request.mode)

    if not strategy_cls:
        raise CalculationError(f"Mode de valorisation inconnu ou non implémenté : {request.mode}")

    try:
        # Instanciation et Exécution
        strategy = strategy_cls()
        result = strategy.execute(financials, params)

        # On rattache la requête originale au résultat pour le traçage
        object.__setattr__(result, 'request', request)

        return result

    except CalculationError as e:
        logger.error(f"Calculation Error in {request.mode}: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected Error in Engine ({request.mode}): {e}", exc_info=True)
        raise CalculationError(f"Erreur interne du moteur de calcul : {str(e)}")


def run_reverse_dcf(
        financials: CompanyFinancials,
        params: DCFParameters,
        market_price: float,
        max_iterations: int = 50
) -> Optional[float]:
    """
    Calcule le taux de croissance implicite (Reverse DCF) pour justifier le prix actuel.
    Utilise la stratégie Fondamentale par défaut.
    """
    if market_price <= 0:
        return None

    low = -0.20
    high = 0.50
    strategy = FundamentalFCFFStrategy()

    for _ in range(max_iterations):
        mid = (low + high) / 2.0

        # On crée des paramètres temporaires avec le taux de croissance testé
        # Note: on utilise replace() si disponible ou on recrée l'objet
        from dataclasses import replace
        test_params = replace(params, fcf_growth_rate=mid)

        try:
            result = strategy.execute(financials, test_params)
            iv = result.intrinsic_value_per_share

            if abs(iv - market_price) < 0.5:  # Convergence à 0.5$ près
                return mid

            if iv < market_price:
                low = mid
            else:
                high = mid
        except:
            # Si le calcul plante (ex: WACC < g), on ajuste les bornes
            high = mid

    return None