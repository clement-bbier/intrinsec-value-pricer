# TECHNICAL DEBT — État des Corrections

**Dernière mise à jour :** Janvier 2026  
**Total Dettes :** 24 identifiées  
**Corrigées :** 17 ✅  
**Restantes :** 7 (Sprints futurs)

---

## ✅ DETTES CORRIGÉES

### 1. Violations d'Architecture (DT-001, DT-002) ✅

**Solution appliquée :** Pattern Strangler Fig
- Création de `core/i18n/texts.py` (source canonique)
- `app/ui_components/ui_texts.py` devient une facade de ré-export
- Migration de tous les imports `core/` et `infra/` vers `core.i18n`

**Fichiers modifiés :**
- 15+ fichiers dans `core/` et `infra/` migrés

---

### 2. Registres Manuels (DT-007, DT-008, DT-009) ✅

**Solution appliquée :** Decorator Pattern + Centralized Registry
- Création de `core/valuation/registry.py`
- Décorateur `@register_strategy(mode, auditor, ui_renderer)`
- Unification des 3 registres en une seule source

**Fichiers créés/modifiés :**
- `core/valuation/registry.py` (nouveau)
- `core/valuation/engines.py` (utilise le registry)
- `infra/auditing/audit_engine.py` (utilise le registry)
- `app/main.py` (utilise le registry)

---

### 3. Constantes Hardcodées (DT-010, DT-011, DT-012, DT-013) ✅

**Solution appliquée :** Configuration Object Pattern
- Création de `core/config/constants.py`
- Classes immutables : `MonteCarloDefaults`, `PeerDefaults`, `AuditThresholds`, `AuditPenalties`, `AuditWeights`, `SystemDefaults`
- Validation à l'import du module

**Fichiers créés/modifiés :**
- `core/config/__init__.py` (nouveau)
- `core/config/constants.py` (nouveau)
- `app/main.py`, `infra/auditing/auditors.py`, `infra/auditing/audit_engine.py`, `infra/data_providers/yahoo_provider.py`

---

### 4. Couplage UI/Logique (DT-016, DT-017) ✅

**Solution appliquée :** Dependency Inversion + Adapter Pattern
- Création de `core/interfaces/` avec `IUIProgressHandler`, `IResultRenderer`
- Implémentations `NullProgressHandler`, `NullResultRenderer` pour les tests
- Création de `app/adapters/` avec `StreamlitProgressHandler`, `StreamlitResultRenderer`
- `workflow.py` refactoré avec injection de dépendances

**Fichiers créés :**
- `core/interfaces/__init__.py`
- `core/interfaces/ui_handlers.py`
- `app/adapters/__init__.py`
- `app/adapters/streamlit_adapters.py`

---

### 5. Performance Providers (DT-022, DT-023) ✅

**Solution appliquée :**
- DT-022 : Ajout de timeout dans `safe_api_call()` via `ThreadPoolExecutor`
- DT-023 : Création de `config/sector_multiples.yaml` + `infra/ref_data/sector_fallback.py`

**Fichiers créés/modifiés :**
- `infra/data_providers/extraction_utils.py` (timeout ajouté)
- `config/sector_multiples.yaml` (nouveau)
- `infra/ref_data/sector_fallback.py` (nouveau)

---

### 6. Tests Insuffisants (DT-024) ✅

**Solution appliquée :** Suite de tests structurée
- 119 tests (contre 8 initialement)
- Organisation : `unit/`, `contracts/`, `integration/`, `e2e/`
- Fixtures enrichies dans `conftest.py`
- Markers pytest : `@pytest.mark.unit`, `@pytest.mark.integration`, etc.

**Fichiers créés :**
- `tests/__init__.py`, `tests/unit/__init__.py`, `tests/contracts/__init__.py`, etc.
- 12 nouveaux fichiers de tests

---

### 7. Gestion d'Erreurs (DT-020, DT-021) ✅

**Solution appliquée :**
- Migration de `core/exceptions.py` vers `core.i18n`
- Hiérarchie d'exceptions typées préservée

---

## 🔄 DETTES RESTANTES (Sprints Futurs)

### DT-003, DT-004, DT-005, DT-006 : Fichiers Monolithiques

**Statut :** Sprint 2-3 recommandé

| Fichier | Lignes | Proposition |
|---------|--------|-------------|
| `ui_inputs_expert.py` | 523 | Éclater en 1 fichier/terminal + `atoms/` |
| `ui_kpis.py` | 409 | Séparer `components/`, `results/` |
| `ui_texts.py` (core/i18n) | 917 | Réorganiser par domaine → YAML (Sprint 8) |
| `models.py` | 533 | Segmenter en `models/enums.py`, `models/results.py` |

**Risque :** Moyen — Impact sur toute l'UI, nécessite tests E2E complets.

---

### DT-014, DT-015 : Glass Box Incomplète

**Statut :** Sprint 3 recommandé

**Travail requis :**
- Audit de tous les `CalculationStep`
- Compléter `numerical_substitution` et `theoretical_formula`
- Ajouter les formules LaTeX manquantes

**Risque :** Faible — Pas d'impact fonctionnel, amélioration de la transparence.

---

### DT-018, DT-019 : Typage et Docstrings

**Statut :** Continu (au fil des refactorings)

**Travail requis :**
- Ajouter docstrings NumPy Style aux fonctions publiques
- Corriger les type hints (`_self` → `self`, etc.)

**Risque :** Très faible — Amélioration documentaire uniquement.

---

## Résumé par Priorité

| Priorité | ID | Description | Statut |
|----------|-----|-------------|--------|
| CRITIQUE | DT-001, DT-002 | Violations layering | ✅ Corrigé |
| HAUTE | DT-007, DT-008, DT-009 | Registres manuels | ✅ Corrigé |
| HAUTE | DT-010 à DT-013 | Constantes hardcodées | ✅ Corrigé |
| HAUTE | DT-016, DT-017 | Couplage UI/Logique | ✅ Corrigé |
| HAUTE | DT-022, DT-023 | Performance providers | ✅ Corrigé |
| HAUTE | DT-024 | Tests insuffisants | ✅ Corrigé |
| MOYENNE | DT-020, DT-021 | Gestion d'erreurs | ✅ Corrigé |
| MOYENNE | DT-003, DT-004, DT-005, DT-006 | Fichiers monolithiques | 🔄 Sprint 2-3 |
| MOYENNE | DT-014, DT-015 | Glass Box incomplète | 🔄 Sprint 3 |
| BASSE | DT-018, DT-019 | Typage et Docstrings | 🔄 Continu |

---

## Patterns Utilisés

| Pattern | Dettes Résolues | Description |
|---------|-----------------|-------------|
| **Strangler Fig** | DT-001, DT-002 | Migration progressive sans casser l'existant |
| **Decorator** | DT-007, DT-008, DT-009 | Auto-registration des stratégies |
| **Configuration Object** | DT-010 à DT-013 | Centralisation des constantes |
| **Dependency Inversion** | DT-016, DT-017 | Interfaces abstraites + injection |
| **Adapter** | DT-016, DT-017 | Implémentations Streamlit des interfaces |
| **Null Object** | DT-016, DT-017 | Handlers de test sans side-effects |
| **Facade** | DT-001, DT-002 | Ré-export pour compatibilité |

---

## Métriques de Qualité

| Métrique | Avant | Après |
|----------|-------|-------|
| Tests | 8 | 119 |
| Imports app/ dans core/ | 16 | 0 |
| Imports app/ dans infra/ | 3 | 0 |
| Registres manuels | 3 | 1 (centralisé) |
| Constantes hardcodées | ~15 | 0 (config/) |
