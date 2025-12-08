import logging
from typing import List

from core.exceptions import CalculationError

logger = logging.getLogger(__name__)


def project_fcfs(
        fcf_last: float,
        years: int,
        growth_rate_start: float,
        growth_rate_terminal: float,
        high_growth_years: int = 0
) -> List[float]:
    """
    Projette les Flux de Trésorerie Disponibles (FCFF) futurs.

    Ce moteur supporte deux modes de modélisation financière :

    1. Mode "Fade-Down" (Prudent / Classique) :
       - Activé si high_growth_years = 0.
       - La croissance décélère linéairement dès l'année 1 pour atteindre
         le taux terminal à l'année n.
       - Idéal pour les entreprises matures ou cycliques.

    2. Mode "Three-Stage" (Aggressif / Growth) :
       - Activé si high_growth_years > 0 (ex: 3 ans).
       - Phase 1 (Plateau) : Maintient la croissance forte (g_start) pendant X années.
       - Phase 2 (Transition) : Décélération progressive vers le taux terminal.
       - Idéal pour les entreprises en hyper-croissance (Tech, BioTech).

    Args:
        fcf_last: Le dernier FCFF connu (TTM ou Normatif).
        years: Nombre d'années de projection explicite (n).
        growth_rate_start: Taux de croissance initial (g).
        growth_rate_terminal: Taux de croissance final cible (g_inf).
        high_growth_years: Durée du plateau de haute croissance (0 = désactivé).

    Returns:
        List[float]: La liste des FCFF projetés pour les années 1 à n.
    """

    # Logs de traçabilité pour le debug
    logger.info(
        "[FCF] Projection Start: Base=%.2f | g_start=%.2f%% | g_term=%.2f%% | Plateau=%d ans",
        fcf_last, growth_rate_start * 100, growth_rate_terminal * 100, high_growth_years
    )

    # 1. Validations de sécurité
    if years <= 0:
        logger.error("[FCF] Invalid projection years: %d", years)
        raise CalculationError("La durée de projection doit être positive.")

    if fcf_last is None:
        logger.error("[FCF] fcf_last is None")
        raise CalculationError("Impossible de projeter : le flux de départ est manquant.")

    fcfs: List[float] = []
    current_fcf = fcf_last

    # Sécurité : le plateau ne peut pas dépasser la durée totale de projection - 1
    # (Il faut laisser au moins 1 an pour la transition mathématique)
    n_high = max(0, min(high_growth_years, years - 1))

    # 2. Boucle de Projection (Année par Année)
    for t in range(1, years + 1):

        # --- Cœur de la Logique Multi-Stage ---

        if t <= n_high:
            # PHASE 1 : PLATEAU DE CROISSANCE (High Growth)
            # On maintient le taux fort tant qu'on est dans la fenêtre du plateau.
            current_g = growth_rate_start
            stage = "Plateau High-Growth"

        else:
            # PHASE 2 : TRANSITION (Fade-Down)
            # On doit atterrir en douceur vers g_terminal.

            # Temps écoulé dans la phase de transition (1, 2, ...)
            t_trans = t - n_high
            # Durée totale disponible pour la transition
            duration_trans = years - n_high

            # Formule d'Interpolation Linéaire :
            # g(t) = Start - (Start - End) * (TempsÉcoulé / DuréeTotale)
            if duration_trans > 0:
                progress = t_trans / duration_trans
                current_g = growth_rate_start - progress * (growth_rate_start - growth_rate_terminal)
            else:
                # Cas limite (dernière année si pas de transition)
                current_g = growth_rate_terminal

            stage = "Transition Fade-Down"

        # Application de la croissance au flux précédent
        current_fcf = current_fcf * (1.0 + current_g)
        fcfs.append(current_fcf)

        # Log détaillé pour vérifier la courbe
        logger.debug(
            "[FCF] Année %d (%s) : Croissance=%.2f%% -> FCF=%.2f",
            t, stage, current_g * 100, current_fcf
        )

    # Log du résultat final pour confirmation
    logger.info("[FCF] Projection terminée. Flux Final (An %d) = %.2f", years, fcfs[-1])

    return fcfs