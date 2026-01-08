"""
core/computation/growth.py
MOTEUR DE PROJECTION DES FLUX
Version : V3.1 — Résilience des Paramètres (None-Safe)
Rôle : Calcul des trajectoires de croissance multi-phases.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def project_flows(
        base_flow: float,
        years: int,
        g_start: float,
        g_term: float,
        high_growth_years: Optional[int] = 0
) -> List[float]:
    """
    Projette des flux financiers (FCF) sur 'years' années.

    Phases :
    1. 'High-Growth Plateau' (si high_growth_years > 0) : Croissance = g_start
    2. 'Linear Fade-Down' : Transition linéaire de g_start vers g_term

    Args:
        base_flow: Le flux de l'année 0.
        years: Horizon de projection (ex: 5).
        g_start: Croissance initiale (décimale).
        g_term: Croissance terminale (décimale).
        high_growth_years: Durée du plateau (Expert Option).

    Returns:
        List[float]: Flux projetés (Année 1 à N).
    """
    if years <= 0:
        return []

    flows: List[float] = []
    current_flow = base_flow

    # Sécurisation du paramètre optionnel pour éviter le crash sur comparaison
    # Si None, on considère qu'il n'y a pas de plateau (0)
    safe_high_growth = high_growth_years if high_growth_years is not None else 0
    n_high = max(0, min(safe_high_growth, years))

    # Sécurisation des taux pour éviter les erreurs de multiplication
    gs = g_start if g_start is not None else 0.0
    gt = g_term if g_term is not None else 0.0

    for t in range(1, years + 1):

        if t <= n_high:
            # PHASE 1 : PLATEAU (Croissance constante)
            current_g = gs
        else:
            # PHASE 2 : FADE-DOWN (Interpolation Linéaire vers g_term)
            years_remaining = years - n_high

            if years_remaining > 0:
                step_in_fade = t - n_high

                # Calcul du facteur d'interpolation (alpha)
                # t=n_high+1 -> alpha petit (proche de g_start)
                # t=years -> alpha = 1 (égal à g_term)
                alpha = step_in_fade / years_remaining
                current_g = gs * (1 - alpha) + gt * alpha
            else:
                current_g = gt

        # Application de la croissance au flux
        current_flow = current_flow * (1.0 + current_g)
        flows.append(current_flow)

    return flows