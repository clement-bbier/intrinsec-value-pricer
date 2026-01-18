# CONTRIBUTING.md — Manifeste de Développement

## Objectif

Ce manifeste définit les standards de qualité, de cohérence financière et de maintenabilité pour l'application **Intrinsic Value Pricer**.

L'objectif est de produire un outil de valorisation :
- **pédagogique** (compréhensible même sans formation financière),
- **rigoureux** (méthodes institutionnelles),
- **transparent** (Glass Box, auditabilité),
- **maintenable et évolutif**,
- digne d’un **outil financier professionnel**.

L’application repose sur une **valeur intrinsèque centrale** (DCF), enrichie par des **modules complémentaires** permettant de contextualiser, comparer et auditer cette valeur.

---

## Philosophie Financière Générale

### Valeur intrinsèque (Pilier central)

La valeur intrinsèque représente la **valeur économique fondamentale** d’une entreprise, indépendamment de l’offre et de la demande de marché à court terme.

Elle répond à la question :
> *« Que vaut réellement cette entreprise compte tenu de ses flux futurs et de son risque ? »*

Dans l’application, cette valeur est calculée via un **DCF (Discounted Cash Flow)** et constitue **le point d’ancrage principal**.

### Modules Complémentaires (Contextualisation)

Les autres onglets ne remplacent **jamais** la valeur intrinsèque.  
Ils servent à :
- **contextualiser** le résultat,
- **le comparer** à d’autres approches,
- **tester sa robustesse**,
- **auditer ses hypothèses**.

Chaque onglet a une responsabilité claire et indépendante.

---

## Cohérence de l’Architecture UI

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

````

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
  Valorisation par découpage des activités lorsque l’entreprise est diversifiée.  
  Sert à détecter sous/sur-valorisation structurelle.

- **Scenarios (Bull/Base/Bear)**  
  Analyse de sensibilité macro et stratégique.

- **Backtest**  
  Vérification historique de la pertinence des hypothèses.

- **Monte Carlo**  
  Passage d’une valeur unique à une **distribution probabiliste**.

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
from typing import Dict, Optional, Any

# Third-party
import streamlit as st
import pandas as pd

# Local
from core.models import ValuationMode, ValuationRequest
from app.ui.expert_terminals import ExpertTerminalFactory
````

**Règles :**

* `__future__` en premier
* Standard library
* Tiers
* Locaux
* Pas de `import *`
* Imports locaux uniquement si nécessaires

---

### 1. Docstrings : Numpy Style (Obligatoire)

Toutes les fonctions, classes et méthodes doivent être documentées de manière explicite, pédagogique et testable.

*(exemple conservé tel quel)*

---

### 2. Typage Python 3.10+ (Obligatoire)

Toutes les fonctions doivent être entièrement typées.

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
* garantir l’intégrité des résultats financiers.

#### Exemples de sanitisation

```python
def sanitize_percentage(value: Any) -> float:
    """
    Sanitize a percentage input from user.

    - Converts strings to float
    - Removes '%' if present
    - Clamps value between 0 and 1
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

```python
def sanitize_ticker(ticker: str) -> str:
    """
    Normalize and sanitize ticker symbol.
    """
    ticker = ticker.strip().upper()

    if not ticker.isalnum():
        raise ValueError("Invalid ticker format")

    return ticker
```

**Règle absolue :**

> Aucune donnée utilisateur ne doit entrer dans le moteur de valorisation sans être validée ET sanitizée.

---

### 3. Gestion des Secrets

Toujours via variables d’environnement :

```python
import os
API_KEY = os.getenv("YAHOO_FINANCE_API_KEY")
```

---

## Architecture et Patterns

### Principes SOLID (Obligatoires)

* Single Responsibility
* Open / Closed
* Liskov Substitution
* Interface Segregation
* Dependency Inversion

---

## Logging Standardisé

* Logs en anglais
* Format structuré
* Niveaux cohérents

---

## Tests et Qualité

* Couverture minimale : **85%**
* Tests unitaires, intégration, end-to-end
* Fixtures explicites

---

## Checklist Pre-Commit

* [ ] Header standard
* [ ] Docstrings complètes
* [ ] Typage complet
* [ ] Inputs validés ET sanitizés
* [ ] Logs conformes
* [ ] Tests OK (>85%)
* [ ] Aucun hardcoding métier
* [ ] Aucun calcul opaque

---

*Ce manifeste formalise une application de valorisation financière sérieuse, transparente et pédagogiquement robuste.*

**Dernière mise à jour : 2026-01-17**

```