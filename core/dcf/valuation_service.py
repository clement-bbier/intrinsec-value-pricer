import logging
from typing import Callable, Dict

from core.models import CompanyFinancials, DCFParameters, DCFResult, ValuationMode
from core.dcf.basic_engine import run_dcf_simple_fcff
from core.dcf.fundamental_engine import run_dcf_fundamental_fcff

logger = logging.getLogger(__name__)


# Registre des moteurs de valorisation
ENGINE_REGISTRY: Dict[
    ValuationMode,
    Callable[[CompanyFinancials, DCFParameters], DCFResult],
] = {
    ValuationMode.SIMPLE_FCFF: run_dcf_simple_fcff,
    ValuationMode.FUNDAMENTAL_FCFF: run_dcf_fundamental_fcff,
    # ValuationMode.MARKET_MULTIPLES: run_dcf_multiples,              # À ajouter plus tard
    # ValuationMode.ADVANCED_SIMULATION: run_dcf_advanced_simulation, # À ajouter plus tard
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
        # Messages d'erreur explicites pour les modes non encore implémentés
        if mode == ValuationMode.MARKET_MULTIPLES:
            raise NotImplementedError("MARKET_MULTIPLES engine not implemented yet.")
        if mode == ValuationMode.ADVANCED_SIMULATION:
            raise NotImplementedError("ADVANCED_SIMULATION engine not implemented yet.")

        # Safety catch (ne devrait pas arriver si l'énumération et le registre sont alignés)
        raise ValueError(f"Unsupported valuation mode: {mode}")

    return engine(financials, params)
