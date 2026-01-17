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
    Affiche le terminal expert et retourne la requete si soumise.
    
    Cette fonction est le point d'entree pour la nouvelle architecture.
    Elle delegue a la factory qui cree le bon terminal.
    
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
    from app.ui.expert_terminals import create_expert_terminal
    
    terminal = create_expert_terminal(mode, ticker)
    return terminal.render()


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


# ==============================================================================
# BACKWARD COMPATIBILITY — Re-exports depuis ui_inputs_expert.py
# Ces fonctions seront depreciees dans une version future.
# ==============================================================================

def safe_factory_params(*args, **kwargs):
    """Deprecated: Use app.ui.expert_terminals.shared_widgets.build_dcf_parameters"""
    from app.ui_components.ui_inputs_expert import safe_factory_params as _legacy
    return _legacy(*args, **kwargs)


def render_standard_fcff_inputs(*args, **kwargs):
    """Deprecated: Use app.ui.expert_terminals.fcff_standard_terminal"""
    from app.ui_components.ui_inputs_expert import render_standard_fcff_inputs as _legacy
    return _legacy(*args, **kwargs)


def render_fundamental_fcff_inputs(*args, **kwargs):
    """Deprecated: Use app.ui.expert_terminals.fcff_normalized_terminal"""
    from app.ui_components.ui_inputs_expert import render_fundamental_fcff_inputs as _legacy
    return _legacy(*args, **kwargs)


def render_growth_fcff_inputs(*args, **kwargs):
    """Deprecated: Use app.ui.expert_terminals.fcff_growth_terminal"""
    from app.ui_components.ui_inputs_expert import render_growth_fcff_inputs as _legacy
    return _legacy(*args, **kwargs)


def render_fcfe_inputs(*args, **kwargs):
    """Deprecated: Use app.ui.expert_terminals.fcfe_terminal"""
    from app.ui_components.ui_inputs_expert import render_fcfe_inputs as _legacy
    return _legacy(*args, **kwargs)


def render_ddm_inputs(*args, **kwargs):
    """Deprecated: Use app.ui.expert_terminals.ddm_terminal"""
    from app.ui_components.ui_inputs_expert import render_ddm_inputs as _legacy
    return _legacy(*args, **kwargs)


def render_rim_inputs(*args, **kwargs):
    """Deprecated: Use app.ui.expert_terminals.rim_bank_terminal"""
    from app.ui_components.ui_inputs_expert import render_rim_inputs as _legacy
    return _legacy(*args, **kwargs)


def render_graham_inputs(*args, **kwargs):
    """Deprecated: Use app.ui.expert_terminals.graham_value_terminal"""
    from app.ui_components.ui_inputs_expert import render_graham_inputs as _legacy
    return _legacy(*args, **kwargs)