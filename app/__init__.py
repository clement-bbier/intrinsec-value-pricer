"""
app/__init__.py
Point d'entrée principal du package applicatif.
Expose les fonctionnalités clés de l'interface et du workflow.
"""

# 1. Exposition de la Factory Expert
# On remonte la profondeur : app -> ui -> expert -> factory
from .ui.expert.factory import create_expert_terminal, ExpertTerminalFactory

# 2. Exposition du Workflow logique (Calcul)
# Permet de faire : from app import run_workflow
from .workflow import run_workflow

# 3. On expose les sous-modules pour la navigation de l'IDE
from . import ui
from . import adapters

__all__ = [
    "create_expert_terminal",
    "ExpertTerminalFactory",
    "run_workflow",
    "ui",
    "adapters"
]