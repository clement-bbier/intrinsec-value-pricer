# SPRINT ROADMAP — Intrinsic Value Pricer

**Version** : 2.0  
**Date** : Janvier 2026  
**Statut** : Architecture V2 etablie

---

## Etat Actuel de l'Architecture

### Structure Validee

```
intrinsec-value-pricer/
├── core/                           # Logique metier pure
│   ├── models/                     # ✅ Decoupe (7 fichiers)
│   │   ├── enums.py
│   │   ├── glass_box.py
│   │   ├── scenarios.py
│   │   ├── company.py
│   │   ├── dcf_inputs.py
│   │   ├── audit.py
│   │   └── request_response.py
│   ├── i18n/                       # ✅ Structure i18n
│   │   └── fr/
│   │       ├── ui/                 # Textes interface
│   │       └── backend/            # Textes internes
│   ├── config/                     # ✅ Constantes centralisees
│   ├── interfaces/                 # ✅ Abstractions UI
│   ├── computation/                # ✅ Fonctions mathematiques
│   └── valuation/                  # ✅ Moteur + Strategies
│
├── app/                            # Couche presentation
│   ├── ui/                         # ✅ Nouvelle structure
│   │   ├── base/                   # Classes abstraites
│   │   ├── expert_terminals/       # 7 terminaux + factory
│   │   └── result_tabs/            # Onglets resultats
│   ├── ui_components/              # ❌ A MIGRER (legacy)
│   │   ├── ui_inputs_expert.py     # → Remplacer par app/ui/
│   │   └── ui_kpis.py              # → Remplacer par app/ui/
│   └── adapters/                   # ✅ Streamlit adapters
│
├── infra/                          # ✅ Infrastructure complete
│   ├── auditing/
│   ├── data_providers/
│   └── ref_data/
│
└── tests/                          # ✅ 119 tests
    ├── unit/
    ├── contracts/
    ├── integration/
    └── e2e/
```

---

## Sprint 1 : Finalisation Migration UI (Priorite HAUTE)

**Objectif** : Supprimer les fichiers legacy `ui_components/` et basculer sur `app/ui/`.

### ST 1.1 : Migration de `ui_inputs_expert.py`
- [ ] Identifier les fonctions encore utilisees dans `app/main.py`
- [ ] Les remplacer par les appels vers `app/ui/expert_terminals/factory.py`
- [ ] Supprimer `ui_inputs_expert.py`

### ST 1.2 : Migration de `ui_kpis.py`
- [ ] Identifier les fonctions de rendu encore utilisees
- [ ] Les remplacer par `app/ui/result_tabs/orchestrator.py`
- [ ] Supprimer `ui_kpis.py`

### ST 1.3 : Nettoyage de `app/main.py`
- [ ] Mettre a jour tous les imports
- [ ] Valider le workflow complet
- [ ] Supprimer `app/ui/facade.py` si inutile

**Critere de succes** : `app/ui_components/` ne contient plus que `ui_glass_box_registry.py` et `ui_charts.py`.

---

## Sprint 2 : Gouvernance et Standards (Priorite MOYENNE)

**Objectif** : Etablir les regles de developpement.

### ST 2.1 : Creation de CONTRIBUTING.md
- [ ] Format Docstring : Google Style (Args, Returns, Raises)
- [ ] Type Hints : Obligatoires sur toutes les fonctions
- [ ] Header de fichier standard

### ST 2.2 : Application des Docstrings
- [ ] `core/models/` : Toutes les classes et methodes
- [ ] `core/valuation/strategies/` : Toutes les strategies
- [ ] `core/computation/` : Toutes les fonctions

### ST 2.3 : Application du Typage
- [ ] Ajouter les type hints manquants
- [ ] Configurer mypy pour validation

**Critere de succes** : `mypy --strict core/` passe sans erreur.

---

## Sprint 3 : Glass Box 2.0 — Tracabilite Complete (Priorite MOYENNE)

**Objectif** : Formules LaTeX completes et substitutions numeriques.

### ST 3.1 : Audit des CalculationStep
- [ ] Lister tous les steps avec "Calcul interne"
- [ ] Remplacer par formules LaTeX detaillees

### ST 3.2 : Enrichissement numerical_substitution
- [ ] Injecter les vraies valeurs formatees
- [ ] Exemple : `150M × (1 + 0.03)^1 / (1 + 0.08)^1 = 143.5M`

### ST 3.3 : Harmonisation des symboles
- [ ] Verifier coherence UI/Maths (Rf, Ke, WACC, etc.)

**Critere de succes** : Toutes les etapes Glass Box sont verifiables mathematiquement.

---

## Sprint 4 : Internationalisation YAML (Priorite BASSE)

**Objectif** : Passer de classes Python a fichiers YAML pour l'i18n.

### ST 4.1 : Export YAML
- [ ] Generer `locales/fr.yaml` depuis `core/i18n/fr/`
- [ ] Generer `locales/en.yaml` (traduction)

### ST 4.2 : TextRegistry
- [ ] Classe Pydantic pour charger YAML
- [ ] Validation des cles au demarrage

### ST 4.3 : Switcher UI
- [ ] Selecteur de langue dans sidebar
- [ ] `registry.tr("ma_cle")` partout

**Critere de succes** : L'app fonctionne en FR et EN.

---

## Sprint 5 : UX et Data Intelligence (Priorite BASSE)

**Objectif** : Ameliorer l'experience utilisateur.

### ST 5.1 : Reorganisation des Widgets
- [ ] Ordre logique : Operationnel → Risque → Sortie → Structure

### ST 5.2 : Mode Expert Avance
- [ ] Cacher options complexes dans `st.expander`

### ST 5.3 : Timeout Peers
- [ ] 12 secondes max pour recherche de comparables
- [ ] Fallback gracieux avec `sector_multiples.yaml`

**Critere de succes** : Workflow fluide pour nouveaux utilisateurs.

---

## Sprint 6 : Reporting Premium (Priorite BASSE)

**Objectif** : Export PDF professionnel.

### ST 6.1 : Moteur FPDF2
- [ ] Header institutionnel
- [ ] Executive Summary
- [ ] Tableaux de calcul
- [ ] Annexes Audit

### ST 6.2 : Sensibilite 3D
- [ ] Matrices croisees (g × WACC × Marge)

**Critere de succes** : PDF exportable de qualite institutionnelle.

---

## Priorites Recommandees

| Sprint | Priorite | Effort | Impact |
|--------|----------|--------|--------|
| **1 - Migration UI** | HAUTE | 2-3h | Elimine legacy |
| **2 - Gouvernance** | MOYENNE | 4-6h | Maintenabilite |
| **3 - Glass Box 2.0** | MOYENNE | 3-4h | Transparence |
| **4 - i18n YAML** | BASSE | 6-8h | Multi-langue |
| **5 - UX** | BASSE | 4-6h | Experience |
| **6 - PDF** | BASSE | 8-10h | Valeur ajoutee |

---

## Metriques de Qualite Actuelles

- **Tests** : 119/119 passent ✅
- **Couverture structurelle** : Packages bien decoupes ✅
- **Imports propres** : Pas de facades ✅
- **Docstrings** : ~40% (a ameliorer)
- **Type Hints** : ~50% (a ameliorer)
