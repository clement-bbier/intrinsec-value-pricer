"""
tests/contracts/
Tests de Contrats API — Garantissent la stabilité des interfaces publiques.

Ces tests NE DOIVENT PAS CHANGER lors des refactorings internes.
Ils définissent le "contrat" que le code doit respecter.

Si un test de contrat échoue après un refactoring, c'est que
l'interface publique a changé de manière non rétrocompatible.

Organisation :
- test_models_contracts.py      → Schémas Pydantic stables
- test_engines_contracts.py     → API run_valuation()
- test_registry_contracts.py    → API du registre centralisé
- test_audit_contracts.py       → API AuditEngine
- test_i18n_contracts.py        → Exports core.i18n stables
"""
