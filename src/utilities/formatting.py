"""
src/utilities/formatting.py
Utilitaires de formatage partagés — Grade Institutionnel.
"""
from __future__ import annotations
import numpy as np
from typing import Optional
from src.i18n import CommonTexts

def format_smart_number(
    val: Optional[float],
    currency: str = "",
    is_pct: bool = False,
    decimals: int = 2
) -> str:
    """
    Formatte les nombres pour éviter les coupures UI (Millions, Billions, Trillions).
    Source unique de vérité pour l'application.
    """
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return CommonTexts.VALUE_NOT_AVAILABLE

    if is_pct:
        return f"{val:.{decimals}%}"

    abs_val = abs(val)
    # Conventions institutionnelles : T, B, M
    if abs_val >= 1e12:
        return f"{val/1e12:,.{decimals}f} T {currency}".strip()
    if abs_val >= 1e9:
        return f"{val/1e9:,.{decimals}f} B {currency}".strip()
    if abs_val >= 1e6:
        return f"{val/1e6:,.{decimals}f} M {currency}".strip()

    return f"{val:,.{decimals}f} {currency}".strip()