# CONTRIBUTING.md — Manifeste de Développement

## Objectif

Ce manifeste définit les standards de qualité, de cohérence financière et de maintenabilité pour l'application **Intrinsic Value Pricer**.

L'objectif est de produire un outil de valorisation :
- **pédagogique** (compréhensible même sans formation financière),
- **rigoureux** (méthodes institutionnelles),
- **transparent** (Glass Box, auditabilité),
- **maintenable et évolutif**,
- digne d'un **outil financier professionnel**.

L'application repose sur une **valeur intrinsèque centrale** (DCF), enrichie par des **modules complémentaires** permettant de contextualiser, comparer et auditer cette valeur.

---

## Étanchéité Architecturale (RÈGLE ABSOLUE)

### Principe de Souveraineté du Core Financier

Le dossier `src/` constitue le **Core Financier** de l'application. Il doit rester **totalement indépendant** de toute couche de présentation.

```
src/                    # Core Financier — ZONE PROTÉGÉE
├── computation/        # Mathématiques financières pures
├── config/             # Configuration et constantes
├── domain/models/      # Modèles de données (Pydantic)
├── i18n/               # Internationalisation
├── interfaces/         # Interfaces abstraites (pas d'implémentations UI)
├── utilities/          # Utilitaires génériques
└── valuation/          # Moteurs de valorisation

app/                    # Couche de Présentation — DÉPEND DE src/
├── adapters/           # Implémentations concrètes des interfaces
├── ui/                 # Composants Streamlit
└── workflow.py         # Orchestration UI
```

### Règles d'Import Strictes

**INTERDIT dans `src/` :**
```python
# ❌ JAMAIS : Import direct de Streamlit
import streamlit as st
from streamlit import something

# ❌ JAMAIS : Import de modules app/
from app.anything import something
from app.ui.components import SomeWidget
```

**AUTORISÉ :**
```python
# ✅ CORRECT dans src/ : Imports internes au core
from src.domain.models import ValuationRequest
from src.computation.financial_math import calculate_wacc

# ✅ CORRECT dans app/ : Import depuis src/
from src.valuation.engines import run_valuation
from src.domain.models import CompanyFinancials
```

### Inversion de Dépendances (Pattern DIP)

Pour les fonctionnalités nécessitant une interaction UI, utiliser des **interfaces abstraites** :

```python
# src/interfaces/ui_handlers.py — Interface abstraite
class IUIProgressHandler(ABC):
    @abstractmethod
    def update_status(self, message: str) -> None: ...

# app/adapters/streamlit_adapters.py — Implémentation concrète
class StreamlitProgressHandler(IUIProgressHandler):
    def update_status(self, message: str) -> None:
        st.write(message)
```

### Validation Automatique

Un test contractuel (`tests/contracts/test_architecture_contracts.py`) vérifie automatiquement :
- Aucun import de `streamlit` dans `src/`
- Aucun import de `app.*` dans `src/`
- Présence de `from __future__ import annotations` dans tous les fichiers `src/`

---

## Philosophie Financière Générale

### Valeur intrinsèque (Pilier central)

La valeur intrinsèque représente la **valeur économique fondamentale** d'une entreprise, indépendamment de l'offre et de la demande de marché à court terme.

Elle répond à la question :
> *« Que vaut réellement cette entreprise compte tenu de ses flux futurs et de son risque ? »*

Dans l'application, cette valeur est calculée via un **DCF (Discounted Cash Flow)** et constitue **le point d'ancrage principal**.

### Modules Complémentaires (Contextualisation)

Les autres onglets ne remplacent **jamais** la valeur intrinsèque.  
Ils servent à :
- **contextualiser** le résultat,
- **le comparer** à d'autres approches,
- **tester sa robustesse**,
- **auditer ses hypothèses**.

Chaque onglet a une responsabilité claire et indépendante.

---

## Cohérence de l'Architecture UI

La structure suivante est **totalement cohérente** et institutionnelle :

```
├── render_executive_summary.py      # Synthèse décisionnelle
├── render_inputs_tab.py             # Inputs utilisateur
├── render_calculation_proof.py      # Glass Box (preuves de calcul)
├── render_relative_valuation.py     # Triangulation (comparables)
├── render_sotp_tab.py               # Sum-of-the-Parts
├── render_scenarios_tab.py          # Bull / Base / Bear
├── render_backtest_tab.py           # Validation historique
├── render_audit_report.py           # Audit & diagnostics
└── render_monte_carlo_tab.py        # Distribution probabiliste
```

### Rôle de chaque onglet

- **Executive Summary**  
  Vue synthétique pour décision rapide (KPIs, verdict, signaux clés).

- **Inputs**  
  Transparence totale sur les hypothèses utilisées.

- **Calculation Proof (Glass Box)**  
  Démonstration mathématique complète des calculs (anti boîte noire).

- **Relative Valuation (Triangulation)**  
  Comparaison avec le marché via multiples (P/E, EV/EBITDA, etc.).  
  Sert à répondre à : *« Le DCF est-il cohérent avec le marché ? »*

