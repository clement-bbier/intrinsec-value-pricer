"""
tests/unit/test_ui_backend_contract_integrity.py

UI / BACKEND CONTRACT INTEGRITY TEST
=====================================
Role: Ensures that every UIKey suffix defined in Pydantic models has
a matching session key in the Streamlit UI layer and vice-versa.
Uses Python introspection to detect drift automatically.

Coverage:
  1. UIKeys registry completeness (all extension keys present).
  2. options.py UIKey suffixes reference UIKeys constants.
  3. common.py UIKey suffixes reference UIKeys constants.
  4. InputFactory pulls CommonParameters with correct prefixes.
  5. Sensitivity widget uses global key (no strategy prefix).
  6. shared_widgets.py references UIKeys for extension keys.
"""

import inspect

import pytest

from src.config.constants import UIKeys
from src.models.parameters.common import (
    CapitalStructureParameters,
    FinancialRatesParameters,
)
from src.models.parameters.input_metadata import UIKey
from src.models.parameters.options import (
    BacktestParameters,
    MCParameters,
    PeersParameters,
    ScenariosParameters,
    SensitivityParameters,
    SOTPParameters,
)

# ═══════════════════════════════════════════════════════════════════════════
# 1. UIKeys REGISTRY COMPLETENESS
# ═══════════════════════════════════════════════════════════════════════════

class TestUIKeysRegistryCompleteness:
    """UIKeys registry must define every extension key used by options.py."""

    EXPECTED_EXTENSION_KEYS = [
        "MC_ENABLE", "MC_SIMS",
        "SENS_ENABLE", "SENS_STEP", "SENS_RANGE",
        "SCENARIO_ENABLE",
        "BT_ENABLE", "BT_LOOKBACK",
        "PEER_ENABLE", "PEER_LIST",
        "SOTP_ENABLE", "SOTP_DISCOUNT", "SOTP_SEGS",
    ]

    @pytest.mark.parametrize("attr", EXPECTED_EXTENSION_KEYS)
    def test_extension_key_defined(self, attr):
        """Every extension key constant must exist in UIKeys."""
        assert hasattr(UIKeys, attr), f"UIKeys missing attribute: {attr}"
        val = getattr(UIKeys, attr)
        assert isinstance(val, str) and len(val) > 0

    EXPECTED_RATES_KEYS = ["RF", "MRP", "BETA", "KD", "TAX"]

    @pytest.mark.parametrize("attr", EXPECTED_RATES_KEYS)
    def test_rates_key_defined(self, attr):
        """Every financial rates key constant must exist in UIKeys."""
        assert hasattr(UIKeys, attr)

    EXPECTED_CAPITAL_KEYS = ["DEBT", "CASH", "MINORITIES", "PENSIONS", "SHARES", "SBC_RATE"]

    @pytest.mark.parametrize("attr", EXPECTED_CAPITAL_KEYS)
    def test_capital_key_defined(self, attr):
        """Every capital structure key constant must exist in UIKeys."""
        assert hasattr(UIKeys, attr)


# ═══════════════════════════════════════════════════════════════════════════
# 2. UIKey SUFFIXES MATCH UIKeys CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

def _get_uikey_suffixes(model_cls):
    """Extract all UIKey suffixes from a Pydantic model class."""
    suffixes = {}
    for name, field_info in model_cls.model_fields.items():
        meta = next(
            (m for m in field_info.metadata if isinstance(m, UIKey)),
            None,
        )
        if meta:
            suffixes[name] = meta.suffix
    return suffixes


