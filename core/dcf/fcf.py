from typing import List


def project_fcfs(fcf_last: float, years: int, growth_rate: float) -> List[float]:
    """
    Simple deterministic projection:
    FCF_t = FCF_{t-1} * (1 + g)

    Returns a list [FCF_1, FCF_2, ..., FCF_n].
    """
    if years <= 0:
        return []

    fcfs = []
    current = fcf_last
    for _ in range(years):
        current *= (1.0 + growth_rate)
        fcfs.append(current)

    return fcfs
