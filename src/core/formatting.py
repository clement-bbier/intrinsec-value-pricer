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
from dataclasses import dataclass
from enum import Enum

# Standard Institutional Colors (Tailwind CSS Palette)
COLOR_POSITIVE = "#22C55E"  # Green-500
COLOR_NEGATIVE = "#EF4444"  # Red-500
COLOR_NEUTRAL = "#808080"   # Gray-500


class CurrencyPlacement(Enum):
    """Currency symbol placement strategy."""
    PREFIX = "prefix"  # e.g., $100
    SUFFIX = "suffix"  # e.g., 100 €


@dataclass(frozen=True)
class CurrencyInfo:
    """
    Currency metadata for institutional formatting.

    Attributes
    ----------
    code : str
        ISO 4217 currency code (e.g., "USD", "EUR").
    symbol : str
        Visual representation (e.g., "$", "€").
    placement : CurrencyPlacement
        Where to position the symbol relative to the value.
    """
    code: str
    symbol: str
    placement: CurrencyPlacement


class CurrencyFormatter:
    """
    Institutional currency formatting engine.

    Provides ISO 4217 compliant formatting with regional conventions
    for symbol placement and decimal handling.

    Examples
    --------
    >>> formatter = CurrencyFormatter()
    >>> formatter.format(1500000, "USD")
    '$1.50M'
    >>> formatter.format(2300000, "EUR")
    '2.30M €'
    >>> formatter.format(150000000, "JPY")
    '¥150.00M'

    Notes
    -----
    Follows Bloomberg Terminal conventions for consistency across
    institutional workflows.
    """

    # ISO 4217 Currency Registry
    _CURRENCY_REGISTRY: dict[str, CurrencyInfo] = {
        "USD": CurrencyInfo("USD", "$", CurrencyPlacement.PREFIX),
        "EUR": CurrencyInfo("EUR", "€", CurrencyPlacement.SUFFIX),
        "GBP": CurrencyInfo("GBP", "£", CurrencyPlacement.PREFIX),
        "JPY": CurrencyInfo("JPY", "¥", CurrencyPlacement.PREFIX),
        "CHF": CurrencyInfo("CHF", "CHF", CurrencyPlacement.SUFFIX),
        "CAD": CurrencyInfo("CAD", "C$", CurrencyPlacement.PREFIX),
        "AUD": CurrencyInfo("AUD", "A$", CurrencyPlacement.PREFIX),
        "CNY": CurrencyInfo("CNY", "¥", CurrencyPlacement.PREFIX),
        "HKD": CurrencyInfo("HKD", "HK$", CurrencyPlacement.PREFIX),
        "SGD": CurrencyInfo("SGD", "S$", CurrencyPlacement.PREFIX),
        "SEK": CurrencyInfo("SEK", "SEK", CurrencyPlacement.SUFFIX),
        "NOK": CurrencyInfo("NOK", "NOK", CurrencyPlacement.SUFFIX),
        "DKK": CurrencyInfo("DKK", "DKK", CurrencyPlacement.SUFFIX),
        "INR": CurrencyInfo("INR", "₹", CurrencyPlacement.PREFIX),
        "BRL": CurrencyInfo("BRL", "R$", CurrencyPlacement.PREFIX),
        "KRW": CurrencyInfo("KRW", "₩", CurrencyPlacement.PREFIX),
    }

    def __init__(self) -> None:
        """Initialize the currency formatter."""
        pass

    def format(
        self,
        value: float | int | None,
        currency_code: str = "USD",
        decimals: int = 2,
        smart_scale: bool = True
    ) -> str:
        """
        Format a monetary value with proper currency symbol and placement.

        Parameters
        ----------
        value : float | int | None
            The monetary value to format.
        currency_code : str, default="USD"
            ISO 4217 currency code (e.g., "USD", "EUR", "JPY").
        decimals : int, default=2
            Number of decimal places for the scaled value.
        smart_scale : bool, default=True
            Apply institutional scaling (M, B, T) for large values.

        Returns
        -------
        str
            Formatted currency string with proper symbol placement.

        Examples
        --------
        >>> formatter = CurrencyFormatter()
        >>> formatter.format(1500000, "USD")
        '$1.50M'
        >>> formatter.format(2300000, "EUR")
        '2.30M €'
        """
        # Handle null/NaN values
        if value is None:
            return "-"

        if isinstance(value, float) and math.isnan(value):
            return "-"

        # Get currency info
        currency_info = self._CURRENCY_REGISTRY.get(
            currency_code.upper(),
            CurrencyInfo(currency_code, currency_code, CurrencyPlacement.SUFFIX)
        )

        # Format the numeric value
        if smart_scale:
            formatted_value = self._format_with_scale(value, decimals)
        else:
            formatted_value = f"{value:,.{decimals}f}"

        # Apply symbol placement
        if currency_info.placement == CurrencyPlacement.PREFIX:
            return f"{currency_info.symbol}{formatted_value}"
        else:
            return f"{formatted_value} {currency_info.symbol}"

    def _format_with_scale(self, value: float | int, decimals: int) -> str:
        """
        Apply institutional scaling (M, B, T) to large values.

        Parameters
        ----------
        value : float | int
            The value to format.
        decimals : int
            Number of decimal places.

        Returns
        -------
        str
            Scaled value with suffix (e.g., "1.50M").
        """
        abs_val = abs(value)
        suffix = ""
        scaled_val = float(value)

        if abs_val >= 1e12:
            scaled_val = value / 1e12
            suffix = "T"
        elif abs_val >= 1e9:
            scaled_val = value / 1e9
            suffix = "B"
        elif abs_val >= 1e6:
            scaled_val = value / 1e6
            suffix = "M"

        return f"{scaled_val:,.{decimals}f}{suffix}"

    def get_symbol(self, currency_code: str) -> str:
        """
        Get the symbol for a given currency code.

        Parameters
        ----------
        currency_code : str
            ISO 4217 currency code.

        Returns
        -------
        str
            Currency symbol.
        """
        currency_info = self._CURRENCY_REGISTRY.get(
            currency_code.upper(),
            CurrencyInfo(currency_code, currency_code, CurrencyPlacement.SUFFIX)
        )
        return currency_info.symbol


def format_smart_number(
    val: float | int | None,
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
        The currency code (e.g., "USD", "EUR") for proper symbol formatting.
    is_pct : bool, default=False
        If True, formats as a percentage (e.g., 0.05 -> "5.00%").
    decimals : int, default=2
        Number of decimal places to display.

    Returns
    -------
    str
        The formatted string (e.g., "$1.50B" or "5.20%").

    Notes
    -----
    Uses CurrencyFormatter for proper symbol placement when currency is provided.
    """
    # 1. Handling Nulls/NaNs safely
    if val is None:
        return "-"

    if isinstance(val, float) and math.isnan(val):
        return "-"

    # 2. Percentage Case (priority)
    if is_pct:
        return f"{val:.{decimals}%}"

    # 3. Use CurrencyFormatter if currency is provided
    if currency:
        formatter = CurrencyFormatter()
        return formatter.format(val, currency_code=currency, decimals=decimals)

    # 4. Fallback to simple scaling without currency
    abs_val = abs(val)
    suffix = ""
    scaled_val = float(val)

    if abs_val >= 1e12:
        scaled_val = val / 1e12
        suffix = "T"
    elif abs_val >= 1e9:
        scaled_val = val / 1e9
        suffix = "B"
    elif abs_val >= 1e6:
        scaled_val = val / 1e6
        suffix = "M"

    return f"{scaled_val:,.{decimals}f}{suffix}"


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
