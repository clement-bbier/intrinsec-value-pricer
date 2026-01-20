# Guide de Maintenance - Intrinsic Value Pricer

## Internationalisation (i18n)

### Ajout d'une Nouvelle Langue

#### 1. Structure des Dossiers

Créer la hiérarchie suivante dans `src/i18n/` :

```
src/i18n/
├── [code_langue]/              # ex: 'en', 'es', 'de'
│   ├── __init__.py
│   ├── ui/                     # Textes d'interface utilisateur
│   │   ├── __init__.py
│   │   ├── common.py          # Textes communs (boutons, labels)
│   │   ├── expert.py          # Textes du mode expert
│   │   └── results.py         # Textes des résultats
│   └── backend/                # Messages système et diagnostics
│       ├── __init__.py
│       ├── audit.py           # Messages d'audit
│       ├── errors.py          # Messages d'erreur
│       ├── models.py          # Messages de validation des modèles
│       ├── registry.py        # Messages du registre
│       ├── strategies.py      # Messages des stratégies
│       └── workflow.py        # Messages du workflow
```

#### 2. Fichiers de Base

**`src/i18n/[langue]/__init__.py`** :
```python
# Import depuis la langue choisie
from src.i18n.[langue].ui import (
    CommonTexts,
    SidebarTexts,
    # ... autres imports UI
)

from src.i18n.[langue].backend import (
    DiagnosticTexts,
    CalculationErrors,
    # ... autres imports backend
)

__all__ = [
    # UI
    "CommonTexts",
    "SidebarTexts",
    # ... autres exports UI

    # Backend
    "DiagnosticTexts",
    "CalculationErrors",
    # ... autres exports backend
]
```

#### 3. Traduction des Classes

Pour chaque classe de textes (ex: `CommonTexts`), créer une version traduite :

**`src/i18n/[langue]/ui/common.py`** :
```python
@dataclass(frozen=True)
class CommonTexts:
    """Textes communs de l'interface utilisateur."""

    # Boutons et actions
    VALIDATE_BUTTON: str = "Validate"
    CANCEL_BUTTON: str = "Cancel"
    SAVE_BUTTON: str = "Save"
    RESET_BUTTON: str = "Reset"

    # Messages
    LOADING_MESSAGE: str = "Loading..."
    SUCCESS_MESSAGE: str = "Operation completed successfully"
    ERROR_MESSAGE: str = "An error occurred"
```

#### 4. Mise à Jour du Registre Principal

**`src/i18n/__init__.py`** :
```python
# Ajouter l'import de la nouvelle langue
from src.i18n.[langue] import (
    # Importer tous les textes de la nouvelle langue
)

# Ajouter au __all__
__all__ = [
    # ... langues existantes
    "[langue]",  # ex: "en", "es", "de"
]
```

#### 5. Configuration de l'Application

Dans `app/main.py` ou la configuration appropriée, ajouter le support de la nouvelle langue :

```python
# Configuration des langues supportées
SUPPORTED_LANGUAGES = {
    'fr': 'Français',
    'en': 'English',
    '[langue]': 'Nom de la langue'
}
```

#### 6. Tests de Traduction

Vérifier que :
- Tous les imports fonctionnent
- Les textes s'affichent correctement dans l'interface
- Les messages d'erreur sont bien traduits
- Les formats de nombre et devises sont adaptés

### Maintenance des Traductions Existantes

#### Mise à Jour de Textes

Lorsqu'un nouveau texte est ajouté à une classe existante :

1. **Ajouter en français** dans `src/i18n/fr/`
2. **Ajouter dans toutes les langues** supportées
3. **Vérifier la cohérence** des clés entre langues
4. **Tester l'affichage** dans l'interface

#### Bonnes Pratiques

- **Clés explicites** : Préférer `CALCULATION_ERROR` à `ERR_001`
- **Contextualisation** : Inclure le contexte d'usage dans les commentaires
- **Formats** : Respecter les conventions locales (dates, nombres, devises)
- **Longueur** : Adapter la longueur des textes aux contraintes d'interface

## Ajout d'une Nouvelle Stratégie de Valorisation

### 1. Création de la Classe

**`src/valuation/strategies/[nouvelle_strategie].py`** :
```python
from src.valuation.strategies.abstract import ValuationStrategy

class NewStrategy(ValuationStrategy):
    """Description de la nouvelle stratégie."""

    academic_reference = "Auteur, Année"
    economic_domain = "Secteur d'application"

    def execute(self, financials, params):
        # Implémentation
        pass
```

### 2. Enregistrement dans le Registre

**`src/valuation/registry.py`** :
```python
# Ajouter le mapping dans la configuration
STRATEGY_MAPPINGS = {
    # ... stratégies existantes
    ValuationMode.NEW_METHOD: StrategyMetadata(
        strategy_cls=NewStrategy,
        auditor_cls=StandardValuationAuditor,  # ou auditeur spécifique
        ui_renderer_name="render_new_strategy"
    )
}
```

### 3. Interface Utilisateur

Créer le terminal dans `app/ui/expert/terminals/` et l'enregistrer dans la factory.

### 4. Tests

- Tests unitaires de la stratégie
- Tests d'intégration avec le pipeline
- Tests contractuels de sortie
- Tests d'audit

## Ajout d'un Nouveau Fournisseur de Données

### 1. Interface de Base

**`infra/data_providers/base_provider.py`** :
Étendre `DataProvider` avec les méthodes requises.

### 2. Implémentation

**`infra/data_providers/[nouveau_provider].py`** :
```python
from infra.data_providers.base_provider import DataProvider

class NewProvider(DataProvider):
    def fetch_financials(self, ticker: str) -> CompanyFinancials:
        # Implémentation de récupération des données
        pass

    def get_multiples_data(self, sector: str) -> MultiplesData:
        # Implémentation des multiples sectoriels
        pass
```

### 3. Enregistrement

Mettre à jour `YahooProvider` ou créer un nouveau provider principal avec fallback chain incluant le nouveau fournisseur.

### 4. Tests

- Tests de connectivité
- Tests de formatage des données
- Tests de fallback en cas d'erreur

## Déploiement et Mises à Jour

### Variables d'Environnement

- `IVP_LANGUAGE` : Langue par défaut ('fr', 'en', etc.)
- `IVP_CACHE_TTL` : Durée de vie du cache en secondes
- `YAHOO_API_TIMEOUT` : Timeout pour les appels Yahoo Finance

### Mise à Jour de Version

1. **Mettre à jour** `pyproject.toml` ou `setup.py`
2. **Tagger** le commit avec `git tag vX.Y.Z`
3. **Générer** les notes de version
4. **Publier** sur PyPI si applicable

### Monitoring

- Logs d'erreur dans les providers
- Métriques de performance des calculs
- Taux de succès des valorisations
- Utilisation des différentes méthodes