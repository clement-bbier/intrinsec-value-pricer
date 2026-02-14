"""
infra/data_providers/config.py
Technical configuration for API calls and data extraction.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    """Resiliency and performance parameters for API providers."""

    # Resiliency
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_BASE: float = 1.0  # seconds
    REQUEST_TIMEOUT: float = 10.0  # seconds

    # Caching
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600

    # Data Fetching
    DEFAULT_PERIOD: str = "annual"
    DEFAULT_LIMIT: int = 5
