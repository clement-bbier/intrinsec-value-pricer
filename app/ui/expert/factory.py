"""
app/ui/expert/factory.py

TERMINAL FACTORY — Dynamic creation of expert terminals.
========================================================
Role: Centralizes the instantiation logic for all valuation interfaces.
Responsibility: Implements Dependency Injection (DI) by providing the
                FinancialDataProvider to concrete terminals.

Architecture: Factory Method (GoF).
Style: Numpy docstrings.
"""

from __future__ import annotations
from typing import Dict, Type, List, Tuple
from dataclasses import dataclass
from enum import IntEnum

from infra.data_providers import YahooFinancialProvider
from infra.macro.default_macro_provider import DefaultMacroProvider
from src.models.enums import ValuationMethodology
from src.i18n import SharedTexts
from .base_terminal import BaseTerminalExpert

# Concrete terminal imports
from app.ui.expert.terminals.fcff_standard_terminal import FCFFStandardTerminalExpert
from app.ui.expert.terminals.fcff_normalized_terminal import FCFFNormalizedTerminalExpert
from app.ui.expert.terminals.fcff_growth_terminal import FCFFGrowthTerminalExpert
from app.ui.expert.terminals.fcfe_terminal import FCFETerminalExpert
from app.ui.expert.terminals.ddm_terminal import DDMTerminalExpert
from app.ui.expert.terminals.rim_bank_terminal import RIMBankTerminalExpert
from app.ui.expert.terminals.graham_value_terminal import GrahamValueTerminalExpert


class AnalyticalTier(IntEnum):
    """
    Analytical complexity level for model sorting.
    Used to guide the user from defensive to fundamental models (ST-3.1).
    """
    DEFENSIVE = 1      # Quick screening
    RELATIVE = 2       # Market comparison
    FUNDAMENTAL = 3    # Intrinsic value (DCF)


@dataclass(frozen=True)
class TerminalMetadata:
    """
    Metadata for terminal organization and UI rendering.
    """
    terminal_cls: Type[BaseTerminalExpert]
    tier: AnalyticalTier
    sort_order: int
    category_label: str


class ExpertTerminalFactory:
    """
    Registry and factory for Expert Terminals.

    This factory handles the mapping between a methodology and its UI implementation,
    ensuring that all dependencies (Providers) are correctly injected.
    """

    # Registry aligned with the Analytical Hierarchy (ST-3.1)
    _REGISTRY: Dict[ValuationMethodology, TerminalMetadata] = {
        # --- TIER 1: DEFENSIVE ---
        ValuationMethodology.GRAHAM: TerminalMetadata(
            terminal_cls=GrahamValueTerminalExpert,
            tier=AnalyticalTier.DEFENSIVE,
            sort_order=1,
            category_label=SharedTexts.CATEGORY_DEFENSIVE
        ),

        # --- TIER 2: RELATIVE ---
        ValuationMethodology.RIM: TerminalMetadata(
            terminal_cls=RIMBankTerminalExpert,
            tier=AnalyticalTier.RELATIVE,
            sort_order=1,
            category_label=SharedTexts.CATEGORY_RELATIVE_SECTORIAL
        ),
        ValuationMethodology.DDM: TerminalMetadata(
            terminal_cls=DDMTerminalExpert,
            tier=AnalyticalTier.RELATIVE,
            sort_order=2,
            category_label=SharedTexts.CATEGORY_RELATIVE_SECTORIAL
        ),

        # --- TIER 3: FUNDAMENTAL ---
        ValuationMethodology.FCFF_STANDARD: TerminalMetadata(
            terminal_cls=FCFFStandardTerminalExpert,
            tier=AnalyticalTier.FUNDAMENTAL,
            sort_order=1,
            category_label=SharedTexts.CATEGORY_FUNDAMENTAL_DCF
        ),
        ValuationMethodology.FCFF_NORMALIZED: TerminalMetadata(
            terminal_cls=FCFFNormalizedTerminalExpert,
            tier=AnalyticalTier.FUNDAMENTAL,
            sort_order=2,
            category_label=SharedTexts.CATEGORY_FUNDAMENTAL_DCF
        ),
        ValuationMethodology.FCFF_GROWTH: TerminalMetadata(
            terminal_cls=FCFFGrowthTerminalExpert,
            tier=AnalyticalTier.FUNDAMENTAL,
            sort_order=3,
            category_label=SharedTexts.CATEGORY_FUNDAMENTAL_DCF
        ),
        ValuationMethodology.FCFE: TerminalMetadata(
            terminal_cls=FCFETerminalExpert,
            tier=AnalyticalTier.FUNDAMENTAL,
            sort_order=4,
            category_label=SharedTexts.CATEGORY_FUNDAMENTAL_DCF
        ),
    }

    @classmethod
    def create_terminal(cls, mode: ValuationMethodology, ticker: str) -> BaseTerminalExpert:
        """
        Instantiates a terminal with its infrastructure dependencies.

        Parameters
        ----------
        mode : ValuationMethodology
            The selected valuation strategy.
        ticker : str
            The stock ticker symbol.

        Returns
        -------
        BaseTerminalExpert
            A fully initialized terminal instance.
        """
        metadata = cls._REGISTRY.get(mode)
        if not metadata:
            raise ValueError(f"Methodology {mode} not registered in Factory.")

        # 1. Setup Infrastructure (Single Source of Truth)
        macro_provider = DefaultMacroProvider()
        financial_provider = YahooFinancialProvider(macro_provider=macro_provider)

        # 2. Injection: Instantiate the terminal with the provider
        return metadata.terminal_cls(ticker=ticker, provider=financial_provider)

    @classmethod
    def get_available_modes(cls) -> List[ValuationMethodology]:
        """Returns modes sorted by analytical hierarchy."""
        return sorted(
            cls._REGISTRY.keys(),
            key=lambda m: (cls._REGISTRY[m].tier, cls._REGISTRY[m].sort_order)
        )

    @classmethod
    def get_modes_by_tier(cls) -> Dict[AnalyticalTier, List[Tuple[ValuationMethodology, TerminalMetadata]]]:
        """Groups modes for tiered UI display."""
        result: Dict[AnalyticalTier, List[Tuple[ValuationMethodology, TerminalMetadata]]] = {}
        for mode, meta in cls._REGISTRY.items():
            if meta.tier not in result:
                result[meta.tier] = []
            result[meta.tier].append((mode, meta))

        for tier in result:
            result[tier].sort(key=lambda x: x[1].sort_order)
        return result


def create_expert_terminal(mode: ValuationMethodology, ticker: str) -> BaseTerminalExpert:
    """
    Public entry point for terminal creation.
    """
    return ExpertTerminalFactory.create_terminal(mode, ticker)