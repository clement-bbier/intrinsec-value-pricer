"""
infra/data_providers/config.py
Configuration technique pour les appels API et l'extraction de données.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    """Paramètres de résilience et de performance pour les APIs."""
    # Resiliency
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_BASE: float = 1.0  # secondes
    REQUEST_TIMEOUT: float = 10.0  # secondes

    # Caching
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600

    # Data Fetching
    DEFAULT_PERIOD: str = "annual"
    DEFAULT_LIMIT: int = 5
