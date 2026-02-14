"""
tests/unit/test_i18n_coherence.py

UNIT TESTS FOR I18N MODULE COHERENCE
====================================
Role: Validates i18n module exports and class availability.
Coverage: i18n module structure, duplicate imports, class accessibility.
Architecture: i18n Layer Tests.
Style: Pytest with import validation.
"""

import pytest

import src.i18n as i18n_module


class TestI18nModuleImports:
    """Test suite for validating i18n module imports and exports."""

    def test_module_imports_successfully(self):
        """The i18n module should import without errors despite duplicates."""
        # If we got here, the module imported successfully
        assert i18n_module is not None

    def test_all_exports_in_all_list(self):
        """All classes listed in __all__ should be importable."""
        all_exports = i18n_module.__all__

        # Verify __all__ exists and is a list
        assert isinstance(all_exports, list)
        assert len(all_exports) > 0

        # Check each export is actually available in the module
        for export_name in all_exports:
            assert hasattr(i18n_module, export_name), (
                f"Export '{export_name}' listed in __all__ but not found in module"
            )

    def test_duplicate_imports_documented(self):
        """
        Document the duplicate imports in the i18n module.

        The i18n/__init__.py file has duplicate imports:
        - RegistryTexts is imported twice (lines 9 and 28)
        - StrategyFormulas is imported twice (lines 10 and 29)

        This test verifies that despite the duplicates, the module works correctly.
        """
        # Verify that the duplicated classes are still accessible
        assert hasattr(i18n_module, 'RegistryTexts')
        assert hasattr(i18n_module, 'StrategyFormulas')

        # The duplicates shouldn't cause runtime errors - Python just uses the last one
        registry_texts = getattr(i18n_module, 'RegistryTexts')
        strategy_formulas = getattr(i18n_module, 'StrategyFormulas')

        assert registry_texts is not None
        assert strategy_formulas is not None


class TestKeyI18nClasses:
    """Test suite for validating key i18n class availability."""

    def test_calculation_errors_class_exists(self):
        """CalculationErrors class should be importable and have string attributes."""
        from src.i18n import CalculationErrors

        assert CalculationErrors is not None

        # Spot check: It should have some error message attributes
        # (We'll check if it has at least some attributes)
        attrs = [attr for attr in dir(CalculationErrors) if not attr.startswith('_')]
        assert len(attrs) > 0

    def test_common_texts_class_exists(self):
        """CommonTexts class should be importable and have string attributes."""
        from src.i18n import CommonTexts

        assert CommonTexts is not None

        # Spot check for some attributes
        attrs = [attr for attr in dir(CommonTexts) if not attr.startswith('_')]
        assert len(attrs) > 0

    def test_registry_texts_class_exists(self):
        """RegistryTexts class should be importable."""
        from src.i18n import RegistryTexts

        assert RegistryTexts is not None

        # Spot check for attributes
        attrs = [attr for attr in dir(RegistryTexts) if not attr.startswith('_')]
        assert len(attrs) > 0

    def test_strategy_sources_class_exists(self):
        """StrategySources class should be importable."""
        from src.i18n import StrategySources

        assert StrategySources is not None

        # Spot check for attributes
        attrs = [attr for attr in dir(StrategySources) if not attr.startswith('_')]
        assert len(attrs) > 0

    def test_strategy_formulas_class_exists(self):
        """StrategyFormulas class should be importable despite duplicate import."""
        from src.i18n import StrategyFormulas

        assert StrategyFormulas is not None

        # Spot check for attributes
        attrs = [attr for attr in dir(StrategyFormulas) if not attr.startswith('_')]
        assert len(attrs) > 0


class TestI18nClassAttributes:
    """Test suite for spot-checking i18n class attributes."""

    def test_calculation_errors_has_string_attributes(self):
        """CalculationErrors should have string constants for error messages."""
        from src.i18n import CalculationErrors

        # Get all non-private attributes
        attrs = [attr for attr in dir(CalculationErrors) if not attr.startswith('_')]

        # At least one should be a string (error messages)
        string_attrs = [
            attr for attr in attrs
            if isinstance(getattr(CalculationErrors, attr, None), str)
        ]

        assert len(string_attrs) > 0, "CalculationErrors should have string attributes"

    def test_common_texts_has_string_attributes(self):
        """CommonTexts should have string constants for UI text."""
        from src.i18n import CommonTexts

        attrs = [attr for attr in dir(CommonTexts) if not attr.startswith('_')]

        # At least one should be a string
        string_attrs = [
            attr for attr in attrs
            if isinstance(getattr(CommonTexts, attr, None), str)
        ]

        assert len(string_attrs) > 0, "CommonTexts should have string attributes"

    def test_registry_texts_has_string_attributes(self):
        """RegistryTexts should have string constants for strategy labels."""
        from src.i18n import RegistryTexts

        attrs = [attr for attr in dir(RegistryTexts) if not attr.startswith('_')]

        # At least one should be a string
        string_attrs = [
            attr for attr in attrs
            if isinstance(getattr(RegistryTexts, attr, None), str)
        ]

        assert len(string_attrs) > 0, "RegistryTexts should have string attributes"


class TestAllExportsImportable:
    """Test suite for validating all exports are importable."""

    @pytest.mark.parametrize("export_name", [
        "CalculationErrors",
        "DiagnosticTexts",
        "ModelTexts",
        "KPITexts",
        "RegistryTexts",
        "StrategyFormulas",
        "StrategyInterpretations",
        "StrategySources",
        "SharedTexts",
        "WorkflowTexts",
        "CommonTexts",
        "ExpertTexts",
        "ExtensionTexts",
        "ResultsTexts",
        "SidebarTexts",
        "LegalTexts",
        "QuantTexts",
        "ChartTexts",
        "BacktestTexts",
        "PillarLabels",
        "SOTPTexts",
        "InputLabels",
        "BenchmarkTexts",
        "MarketTexts",
        "PeersTexts"
    ])
    def test_export_is_importable(self, export_name):
        """Each export in __all__ should be importable from the i18n module."""
        assert hasattr(i18n_module, export_name), f"{export_name} not found in i18n module"

        exported_class = getattr(i18n_module, export_name)
        assert exported_class is not None
