import logging
from typing import Dict, Type, Tuple, Optional

from core.exceptions import CalculationError, WorkflowError
from core.models import CompanyFinancials, DCFParameters, DCFResult, InputSource, ValuationMode, ValuationRequest
from core.valuation.strategies.abstract import ValuationStrategy

# Import des stratégies concrètes
from core.valuation.strategies.dcf_simple import SimpleFCFFStrategy
from core.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy
from core.valuation.strategies.monte_carlo import MonteCarloDCFStrategy

logger = logging.getLogger(__name__)

# ============================================================
# REGISTRE DES STRATÉGIES (1 Mode = 1 Classe)
# ============================================================
STRATEGY_REGISTRY: Dict[ValuationMode, Type[ValuationStrategy]] = {
    ValuationMode.SIMPLE_FCFF: SimpleFCFFStrategy,
    ValuationMode.FUNDAMENTAL_FCFF: FundamentalFCFFStrategy,
    ValuationMode.MONTE_CARLO: MonteCarloDCFStrategy,
}


def run_valuation(
        request: ValuationRequest,
        financials: CompanyFinancials,
        auto_params: DCFParameters,
) -> Tuple[DCFParameters, DCFResult]:
    """
    Point d'entrée unique et agnostique du moteur de valorisation.

    Responsabilités :
    1. Préparer les paramètres (Auto vs Manuel).
    2. Sélectionner la bonne stratégie via le Registre.
    3. Exécuter.
    """

    # 1. Résolution des paramètres (Priorité : Manuel > Auto)
    if request.input_source == InputSource.MANUAL:
        if request.manual_params is None:
            raise WorkflowError("manual_params est requis en mode MANUAL")

        params = request.manual_params

        # Injection du Beta manuel si présent
        if request.manual_beta is not None:
            financials.beta = float(request.manual_beta)

        # Préservation des volatilités (pour Monte Carlo) depuis l'auto si non définies
        # (Pour éviter des volatilités à 0 si l'expert ne les a pas touchées)
        if params.beta_volatility == 0:
            params.beta_volatility = auto_params.beta_volatility
            params.growth_volatility = auto_params.growth_volatility
            params.terminal_growth_volatility = auto_params.terminal_growth_volatility
    else:
        params = auto_params

    # Override final : Horizon de projection
    params.projection_years = int(request.projection_years)

    # Injection des options Monte Carlo dans les paramètres (Stateless)
    if request.mode == ValuationMode.MONTE_CARLO:
        sims = request.options.get("num_simulations")
        if sims:
            params.num_simulations = int(sims)

    params.normalize_weights()

    logger.info(
        "[Engine] run_valuation | ticker=%s | mode=%s | source=%s",
        request.ticker,
        request.mode.value,
        request.input_source.value,
    )

    # 2. Sélection de la Stratégie (Lookup O(1))
    strategy_cls = STRATEGY_REGISTRY.get(request.mode)

    if not strategy_cls:
        raise CalculationError(f"Mode de valorisation non supporté : {request.mode}")

    # 3. Exécution
    strategy = strategy_cls()
    result = strategy.execute(financials, params)

    return params, result


def run_reverse_dcf(
        financials: CompanyFinancials,
        params: DCFParameters,
        market_price: float,
        tolerance: float = 0.01,
        max_iterations: int = 50,
) -> Optional[float]:
    """
    Reverse DCF (recherche binaire sur fcf_growth_rate).
    Utilise exclusivement la méthode Fondamentale pour la cohérence.
    """
    if market_price <= 0:
        return None

    low = -0.10
    high = 0.30
    strategy = FundamentalFCFFStrategy()

    # Copie propre des params pour éviter les effets de bord
    from dataclasses import replace
    test_params = replace(params)

    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        if abs(high - low) < 1e-5:
            return mid

        test_params.fcf_growth_rate = mid

        try:
            result = strategy.execute(financials, test_params)
            iv = result.intrinsic_value_per_share
        except Exception:
            iv = -999.0

        diff = iv - market_price
        if abs(diff) < tolerance:
            return mid

        if diff > 0:
            high = mid
        else:
            low = mid

    return (low + high) / 2.0