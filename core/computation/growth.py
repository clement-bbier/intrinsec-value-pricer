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
    Projette des flux financiers (FCF, Dividendes, etc.) sur 'years' années.
    
    Implémente la logique double :
    1. 'High-Growth Plateau' (si high_growth_years > 0)
    2. 'Linear Fade-Down' (Transition vers g_term)
    
    Args:
        base_flow: Le flux de l'année 0 (TTM ou Normatif).
        years: Horizon de projection.
        g_start: Croissance initiale.
        g_term: Croissance terminale.
        high_growth_years: Durée du plateau de croissance forte.
        
    Returns:
        List[float]: Liste des flux projetés (Année 1 à N).
    """
    # Validation basique
    if years <= 0:
        return []
    
    flows: List[float] = []
    current_flow = base_flow
    
    # Le plateau ne peut pas durer toute la période (il faut min 1 an de transition/fin)
    n_high = max(0, min(high_growth_years, years - 1))
    
    for t in range(1, years + 1):
        
        if t <= n_high:
            # PHASE 1 : PLATEAU
            current_g = g_start
        else:
            # PHASE 2 : FADE-DOWN (Interpolation Linéaire)
            t_trans = t - n_high
            duration_trans = years - n_high
            
            if duration_trans > 0:
                # Progresse de 0.0 à 1.0
                progress = t_trans / duration_trans
                # Lerp: Start -> End
                current_g = g_start - progress * (g_start - g_term)
            else:
                current_g = g_term
        
        current_flow = current_flow * (1.0 + current_g)
        flows.append(current_flow)
        
    return flows