"""
src/core/formatting.py

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

import math
from typing import Optional, Union

# Standard Institutional Colors (Tailwind CSS Palette)
COLOR_POSITIVE = "#22C55E"  # Green-500
COLOR_NEGATIVE = "#EF4444"  # Red-500
COLOR_NEUTRAL = "#808080"   # Gray-500


def format_smart_number(
    val: Optional[Union[float, int]],
    currency: str = "",
    is_pct: bool = False,
    decimals: int = 2
) -> str:
    """
    Applies institutional Bloomberg-style formatting to numeric values.
    Handles large magnitudes (M, B, T) automatically.

    Parameters
    ----------
    val : float | int | None
        The numeric value to format.
    currency : str, optional
        The currency symbol to append (e.g., "USD", "EUR").
    is_pct : bool, default=False
        If True, formats as a percentage (e.g., 0.05 -> "5.00%").
    decimals : int, default=2
        Number of decimal places to display.

    Returns
    -------
    str
        The formatted string (e.g., "1.50B USD" or "5.20%").
    """
    # 1. Handling Nulls/NaNs safely
    if val is None:
        return "-"

    if isinstance(val, float) and math.isnan(val):
        return "-"

    # 2. Percentage Case (priority)
    if is_pct:
        return f"{val:.{decimals}%}"

    abs_val = abs(val)
    suffix = ""
    scaled_val = float(val)

    # 3. Institutional Scaling logic
    if abs_val >= 1e12:
        scaled_val = val / 1e12
        suffix = "T"
    elif abs_val >= 1e9:
        scaled_val = val / 1e9
        suffix = "B"
    elif abs_val >= 1e6:
        scaled_val = val / 1e6
        suffix = "M"

    # 4. Final assembly
    # Using comma as thousand separator for the scaled number
    formatted_number = f"{scaled_val:,.{decimals}f}{suffix}"

    if currency:
        return f"{formatted_number} {currency.strip()}"

    return formatted_number


def get_delta_color(val: float, inverse: bool = False) -> str:
    """
    Returns the hex color code based on a numeric delta.

    Standard: Green for positive, Red for negative.
    Used for Upside/Downside rendering in executive summaries.

    Parameters
    ----------
    val : float
        The value to evaluate (usually a percentage delta).
    inverse : bool, default=False
        If True, reverses the logic (useful for Cost/Risk metrics like WACC
        where a higher value is negative).

    Returns
    -------
    str
        Hex color code (e.g., "#22C55E").
    """
    if val == 0:
        return COLOR_NEUTRAL

    is_positive = val > 0

    if inverse:
        is_positive = not is_positive

    return COLOR_POSITIVE if is_positive else COLOR_NEGATIVE