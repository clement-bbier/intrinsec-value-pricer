import logging
from typing import List

from core.exceptions import CalculationError

logger = logging.getLogger(__name__)


def project_fcfs(fcf_last: float, years: int, growth_rate: float) -> List[float]:
    """
    Deterministic projection of FCFF values:

        FCF_t = FCF_{t-1} * (1 + g)

    Returns a list:
        [FCF_1, FCF_2, ..., FCF_n]

    Provides full logging for transparency.
    """

    logger.info(
        "[FCF] Starting projection: FCF_last=%.2f | growth_rate=%.4f | years=%d",
        fcf_last,
        growth_rate,
        years,
    )

    if years <= 0:
        logger.error("[FCF] Invalid number of years: %d (must be > 0)", years)
        raise CalculationError("projection_years must be > 0 to project FCFFs.")

    if fcf_last is None:
        logger.error("[FCF] fcf_last is None — cannot project FCFF.")
        raise CalculationError("Cannot project FCFF because fcf_last is missing.")

    fcfs = []
    current = fcf_last

    for t in range(1, years + 1):
        current = current * (1.0 + growth_rate)
        fcfs.append(current)

        logger.info(
            "[FCF] Year %d: FCF_%d = FCF_%d * (1 + g) = %.2f",
            t,
            t,
            t - 1,
            current,
        )

    logger.info("[FCF] Final projected FCFF list: %s", [round(x, 2) for x in fcfs])

    return fcfs
