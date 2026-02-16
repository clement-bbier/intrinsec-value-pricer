"""
src/valuation/registry.py

CENTRALIZED VALUATION STRATEGY REGISTRY
=======================================
Role: Singleton registry for mapping analytical modes to strategies.
Pattern: Registry with Decorator-based Auto-Discovery.
Architecture: Decouples strategy execution from UI layers.

Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from src.i18n import RegistryTexts
from src.models import ValuationMethodology
from src.valuation.strategies.interface import IValuationRunner

logger = logging.getLogger(__name__)


@dataclass
class StrategyMetadata:
    """
    Metadata container for valuation strategy mapping.

    Attributes
    ----------
    mode : ValuationMethodology
        Unique identifier for the valuation methodology.
    strategy_cls : Type[IValuationRunner]
        The class implementing the specific valuation algorithm.
    ui_renderer_name : str, optional
        The identifier for the specialized UI renderer in the Expert Terminal.
    display_name : str, optional
        The localized (i18n) label displayed in the application.
    """

    mode: ValuationMethodology
    strategy_cls: type[IValuationRunner]
    ui_renderer_name: str | None = None
    display_name: str | None = None


class StrategyRegistry:
    """
    Global Singleton Registry for valuation methodologies.

    Manages the lifecycle and centralized access to financial strategies.
    """

    _instance: StrategyRegistry | None = None
    _strategies: dict[ValuationMethodology, StrategyMetadata] = {}

    def __new__(cls) -> StrategyRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._strategies = {}
        return cls._instance

    @classmethod
    def register(
        cls,
        mode: ValuationMethodology,
        strategy_cls: type[IValuationRunner],
        ui_renderer_name: str | None = None,
        display_name: str | None = None,
    ) -> None:
        """
        Formally registers a strategy into the calculation core.
        """
        metadata = StrategyMetadata(
            mode=mode,
            strategy_cls=strategy_cls,
            ui_renderer_name=ui_renderer_name,
            display_name=display_name or mode.value,
        )
        cls._strategies[mode] = metadata
        logger.debug("[Registry] Strategy registered | mode=%s", mode.value)

    @classmethod
    def get_strategy_cls(cls, mode: ValuationMethodology) -> type[IValuationRunner] | None:
        """Retrieves the calculation class for a specific mode."""
        metadata = cls._strategies.get(mode)
        return metadata.strategy_cls if metadata else None

    @classmethod
    def get_ui_renderer_name(cls, mode: ValuationMethodology) -> str | None:
        """Identifies the specialized UI renderer for the given mode."""
        metadata = cls._strategies.get(mode)
        return metadata.ui_renderer_name if metadata else None

    @classmethod
    def get_display_name(cls, mode: ValuationMethodology) -> str:
        """Retrieves the localized (i18n) label for the model."""
        metadata = cls._strategies.get(mode)
        return metadata.display_name if metadata else mode.value  # type: ignore[return-value]

    @classmethod
    def get_all_modes(cls) -> dict[ValuationMethodology, StrategyMetadata]:
        """Provides a copy of the full strategy catalog."""
        return cls._strategies.copy()

    @classmethod
    def get_display_names_map(cls) -> dict[ValuationMethodology, str]:
        """Generates a mapping of modes to localized labels for UI components."""
        return {mode: meta.display_name for mode, meta in cls._strategies.items() if meta.display_name}


def register_strategy(
    mode: ValuationMethodology, ui_renderer: str | None = None, display_name: str | None = None
) -> Callable[[type[IValuationRunner]], type[IValuationRunner]]:
    """
    Decorator for automated registration of valuation strategies.
    """

    def decorator(cls: type[IValuationRunner]) -> type[IValuationRunner]:
        StrategyRegistry.register(mode=mode, strategy_cls=cls, ui_renderer_name=ui_renderer, display_name=display_name)
        setattr(cls, "_registered_mode", mode)
        return cls

    return decorator


def get_strategy(mode: ValuationMethodology) -> type[IValuationRunner] | None:
    """Simplified facade for accessing strategy classes."""
    return StrategyRegistry.get_strategy_cls(mode)


def get_all_strategies() -> dict[ValuationMethodology, StrategyMetadata]:
    """Global access to the metadata catalog."""
    return StrategyRegistry.get_all_modes()


def get_display_names() -> dict[ValuationMethodology, str]:
    """Simplified access to localized i18n label mapping."""
    return StrategyRegistry.get_display_names_map()


_REGISTRY_INITIALIZED = False


def _register_all_strategies() -> None:
    """
    Bootstrap function using the CORRECT physical filenames from the filesystem.
    Guarded against double-registration during Streamlit hot-reload.
    """
    global _REGISTRY_INITIALIZED
    if _REGISTRY_INITIALIZED:
        return

    from src.valuation.strategies.ddm import DividendDiscountStrategy
    from src.valuation.strategies.fcfe import FCFEStrategy
    from src.valuation.strategies.fundamental_fcff import FundamentalFCFFStrategy
    from src.valuation.strategies.graham_value import GrahamNumberStrategy
    from src.valuation.strategies.revenue_growth_fcff import RevenueGrowthFCFFStrategy
    from src.valuation.strategies.rim_banks import RIMBankingStrategy
    from src.valuation.strategies.standard_fcff import StandardFCFFStrategy

    # --- Firm Value Approaches (WACC-Based) ---
    StrategyRegistry.register(
        mode=ValuationMethodology.FCFF_STANDARD,
        strategy_cls=StandardFCFFStrategy,
        ui_renderer_name="render_expert_fcff_standard",
        display_name=RegistryTexts.FCFF_STANDARD_L,  # OK
    )

    StrategyRegistry.register(
        mode=ValuationMethodology.FCFF_NORMALIZED,
        strategy_cls=FundamentalFCFFStrategy,
        ui_renderer_name="render_expert_fcff_fundamental",
        display_name=RegistryTexts.FCFF_NORM_L,
    )

    StrategyRegistry.register(
        mode=ValuationMethodology.FCFF_GROWTH,
        strategy_cls=RevenueGrowthFCFFStrategy,
        ui_renderer_name="render_expert_fcff_growth",
        display_name=RegistryTexts.FCFF_GROWTH_L,
    )

    # --- Shareholder Value Approaches (Ke-Based) ---
    StrategyRegistry.register(
        mode=ValuationMethodology.FCFE,
        strategy_cls=FCFEStrategy,
        ui_renderer_name="render_expert_fcfe",
        display_name=RegistryTexts.FCFE_L,
    )

    StrategyRegistry.register(
        mode=ValuationMethodology.DDM,
        strategy_cls=DividendDiscountStrategy,
        ui_renderer_name="render_expert_ddm",
        display_name=RegistryTexts.DDM_L,
    )

    # --- Alternative Models ---
    StrategyRegistry.register(
        mode=ValuationMethodology.RIM,
        strategy_cls=RIMBankingStrategy,
        ui_renderer_name="render_expert_rim",
        display_name=RegistryTexts.RIM_IV_L,
    )

    StrategyRegistry.register(
        mode=ValuationMethodology.GRAHAM,
        strategy_cls=GrahamNumberStrategy,
        ui_renderer_name="render_expert_graham",
        display_name=RegistryTexts.GRAHAM_IV_L,
    )

    _REGISTRY_INITIALIZED = True
    count = len(StrategyRegistry.get_all_modes())
    logger.info("[Registry] %d Strategies loaded successfully.", count)


# Initialization on module load (guarded)
_register_all_strategies()
