"""
tests/e2e/
Tests End-to-End — Simulent le parcours utilisateur complet.

Ces tests vérifient que l'application fonctionne de bout en bout,
comme si un utilisateur réel l'utilisait.

Note: Les tests E2E avec appels réseau réels sont marqués @pytest.mark.slow
et peuvent être exclus avec `pytest -m "not slow"`.

Organisation :
- test_auto_mode_workflow.py    → Workflow mode Auto complet
- test_expert_mode_workflow.py  → Workflow mode Expert complet
- test_error_handling.py        → Gestion des erreurs utilisateur
"""
