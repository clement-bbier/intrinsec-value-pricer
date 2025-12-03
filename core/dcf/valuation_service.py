import logging

from core.models import CompanyFinancials, DCFParameters, DCFResult, ValuationMode
from core.dcf.basic_engine import run_dcf_simple_fcff

logger = logging.getLogger(__name__)


def run_valuation(
    financials: CompanyFinancials,
    params: DCFParameters,
    mode: ValuationMode,
) -> DCFResult:
    """
    Central valuation entry point.

    According to the chosen ValuationMode, this function dispatches
    to the appropriate engine (simple FCFF, fundamental, multiples, etc.).
    """

    logger.info("[ValuationService] Mode selected: %s", mode.value)

    if mode == ValuationMode.SIMPLE_FCFF:
        return run_dcf_simple_fcff(financials, params)

    # Placeholders for future engines
    if mode == ValuationMode.FUNDAMENTAL_FCFF:
        raise NotImplementedError("FUNDAMENTAL_FCFF engine not implemented yet.")

    if mode == ValuationMode.MARKET_MULTIPLES:
        raise NotImplementedError("MARKET_MULTIPLES engine not implemented yet.")

    if mode == ValuationMode.ADVANCED_SIMULATION:
        raise NotImplementedError("ADVANCED_SIMULATION engine not implemented yet.")

    # Safety catch (should not happen)
    raise ValueError(f"Unsupported valuation mode: {mode}")
