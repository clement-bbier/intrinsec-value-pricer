# Audit Engine & Confidence Score

**Version** : 2.0 — Janvier 2026  
**Sprint** : 4.2 (Diagnostic Pédagogique)

Ce document décrit le rôle du **moteur d'audit**
chargé d'évaluer la robustesse d'une valorisation.

L'audit ne modifie jamais la valeur intrinsèque calculée.
Il fournit une **mesure de confiance** associée au résultat.

---

## Objectif de l'Audit

- Détecter les incohérences économiques
- Mesurer l'incertitude structurelle
- Qualifier la fiabilité du résultat
- **Éduquer l'utilisateur** sur les risques (ST-4.2)

L'audit est une **méthode d'évaluation**, pas un jugement d'investissement.

---

## Architecture

```
infra/auditing/
├── audit_engine.py     # Orchestrateur principal
├── auditors.py         # Auditeurs spécialisés par pilier
└── backtester.py       # Validation historique

src/diagnostics.py      # DiagnosticEvent + FinancialContext
```

---

## Implémentation

### AuditEngine

```python
class AuditEngine:
    """
    Moteur d'audit institutionnel.
    
    Évalue 4 piliers de risque et produit un score global.
    """
    
    def compute_audit(
        self,
        result: ValuationResult,
        mode: ValuationMode
    ) -> AuditReport:
        """Exécute l'audit complet."""
```

### AuditorFactory

```python
class AuditorFactory:
    """Factory pour les auditeurs spécialisés."""
    
    @staticmethod
    def get_auditor(mode: ValuationMode) -> BaseAuditor:
        """Retourne l'auditeur approprié au mode."""
```

---

## Piliers Évalués

| Pilier | Description | Exemples de Tests |
|--------|-------------|-------------------|
| **Profitabilité** | Qualité des marges | ROE > 0, Marge opérationnelle positive |
| **Solvabilité** | Risque financier | ICR > 2.0, D/E < 2.0 |
| **Valorisation** | Cohérence du modèle | g < WACC, Beta ∈ [0.5, 2.0] |
| **Marché** | Données de marché | Prix disponible, Volume > 0 |

---

## Diagnostic Pédagogique (ST-4.2)

### FinancialContext

Chaque diagnostic peut inclure un contexte financier explicatif :

```python
@dataclass
class FinancialContext:
    parameter_name: str      # "Beta"
    current_value: float     # 3.5
    typical_range: tuple     # (0.5, 2.0)
    statistical_risk: str    # "Beta > 3.0 = volatilité extrême"
    recommendation: str      # "Utiliser proxy sectoriel"
```

### Exemple de Transformation

**Avant (erreur brute)** :
```
Math Error: Division by zero
```

**Après (diagnostic pédagogique)** :
```
La croissance perpétuelle (5.00%) dépasse le WACC (4.50%).
Le modèle de Gordon ne peut pas converger.

Le paramètre Taux de croissance perpétuelle (g) (5.00%) est hors de 
la plage typique (1.00% - 3.00%). Le modèle de Gordon requiert g < WACC.
Avec g=5.00% et WACC=4.50%, la formule TV = FCF/(WACC-g) produit une 
valeur négative ou infinie.

Recommandation : Réduire g en dessous de 3% ou utiliser Exit Multiple.
```

---

## DiagnosticRegistry

Catalogue centralisé des événements :

```python
class DiagnosticRegistry:
    @staticmethod
    def model_g_divergence(g: float, wacc: float) -> DiagnosticEvent:
        """Erreur de convergence Gordon Shapiro."""
        return DiagnosticEvent(
            code="MODEL_G_DIVERGENCE",
            severity=SeverityLevel.CRITICAL,
            message=f"La croissance g ({g:.2%}) dépasse le WACC ({wacc:.2%})",
            financial_context=FinancialContext(
                parameter_name="Taux de croissance perpétuelle (g)",
                current_value=g,
                typical_range=(0.01, 0.03),
                statistical_risk="Le modèle de Gordon requiert g < WACC",
                recommendation="Réduire g ou utiliser Exit Multiple"
            )
        )
```

### Événements Disponibles

| Code | Sévérité | Description |
|------|----------|-------------|
| `MODEL_G_DIVERGENCE` | CRITICAL | g ≥ WACC |
| `MODEL_MC_INSTABILITY` | ERROR | Simulations instables |
| `DATA_MISSING_CORE_METRIC` | ERROR | Donnée essentielle manquante |
| `RISK_EXCESSIVE_GROWTH` | WARNING | g > 10% |
| `RISK_EXTREME_BETA` | WARNING | Beta > 3.0 |
| `DATA_NEGATIVE_BETA` | WARNING | Beta < 0 |
| `FCFE_NEGATIVE_FLOW` | CRITICAL | FCFE < 0 |
| `DDM_PAYOUT_EXCESSIVE` | WARNING | Payout > 100% |
| `MODEL_SGR_DIVERGENCE` | WARNING | g > SGR |
| `PROVIDER_API_FAILURE` | WARNING | API en erreur |

---

## Calcul du Score

### Pondération par Mode

```python
class AuditWeights:
    AUTO = {
        "profitability": 0.25,
        "solvency": 0.25,
        "valuation": 0.30,
        "market": 0.20,
    }
    
    MANUAL = {
        "profitability": 0.20,
        "solvency": 0.20,
        "valuation": 0.40,
        "market": 0.20,
    }
```

### Pénalités

| Condition | Pénalité |
|-----------|----------|
| Test échoué (WARNING) | -5 points |
| Test échoué (ERROR) | -15 points |
| Mode dégradé actif | -10 × (1 - confidence) |
| Données manquantes | -10 points |

### Grading

| Score | Grade | Signification |
|-------|-------|---------------|
| 90-100 | A | Excellent, haute confiance |
| 80-89 | B | Bon, confiance modérée |
| 70-79 | C | Acceptable, vigilance requise |
| 60-69 | D | Risqué, hypothèses fragiles |
| 0-59 | F | Critique, résultat non fiable |

---

## Intégration avec Glass Box

Chaque `AuditStep` est visible dans l'onglet "Rapport d'Audit" :

```python
@dataclass
class AuditStep:
    step_key: str           # "audit_icr_check"
    label: str              # "Interest Coverage Ratio"
    verdict: bool           # True = OK, False = Alerte
    evidence: str           # "ICR = 3.5 > 2.0"
    severity: AuditSeverity # WARNING, ERROR, INFO
```

---

## Logging

Format QuantLogger (ST-4.2) :

```
[AUDIT][INFO] Ticker: AAPL | Score: 88.5% | Passed: 12 | Failed: 2 | Grade: B
```

---

## Invariants

- L'audit est **post-calcul** (jamais avant)
- Aucune hypothèse n'est modifiée par l'audit
- Tout signal est traçable et explicite
- Les diagnostics sont toujours pédagogiques