- **SOTP (Sum-of-the-Parts)**  
  Valorisation par découpage des activités lorsque l'entreprise est diversifiée.  
  Sert à détecter sous/sur-valorisation structurelle.

- **Scenarios (Bull/Base/Bear)**  
  Analyse de sensibilité macro et stratégique.

- **Backtest**  
  Vérification historique de la pertinence des hypothèses.

- **Monte Carlo**  
  Passage d'une valeur unique à une **distribution probabiliste**.

- **Audit Report**  
  Synthèse des risques, incohérences et alertes méthodologiques.

Chaque onglet = **une responsabilité unique** (principe SOLID).

---

## Standards Obligatoires

### 0. Imports : En Haut des Fichiers (Obligatoire)

```python
"""
path/to/file.py
[Header de fichier...]
"""

from __future__ import annotations

# Standard library
import logging
from typing import Dict, Optional

# Third-party
import pandas as pd

# Local
from src.domain.models import ValuationMode, ValuationRequest
```

**Règles :**

* `__future__` en premier (après la docstring)
* Standard library
* Tiers
* Locaux
* Pas de `import *`
* Imports locaux uniquement si nécessaires

---

### 1. Docstrings : Numpy Style avec Financial Impact (Obligatoire)

Toutes les fonctions, classes et méthodes doivent être documentées selon le standard Numpy Style, **enrichi d'une section Financial Impact** pour les fonctions du core financier.

**Exemple standard pour `src/valuation/engines.py` :**

```python
def run_valuation(request: ValuationRequest, financials: CompanyFinancials) -> ValuationResult:
    """
    Exécute le moteur de valorisation unifié.

    Args
    ----
    request : ValuationRequest
        Contrat de requête immuable définissant le mode et les options.
    financials : CompanyFinancials
        Données financières normalisées (TTM).

    Returns
    -------
    ValuationResult
        Objet riche incluant la trace Glass Box et le rapport d'audit.

    Raises
    ------
    ValuationException
        Si le mode de valorisation n'est pas supporté ou si les données sont invalides.
    CalculationError
        Si une erreur mathématique survient (division par zéro, convergence impossible).

    Financial Impact
    ----------------
    Point d'entrée critique du moteur de valorisation. Une défaillance ici 
    invalide l'intégralité du Pitchbook et peut conduire à des décisions 
    d'investissement erronées. Toute modification doit être validée contre 
    le Golden Dataset (50 tickers de référence).

    Examples
    --------
    >>> request = ValuationRequest(ticker="AAPL", mode=ValuationMode.FCFF_STANDARD)
    >>> result = run_valuation(request, financials)
    >>> print(f"Valeur intrinsèque: ${result.intrinsic_value_per_share:.2f}")
    """
```

**Sections obligatoires pour les fonctions `src/` :**

| Section | Obligatoire | Description |
|---------|-------------|-------------|
| Args | ✅ Oui | Paramètres avec types et descriptions |
| Returns | ✅ Oui | Type de retour et description |
| Raises | ✅ Oui | Exceptions possibles |
| Financial Impact | ✅ Oui (src/) | Impact sur la valorisation finale |
| Examples | Recommandé | Cas d'utilisation typiques |

---

### 2. Typage Python 3.10+ (Obligatoire)

Toutes les fonctions doivent être entièrement typées avec les annotations modernes Python 3.10+.

**Alias Financiers (src/domain/models/enums.py) :**

```python
from typing import TypeAlias

# Alias financiers explicites — améliore la lisibilité et la validation
Rate: TypeAlias = float          # Taux (WACC, croissance, actualisation)
Currency: TypeAlias = float      # Montants monétaires
Percentage: TypeAlias = float    # Pourcentages (0.0 à 1.0)
Multiple: TypeAlias = float      # Multiples de valorisation (P/E, EV/EBITDA)
ShareCount: TypeAlias = int      # Nombre d'actions
Years: TypeAlias = int           # Durées en années
```

**Interdiction absolue de `Any` dans les fichiers critiques :**

Les fichiers suivants ne doivent **jamais** contenir le type `Any` :
- `src/valuation/engines.py`
- `src/valuation/pipelines.py`
- `src/domain/models/*.py`

Utiliser des types Union, Optional ou des TypeVar si nécessaire.

---

### 3. Header de Fichier Standard

Chaque fichier Python doit commencer par :

```python
"""
path/to/file.py

[DESCRIPTION BREVE DU ROLE DU FICHIER]

Version : V[X.Y] — [DT-XXX] Resolution
Pattern : [Factory | Strategy | etc.]
Style : Numpy Style docstrings

[RISQUES FINANCIERS]
- Mauvaise hypothèse => valorisation incorrecte
- Dépendance aux données externes

[DEPENDANCES CRITIQUES]
- numpy >= 1.21.0
- pandas >= 1.3.0
"""
```

---

## Sécurité et Conformité

### 1. Validation des Inputs

