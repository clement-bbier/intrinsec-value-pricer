"""
src/utilities/formatting.py

INSTITUTIONAL FORMATTING UTILITIES
==================================
Role: Shared logic for data representation across UI, PDF Reports, and Logs.
Standard: Bloomberg/Reuters style notation (M, B, T).

Financial Impact:
-----------------
Visual consistency is critical for rapid decision-making. This module ensures
that magnitudes are immediately recognizable by the analyst.
"""

from __future__ import annotations
import numpy as np
from typing import Optional, Union
from src.i18n import CommonTexts

def format_smart_number(
    val: Optional[Union[float, int]],
    currency: str = "",
    is_pct: bool = False,
    decimals: int = 2
) -> str:
    """
    Formats numbers into human-readable institutional notation.

    Handles Billions (B), Millions (M), and Trillions (T) to prevent
    UI overflow and cognitive overload.

    Parameters
    ----------
    val : float | int, optional
        The raw numeric value to format.
    currency : str, default=""
        The currency symbol (e.g., "$", "€").
    is_pct : bool, default=False
        If True, formats as a percentage (value 0.05 -> "5.00%").
    decimals : int, default=2
        Number of decimal places to preserve.

    Returns
    -------
    str
        Formatted string (e.g., "1.50 B €" or "8.45%").
    """
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return CommonTexts.VALUE_NOT_AVAILABLE

    if is_pct:
        return f"{val:.{decimals}%}"

    abs_val = abs(val)

    # Institutional Scale Logic (Standard Bloomberg/Reuters)
    if abs_val >= 1e12:
        return f"{val/1e12:,.{decimals}f} T {currency}".strip()
    if abs_val >= 1e9:
        return f"{val/1e9:,.{decimals}f} B {currency}".strip()
    if abs_val >= 1e6:
        return f"{val/1e6:,.{decimals}f} M {currency}".strip()

    return f"{val:,.{decimals}f} {currency}".strip()


def get_delta_color(val: float, inverse: bool = False) -> str:
    """
    Returns the hex color code based on a numeric delta.

    Standard: Green for positive, Red for negative.
    Used for Upside/Downside rendering in the Golden Header.

    Parameters
    ----------
    val : float
        The value to evaluate (usually a percentage delta).
    inverse : bool, default=False
        If True, reverses the logic (useful for Cost/Risk metrics like WACC).
    """
    if val == 0:
        return "#808080"  # Gray

    is_positive = val > 0
    if inverse:
        is_positive = not is_positive

    return "#22C55E" if is_positive else "#EF4444"  # Tailwind Green-500 / Red-500

def format_audit_score(score: float) -> str:
    """
    Formats an audit score (0-100) with its institutional rank.
    Maps numeric reliability to qualitative grades used in buy-side reports.

    Example: "85.5/100 (A)"
    """
    rank = "F"
    if score >= 90: rank = "AAA"
    elif score >= 80: rank = "A"
    elif score >= 70: rank = "B"
    elif score >= 50: rank = "C"

    return f"{score:.1f}/100 ({rank})"