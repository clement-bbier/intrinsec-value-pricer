# REFACTOR PLAN — Historique

**Version** : 2.0 — Janvier 2026  
**Statut** : Complété

Ce document retrace l'historique des refactorisations majeures
du projet *Intrinsic Value Pricer*.

---

## Refactorisations Complétées

### Phase 1 : Architecture V2 (Sprint 1)

**Objectif** : Étanchéité des couches

| Action | Avant | Après |
|--------|-------|-------|
| Structure | `core/` | `src/` |
| Imports | Circulaires | Unidirectionnels |
| Streamlit dans src/ | 16 imports | 0 |

### Phase 2 : Modèles Segmentés (Sprint 1)

**Objectif** : Découper les fichiers monolithiques

| Fichier | Avant | Après |
|---------|-------|-------|
| `models.py` | 533 lignes | 9 fichiers dans `src/domain/models/` |
| `enums.py` | Épars | Centralisé |
| `glass_box.py` | Basique | V2 avec VariableInfo |

### Phase 3 : Configuration Object (Sprint 1-2)

**Objectif** : Centraliser les constantes

| Avant | Après |
|-------|-------|
| Hardcodé partout | `src/config/constants.py` |
| ~15 constantes | Classes immutables |

### Phase 4 : Registry Centralisé (Sprint 2)

**Objectif** : Unifier les registres

| Avant | Après |
|-------|-------|
| 3 registres manuels | 1 registre centralisé |
| Duplication | `@register_strategy` decorator |

### Phase 5 : Glass Box V2 (Sprint 2-3)

**Objectif** : Traçabilité complète

| Avant | Après |
|-------|-------|
| `theoretical_formula` seul | + `actual_calculation` |
| Pas de source | + `variables_map` |
| Pas de badge | + Badge de confiance |

### Phase 6 : UI Expert Terminals (Sprint 3)

**Objectif** : Découper l'UI en composants

| Avant | Après |
|-------|-------|
| `ui_inputs_expert.py` (523 lignes) | 7 terminaux dans `app/ui/expert/terminals/` |
| Rendu monolithique | Factory + Template Method |
| Pas de @st.fragment | 6 fonctions fragmentées |

### Phase 7 : Mode Dégradé (Sprint 4)

**Objectif** : Résilience API

| Avant | Après |
|-------|-------|
| Crash si API down | Fallback sectoriel |
| Pas de signalétique | Bandeau + confidence score |
| Erreurs brutes | Diagnostics pédagogiques |

### Phase 8 : Internationalisation (Sprint 5)

**Objectif** : Externaliser les textes

| Avant | Après |
|-------|-------|
| Classes Python | `locales/*.yaml` |
| Hardcodé | `TextRegistry.get()` |
| FR only | Extensible (EN planned) |

### Phase 9 : Reporting PDF (Sprint 5)

**Objectif** : Export professionnel

| Avant | Après |
|-------|-------|
| Pas d'export | Pitchbook PDF 3 pages |
| N/A | `PitchbookPDFGenerator` |

---

## Design Patterns Introduits

| Pattern | Usage | Sprint |
|---------|-------|--------|
| **Strangler Fig** | Migration progressive | 1 |
| **Decorator** | Auto-registration | 2 |
| **Configuration Object** | Constantes | 1-2 |
| **Factory Method** | Terminaux experts | 3 |
| **Template Method** | Rendu séquencé | 3 |
| **Mediator** | Orchestration onglets | 3 |
| **Adapter** | Streamlit abstraction | 1 |
| **Null Object** | Handlers de test | 1 |
| **Builder** | PDF generation | 5 |

---

## Fichiers Supprimés

| Fichier | Raison | Sprint |
|---------|--------|--------|
| `core/` (dossier) | Renommé en `src/` | 1 |
| Imports circulaires | Corrigés | 1 |
| Constantes hardcodées | Migrées vers `config/` | 2 |

---

## Fichiers Créés

| Fichier | Rôle | Sprint |
|---------|------|--------|
| `src/config/constants.py` | Constantes | 1 |
| `src/valuation/registry.py` | Registre | 2 |
| `src/interfaces/ui_handlers.py` | Abstractions | 1 |
| `app/adapters/streamlit_adapters.py` | Implémentations | 1 |
| `app/ui/expert/factory.py` | Factory terminaux | 3 |
| `app/ui/base/expert_terminal.py` | Template Method | 3 |
| `app/ui/results/orchestrator.py` | Mediator | 3 |
| `infra/ref_data/sector_fallback.py` | Fallback | 4 |
| `src/diagnostics.py` | Diagnostics V2 | 4 |
| `src/quant_logger.py` | Logging | 4 |
| `locales/fr.yaml` | Textes FR | 5 |
| `src/i18n/text_registry.py` | Registry i18n | 5 |
| `src/domain/models/pitchbook.py` | DTO PDF | 5 |
| `src/reporting/pdf_generator.py` | Générateur PDF | 5 |

---

## Prochaines Refactorisations (Backlog)

| Action | Description | Priorité |
|--------|-------------|----------|
| Tests E2E | Playwright sur l'UI | MOYENNE |
| locales/en.yaml | Traduction anglaise | MOYENNE |
| Performance | Benchmarks | BASSE |

---

## Conclusion

Toutes les refactorisations planifiées pour les Sprints 1-5
ont été complétées avec succès.

Le code est maintenant :
- **Étanche** (src/ indépendant de app/)
- **Typé** (mypy strict)
- **Testé** (51+ contrats)
- **Documenté** (docstrings NumPy)
- **Résilient** (mode dégradé)
- **Internationalisé** (YAML)
- **Exportable** (PDF)
