"""
app/ui/expert_terminals/
Terminaux de saisie expert — 1 fichier par modèle de valorisation.

Chaque terminal hérite de ExpertTerminalBase et implémente
uniquement render_model_inputs() avec les widgets spécifiques.

Usage :
    from app.ui.expert_terminals import create_expert_terminal
    
    terminal = create_expert_terminal(ValuationMode.DDM, "AAPL")
    request = terminal.render()  # Affiche l'UI et retourne la requête
"""

from app.ui.expert_terminals.factory import (
    ExpertTerminalFactory,
    create_expert_terminal,
)

__all__ = [
    "ExpertTerminalFactory",
    "create_expert_terminal",
]
