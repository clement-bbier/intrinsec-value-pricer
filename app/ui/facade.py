"""
app/ui/facade.py
FACADE DE COMPATIBILITE — Migration Progressive (Strangler Fig)

Cette facade permet d'utiliser la nouvelle architecture UI
tout en maintenant la compatibilite avec le code existant.

Usage dans main.py (futur) :
    from app.ui.facade import render_expert_terminal, render_results
    
    request = render_expert_terminal(mode, ticker)
    if request:
        result = run_valuation(request, ...)
        render_results(result, provider)

La migration se fait progressivement :
1. Ancienne architecture continue a fonctionner (ui_inputs_expert.py)
2. Nouvelle architecture disponible via cette facade
3. A terme, main.py bascule vers la facade
4. Anciens fichiers supprimes
"""

from __future__ import annotations

from typing import Optional, Any

from core.models import ValuationMode, ValuationRequest, ValuationResult


def render_expert_terminal(mode: ValuationMode, ticker: str) -> Optional[ValuationRequest]:
    """
    Point d'entree unifie pour tous les terminaux experts.

    Utilise la Factory pour creer le bon terminal puis le rend.
    Inclut logging pour debuggage.

    Parameters
    ----------
    mode : ValuationMode
        Le mode de valorisation selectionne.
    ticker : str
        Le symbole boursier.

    Returns
    -------
    Optional[ValuationRequest]
        La requete si le formulaire est soumis, None sinon.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.debug(f"[Facade] Creation terminal {mode.value} pour {ticker}")
        from app.ui.expert_terminals import create_expert_terminal

        terminal = create_expert_terminal(mode, ticker)
        logger.debug(f"[Facade] Terminal cree: {type(terminal).__name__}")

        result = terminal.render()
        logger.debug(f"[Facade] Rendu termine, request: {result is not None}")

        return result

    except Exception as e:
        logger.error(f"[Facade] Erreur rendu terminal {mode.value}: {str(e)}")
        return None


def render_results(result: ValuationResult, **kwargs: Any) -> None:
    """
    Affiche les resultats de valorisation.
    
    Cette fonction orchestre l'affichage de tous les onglets
    de resultats (core + optional).
    
    Parameters
    ----------
    result : ValuationResult
        Le resultat de valorisation.
    **kwargs
        Arguments supplementaires (provider, etc.).
    """
    from app.ui.result_tabs import ResultTabOrchestrator
    
    orchestrator = ResultTabOrchestrator()
    orchestrator.render(result, **kwargs)


def get_available_modes():
    """
    Retourne la liste des modes disponibles avec leurs noms d'affichage.
    
    Returns
    -------
    Dict[ValuationMode, str]
        Mapping mode -> nom d'affichage.
    """
    from app.ui.expert_terminals import ExpertTerminalFactory
    return ExpertTerminalFactory.get_mode_display_names()


def get_mode_descriptions():
    """
    Retourne les descriptions des modes.
    
    Returns
    -------
    Dict[ValuationMode, str]
        Mapping mode -> description.
    """
    from app.ui.expert_terminals import ExpertTerminalFactory
    return ExpertTerminalFactory.get_mode_descriptions()


def get_available_modes() -> Dict[ValuationMode, str]:
    """
    Retourne les modes disponibles avec leurs noms d'affichage.

    Utilise la Factory comme source de verite pour les modes supportes.

    Returns
    -------
    Dict[ValuationMode, str]
        Mapping mode -> nom d'affichage.
    """
    return ExpertTerminalFactory.get_mode_display_names()


# ==============================================================================
# MIGRATION COMPLETED — Les fonctions legacy ont été supprimées
# Le nouveau système utilise ExpertTerminalFactory directement
# ==============================================================================
