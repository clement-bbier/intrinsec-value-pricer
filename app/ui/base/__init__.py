"""
app/ui/base/
Classes abstraites pour l'UI.

Contenu :
- ExpertTerminalBase : ABC pour les terminaux de saisie expert
- ResultTabBase : ABC pour les onglets de résultats
"""

from app.ui.base.expert_terminal import ExpertTerminalBase
from app.ui.base.result_tab import ResultTabBase

__all__ = [
    "ExpertTerminalBase",
    "ResultTabBase",
]
