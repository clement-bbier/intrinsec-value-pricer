# CONTRIBUTING.md — Manifeste de Developpement

## Objectif

Ce manifeste definit les standards de qualite et de maintenabilite pour l'application **Intrinsic Value Pricer**. Il garantit un code professionnel, maintenable et evolutif, digne d'un outil financier institutionnel.

---

## Standards Obligatoires

### 0. Imports : En Haut des Fichiers (Obligatoire)

Tous les imports doivent être regroupés en haut du fichier, après le header de fichier :

```python
"""
path/to/file.py
[Header de fichier...]
"""

from __future__ import annotations

# Imports standard library
import logging
from typing import Dict, Optional, Any

# Imports tiers (third-party)
import streamlit as st
import pandas as pd

# Imports locaux (local)
from core.models import ValuationMode, ValuationRequest
from app.ui.expert_terminals import ExpertTerminalFactory

# Code...
```

**Règles :**
- `__future__` imports en premier
- Imports standard library
- Imports tiers (séparés par une ligne vide)
- Imports locaux (séparés par une ligne vide)
- Imports relatifs avec `from` préférés aux imports absolus
- Éviter les imports avec `*` (sauf exceptions justifiées)
- Imports locaux seulement si nécessaire pour éviter dépendances circulaires

### 1. Style de Docstring : Format Google Style (Obligatoire)

Toutes les fonctions, classes et methodes doivent utiliser le format Google Style :

```python
def calculate_wacc(
    equity_value: float,
    debt_value: float,
    equity_cost: float,
    debt_cost: float,
    tax_rate: float
) -> float:
    """
    Calculate Weighted Average Cost of Capital.

    WACC = (E/V) * Ke + (D/V) * Kd * (1 - Tc)

    Parameters
    ----------
    equity_value : float
        Market value of equity.
    debt_value : float
        Market value of debt.
    equity_cost : float
        Cost of equity (Ke).
    debt_cost : float
        Cost of debt before tax (Kd).
    tax_rate : float
        Corporate tax rate (Tc).

    Returns
    -------
    float
        WACC as decimal (e.g., 0.085 for 8.5%).

    Raises
    ------
    ValueError
        If equity_value or debt_value is negative.

    Examples
    --------
    >>> calculate_wacc(1000, 500, 0.10, 0.05, 0.25)
    0.08125
    """
    if equity_value < 0 or debt_value < 0:
        raise ValueError("Values must be non-negative")

    total_value = equity_value + debt_value
    wacc = (
        (equity_value / total_value) * equity_cost +
        (debt_value / total_value) * debt_cost * (1 - tax_rate)
    )
    return wacc
```

### 2. Typage Python 3.10+ : Type Hints Obligatoires

Toutes les signatures de fonctions doivent inclure des type hints complets :

```python
from typing import Optional, List, Dict, Any
from core.models import ValuationResult

def process_valuation_result(
    result: ValuationResult,
    format_currency: bool = True,
    precision: int = 2
) -> Dict[str, Any]:
    """Process valuation result with formatting options."""
    # Implementation...
```

### 3. Header de Fichier Standard

Chaque fichier Python doit commencer par ce bloc de commentaires :

```python
"""
path/to/file.py

[DESCRIPTION BREVE DU ROLE DU FICHIER]

Version : V[X.Y] — [DT-XXX] Resolution
Pattern : [Design Pattern utilise, ex: Factory, Strategy]
Style : Numpy docstrings

[RISQUES FINANCIERS eventuels]
- Erreur de calcul peut mener a valorisations incorrectes
- Dependance aux donnees Yahoo Finance (risque de disponibilite)

[DEPENDANCES CRITIQUES]
- numpy >= 1.21.0
- pandas >= 1.3.0
"""

from __future__ import annotations

import logging
from typing import [imports]

logger = logging.getLogger(__name__)
```

---

## Architecture et Patterns

### 1. Principes SOLID Obligatoires

- **S**ingle Responsibility : Une classe = une responsabilite
- **O**pen/Closed : Extension sans modification
- **L**iskov Substitution : Sous-classes interchangeables
- **I**nterface Segregation : Interfaces minimales
- **D**ependency Inversion : Dependre d'abstractions

