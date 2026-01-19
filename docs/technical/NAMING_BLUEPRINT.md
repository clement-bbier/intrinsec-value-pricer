# NAMING BLUEPRINT

**Version** : 2.0 — Janvier 2026

Ce document définit les conventions de nommage
du projet *Intrinsic Value Pricer*.

---

## Principes Généraux

| Principe | Description |
|----------|-------------|
| **Clarté** | Le nom décrit la fonction |
| **Cohérence** | Même pattern partout |
| **Préfixes normalisés** | Indiquent le type |
| **Pas d'abréviations** | Sauf standards (TTM, WACC) |

---

## Fichiers Python

### Structure

```
{domain}_{type}.py
```

### Exemples

| Fichier | Description |
|---------|-------------|
| `dcf_standard.py` | Stratégie DCF Standard |
| `yahoo_provider.py` | Provider Yahoo |
| `financial_math.py` | Fonctions mathématiques |
| `glass_box.py` | Modèle Glass Box |

---

## Classes

### Pattern

```python
class {Noun}{Role}:
    """Description."""
```

### Exemples

| Classe | Rôle |
|--------|------|
| `StandardFCFFStrategy` | Stratégie de valorisation |
| `YahooFinanceProvider` | Provider de données |
| `AuditEngine` | Moteur d'audit |
| `TextRegistry` | Registre de textes |
| `PitchbookPDFGenerator` | Générateur PDF |

### Suffixes Standardisés

| Suffixe | Usage |
|---------|-------|
| `Strategy` | Stratégie de valorisation |
| `Provider` | Source de données |
| `Engine` | Moteur/Orchestrateur |
| `Factory` | Création dynamique |
| `Registry` | Registre/Catalogue |
| `Renderer` | Rendu UI |
| `Generator` | Génération de contenu |

---

## Fonctions

### Pattern

```python
def {verb}_{object}(...):
    """Description."""
```

### Verbes Normalisés

| Verbe | Usage | Exemple |
|-------|-------|---------|
| `get_` | Récupération | `get_company_financials()` |
| `compute_` | Calcul | `compute_wacc()` |
| `run_` | Exécution | `run_valuation()` |
| `render_` | Affichage UI | `render_results()` |
| `generate_` | Génération | `generate_pitchbook_pdf()` |
| `validate_` | Validation | `validate_multiples()` |
| `create_` | Création | `create_terminal()` |
| `map_` | Transformation | `map_request_to_params()` |
| `format_` | Formatage | `format_smart_number()` |
| `log_` | Logging | `log_success()` |

### Préfixes Privés

| Préfixe | Usage |
|---------|-------|
| `_` | Méthode privée |
| `__` | Méthode très privée (rare) |

---

## Variables

### Pattern

```python
{adjective}_{noun}
```

### Exemples

| Variable | Description |
|----------|-------------|
| `final_params` | Paramètres finaux |
| `raw_data` | Données brutes |
| `median_pe` | P/E médian |
| `is_degraded` | État dégradé |
| `confidence_score` | Score de confiance |

### Types Aliasés

| Alias | Type | Usage |
|-------|------|-------|
| `Rate` | `float` | Taux (Rf, Ke, WACC) |
| `Currency` | `str` | Devise (USD, EUR) |

---

## Constantes

### Pattern

```python
UPPER_SNAKE_CASE = value
```

### Exemples

| Constante | Description |
|-----------|-------------|
| `MAX_PEERS_ANALYSIS` | Limite de peers |
| `DEFAULT_SIMULATIONS` | Simulations par défaut |
| `MIN_PE_RATIO` | P/E minimum valide |

---

## Enums

### Pattern

```python
class {Noun}(Enum):
    UPPER_CASE = "value"
```

### Exemples

```python
class ValuationMode(Enum):
    FCFF_STANDARD = "FCFF_STANDARD"
    GRAHAM_VALUE = "GRAHAM_VALUE"

class SeverityLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
```

---

## Modèles Pydantic

### Pattern

```python
class {Noun}(BaseModel):
    field_name: type
```

### Exemples

| Modèle | Description |
|--------|-------------|
| `ValuationRequest` | Requête de valorisation |
| `ValuationResult` | Résultat de valorisation |
| `CompanyFinancials` | Données financières |
| `DCFParameters` | Paramètres DCF |
| `PitchbookData` | Données Pitchbook |

---

## Fichiers YAML

### Pattern

```
{domain}_{type}.yaml
```

### Exemples

| Fichier | Description |
|---------|-------------|
| `sector_multiples.yaml` | Multiples sectoriels |
| `settings.yaml` | Configuration globale |
| `fr.yaml` | Textes français |

---

## Clés i18n

### Pattern

```
{section}.{subsection}.{key}
```

### Exemples

| Clé | Valeur |
|-----|--------|
| `sidebar.title` | Titre de la sidebar |
| `workflow.status_complete` | Message de fin |
| `expert_terminal.inp_rf` | Label taux sans risque |

---

## Tests

### Pattern

```
test_{module}_{feature}.py
```

### Exemples

| Fichier | Description |
|---------|-------------|
| `test_architecture_contracts.py` | Contrats d'architecture |
| `test_models_contracts.py` | Contrats de modèles |
| `test_valuation_pipeline.py` | Pipeline de valorisation |

---

## Docstrings

### Pattern (NumPy Style)

```python
def function_name(param: Type) -> ReturnType:
    """
    Description courte.
    
    Description longue si nécessaire.
    
    Parameters
    ----------
    param : Type
        Description du paramètre.
    
    Returns
    -------
    ReturnType
        Description du retour.
    
    Raises
    ------
    ExceptionType
        Quand l'exception est levée.
    
    Financial Impact
    ----------------
    Impact sur la valorisation.
    
    Examples
    --------
    >>> function_name(value)
    result
    """
```

---

## Anti-Patterns

| Anti-Pattern | Problème | Solution |
|--------------|----------|----------|
| `data` | Trop générique | `raw_data`, `financials` |
| `process` | Trop vague | `compute_wacc`, `run_audit` |
| `handle` | Imprécis | `validate_`, `transform_` |
| `util` | Fourre-tout | Fichier dédié par domaine |
| `helper` | Non descriptif | Nom de fonction explicite |
