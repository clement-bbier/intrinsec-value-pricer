# Architecture Documentation

## Vue d'ensemble

L'Intrinsic Value Pricer suit une architecture en couches strictement séparée, garantissant la testabilité, la maintenabilité et la réutilisabilité du code quantitatif.

---

## Diagramme de l'architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                        (Streamlit App)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       PRESENTATION LAYER                         │
│                            app/                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Views      │  │ Controllers  │  │    State     │          │
│  │  (UI Logic)  │  │  (Routing)   │  │ (Session)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                        │
│                            src/                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     Valuation Engine                     │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │   │
│  │  │ Strategies  │  │ Orchestrator │  │   Guardrails   │ │   │
│  │  │  (DCF,RIM)  │  │  (Workflow)  │  │  (Validation)  │ │   │
│  │  └─────────────┘  └──────────────┘  └────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Computation Layer                     │   │
│  │  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐ │   │
│  │  │   Financial  │  │ Flow Projector│  │  Statistics  │ │   │
│  │  │     Math     │  │   (NPV, IRR)  │  │ (Monte Carlo)│ │   │
│  │  └──────────────┘  └───────────────┘  └──────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                       Models Layer                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │   Company    │  │  Parameters  │  │   Results    │  │   │
│  │  │  (Pydantic)  │  │  (Pydantic)  │  │  (Pydantic)  │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE LAYER                         │
│                            infra/                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Data Providers│  │  Macro Data  │  │  Ref Data    │          │
│  │  (Yahoo)     │  │  (Spreads)   │  │  (Sectors)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SERVICES                         │
│              (Yahoo Finance API, Market Data)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Principes Architecturaux

### 1. Séparation des Préoccupations

#### **app/** - Couche de Présentation (UI)
- **Responsabilité** : Interface utilisateur uniquement
- **Dépendances** : Streamlit, composants visuels
- **Interdiction** : Logique de calcul ou formules financières
- **Principe** : L'application UI doit pouvoir être remplacée (CLI, API REST) sans toucher à `src/`

#### **src/** - Cœur Quantitatif
- **Responsabilité** : Logique métier pure et calculs financiers
- **Dépendances** : NumPy, Pandas, Pydantic (pas de Streamlit)
- **Utilisable** : Indépendamment de l'UI, via import Python standard
- **Principe** : Code réutilisable dans Jupyter, scripts batch, API

#### **infra/** - Infrastructure et I/O
- **Responsabilité** : Accès aux données externes, persistance
- **Dépendances** : Clients API, parsers de données
- **Principe** : Abstraction des sources de données (Provider pattern)

### 2. Flux de Données

```
User Input (app/)
    ↓
Input Validation (src/models/)
    ↓
Parameter Construction (src/models/parameters/)
    ↓
Strategy Selection (src/valuation/registry.py)
    ↓
Orchestration (src/valuation/orchestrator.py)
    ↓
Strategy Execution (src/valuation/strategies/)
    ↓
Financial Calculations (src/computation/)
    ↓
Result Construction (src/models/results/)
    ↓
Audit & Quality Check (infra/auditing/)
    ↓
Display Results (app/views/results/)
```

### 3. Injection de Dépendances

Le système utilise un registre centralisé pour la configuration :

```python
# src/config/settings.py
class ConfigRegistry:
    - Constantes macroéconomiques (taux sans risque, etc.)
    - Paramètres de validation (guardrails)
    - Seuils de qualité des données
```

### 4. Extensibilité

#### Ajouter une nouvelle stratégie de valorisation

1. **Créer le modèle de paramètres** dans `src/models/parameters/strategies.py`
2. **Implémenter la stratégie** dans `src/valuation/strategies/`
3. **Enregistrer la stratégie** dans `src/valuation/registry.py`
4. **Créer la vue UI** dans `app/views/inputs/strategies/`
5. **Ajouter les tests** dans `tests/unit/strategies/`

Aucune modification du workflow global n'est nécessaire.

---

## Modules Clés

### src/valuation/orchestrator.py
**Responsabilité** : Chef d'orchestre du processus de valorisation

- Coordonne l'exécution des stratégies
- Gère les options (Monte Carlo, scenarios, sensibilité)
- Produit le Glass Box (traçabilité des calculs)
- Génère les diagnostics de qualité

### src/valuation/strategies/
**Responsabilité** : Implémentation des méthodes de valorisation

Chaque stratégie hérite de `BaseValuationStrategy` et implémente :
- `validate_parameters()` : Validation des inputs
- `compute()` : Calcul de la valeur intrinsèque
- `generate_glass_box()` : Traçabilité des étapes

Stratégies disponibles :
- `standard_fcff.py` : DCF classique (entreprises matures)
- `fundamental_fcff.py` : DCF normalisé (sociétés cycliques)
- `revenue_growth_fcff.py` : DCF croissance (tech, pharma)
- `fcfe.py` : Free Cash Flow to Equity
- `ddm.py` : Dividend Discount Model
- `rim_banks.py` : Residual Income Model
- `graham_value.py` : Formule de Benjamin Graham

### src/computation/financial_math.py
**Responsabilité** : Fonctions mathématiques pures

- `compute_wacc()` : Coût moyen pondéré du capital
- `compute_terminal_value()` : Valeur terminale (Gordon Growth)
- `unlever_beta()` / `relever_beta()` : Formule de Hamada
- `npv()` : Valeur actuelle nette
- `irr()` : Taux de rendement interne

### src/models/
**Responsabilité** : Contrats de données (Pydantic)

