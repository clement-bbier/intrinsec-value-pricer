import logging
from typing import Dict, Type, Optional

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    ValuationResult,
    ValuationMode,
    ValuationRequest
)
from core.valuation.strategies.abstract import ValuationStrategy

# --- IMPORT DES STRATÉGIES (NOUVELLE NOMENCLATURE) ---
# Assurez-vous que les fichiers stratégies contiennent bien ces noms de classes
from core.valuation.strategies.dcf_standard import StandardFCFFStrategy
from core.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy
from core.valuation.strategies.dcf_growth import RevenueBasedStrategy
from core.valuation.strategies.rim_banks import RIMBankingStrategy
from core.valuation.strategies.graham_value import GrahamNumberStrategy
from core.valuation.strategies.monte_carlo import MonteCarloDCFStrategy

logger = logging.getLogger(__name__)

# --- REGISTRE DES STRATÉGIES ---
# Mapping strict : Enum (models.py) -> Classe Python (strategies/*.py)
STRATEGY_REGISTRY: Dict[ValuationMode, Type[ValuationStrategy]] = {
    # 1. Standard DCF (ex-Simple)
    ValuationMode.DISCOUNTED_CASH_FLOW_STANDARD: StandardFCFFStrategy,

    # 2. Cyclical / Fundamental (ex-Fundamental)
    ValuationMode.NORMALIZED_FCFF_CYCLICAL: FundamentalFCFFStrategy,

    # 3. High Growth / Tech
    ValuationMode.REVENUE_DRIVEN_GROWTH: RevenueBasedStrategy,

    # 4. Banks & Insurance (Nouveau RIM)
    ValuationMode.RESIDUAL_INCOME_MODEL: RIMBankingStrategy,

    # 5. Graham 1974 (Revised)
    ValuationMode.GRAHAM_1974_REVISED: GrahamNumberStrategy,

    # 6. Monte Carlo
    ValuationMode.PROBABILISTIC_DCF_MONTE_CARLO: MonteCarloDCFStrategy,
}


def run_valuation(request: ValuationRequest, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
    """
    Fonction principale d'exécution.
    Instancie la bonne stratégie et retourne un résultat typé (Polymorphique).
    """
    logger.info(f"Engine requested: {request.mode} for {request.ticker}")

    strategy_cls = STRATEGY_REGISTRY.get(request.mode)

    if not strategy_cls:
        # Erreur fatale si le mode demandé n'est pas dans le registre
        raise CalculationError(f"Mode de valorisation inconnu ou non implémenté : {request.mode}")

    try:
        # Instanciation et Exécution de la stratégie
        strategy = strategy_cls()
        result = strategy.execute(financials, params)

        # On rattache la requête originale au résultat pour le traçage UI
        # (Permet à l'UI de savoir quel mode a été demandé pour afficher le bon titre)
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
    Calcule le taux de croissance implicite (Reverse DCF).
    Utilise la stratégie Fondamentale (Bottom-Up) par défaut car plus stable.
    """
    if market_price <= 0:
        return None

    low = -0.20
    high = 0.50
    # On utilise la stratégie fondamentale pour le Reverse DCF
    strategy = FundamentalFCFFStrategy()

    for _ in range(max_iterations):
        mid = (low + high) / 2.0

        # On crée une copie des paramètres avec le taux testé
        from dataclasses import replace
        test_params = replace(params, fcf_growth_rate=mid)

        try:
            result = strategy.execute(financials, test_params)
            iv = result.intrinsic_value_per_share

            # Convergence trouvée
            if abs(iv - market_price) < 0.5:
                return mid

            # Dichotomie
            if iv < market_price:
                low = mid
            else:
                high = mid
        except:
            # En cas d'erreur de calcul (ex: WACC < g), on réduit la borne haute
            high = mid

    return None