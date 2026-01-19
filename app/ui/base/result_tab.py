"""
app/ui/base/result_tab.py
CLASSE ABSTRAITE — Onglet de Résultats

Pattern : Strategy (GoF)

Chaque onglet implémente cette interface.
L'orchestrator gère l'ordre et la visibilité.

Onglets Core (toujours visibles) :
- InputsSummaryTab       : Hypothèses utilisées
- CalculationProofTab    : Glass Box
- AuditReportTab         : Score de fiabilité

Onglets Optional (conditionnels) :
- PeerMultiplesTab       : Triangulation par multiples
- SOTPBreakdownTab       : Sum-of-the-Parts
- ScenarioAnalysisTab    : Bull/Base/Bear
- HistoricalBacktestTab  : Validation passée
- MonteCarloDistributionTab : Simulations
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.domain.models import ValuationResult


class ResultTabBase(ABC):
    """
    Interface abstraite pour un onglet de résultats.
    
    Attributes
    ----------
    TAB_ID : str
        Identifiant unique (snake_case).
    LABEL : str
        Label affiché dans l'UI.
    ICON : str
        Emoji représentatif.
    ORDER : int
        Priorité d'affichage (1 = premier).
    IS_CORE : bool
        True si toujours visible, False si conditionnel.
    """
    
    # A surcharger dans chaque sous-classe
    TAB_ID: str = "base"
    LABEL: str = "Onglet"
    ICON: str = ""  # Style sobre, pas d'emojis
    ORDER: int = 100
    IS_CORE: bool = False
    
    @abstractmethod
    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche le contenu de l'onglet.
        
        Parameters
        ----------
        result : ValuationResult
            Résultat de valorisation.
        **kwargs
            Contexte additionnel (provider, etc.).
        """
        pass
    
    def is_visible(self, result: ValuationResult) -> bool:
        """
        Détermine si l'onglet doit être affiché.
        
        Les onglets core retournent toujours True.
        Les onglets optionnels vérifient leurs conditions.
        
        Returns
        -------
        bool
            True si visible.
        """
        return self.IS_CORE
    
    def get_display_label(self) -> str:
        """Label pour st.tabs()."""
        return self.LABEL
