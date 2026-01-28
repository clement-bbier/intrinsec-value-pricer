"""
app/ui/expert_terminals/factory.py

TERMINAL FACTORY — Dynamic creation of expert terminals.

Logical Path Factory
Pattern: Factory Method (GoF)
Style: Numpy docstrings

The factory maintains a registry of all available terminals and
instantiates the correct one based on the selected valuation mode.

ANALYTICAL HIERARCHY (ST-3.1 — McKinsey/Damodaran):
=====================================================
Modes are ordered by increasing analytical depth:

1. DEFENSIVE (Quick Screening)
   - Graham Value: Conservative safety barrier

2. RELATIVE (Market Comparison)
   - RIM Banks: Specialized for financial institutions
   - DDM: Dividend Discount for mature firms

3. FUNDAMENTAL (Intrinsic Value)
   - FCFF Standard: Classic DCF for stable firms
   - FCFF Normalized: DCF with smoothed flows (cyclical)
   - FCFF Growth: Revenue-driven DCF (high-growth)
   - FCFE: Direct Equity for complex structures
"""

from __future__ import annotations

from typing import Dict, Type, List, Tuple
from dataclasses import dataclass
from enum import IntEnum

from src.models import ValuationMode
from src.i18n import SharedTexts
from .base_terminal import ExpertTerminalBase

# Concrete terminal imports
from app.ui.expert.terminals.fcff_standard_terminal import FCFFStandardTerminal
from app.ui.expert.terminals.fcff_normalized_terminal import FCFFNormalizedTerminal
from app.ui.expert.terminals.fcff_growth_terminal import FCFFGrowthTerminal
from app.ui.expert.terminals.fcfe_terminal import FCFETerminal
from app.ui.expert.terminals.ddm_terminal import DDMTerminal
from app.ui.expert.terminals.rim_bank_terminal import RIMBankTerminal
from app.ui.expert.terminals.graham_value_terminal import GrahamValueTerminal


class AnalyticalTier(IntEnum):
    """
    Analytical complexity level for model sorting.

    A lower tier indicates a simpler/more defensive model.
    """
    DEFENSIVE = 1      # Quick screening, safety barrier
    RELATIVE = 2       # Market comparison, multiples
    FUNDAMENTAL = 3    # Intrinsic value, full DCF


@dataclass(frozen=True)
class TerminalMetadata:
    """
    Terminal metadata for sorting and display purposes.

    Attributes
    ----------
    terminal_cls : Type[ExpertTerminalBase]
        The terminal class to instantiate.
    tier : AnalyticalTier
        Analytical complexity tier.
    sort_order : int
        Sorting order within the tier.
    category_label : str
        I18n label for the UI category display.
    """
    terminal_cls: Type[ExpertTerminalBase]
    tier: AnalyticalTier
    sort_order: int
    category_label: str