class TestOptionsUIKeySuffixes:
    """All UIKey suffixes in options.py must match UIKeys constants."""

    def test_mc_keys_use_constants(self):
        """MCParameters UIKey suffixes must match UIKeys values."""
        suffixes = _get_uikey_suffixes(MCParameters)
        assert suffixes["enabled"] == UIKeys.MC_ENABLE
        assert suffixes["iterations"] == UIKeys.MC_SIMS

    def test_sensitivity_keys_use_constants(self):
        """SensitivityParameters UIKey suffixes must match UIKeys values."""
        suffixes = _get_uikey_suffixes(SensitivityParameters)
        assert suffixes["enabled"] == UIKeys.SENS_ENABLE
        assert suffixes["steps"] == UIKeys.SENS_RANGE
        assert suffixes["wacc_span"] == UIKeys.SENS_STEP
        assert suffixes["growth_span"] == UIKeys.SENS_STEP

    def test_scenario_key_uses_constant(self):
        """ScenariosParameters UIKey suffix must match UIKeys value."""
        suffixes = _get_uikey_suffixes(ScenariosParameters)
        assert suffixes["enabled"] == UIKeys.SCENARIO_ENABLE

    def test_backtest_keys_use_constants(self):
        """BacktestParameters UIKey suffixes must match UIKeys values."""
        suffixes = _get_uikey_suffixes(BacktestParameters)
        assert suffixes["enabled"] == UIKeys.BT_ENABLE
        assert suffixes["lookback_years"] == UIKeys.BT_LOOKBACK

    def test_peer_keys_use_constants(self):
        """PeersParameters UIKey suffixes must match UIKeys values."""
        suffixes = _get_uikey_suffixes(PeersParameters)
        assert suffixes["enabled"] == UIKeys.PEER_ENABLE
        assert suffixes["tickers"] == UIKeys.PEER_LIST

    def test_sotp_keys_use_constants(self):
        """SOTPParameters UIKey suffixes must match UIKeys values."""
        suffixes = _get_uikey_suffixes(SOTPParameters)
        assert suffixes["enabled"] == UIKeys.SOTP_ENABLE
        assert suffixes["conglomerate_discount"] == UIKeys.SOTP_DISCOUNT
        assert suffixes["segments"] == UIKeys.SOTP_SEGS


class TestCommonUIKeySuffixes:
    """All UIKey suffixes in common.py must match UIKeys constants."""

    def test_rates_keys_use_constants(self):
        """FinancialRatesParameters UIKey suffixes must match UIKeys values."""
        suffixes = _get_uikey_suffixes(FinancialRatesParameters)
        assert suffixes["risk_free_rate"] == UIKeys.RF
        assert suffixes["market_risk_premium"] == UIKeys.MRP
        assert suffixes["beta"] == UIKeys.BETA
        assert suffixes["cost_of_debt"] == UIKeys.KD
        assert suffixes["tax_rate"] == UIKeys.TAX

    def test_capital_keys_use_constants(self):
        """CapitalStructureParameters UIKey suffixes must match UIKeys values."""
        suffixes = _get_uikey_suffixes(CapitalStructureParameters)
        assert suffixes["total_debt"] == UIKeys.DEBT
        assert suffixes["cash_and_equivalents"] == UIKeys.CASH
        assert suffixes["minority_interests"] == UIKeys.MINORITIES
        assert suffixes["pension_provisions"] == UIKeys.PENSIONS
        assert suffixes["shares_outstanding"] == UIKeys.SHARES
        assert suffixes["annual_dilution_rate"] == UIKeys.SBC_RATE


# ═══════════════════════════════════════════════════════════════════════════
# 3. InputFactory PULLS COMMON PARAMS WITH CORRECT PREFIX
# ═══════════════════════════════════════════════════════════════════════════

class TestInputFactoryPrefixContract:
    """InputFactory must assemble CommonParameters with the correct prefixes."""

    @pytest.fixture
    def factory_source(self):
        """Load InputFactory.build_request source."""
        return inspect.getsource(
            __import__(
                "app.controllers.input_factory", fromlist=["InputFactory"]
            ).InputFactory.build_request
        )

    def test_rates_pulled_with_mode_prefix(self, factory_source):
        """Rates must be pulled with the strategy mode prefix."""
        assert "FinancialRatesParameters" in factory_source
        assert "mode_prefix" in factory_source or "prefix=mode_prefix" in factory_source

    def test_capital_pulled_with_bridge_prefix(self, factory_source):
        """Capital must be pulled with the bridge prefix."""
        assert "CapitalStructureParameters" in factory_source
        assert "bridge_prefix" in factory_source or 'bridge_' in factory_source

    def test_extensions_pulled_without_prefix(self, factory_source):
        """Extensions must be pulled with prefix=None."""
        assert "prefix=None" in factory_source


# ═══════════════════════════════════════════════════════════════════════════
# 4. SENSITIVITY USES GLOBAL KEY (NOT STRATEGY PREFIX)
# ═══════════════════════════════════════════════════════════════════════════

