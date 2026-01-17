"""
app/ui/result_tabs/
Onglets de résultats — Affichage post-valorisation.

Structure :
├── core/          # Onglets toujours visibles
├── optional/      # Onglets conditionnels
└── components/    # Widgets réutilisables

L'orchestrator gère l'ordre et la visibilité des onglets.
"""

from app.ui.result_tabs.orchestrator import ResultTabOrchestrator

__all__ = [
    "ResultTabOrchestrator",
]
