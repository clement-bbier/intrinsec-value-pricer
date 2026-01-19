"""
src/utilities/formatting.py

Utilitaires de formatage partagés.

Ces fonctions sont utilisées à la fois par la logique métier
et par l'interface utilisateur pour un formatage cohérent.

Version : V2.0 — ST-1.2 Type-Safe Resolution
Pattern : Pure Functions
Style : Numpy Style docstrings

RISQUES FINANCIERS:
- Un formatage incorrect peut induire en erreur l'utilisateur
- Les arrondis doivent être cohérents avec les conventions financières
"""

from __future__ import annotations

import numpy as np
from typing import Optional


def format_smart_number(val: Optional[float], currency: str = "", is_pct: bool = False) -> str:
    """Formatte les nombres pour éviter les coupures UI (Millions, Billions)."""
    if val is None or (isinstance(val, float) and np.isnan(val)): return "—"
    if is_pct: return f"{val:.2%}"

    abs_val = abs(val)
    if abs_val >= 1e12: return f"{val/1e12:,.2f} T {currency}"
    if abs_val >= 1e9:  return f"{val/1e9:,.2f} B {currency}"
    if abs_val >= 1e6:  return f"{val/1e6:,.2f} M {currency}"
    return f"{val:,.2f} {currency}"
