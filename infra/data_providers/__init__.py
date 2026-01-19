"""
infra/data_providers/__init__.py

Package des fournisseurs de données financières.

Version : V2.0 — ST-1.3 Encapsulation Resolution
Pattern : Facade + Adapter
Style : Numpy Style docstrings

Ce package expose uniquement la façade YahooFinanceProvider via __all__.
Les classes internes (YahooRawFetcher, extraction_utils) sont masquées
pour garantir l'encapsulation et permettre des refactorings internes.

Usage recommandé:
    from infra.data_providers import YahooFinanceProvider

Usage avancé (non garanti):
    from infra.data_providers.yahoo_raw_fetcher import YahooRawFetcher

RISQUES FINANCIERS:
- Le provider est la source de données pour toutes les valorisations
- Une erreur de mapping peut invalider l'ensemble des calculs
"""

from __future__ import annotations

# Façade publique (seule interface garantie)
from .yahoo_provider import YahooFinanceProvider

# Classe de base (pour extension de providers)
from .base_provider import DataProvider

# API publique garantie
__all__ = [
    "YahooFinanceProvider",
    "DataProvider",
]
