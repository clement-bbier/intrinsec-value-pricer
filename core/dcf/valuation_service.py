import logging
from typing import Callable, Dict

from core.models import CompanyFinancials, DCFParameters, DCFResult, ValuationMode
from core.dcf.basic_engine import run_dcf_simple_fcff
from core.dcf.fundamental_engine import run_dcf_fundamental_fcff
from core.dcf.simulation_engine import run_dcf_advanced_simulation

logger = logging.getLogger(__name__)


# Registre des moteurs de valorisation
# Associe chaque mode (Enum) à sa fonction de calcul (Callable)
ENGINE_REGISTRY: Dict[
    ValuationMode,
    Callable[[CompanyFinancials, DCFParameters], DCFResult],
] = {
    ValuationMode.SIMPLE_FCFF: run_dcf_simple_fcff,
    ValuationMode.FUNDAMENTAL_FCFF: run_dcf_fundamental_fcff,
    ValuationMode.MONTE_CARLO: run_dcf_advanced_simulation,
}


def run_valuation(
    financials: CompanyFinancials,
    params: DCFParameters,
    mode: ValuationMode,
) -> DCFResult:
    """
    Point d'entrée central pour la valorisation.
    Route vers le moteur enregistré dans ENGINE_REGISTRY.
    """
    logger.info("[ValuationService] Mode selected: %s", mode.value)

    engine = ENGINE_REGISTRY.get(mode)

    if engine is None:
        # Si le mode n'est pas dans le registre (ne devrait pas arriver avec l'Enum strict)
        raise ValueError(f"Unsupported valuation mode: {mode}")

    return engine(financials, params)