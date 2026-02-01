"""
tests/unit/test_valuation_engines.py
Version "Pure Engine" - Correction du chemin de Patching
"""

from src.valuation.engines import _build_legacy_registry
from src.models import ValuationMethodology


class TestStrategyRegistry:
    def test_registry_integrity(self):
        registry = _build_legacy_registry()
        assert ValuationMethodology.FCFF_STANDARD in registry
