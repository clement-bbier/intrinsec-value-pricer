# Orchestration des Moteurs de Valorisation

**Version** : 2.0 — Janvier 2026  
**Sprint** : 2-3 (Glass Box V2)

Ce document décrit le rôle du module d'orchestration
chargé d'exécuter les stratégies de valorisation.

---

## Rôle du Moteur

Le moteur de valorisation (`src/valuation/engines.py`) :
- Sélectionne la stratégie appropriée via le Registry
- Injecte les données et paramètres
- Exécute le calcul déterministe
- Collecte la trace Glass Box V2
- Lance l'audit post-calcul

**Point d'entrée** :

```python
def run_valuation(
    request: ValuationRequest,
    financials: CompanyFinancials,
    params: DCFParameters
) -> ValuationResult:
    """
    Exécute le moteur de valorisation unifié.
    
    Financial Impact:
        Point d'entrée critique. Une défaillance ici
        invalide l'intégralité du Pitchbook.
    """
```

---

## Architecture

```
src/valuation/
├── engines.py       # Orchestrateur principal
├── pipelines.py     # Chaînage calcul → audit → trace
├── registry.py      # Registre centralisé
├── sotp_engine.py   # Sum-of-the-Parts
└── strategies/
    ├── abstract.py           # Interface commune
    ├── dcf_standard.py       # FCFF Two-Stage
    ├── dcf_fundamental.py    # FCFF Normalisé
    ├── dcf_growth.py         # Revenue-Driven
    ├── dcf_equity.py         # FCFE
    ├── dcf_dividend.py       # DDM
    ├── graham_value.py       # Graham 1974
    ├── rim_banks.py          # Residual Income
    ├── multiples.py          # Valorisation relative
    └── monte_carlo.py        # Extension stochastique
```

---

## Sélection des Stratégies

### Registre Centralisé

```python
# src/valuation/registry.py
class StrategyRegistry:
    """
    Registre unifié des stratégies de valorisation.
    Pattern: Decorator-based auto-registration.
    """
    
    @classmethod
    def get_strategy(cls, mode: ValuationMode) -> Type[BaseStrategy]:
        """Retourne la classe de stratégie pour un mode."""
```

### Hiérarchie Analytique (ST-3.1)

Les modes sont ordonnés par niveau analytique :

```python
class AnalyticalTier(IntEnum):
    DEFENSIVE = 1      # Graham Value
    RELATIVE = 2       # RIM, DDM, Multiples
    FUNDAMENTAL = 3    # DCF variants
```

### Modes Disponibles

| Mode | Stratégie | Description |
|------|-----------|-------------|
| `GRAHAM_VALUE` | `GrahamValueStrategy` | Formule heuristique 1974 |
| `RIM_BANKS` | `RIMBanksStrategy` | Residual Income (banques) |
| `DDM` | `DDMStrategy` | Dividend Discount Model |
| `MULTIPLES` | `MultiplesStrategy` | Valorisation relative |
| `FCFF_STANDARD` | `StandardFCFFStrategy` | DCF Two-Stage classique |
| `FCFF_NORMALIZED` | `FundamentalFCFFStrategy` | FCF normalisé |
| `FCFF_GROWTH` | `GrowthFCFFStrategy` | Revenue-driven |
| `FCFE` | `FCFEStrategy` | Flux vers actionnaires |

---

## Pipeline d'Exécution

```
1. Validation des entrées (ValuationRequest)
        ↓
2. Sélection de la stratégie (Registry)
        ↓
3. Construction du contexte (CalculationContext)
        ↓
4. Exécution de la stratégie
        ↓
5. Collecte des étapes (CalculationStep[])
        ↓
6. Extension Monte Carlo (optionnel)
        ↓
7. Audit post-calcul (AuditEngine)
        ↓
8. Construction du ValuationResult
```

---

## Glass Box V2 (Sprint 2-3)

### CalculationStep Enrichi

Chaque étape de calcul contient :

```python
@dataclass
class CalculationStep:
    step_key: str              # "compute_wacc"
    label: str                 # "Calcul du WACC"
    theoretical_formula: str   # LaTeX: "WACC = ..."
    actual_calculation: str    # "8.5% × 70% + 4.2% × 30% × (1 - 25%)"
    numerical_substitution: str # "= 5.95% + 0.95% = 6.90%"
    result: float              # 0.069
    variables_map: Dict[str, VariableInfo]
    interpretation: Optional[str]
```

### VariableInfo

Traçabilité de chaque variable :

```python
@dataclass
class VariableInfo:
    symbol: str           # "Ke"
    value: float          # 0.085
    formatted: str        # "8.50%"
    source: VariableSource  # YAHOO, COMPUTED, MANUAL
    is_override: bool     # True si surcharge expert
```

### Sources de Variables

| Source | Description |
|--------|-------------|
| `YAHOO` | Donnée directe Yahoo Finance |
| `COMPUTED` | Calculée depuis d'autres variables |
| `MANUAL` | Saisie par l'expert |
| `FALLBACK` | Données de secours sectorielles |
| `MACRO_API` | Données macro (obligations) |

---

## Stratégies de Valorisation

### Interface Commune

```python
class BaseStrategy(ABC):
    """Interface abstraite pour toutes les stratégies."""
    
    @abstractmethod
    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters,
        context: CalculationContext
    ) -> StrategyResult:
        """Exécute la valorisation."""
    
    @abstractmethod
    def get_methodology_latex(self) -> str:
        """Retourne la formule LaTeX principale."""
```

### Exemple : DCF Standard

```python
class StandardFCFFStrategy(BaseStrategy):
    """
    DCF Two-Stage FCFF.
    
    Formule:
    V_0 = Σ(FCF_t / (1 + WACC)^t) + TV_n / (1 + WACC)^n
    
    TV = FCF_n × (1 + g) / (WACC - g)
    """
```

---

## Extension Monte Carlo

L'extension Monte Carlo :
- N'est PAS une méthode de valorisation
- Ne modifie JAMAIS la logique des modèles
- Quantifie UNIQUEMENT l'incertitude

```python
class MonteCarloEngine:
    """
    Extension probabiliste.
    
    Paramètres perturbés :
    - FCF de base (vol_base_flow)
    - Beta (vol_beta)
    - Croissance (vol_g)
    """
```

---

## Logging (ST-4.2)

Format QuantLogger institutionnel :

```
[VALUATION][SUCCESS] Ticker: AAPL | Model: FCFF_STANDARD | 
  IV: 185.20 | AuditScore: 88.5% | Duration: 1250ms
```

---

## Invariants

- Une stratégie = une méthode financière
- Aucune stratégie ne dépend de l'UI
- Aucune logique probabiliste dans le moteur déterministe
- Toute étape est traçable via Glass Box
- `from __future__ import annotations` obligatoire