- **company.py** : Structure des données d'entreprise
- **parameters/** : Paramètres d'entrée pour chaque stratégie
- **results/** : Structure des résultats de valorisation
- **glass_box.py** : Enregistrement de la trace de calcul

### app/views/results/orchestrator.py
**Responsabilité** : Interface multi-piliers de résultats

Affiche 10 onglets de résultats :
1. Synthèse des inputs
2. Preuve de calcul (Glass Box)
3. Analyse de sensibilité
4. Scénarios déterministes
5. Distribution Monte Carlo
6. Analyse de marché
7. Multiples de pairs
8. Backtesting historique
9. Ingénierie du risque
10. Rapport de benchmark

---

## Tests et Qualité

### Structure des Tests

```
tests/
├── unit/                    # Tests unitaires (logique isolée)
│   ├── strategies/          # Tests des stratégies de valorisation
│   ├── computation/         # Tests des fonctions mathématiques
│   └── models/              # Tests de validation Pydantic
├── integration/             # Tests d'intégration entre modules
├── contracts/               # Tests de contrats API
└── e2e/                     # Tests end-to-end (workflow complet)
```

### Couverture par Couche

| Couche            | Couverture Cible | Couverture Actuelle |
|-------------------|------------------|---------------------|
| `src/valuation/`  | 95%+             | ~95%                |
| `src/computation/`| 95%+             | ~98%                |
| `src/models/`     | 95%+             | ~98%                |
| `infra/`          | 85%+             | ~85%                |
| `app/`            | 70%+             | ~0%                 |
| **Global**        | **95%+**         | **~72%**            |

**Note** : La couche UI (`app/`) a une couverture faible car elle nécessite des tests d'interface Streamlit spécialisés. Le cœur quantitatif (`src/`) respecte le seuil de 95%.

---

## Sécurité et Conformité

### Validation des Données
- **Pydantic** : Validation automatique des types et contraintes
- **Guardrails** : Seuils économiques pour détecter les valeurs aberrantes
- **Auditing** : Évaluation systématique de la qualité des inputs

### CI/CD Pipeline

```yaml
Pipeline GitHub Actions:
1. ruff         → Linting du code
2. mypy         → Vérification des types
3. pytest       → Tests avec couverture ≥95%
4. pip-audit    → Scan de vulnérabilités
```

### Gestion des Erreurs

Le système distingue 3 types d'erreurs :
1. **Erreurs de validation** : Inputs invalides (levées immédiatement)
2. **Erreurs de calcul** : Convergence impossible (mode dégradé)
3. **Erreurs de données** : API indisponible (fallback sectoriel)

---

## Internationalisation

Architecture multilingue via `src/i18n/` :

```
src/i18n/
├── fr/
│   ├── backend/     # Messages du moteur de calcul
│   └── ui/          # Messages de l'interface
└── en/              # (À venir)
```

Messages séparés entre backend (indépendant de l'UI) et frontend (spécifique à Streamlit).

---

## Diagramme de Séquence : Valorisation DCF Standard

```
User → app/main.py → Controller → Orchestrator → Strategy → Computation → Result
  │        │            │             │             │            │          │
  │   Input Form    Validate      Select       Execute      NPV/WACC   Format
  │        │            │          Strategy       DCF          │       Display
  │        │            │             │             │          │          │
  │        │            │             │             └──────────┘          │
  │        │            │             └────────────────────────────────→  │
  │        │            └───────────────────────────────────────────────→ │
  │        └────────────────────────────────────────────────────────────→│
  └──────────────────────────────────────────────────────────────────────┘
```

---

## Performance

### Optimisations Clés

1. **Vectorisation NumPy** : Calculs Monte Carlo (10 000 simulations < 100ms)
2. **Caching Streamlit** : `@st.cache_data` pour éviter recalculs
3. **Lazy Loading** : Import des modules de stratégies à la demande

### Benchmarks

| Opération                    | Temps (P50) | Temps (P95) |
|------------------------------|-------------|-------------|
| Valorisation DCF simple      | 15ms        | 30ms        |
| Monte Carlo (10k sims)       | 80ms        | 120ms       |
| Backtesting 5 ans            | 200ms       | 400ms       |
| Chargement données Yahoo     | 800ms       | 2000ms      |

---

## Bonnes Pratiques

### Pour les Développeurs

1. **Jamais de Streamlit dans `src/`** : Le cœur quantitatif doit rester framework-agnostic
2. **Pydantic pour tous les modèles** : Validation automatique + documentation
3. **Type hints partout** : Permet mypy de détecter les erreurs
4. **Tests contractuels** : Garantir la stabilité des interfaces publiques
5. **Glass Box obligatoire** : Toute stratégie doit tracer ses calculs

### Pour les Analystes Utilisateurs

1. **Mode Expert recommandé** : Contrôle total des hypothèses
2. **Toujours vérifier l'audit** : Score de confiance et warnings
3. **Monte Carlo pour le risque** : Distribution de probabilités vs point estimate
4. **Backtesting pour validation** : Performance historique du modèle

---

## Roadmap Architecturale

### Court Terme (v1.1)
- Couverture de tests UI : 70%+
- Support multilingue complet (EN)
- API REST pour usage programmatique

### Moyen Terme (v1.5)
- Multi-providers : Bloomberg, Refinitiv
- Persistance des valorisations (PostgreSQL)
- Exports avancés (Excel avec formules)

### Long Terme (v2.0)
- Machine Learning : Prédiction de paramètres
- Blockchain : Traçabilité immuable des valorisations
- Module d'analyse ESG

---

## Références

Voir `CHANGELOG.md` et `README.md` pour les références académiques complètes.

---

**Document maintenu par @clement-bbier**  
**Dernière mise à jour : 2026-02-11**
