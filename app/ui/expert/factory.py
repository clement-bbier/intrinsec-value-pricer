"""
app/ui/expert_terminals/factory.py
FACTORY — Création dynamique des terminaux experts.

Pattern : Factory Method (GoF)

La factory maintient un registre de tous les terminaux disponibles
et instancie le bon selon le mode de valorisation sélectionné.

Usage :
    terminal = create_expert_terminal(ValuationMode.DDM, "AAPL")
    request = terminal.render()
"""

from __future__ import annotations

from typing import Dict, Type, List

from src.domain.models import ValuationMode
from app.ui.base import ExpertTerminalBase

# Import des terminaux concrets
from app.ui.expert.terminals.fcff_standard_terminal import FCFFStandardTerminal
from app.ui.expert.terminals.fcff_normalized_terminal import FCFFNormalizedTerminal
from app.ui.expert.terminals.fcff_growth_terminal import FCFFGrowthTerminal
from app.ui.expert.terminals.fcfe_terminal import FCFETerminal
from app.ui.expert.terminals.ddm_terminal import DDMTerminal
from app.ui.expert.terminals.rim_bank_terminal import RIMBankTerminal
from app.ui.expert.terminals.graham_value_terminal import GrahamValueTerminal


class ExpertTerminalFactory:
    """
    Factory pour créer les terminaux experts.
    
    Le registre associe chaque ValuationMode à sa classe de terminal.
    """
    
    # Registre des terminaux disponibles
    _REGISTRY: Dict[ValuationMode, Type[ExpertTerminalBase]] = {
        ValuationMode.FCFF_STANDARD: FCFFStandardTerminal,
        ValuationMode.FCFF_NORMALIZED: FCFFNormalizedTerminal,
        ValuationMode.FCFF_GROWTH: FCFFGrowthTerminal,
        ValuationMode.FCFE: FCFETerminal,
        ValuationMode.DDM: DDMTerminal,
        ValuationMode.RIM: RIMBankTerminal,
        ValuationMode.GRAHAM: GrahamValueTerminal,
    }
    
    @classmethod
    def create(cls, mode: ValuationMode, ticker: str) -> ExpertTerminalBase:
        """
        Crée le terminal approprié pour le mode donné.
        
        Parameters
        ----------
        mode : ValuationMode
            Le mode de valorisation.
        ticker : str
            Le symbole boursier.
        
        Returns
        -------
        ExpertTerminalBase
            Instance du terminal prête à être rendue.
        
        Raises
        ------
        ValueError
            Si le mode n'a pas de terminal associé.
        """
        terminal_class = cls._REGISTRY.get(mode)
        
        if terminal_class is None:
            available = ", ".join(m.value for m in cls._REGISTRY.keys())
            raise ValueError(
                f"Aucun terminal pour le mode '{mode.value}'. "
                f"Modes disponibles: {available}"
            )
        
        return terminal_class(ticker)
    
    @classmethod
    def get_available_modes(cls) -> List[ValuationMode]:
        """Liste des modes avec un terminal expert."""
        return list(cls._REGISTRY.keys())
    
    @classmethod
    def get_mode_display_names(cls) -> Dict[ValuationMode, str]:
        """Mapping mode -> nom d'affichage."""
        return {
            mode: terminal.DISPLAY_NAME
            for mode, terminal in cls._REGISTRY.items()
        }
    
    @classmethod
    def get_mode_descriptions(cls) -> Dict[ValuationMode, str]:
        """Mapping mode → description."""
        return {
            mode: terminal.DESCRIPTION
            for mode, terminal in cls._REGISTRY.items()
        }


def create_expert_terminal(mode: ValuationMode, ticker: str) -> ExpertTerminalBase:
    """
    Raccourci pour créer un terminal expert.
    
    Parameters
    ----------
    mode : ValuationMode
        Le mode de valorisation.
    ticker : str
        Le symbole boursier.
    
    Returns
    -------
    ExpertTerminalBase
        Terminal prêt à être rendu.
    
    Example
    -------
    >>> terminal = create_expert_terminal(ValuationMode.DDM, "AAPL")
    >>> request = terminal.render()  # Affiche l'UI
    """
    return ExpertTerminalFactory.create(mode, ticker)
