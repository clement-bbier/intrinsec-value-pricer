"""
app/ui/
Interface Utilisateur Restructurée — Sprint 2

Architecture claire et maintenable :

├── base/                    # Classes abstraites (ABC)
├── expert_terminals/        # 1 fichier par terminal expert
└── result_tabs/             # Onglets de résultats organisés
    ├── core/                # Toujours visibles
    ├── optional/            # Conditionnels selon config
    └── components/          # Widgets réutilisables

Patterns :
- Template Method : Squelette commun pour les terminaux
- Strategy : Onglets interchangeables
- Factory : Création dynamique selon le mode
"""

# Exports principaux
from app.ui.expert_terminals import create_expert_terminal, ExpertTerminalFactory
from app.ui.result_tabs import ResultTabOrchestrator

__all__ = [
    "create_expert_terminal",
    "ExpertTerminalFactory",
    "ResultTabOrchestrator",
]
