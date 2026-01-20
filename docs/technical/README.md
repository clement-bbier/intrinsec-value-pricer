# Documentation Technique

**Version** : 3.0 — Janvier 2026  
**Sprints Complétés** : 1-5

Ce dossier décrit l'**architecture interne** du moteur de valorisation.

Il s'adresse principalement à :
- développeurs,
- maintainers,
- reviewers techniques,
- profils quant / risk / model validation.

---

## Architecture Globale

Le moteur est structuré en **couches étanches** :

```
┌─────────────────────────────────────────────────────────────┐
│                        app/ (UI)                            │
│  Streamlit, adapters, ui/expert/terminals, ui/results       │
├─────────────────────────────────────────────────────────────┤
│                   src/ (Logique Métier)                     │
│  valuation/, computation/, domain/models/, diagnostics      │
├─────────────────────────────────────────────────────────────┤
│                   infra/ (Infrastructure)                   │
│  data_providers/, auditing/, ref_data/, macro/              │
└─────────────────────────────────────────────────────────────┘
```

### Règle d'Or
- `src/` n'importe JAMAIS de `app/` ni de `streamlit`
- `infra/` peut importer de `src/` mais pas de `app/`
- `app/` importe de `src/` et `infra/`

---

## Couches Détaillées

### 1. Stratégies de Valorisation (`src/valuation/strategies/`)

9 stratégies implémentées :

| Fichier | Mode | Description |
|---------|------|-------------|
| `dcf_standard.py` | FCFF_STANDARD | DCF Two-Stage classique |
| `dcf_fundamental.py` | FCFF_NORMALIZED | FCF normalisé (cycliques) |
| `dcf_growth.py` | FCFF_GROWTH | Revenue-driven (tech) |
| `dcf_equity.py` | FCFE | Flux vers actionnaires |
| `dcf_dividend.py` | DDM | Dividend Discount Model |
| `graham_value.py` | GRAHAM_VALUE | Formule Graham 1974 |
| `rim_banks.py` | RIM_BANKS | Residual Income (banques) |
| `multiples.py` | MULTIPLES | Valorisation relative |
| `monte_carlo.py` | (Extension) | Simulation stochastique |

### 2. Couche de Calcul (`src/computation/`)

- `financial_math.py` : WACC, Ke, Kd, Beta ajusté
- `growth.py` : SGR, CAGR, croissance normalisée
- `statistics.py` : Percentiles, écart-type, intervalles
- `transformations.py` : Conversions, normalisations

### 3. Orchestration (`src/valuation/`)

- `engines.py` : Point d'entrée `run_valuation()`
- `pipelines.py` : Chaînage calcul → audit → Glass Box
- `registry.py` : Registre centralisé (Decorator Pattern)

### 4. Audit & Gouvernance (`infra/auditing/`)

- `audit_engine.py` : Orchestrateur d'audit
- `auditors.py` : Auditeurs spécialisés par pilier
- `backtester.py` : Validation historique

### 5. Données (`infra/data_providers/`)

- `yahoo_provider.py` : Provider principal + Mode Dégradé (ST-4.1)
- `yahoo_raw_fetcher.py` : Fetcher brut
- `financial_normalizer.py` : Normalisation TTM
- `sector_fallback.py` : Fallback multiples sectoriels

---

## Design Patterns Utilisés

| Pattern | Localisation | Usage |
|---------|--------------|-------|
| **Factory Method** | `app/ui/expert/factory.py` | Création dynamique des terminaux |
| **Template Method** | `app/ui/base/expert_terminal.py` | Workflow de rendu standardisé |
| **Strategy** | `src/valuation/strategies/` | Algorithmes de valorisation |
| **Mediator** | `app/ui/results/orchestrator.py` | Coordination des onglets |
| **Decorator** | `src/valuation/registry.py` | Auto-enregistrement des stratégies |
| **Adapter** | `app/adapters/` | Abstraction Streamlit |
| **Null Object** | `src/interfaces/` | Handlers de test |

---

## Fonctionnalités Avancées

### Glass Box V2 (Sprint 2-3)

Chaque `CalculationStep` contient :
- `theoretical_formula` : Formule LaTeX
- `actual_calculation` : Substitution numérique réelle
- `variables_map` : Dict de `VariableInfo` avec source

```python
@dataclass
class VariableInfo:
    symbol: str           # Ex: "WACC"
    value: float          # Ex: 0.082
    formatted: str        # Ex: "8.20%"
    source: VariableSource  # YAHOO, COMPUTED, MANUAL
    is_override: bool     # True si surchargé par l'expert
```

### Mode Dégradé (Sprint 4.1)

Fallback automatique si Yahoo Finance échoue :

```python
class DataProviderStatus:
    is_degraded_mode: bool
    degraded_reason: str
    fallback_sources: List[str]
    confidence_score: float  # 1.0 = live, 0.7 = fallback
```

### Diagnostic Pédagogique (Sprint 4.2)

Traduction des erreurs techniques en conseils métier :

```python
@dataclass
class FinancialContext:
    parameter_name: str      # "Beta"
    current_value: float     # 3.5
    typical_range: tuple     # (0.5, 2.0)
    statistical_risk: str    # "Beta > 3.0 = volatilité extrême"
    recommendation: str      # "Utiliser proxy sectoriel"
```

### QuantLogger (Sprint 4.2)

Format de log institutionnel :

```
[VALUATION][SUCCESS] Ticker: AAPL | Model: FCFF_STANDARD | IV: 185.20 | AuditScore: 88.5%
[DATA][WARNING] Ticker: MSFT | Mode dégradé activé | Reason: API timeout
```

---

## Contenu du Dossier

| Fichier | Description |
|---------|-------------|
| `valuation_engines.md` | Orchestration des stratégies |
| `audit_engine.md` | Logique d'audit et Confidence Score |
| `data_providers.md` | Acquisition et normalisation des données |
| `governance.md` | Règles de gouvernance du code |
| `MAINTENANCE.md` | Guide de maintenance et évolution |
| `ARCHITECTURE.md` | Architecture technique détaillée |
| `CONTRIBUTING.md` | Guide de contribution |

---

## Règles Techniques

- Aucune stratégie ne contient de logique UI
- Aucune méthode ne mélange calcul et audit
- Les modèles sont déterministes par défaut
- Toute incertitude passe par Monte Carlo
- `from __future__ import annotations` obligatoire
- Type hints sur toutes les fonctions publiques

---

## Tests

51+ tests organisés en :

```
tests/
├── unit/           # Tests unitaires
├── contracts/      # Tests de contrats d'interface
├── integration/    # Tests d'intégration
└── e2e/            # Tests end-to-end
```

Exécution : `pytest tests/contracts/ -v`

---

**Note**  
Cette documentation technique ne remplace pas la lecture du code,
mais fournit une vue d'ensemble des responsabilités et invariants.
