"""
app/ui/expert_terminals/
Terminaux de saisie expert — un fichier par modèle de valorisation.

Chaque terminal hérite de ExpertTerminalBase et implémente
uniquement render_model_inputs() avec les widgets spécifiques.

Usage :
    from app.ui.expert.terminals import create_expert_terminal
    
    terminal = create_expert_terminal(ValuationMode.DDM, "AAPL")
    request = terminal.render()  # Affiche l'UI et retourne la requête
"""

"""
app/ui/expert/terminals/
Terminaux d'expert pour la valorisation avancée.
"""

from .fcff_standard_terminal import FCFFStandardTerminalExpert
from .fcff_normalized_terminal import FCFFNormalizedTerminalExpert
from .fcff_growth_terminal import FCFFGrowthTerminalExpert
from .fcfe_terminal import FCFETerminalExpert
from .ddm_terminal import DDMTerminalExpert
from .rim_bank_terminal import RIMBankTerminalExpert
from .graham_value_terminal import GrahamValueTerminalExpert
from .shared_widgets import (
    widget_projection_years,
    widget_growth_rate,
    widget_cost_of_capital,
    widget_terminal_value_dcf,
    widget_monte_carlo,
    widget_scenarios,
    widget_peer_triangulation,
    build_dcf_parameters
)

__all__ = [
    "FCFFStandardTerminalExpert",
    "FCFFNormalizedTerminalExpert",
    "FCFFGrowthTerminalExpert",
    "FCFETerminalExpert",
    "DDMTerminalExpert",
    "RIMBankTerminalExpert",
    "GrahamValueTerminalExpert",
    "widget_projection_years",
    "widget_growth_rate",
    "widget_cost_of_capital",
    "widget_terminal_value_dcf",
    "widget_monte_carlo",
    "widget_scenarios",
    "widget_peer_triangulation",
    "build_dcf_parameters"
]
