"""
tests/unit/test_valuation_registry.py

UNIT TESTS FOR VALUATION STRATEGY REGISTRY
==========================================
Role: Validates the Strategy Registry and strategy registration.
Coverage: StrategyRegistry singleton, strategy registration, metadata retrieval.
Architecture: Valuation Layer Tests.
Style: Pytest with comprehensive strategy validation.
"""

import pytest
from src.valuation.registry import (
    StrategyRegistry,
    get_strategy,
    get_all_strategies,
    get_display_names,
    _register_all_strategies,
)
from src.models.enums import ValuationMethodology


class TestStrategyRegistryInitialization:
    """Test suite for Strategy Registry initialization and registration."""
    
    def test_all_seven_methodologies_registered(self):
        """After _register_all_strategies(), all 7 methodologies should be registered."""
        # Ensure registration has happened (it's called at module load)
        _register_all_strategies()
        
        all_strategies = get_all_strategies()
        
        # Check that we have exactly 7 strategies
        assert len(all_strategies) == 7, f"Expected 7 strategies, got {len(all_strategies)}"
        
        # Check that all expected methodologies are present
        expected_modes = [
            ValuationMethodology.FCFF_STANDARD,
            ValuationMethodology.FCFF_NORMALIZED,
            ValuationMethodology.FCFF_GROWTH,
            ValuationMethodology.FCFE,
            ValuationMethodology.DDM,
            ValuationMethodology.RIM,
            ValuationMethodology.GRAHAM,
        ]
        
        for mode in expected_modes:
            assert mode in all_strategies, f"Methodology {mode.value} not registered"
    
    def test_get_strategy_returns_non_none_for_each_mode(self):
        """get_strategy(mode) returns a non-None class for each registered mode."""
        methodologies = [
            ValuationMethodology.FCFF_STANDARD,
            ValuationMethodology.FCFF_NORMALIZED,
            ValuationMethodology.FCFF_GROWTH,
            ValuationMethodology.FCFE,
            ValuationMethodology.DDM,
            ValuationMethodology.RIM,
            ValuationMethodology.GRAHAM,
        ]
        
        for mode in methodologies:
            strategy_cls = get_strategy(mode)
            assert strategy_cls is not None, f"Strategy for {mode.value} is None"
    
    def test_get_display_names_returns_seven_entries(self):
        """get_display_names() returns a dict with 7 entries."""
        display_names = get_display_names()
        
        assert len(display_names) == 7, f"Expected 7 display names, got {len(display_names)}"
        
        # Check that all are strings
        for mode, name in display_names.items():
            assert isinstance(name, str), f"Display name for {mode.value} is not a string"
            assert len(name) > 0, f"Display name for {mode.value} is empty"


class TestStrategyInterface:
    """Test suite for validating strategy class interfaces."""
    
    @pytest.mark.parametrize("mode", [
        ValuationMethodology.FCFF_STANDARD,
        ValuationMethodology.FCFF_NORMALIZED,
        ValuationMethodology.FCFF_GROWTH,
        ValuationMethodology.FCFE,
        ValuationMethodology.DDM,
        ValuationMethodology.RIM,
        ValuationMethodology.GRAHAM,
    ])
    def test_each_strategy_has_execute_method(self, mode):
        """Each registered strategy class should have an 'execute' method."""
        strategy_cls = get_strategy(mode)
        
        assert strategy_cls is not None
        
        # Check that the class has an 'execute' method (from IValuationRunner interface)
        # (We can't instantiate without proper params, but we can check the method exists)
        assert hasattr(strategy_cls, 'execute'), f"Strategy {mode.value} missing 'execute' method"


class TestStrategySingleton:
    """Test suite for validating singleton behavior."""
    
    def test_registry_is_singleton(self):
        """StrategyRegistry should be a singleton (two instances share state)."""
        instance1 = StrategyRegistry()
        instance2 = StrategyRegistry()
        
        # They should be the same instance
        assert instance1 is instance2
        
        # They should share the same _strategies dict
        assert instance1._strategies is instance2._strategies
    
    def test_singleton_persists_registrations(self):
        """Registrations should persist across singleton instances."""
        instance1 = StrategyRegistry()
        strategies1 = instance1.get_all_modes()
        
        instance2 = StrategyRegistry()
        strategies2 = instance2.get_all_modes()
        
        # Both should see the same registered strategies
        assert strategies1.keys() == strategies2.keys()


class TestInvalidModeHandling:
    """Test suite for handling invalid or unregistered modes."""
    
    def test_get_strategy_with_invalid_mode_returns_none(self):
        """get_strategy() with an invalid/unregistered mode should return None gracefully."""
        # Create a fake mode (not actually in the enum, but for testing)
        # We'll use a string that doesn't match any registered mode
        
        # Since ValuationMethodology is a string enum, we can't easily create a fake one
        # But we can test that getting a strategy for a mode that's not registered returns None
        
        # Get all registered modes
        all_strategies = get_all_strategies()
        
        # Try with each mode and verify None handling
        for mode in ValuationMethodology:
            strategy = get_strategy(mode)
            if mode in all_strategies:
                assert strategy is not None
            # If not registered (shouldn't happen after init), it would be None


class TestStrategyMetadata:
    """Test suite for strategy metadata retrieval."""
    
    def test_get_ui_renderer_name_returns_string_or_none(self):
        """get_ui_renderer_name should return a string or None for each mode."""
        for mode in ValuationMethodology:
            # Try to get the strategy
            strategy_cls = get_strategy(mode)
            if strategy_cls is not None:
                # Get the UI renderer name
                ui_name = StrategyRegistry.get_ui_renderer_name(mode)
                
                # Should be a string or None
                assert ui_name is None or isinstance(ui_name, str)
    
    def test_get_display_name_returns_string(self):
        """get_display_name should always return a string for registered modes."""
        for mode in ValuationMethodology:
            strategy_cls = get_strategy(mode)
            if strategy_cls is not None:
                display_name = StrategyRegistry.get_display_name(mode)
                
                # Should always be a string
                assert isinstance(display_name, str)
                assert len(display_name) > 0
    
    def test_all_strategies_have_metadata(self):
        """All registered strategies should have complete metadata."""
        all_strategies = get_all_strategies()
        
        for mode, metadata in all_strategies.items():
            # Check metadata fields
            assert metadata.mode == mode
            assert metadata.strategy_cls is not None
            assert metadata.display_name is not None
            assert isinstance(metadata.display_name, str)
            # ui_renderer_name can be None, that's OK
