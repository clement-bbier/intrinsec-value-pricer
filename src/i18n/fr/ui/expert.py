"""
src/i18n/fr/ui/expert.py

DEPRECATED: This module is maintained for backward compatibility only.
==============================================================================
All terminal texts have been migrated to terminals.py (V2 - Institutional Architecture).

For new code, please import from:
    from src.i18n.fr.ui.terminals import CommonTerminals, FCFFStandardTexts, etc.

This file provides aliases for backward compatibility with existing code.
"""

# Import the new centralized structure
from src.i18n.fr.ui.terminals import (
    CommonTerminals,
    DDMTexts,
    FCFETexts,
    FCFFGrowthTexts,
    FCFFNormalizedTexts,
    FCFFStandardTexts,
    GrahamTexts,
    RIMTexts,
)

# Backward compatibility alias
# UISharedTexts is now an alias to CommonTerminals
UISharedTexts = CommonTerminals

# Re-export all classes for backward compatibility
__all__ = [
    "UISharedTexts",  # Alias to CommonTerminals
    "FCFFStandardTexts",
    "FCFFNormalizedTexts",
    "FCFFGrowthTexts",
    "RIMTexts",
    "GrahamTexts",
    "FCFETexts",
    "DDMTexts",
]
