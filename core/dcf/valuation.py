import logging

from core.models import CompanyFinancials, DCFParameters, DCFResult, ValuationMode
from core.dcf.valuation_service import run_valuation

logger = logging.getLogger(__name__)


def run_dcf(financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
    """
    Backward-compatible wrapper around the new multi-mode valuation service.

    For now, it always uses ValuationMode.SIMPLE_FCFF, which corresponds
    to the historical behaviour of this project (basic FCFF DCF).
    """

    logger.info(
        "[run_dcf wrapper] Delegating to run_valuation with mode=SIMPLE_FCFF for %s",
        financials.ticker,
    )

    return run_valuation(
        financials=financials,
        params=params,
        mode=ValuationMode.SIMPLE_FCFF,
    )