### 2. Design Patterns Recommandes

- **Factory** : Pour creation d'objets complexes
- **Strategy** : Pour algorithmes interchangeables
- **Observer** : Pour evenements et notifications
- **Adapter** : Pour interfaces tierces
- **Decorator** : Pour extension fonctionnelle

### 3. Structure de Projet

```
intrinsic-value-pricer/
├── app/                    # Interface utilisateur
│   ├── ui/                # Nouveaux composants (migration en cours)
│   └── ui_components/     # Legacy (a migrer progressivement)
├── core/                  # Logique metier
│   ├── models/           # Structures de donnees
│   ├── valuation/        # Moteur de calcul
│   └── i18n/             # Internationalisation
├── infra/                # Infrastructure
│   ├── data_providers/   # Sources de donnees
│   └── auditing/         # Audit et conformite
└── tests/                # Tests automatises
```

---

## Conventions de Nommage

### 1. Verbes d'Action Standardises

| Action | Prefixe | Exemple |
|--------|---------|---------|
| UI | `render_` | `render_valuation_form()` |
| Calcul | `compute_` | `compute_wacc()` |
| Donnees | `fetch_` | `fetch_historical_prices()` |
| Validation | `validate_` | `validate_inputs()` |
| Conversion | `convert_` | `convert_to_percentage()` |

### 2. Noms de Variables

```python
# Bon
valuation_result: ValuationResult
dcf_parameters: DCFParameters
peer_multiples: List[PeerMultiple]

# Mauvais
result: Any
params: dict
peers: list
```

### 3. Constantes Centralisees

Toutes les constantes sont centralisees dans `core/config/constants.py` pour faciliter l'acces et la maintenance :

```python
# core/config/constants.py
DEFAULT_SIMULATIONS = 5000
MAX_PROJECTION_YEARS = 15
DEFAULT_PROJECTION_YEARS = 5
MIN_PROJECTION_YEARS = 3

# Seuils d'audit
AUDIT_ICR_THRESHOLD = 1.5
AUDIT_SOTP_DISCOUNT_MAX = 0.25

# Parametres Monte Carlo
MONTE_CARLO_RHO_DEFAULT = -0.3
MONTE_CARLO_TIMEOUT_SECONDS = 30
```

---

## Logging Standardise

### 1. Format Standard

```python
logger.info("[Module] Action completed | key=value, key2=value2")
logger.warning("[Module] Non-critical issue | ticker=AAPL, error=timeout")
logger.error("[Module] Critical failure | error=division_by_zero")
```

### 2. Niveaux d'Usage

- `DEBUG` : Informations techniques de developpement
- `INFO` : Evenements metier importants
- `WARNING` : Problemes non-bloquants
- `ERROR` : Erreurs critiques

### 3. Messages en Anglais

Tous les logs doivent etre en anglais pour la maintenabilite internationale.

---

## Internationalisation (i18n)

### 1. Toutes les Chaines Utilisateur dans i18n

```python
# Bon
from core.i18n import ExpertTerminalTexts
st.button(ExpertTerminalTexts.BTN_CALCULATE)

# Mauvais
st.button("Lancer la valorisation")
```

### 2. Structure i18n

```
core/i18n/
├── fr/
│   ├── ui/
│   │   ├── expert.py
│   │   └── results.py
│   └── backend/
│       ├── errors.py
│       └── logs.py
└── en/  # Future
```

---

## Tests et Qualite

### 1. Couverture Minimale : 85%

- Tests unitaires pour toute logique metier
- Tests d'integration pour les workflows
- Tests end-to-end pour les scenarios critiques

### 2. Types de Tests

```python
# tests/unit/test_wacc.py
def test_calculate_wacc_basic():
    """Test calcul WACC basique."""
    # Arrange
    # Act
    # Assert

# tests/integration/test_valuation_workflow.py
def test_full_valuation_pipeline():
    """Test pipeline complet de valorisation."""
    # ...
```

### 3. Fixtures et Mocks

Utiliser `pytest` fixtures pour les donnees de test :

```python
@pytest.fixture
def sample_company() -> CompanyFinancials:
    """Fixture pour donnees entreprise exemple."""
    return CompanyFinancials(
        ticker="AAPL",
        market_cap=3_000_000_000_000,
        # ...
    )
```

