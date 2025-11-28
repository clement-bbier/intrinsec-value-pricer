class CalculationError(Exception):
    """Raised when the DCF valuation cannot be computed with the given inputs."""
    pass


class DataProviderError(Exception):
    """Raised when the data provider (e.g. Yahoo) cannot return valid data."""
    pass
