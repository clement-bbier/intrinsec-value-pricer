"""
tests/unit/test_valuation_engines.py
Version "Pure Engine" - Correction du chemin de Patching
"""

import pytest
from unittest.mock import patch, MagicMock
from src.valuation.engines import run_valuation, _build_legacy_registry, STRATEGY_REGISTRY
from src.domain.models import ValuationRequest, ValuationMode, InputSource

class TestStrategyRegistry:
    def test_registry_integrity(self):
        registry = _build_legacy_registry()
        assert ValuationMode.FCFF_STANDARD in registry