---

## Gestion des Erreurs

### 1. Exceptions Customisees

```python
from core.exceptions import ValuationException, DataUnavailableException

try:
    result = run_valuation(request)
except DataUnavailableException as e:
    logger.error(f"[Engine] Data fetch failed | ticker={request.ticker}")
    st.error(f"Donnees indisponibles pour {request.ticker}")
except ValuationException as e:
    logger.error(f"[Engine] Valuation failed | error={str(e)}")
    st.error("Erreur de calcul - parametres a verifier")
```

### 2. Gestion des Diagnostics

Utiliser le systeme de diagnostics pour les avertissements :

```python
from core.diagnostics import DiagnosticEvent, SeverityLevel

diagnostic = DiagnosticEvent(
    domain=DiagnosticDomain.VALUATION,
    code="WACC_HIGH",
    message="WACC eleve detecte (>15%)",
    severity=SeverityLevel.WARNING,
    remediation="Verifier les inputs de cout du capital"
)
```

---

## Securite et Conformite

### 1. Validation des Inputs

```python
def validate_ticker(ticker: str) -> bool:
    """Valide format du ticker boursier."""
    if not ticker or len(ticker) > 10:
        return False
    # Regex validation...
    return True
```

### 2. Sanitisation des Donnees

Toutes les donnees utilisateur doivent etre sanitisees avant traitement.

### 3. Gestion des Secrets

Utiliser des variables d'environnement pour les cles API :

```python
import os
API_KEY = os.getenv("YAHOO_FINANCE_API_KEY")
```

---

## Performance et Optimisation

### 1. Complexite Algorithmique

- Maintenir O(n) ou mieux pour les calculs principaux
- Eviter les boucles imbriquees couteuses
- Utiliser NumPy pour les operations vectorielles

### 2. Gestion Memoire

```python
# Liberer la memoire apres usage
import gc
del large_dataframe
gc.collect()
```

### 3. Caching Intelligent

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fetch_historical_prices(ticker: str) -> pd.DataFrame:
    """Cache les prix historiques pour eviter les appels repetes."""
    # Implementation...
```

---

## Ressources et References

### 1. Standards Externes

- [PEP 8](https://pep8.org/) : Style Python officiel
- [Google Python Style](https://google.github.io/styleguide/pyguide.html)
- [NumPy Docstring Standard](https://numpydoc.readthedocs.io/)
- [refactoring.guru](https://refactoring.guru/design-patterns) : Catalogue des Design Patterns

### 2. Sources Financieres et Methodologiques

- **Aswath Damodaran** : Reference mondiale en valorisation d'entreprise
  - "Investment Valuation" (3e edition)
  - "Applied Corporate Finance"
  - Site web : [damodaran.com](https://pages.stern.nyu.edu/~adamodar/)

- **CFA Institute** : Standards professionnels en finance
  - CFA Program Curriculum (Corporate Finance)
  - "Standards of Practice Handbook"

- **Bloomberg** : Donnees et methodes de marche
  - Bloomberg Valuation Services
  - DCF Models et Comparables Analysis

- **McKinsey & Company** : Methodes institutionnelles
  - "Valuation: Measuring and Managing the Value of Companies"
  - Frameworks d'analyse strategique

### 3. Outils Recommandes

- `black` : Formatage automatique
- `isort` : Tri des imports
- `mypy` : Verification de types
- `pylint` : Analyse de code
- `pytest` : Tests automatises

### 4. Formation Continue

- Clean Code de Robert C. Martin
- Domain-Driven Design d'Eric Evans
- Python Best Practices

---

## Checklist Pre-Commit

Avant chaque commit, verifier :

- [ ] Tous les nouveaux fichiers ont un header standard
- [ ] Toutes les fonctions ont des docstrings Google Style
- [ ] Tous les parametres ont des type hints
- [ ] Toutes les chaines utilisateur sont dans i18n
- [ ] Tous les logs sont en anglais avec format standard
- [ ] Tests passent avec couverture >85%
- [ ] Linting passe (black, isort, mypy, pylint)
- [ ] Aucune regression detectee

---

*Ce manifeste evolue avec le projet. Derniere mise a jour : 2026-01-17*