class ExpertTerminalFactory:
    """
    Factory for creating expert terminals.

    The registry maps each ValuationMode to its corresponding terminal class
    and metadata for sorting within the analytical hierarchy.

    Notes
    -----
    ST-3.1: Modes are ordered to guide the analyst through a
    progressive buildup: Defensive → Relative → Fundamental.
    """

    # Registry enriched with sorting metadata (ST-3.1)
    _REGISTRY: Dict[ValuationMode, TerminalMetadata] = {
        # ══════════════════════════════════════════════════════════════════
        # TIER 1: DEFENSIVE (Quick Screening)
        # ══════════════════════════════════════════════════════════════════
        ValuationMode.GRAHAM: TerminalMetadata(
            terminal_cls=GrahamValueTerminal,
            tier=AnalyticalTier.DEFENSIVE,
            sort_order=1,
            category_label=SharedTexts.CATEGORY_DEFENSIVE
        ),

        # ══════════════════════════════════════════════════════════════════
        # TIER 2: RELATIVE (Market Comparison)
        # ══════════════════════════════════════════════════════════════════
        ValuationMode.RIM: TerminalMetadata(
            terminal_cls=RIMBankTerminal,
            tier=AnalyticalTier.RELATIVE,
            sort_order=1,
            category_label=SharedTexts.CATEGORY_RELATIVE_SECTORIAL
        ),
        ValuationMode.DDM: TerminalMetadata(
            terminal_cls=DDMTerminal,
            tier=AnalyticalTier.RELATIVE,
            sort_order=2,
            category_label=SharedTexts.CATEGORY_RELATIVE_SECTORIAL
        ),

        # ══════════════════════════════════════════════════════════════════
        # TIER 3: FUNDAMENTAL (Intrinsic Value DCF)
        # ══════════════════════════════════════════════════════════════════
        ValuationMode.FCFF_STANDARD: TerminalMetadata(
            terminal_cls=FCFFStandardTerminal,
            tier=AnalyticalTier.FUNDAMENTAL,
            sort_order=1,
            category_label=SharedTexts.CATEGORY_FUNDAMENTAL_DCF
        ),
        ValuationMode.FCFF_NORMALIZED: TerminalMetadata(
            terminal_cls=FCFFNormalizedTerminal,
            tier=AnalyticalTier.FUNDAMENTAL,
            sort_order=2,
            category_label=SharedTexts.CATEGORY_FUNDAMENTAL_DCF
        ),
        ValuationMode.FCFF_GROWTH: TerminalMetadata(
            terminal_cls=FCFFGrowthTerminal,
            tier=AnalyticalTier.FUNDAMENTAL,
            sort_order=3,
            category_label=SharedTexts.CATEGORY_FUNDAMENTAL_DCF
        ),
        ValuationMode.FCFE: TerminalMetadata(
            terminal_cls=FCFETerminal,
            tier=AnalyticalTier.FUNDAMENTAL,
            sort_order=4,
            category_label=SharedTexts.CATEGORY_FUNDAMENTAL_DCF
        ),
    }

    @classmethod
    def create(cls, mode: ValuationMode, ticker: str) -> ExpertTerminalBase:
        """
        Creates the appropriate terminal for the given mode.

        Parameters
        ----------
        mode : ValuationMode
            The valuation mode to instantiate.
        ticker : str
            Target stock ticker.

        Returns
        -------
        ExpertTerminalBase
            Ready-to-render terminal instance.

        Raises
        ------
        ValueError
            If the mode has no associated terminal in the registry.
        """
        metadata = cls._REGISTRY.get(mode)

        if metadata is None:
            available = ", ".join(m.value for m in cls._REGISTRY.keys())
            raise ValueError(
                f"No terminal found for mode '{mode.value}'. "
                f"Available modes: {available}"
            )

        return metadata.terminal_cls(ticker)

    @classmethod
    def get_available_modes(cls) -> List[ValuationMode]:
        """
        Lists available modes sorted by analytical hierarchy (ST-3.1).

        Returns
        -------
        List[ValuationMode]
            Ordered modes: Defensive → Relative → Fundamental.
        """
        return sorted(
            cls._REGISTRY.keys(),
            key=lambda m: (cls._REGISTRY[m].tier, cls._REGISTRY[m].sort_order)
        )

    @classmethod
    def get_mode_display_names(cls) -> Dict[ValuationMode, str]:
        """Mapping from mode to UI display name."""
        return {
            mode: meta.terminal_cls.DISPLAY_NAME
            for mode, meta in cls._REGISTRY.items()
        }

    @classmethod
    def get_mode_descriptions(cls) -> Dict[ValuationMode, str]:
        """Mapping from mode to UI description."""
        return {
            mode: meta.terminal_cls.DESCRIPTION
            for mode, meta in cls._REGISTRY.items()
        }

    @classmethod
    def get_modes_by_tier(cls) -> Dict[AnalyticalTier, List[Tuple[ValuationMode, TerminalMetadata]]]:
        """
        Returns modes grouped by analytical tier (ST-3.1).

        Returns
        -------
        Dict[AnalyticalTier, List[Tuple[ValuationMode, TerminalMetadata]]]
            Modes grouped and sorted by complexity tier.
        """
        result: Dict[AnalyticalTier, List[Tuple[ValuationMode, TerminalMetadata]]] = {}

        for mode, meta in cls._REGISTRY.items():
            if meta.tier not in result:
                result[meta.tier] = []
            result[meta.tier].append((mode, meta))

        # Internal sorting by sort_order
        for tier in result:
            result[tier].sort(key=lambda x: x[1].sort_order)

        return result

    @classmethod
    def get_tier_label(cls, mode: ValuationMode) -> str:
        """
        Returns the category label for a given mode.

        Parameters
        ----------
        mode : ValuationMode
            Target valuation mode.

        Returns
        -------
        str
            I18n category label (e.g., "Defensive", "Fundamental").
        """
        meta = cls._REGISTRY.get(mode)
        return meta.category_label if meta else SharedTexts.CATEGORY_OTHER


def create_expert_terminal(mode: ValuationMode, ticker: str) -> ExpertTerminalBase:
    """
    Factory helper to instantiate an expert terminal.

    Parameters
    ----------
    mode : ValuationMode
        Target valuation mode.
    ticker : str
        Stock ticker symbol.

    Returns
    -------
    ExpertTerminalBase
        Ready-to-render terminal.
    """
    return ExpertTerminalFactory.create(mode, ticker)