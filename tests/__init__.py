"""
tests/
Suite de tests complète pour Intrinsec Value Pricer.

Structure :
├── unit/           → Tests unitaires par module (évoluent avec le code)
├── contracts/      → Tests de contrats API (garantissent stabilité des interfaces)
├── integration/    → Tests d'intégration entre composants
├── e2e/            → Tests End-to-End du workflow complet
├── conftest.py     → Fixtures partagées
└── test_*.py       → Tests legacy (à migrer progressivement)

Philosophie :
- Les tests `contracts/` NE DOIVENT PAS CHANGER lors des refactorings internes
- Les tests `unit/` peuvent évoluer avec l'implémentation
- Les tests `integration/` vérifient l'assemblage des modules
- Les tests `e2e/` simulent le parcours utilisateur complet

Commandes :
    pytest tests/                       # Tous les tests
    pytest tests/unit/                  # Unitaires uniquement
    pytest tests/contracts/             # Contrats uniquement
    pytest tests/ -m "not slow"         # Exclure les tests lents
    pytest tests/ --cov=core --cov=app  # Avec couverture
"""