La **validation** vérifie que les données sont **correctes et cohérentes**.

Exemples :

* ticker non vide
* horizon > 0
* WACC raisonnable
* marges entre 0 et 1

---

### 2. Sanitisation des Données Utilisateur (Obligatoire)

**Sanitiser** une donnée signifie :

> Nettoyer, normaliser et sécuriser une donnée utilisateur **avant tout traitement métier ou calcul financier**.

Objectifs :

* éviter les erreurs de calcul,
* éviter les comportements inattendus,
* protéger contre les injections ou données malformées,
* garantir l'intégrité des résultats financiers.

#### Exemples de sanitisation

```python
def sanitize_percentage(value: float | str | None) -> float:
    """
    Sanitize a percentage input from user.

    Args
    ----
    value : float | str | None
        Valeur brute de l'utilisateur.

    Returns
    -------
    float
        Pourcentage normalisé entre 0 et 1.

    Raises
    ------
    ValueError
        Si la valeur est None ou hors limites.

    Financial Impact
    ----------------
    Un pourcentage mal sanitizé (ex: 5 au lieu de 0.05) peut 
    multiplier par 100 le WACC et invalider toute la valorisation.
    """
    if value is None:
        raise ValueError("Value cannot be None")

    if isinstance(value, str):
        value = value.replace("%", "").strip()

    value = float(value)

    if not 0 <= value <= 1:
        raise ValueError("Percentage must be between 0 and 1")

    return value
```

**Règle absolue :**

> Aucune donnée utilisateur ne doit entrer dans le moteur de valorisation sans être validée ET sanitizée.

---

### 3. Gestion des Secrets

Toujours via variables d'environnement :

```python
import os
API_KEY = os.getenv("YAHOO_FINANCE_API_KEY")
```

---

## Architecture et Patterns

### Principes SOLID (Obligatoires)

* **S**ingle Responsibility — Une classe, une responsabilité
* **O**pen / Closed — Ouvert à l'extension, fermé à la modification
* **L**iskov Substitution — Les sous-types doivent être substituables
* **I**nterface Segregation — Interfaces spécifiques plutôt que générales
* **D**ependency Inversion — Dépendre des abstractions, pas des implémentations

---

## Logging Standardisé

* Logs en anglais
* Format structuré
* Niveaux cohérents

---

## Tests et Qualité

### Couverture et Types de Tests

* Couverture minimale : **85%**
* Tests unitaires, intégration, end-to-end
* Fixtures explicites

### Golden Dataset (Invariants Mathématiques)

Le fichier `tests/integration/test_golden_dataset.py` contient un échantillon de **50 tickers** (Tech, Banques, Industrie) avec leurs valeurs intrinsèques de référence.

**Règle absolue :**

> Chaque refactorisation doit garantir que le résultat final ne dévie pas d'un centime par rapport au Golden Dataset.

Ce test est exécuté automatiquement sur chaque Pull Request.

---

## Checklist Pre-Commit

* [ ] Header standard présent
* [ ] Docstrings complètes avec **Financial Impact** (pour src/)
* [ ] Typage complet (pas de `Any` dans les fichiers critiques)
* [ ] `from __future__ import annotations` présent
* [ ] Inputs validés ET sanitizés
* [ ] Logs conformes
* [ ] Tests OK (>85%)
* [ ] Aucun hardcoding métier
* [ ] Aucun calcul opaque
* [ ] Golden Dataset validé (si modification src/valuation/)

---

---

## Changements Architecturaux Récents (Sprint 6)

### Modules Connectés

| Module | Fichier | Rôle |
|--------|---------|------|
| **QuantLogger** | `src/quant_logger.py` | Logging institutionnel standardisé |
| **Pitchbook PDF** | `src/reporting/pdf_generator.py` | Export PDF 3 pages |
| **PitchbookData** | `src/domain/models/pitchbook.py` | DTO pour le PDF |

### Fichiers Purgés

Les fichiers suivants ont été supprimés car obsolètes :

- `app/ui/facade.py` — Façade legacy non utilisée
- `app/ui/components/ui_inputs_expert.py` — Remplacé par `shared_widgets.py`
- `src/i18n/text_registry.py` — Système YAML abandonné
- `locales/fr.yaml` — Fichier YAML non utilisé

### Architecture i18n Finale

L'internationalisation utilise des **classes Python centralisées** :

```python
from src.i18n import CommonTexts, SidebarTexts, KPITexts

# Usage
title = CommonTexts.APP_TITLE
label = SidebarTexts.TICKER_LABEL
```

Localisation : `src/i18n/fr/ui/` et `src/i18n/fr/backend/`

### Bouton Pitchbook PDF

L'export PDF est disponible via un bouton dans l'orchestrateur des résultats :

```python
# app/ui/results/orchestrator.py
self._render_pdf_download_button(result, **kwargs)
```

---

*Ce manifeste formalise une application de valorisation financière sérieuse, transparente et pédagogiquement robuste.*

**Dernière mise à jour : 2026-01-20**