class TestSensitivityGlobalKey:
    """Sensitivity widget must use its own global prefix, not the strategy prefix."""

    def test_base_strategy_calls_sensitivity_without_prefix(self):
        """base_strategy.py must call widget_sensitivity() without key_prefix argument."""
        source = inspect.getsource(
            __import__(
                "app.views.inputs.base_strategy", fromlist=["BaseStrategyView"]
            ).BaseStrategyView._render_optional_features
        )
        assert "widget_sensitivity()" in source

    def test_shared_widgets_sensitivity_uses_uikeys(self):
        """widget_sensitivity must use UIKeys.SENS_ENABLE for the toggle key."""
        source = inspect.getsource(
            __import__(
                "app.views.inputs.strategies.shared_widgets",
                fromlist=["widget_sensitivity"],
            ).widget_sensitivity
        )
        assert "UIKeys.SENS_ENABLE" in source
        assert "UIKeys.SENS_STEP" in source
        assert "UIKeys.SENS_RANGE" in source


# ═══════════════════════════════════════════════════════════════════════════
# 5. SHARED WIDGETS REFERENCE UIKeys FOR EXTENSION KEYS
# ═══════════════════════════════════════════════════════════════════════════

class TestSharedWidgetsUIKeysUsage:
    """shared_widgets.py must reference UIKeys constants for extension widget keys."""

    @pytest.fixture
    def widgets_source(self):
        """Load entire shared_widgets module source."""
        import app.views.inputs.strategies.shared_widgets as mod
        return inspect.getsource(mod)

    def test_mc_uses_uikeys(self, widgets_source):
        """Monte Carlo widget must reference UIKeys.MC_ENABLE."""
        assert "UIKeys.MC_ENABLE" in widgets_source
        assert "UIKeys.MC_SIMS" in widgets_source

    def test_backtest_uses_uikeys(self, widgets_source):
        """Backtest widget must reference UIKeys.BT_ENABLE."""
        assert "UIKeys.BT_ENABLE" in widgets_source

    def test_peers_uses_uikeys(self, widgets_source):
        """Peer widget must reference UIKeys.PEER_ENABLE."""
        assert "UIKeys.PEER_ENABLE" in widgets_source

    def test_scenario_uses_uikeys(self, widgets_source):
        """Scenario widget must reference UIKeys.SCENARIO_ENABLE."""
        assert "UIKeys.SCENARIO_ENABLE" in widgets_source

    def test_sotp_uses_uikeys(self, widgets_source):
        """SOTP widget must reference UIKeys.SOTP_ENABLE."""
        assert "UIKeys.SOTP_ENABLE" in widgets_source
        assert "UIKeys.SOTP_DISCOUNT" in widgets_source

    def test_rates_use_uikeys(self, widgets_source):
        """Cost of capital widget must reference UIKeys for rate keys."""
        assert "UIKeys.RF" in widgets_source
        assert "UIKeys.BETA" in widgets_source
        assert "UIKeys.MRP" in widgets_source
        assert "UIKeys.KD" in widgets_source
        assert "UIKeys.TAX" in widgets_source

    def test_bridge_uses_uikeys(self, widgets_source):
        """Equity bridge widget must reference UIKeys for capital keys."""
        assert "UIKeys.DEBT" in widgets_source
        assert "UIKeys.CASH" in widgets_source
        assert "UIKeys.SHARES" in widgets_source
        assert "UIKeys.SBC_RATE" in widgets_source


# ═══════════════════════════════════════════════════════════════════════════
# 6. ORCHESTRATOR RESOLUTION LOGGING
# ═══════════════════════════════════════════════════════════════════════════

class TestOrchestratorResolutionLogging:
    """Orchestrator must log critical resolved parameters."""

    @pytest.fixture
    def orchestrator_source(self):
        """Load orchestrator module source."""
        import src.valuation.orchestrator as mod
        return inspect.getsource(mod)

    def test_resolver_logs_risk_free_rate(self, orchestrator_source):
        """Orchestrator must log resolved Risk-Free Rate."""
        assert "[RESOLVER] Risk-Free Rate" in orchestrator_source

    def test_resolver_logs_beta(self, orchestrator_source):
        """Orchestrator must log resolved Beta."""
        assert "[RESOLVER] Beta resolved" in orchestrator_source

    def test_resolver_logs_wacc_components(self, orchestrator_source):
        """Orchestrator must log WACC components (MRP, Kd, Tax)."""
        assert "[RESOLVER] WACC components" in orchestrator_source

    def test_resolver_logs_capital_structure(self, orchestrator_source):
        """Orchestrator must log Capital Structure (Debt, Cash, Shares)."""
        assert "[RESOLVER] Capital" in orchestrator_source


