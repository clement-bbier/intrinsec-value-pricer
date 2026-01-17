"""
app/ui/result_tabs/components/kpi_cards.py
Composants pour l'affichage des KPIs.
"""

from typing import Optional

import numpy as np
import streamlit as st


def format_smart_number(
    value: Optional[float],
    currency: str = "",
    is_pct: bool = False,
    decimals: int = 2
) -> str:
    """
    Formate un nombre de manière lisible (M, B, T).
    
    Parameters
    ----------
    value : float
        Valeur à formater.
    currency : str
        Symbole de devise optionnel.
    is_pct : bool
        Si True, affiche en pourcentage.
    decimals : int
        Nombre de décimales.
    
    Returns
    -------
    str
        Chaîne formatée.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    
    if is_pct:
        return f"{value:.{decimals}%}"
    
    abs_val = abs(value)
    if abs_val >= 1e12:
        return f"{value/1e12:,.{decimals}f} T {currency}".strip()
    if abs_val >= 1e9:
        return f"{value/1e9:,.{decimals}f} B {currency}".strip()
    if abs_val >= 1e6:
        return f"{value/1e6:,.{decimals}f} M {currency}".strip()
    
    return f"{value:,.{decimals}f} {currency}".strip()


def render_kpi_metric(
    label: str,
    value: str,
    delta: Optional[str] = None,
    help_text: Optional[str] = None
) -> None:
    """
    Affiche une métrique KPI avec style institutionnel.
    
    Parameters
    ----------
    label : str
        Libellé de la métrique.
    value : str
        Valeur formatée.
    delta : str, optional
        Variation (affichée en vert/rouge).
    help_text : str, optional
        Texte d'aide au survol.
    """
    st.metric(label, value, delta=delta, help=help_text)
