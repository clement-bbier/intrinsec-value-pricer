import logging
from typing import List

logger = logging.getLogger(__name__)


def project_flows(
        base_flow: float,
        years: int,
        g_start: float,
        g_term: float,
        high_growth_years: int = 0
) -> List[float]:
    """
    Projette des flux financiers (FCF) sur 'years' années.

    Phases :
    1. 'High-Growth Plateau' (si high_growth_years > 0) : Croissance = g_start
    2. 'Linear Fade-Down' : Transition linéaire de g_start vers g_term

    Args:
        base_flow: Le flux de l'année 0.
        years: Horizon de projection (ex: 5).
        g_start: Croissance initiale (ex: 0.05).
        g_term: Croissance terminale (ex: 0.02).
        high_growth_years: Durée du plateau.

    Returns:
        List[float]: Flux projetés (Année 1 à N).
    """
    if years <= 0:
        return []

    flows: List[float] = []
    current_flow = base_flow

    # Le plateau ne peut pas dépasser la période totale moins 1 an (pour permettre la transition)
    # ou alors on reste au taquet tout le long si high_growth >= years
    n_high = max(0, min(high_growth_years, years))

    for t in range(1, years + 1):

        if t <= n_high:
            # PHASE 1 : PLATEAU
            current_g = g_start
        else:
            # PHASE 2 : FADE-DOWN (Interpolation Linéaire)
            # On calcule combien d'années il reste après le plateau pour atteindre la fin
            years_remaining = years - n_high

            if years_remaining > 0:
                # Etape dans la transition (1 = première année de fade, etc.)
                step_in_fade = t - n_high

                # Progression linéaire de 0 (début fade) à 1 (fin période)
                # Mais attention : à la fin de la période (année N), on veut être proche de g_term ?
                # Standard : On interpole pour que la croissance diminue progressivement.

                # Facteur de pondération :
                # Si step_in_fade = 1, on s'éloigne un peu de g_start
                # Si step_in_fade = years_remaining, on touche g_term
                alpha = step_in_fade / years_remaining
                current_g = g_start * (1 - alpha) + g_term * alpha
            else:
                current_g = g_term

        current_flow = current_flow * (1.0 + current_g)
        flows.append(current_flow)

    return flows