# ═══════════════════════════════════════════════════════════════════════════
# 7. MASTER INTROSPECTION: EVERY UIKey POINTS TO A VALID UIKeys CONSTANT
# ═══════════════════════════════════════════════════════════════════════════

def _collect_all_uikey_suffixes():
    """
    Walks every Pydantic model that uses UIKey annotations and collects
    (model_name, field_name, suffix) tuples.

    Returns
    -------
    list[tuple[str, str, str]]
        A list of (model_class_name, field_name, uikey_suffix).
    """
    from src.models.parameters.common import CapitalStructureParameters, FinancialRatesParameters
    from src.models.parameters.options import (
        BacktestParameters,
        BaseMCShocksParameters,
        BetaModelMCShocksParameters,
        GrahamMCShocksParameters,
        MCParameters,
        PeersParameters,
        ScenarioParameters,
        ScenariosParameters,
        SensitivityParameters,
        SOTPParameters,
        StandardMCShocksParameters,
    )
    from src.models.parameters.strategies import (
        BaseProjectedParameters,
        DDMParameters,
        FCFEParameters,
        FCFFGrowthParameters,
        FCFFNormalizedParameters,
        FCFFStandardParameters,
        GrahamParameters,
        RIMParameters,
        TerminalValueParameters,
    )

    all_models = [
        FinancialRatesParameters,
        CapitalStructureParameters,
        MCParameters,
        SensitivityParameters,
        ScenariosParameters,
        ScenarioParameters,
        BacktestParameters,
        PeersParameters,
        SOTPParameters,
        BaseMCShocksParameters,
        BetaModelMCShocksParameters,
        StandardMCShocksParameters,
        GrahamMCShocksParameters,
        TerminalValueParameters,
        BaseProjectedParameters,
        FCFFStandardParameters,
        FCFFNormalizedParameters,
        FCFFGrowthParameters,
        FCFEParameters,
        DDMParameters,
        RIMParameters,
        GrahamParameters,
    ]

    results = []
    for model_cls in all_models:
        for name, field_info in model_cls.model_fields.items():
            meta = next(
                (m for m in field_info.metadata if isinstance(m, UIKey)),
                None,
            )
            if meta:
                results.append((model_cls.__name__, name, meta.suffix))
    return results


def _all_uikeys_values():
    """
    Collects every string value defined as a class attribute on UIKeys.

    Returns
    -------
    set[str]
        The set of all registered UIKeys values.
    """
    return {
        v for k, v in vars(UIKeys).items()
        if not k.startswith("_") and isinstance(v, str)
    }


_ALL_UIKEY_SUFFIXES = _collect_all_uikey_suffixes()


class TestMasterUIKeyContractIntegrity:
    """
    Every UIKey suffix in every Pydantic model must point to a value
    that exists in the UIKeys registry.

    This test uses introspection to walk all models automatically so
    any future addition that uses a raw string instead of a UIKeys
    constant will be caught immediately.
    """

    VALID_VALUES = _all_uikeys_values()

    @pytest.mark.parametrize(
        "model_name,field_name,suffix",
        _ALL_UIKEY_SUFFIXES,
        ids=[f"{m}.{f}" for m, f, _ in _ALL_UIKEY_SUFFIXES],
    )
    def test_uikey_suffix_in_registry(self, model_name, field_name, suffix):
        """UIKey suffix must match a value defined in UIKeys."""
        assert suffix in self.VALID_VALUES, (
            f"{model_name}.{field_name} has UIKey('{suffix}') which is not "
            f"registered in UIKeys. Add it to src/core/constants/ui_keys.py."
        )


class TestUIKeysModuleLocation:
    """UIKeys must be importable from the canonical SSOT location."""

    def test_import_from_core_constants(self):
        """UIKeys must be importable from src.core.constants.ui_keys."""
        from src.core.constants.ui_keys import UIKeys as CanonicalUIKeys
        assert hasattr(CanonicalUIKeys, "MC_ENABLE")
        assert hasattr(CanonicalUIKeys, "RF")

    def test_reexport_from_config(self):
        """UIKeys re-exported from src.config.constants must be the same object."""
        from src.config.constants import UIKeys as ReexportedUIKeys
        from src.core.constants.ui_keys import UIKeys as CanonicalUIKeys
        assert ReexportedUIKeys is CanonicalUIKeys
