# Data Providers & Sources de Données

**Version** : 2.0 — Janvier 2026  
**Sprint** : 4.1 (Mode Dégradé)

Ce document décrit la couche de récupération
et de préparation des données financières et macroéconomiques.

---

## Rôle des Data Providers

Les providers sont responsables de :
- l'accès aux données externes (Yahoo Finance),
- la normalisation des formats (TTM),
- la gestion des données manquantes,
- le **fallback automatique** sur données sectorielles (ST-4.1).

Ils ne contiennent **aucune logique de valorisation**.

---

## Architecture

```
infra/data_providers/
├── base_provider.py          # Interface abstraite
├── yahoo_provider.py         # Provider principal
├── yahoo_raw_fetcher.py      # Fetcher brut
├── financial_normalizer.py   # Normalisation TTM
└── extraction_utils.py       # safe_api_call + timeout

infra/ref_data/
├── country_matrix.py         # Données pays (Rf, MRP)
└── sector_fallback.py        # Fallback multiples sectoriels

infra/macro/
└── yahoo_macro_provider.py   # Données macro (obligations)
```

---

## Implémentation

### YahooFinanceProvider

```python
class YahooFinanceProvider(DataProvider):
    """
    Orchestrateur de données Yahoo Finance.
    
    ST-4.1 : Implémente le Mode Dégradé avec fallback
    automatique sur les multiples sectoriels.
    """
    
    # Seuils de validation des données
    MIN_PE_RATIO: float = 1.0
    MAX_PE_RATIO: float = 500.0
    MIN_EV_EBITDA: float = 0.5
    MAX_EV_EBITDA: float = 100.0
```

### Méthodes Principales

| Méthode | Description |
|---------|-------------|
| `get_company_financials()` | Données financières normalisées |
| `get_peer_multiples()` | Multiples sectoriels (réels ou fallback) |
| `get_price_history()` | Historique des prix |
| `is_degraded_mode()` | Vérifie si fallback activé |
| `get_degraded_mode_info()` | Infos pour bandeau UI |

---

## Mode Dégradé (ST-4.1)

### Déclenchement

Le mode dégradé est activé si :
1. L'API Yahoo Finance échoue (timeout, erreur réseau)
2. Les données retournées sont aberrantes (P/E > 500, etc.)
3. Aucun peer n'est trouvé pour la triangulation

### Fallback Sectoriel

```yaml
# config/sector_multiples.yaml
technology:
  pe_ratio: 28.5
  ev_ebitda: 18.2
  pb_ratio: 6.8
  source: "Damodaran 2024"

_metadata:
  confidence_score: 0.70
```

### Traçabilité

```python
@dataclass
class DataProviderStatus:
    is_degraded_mode: bool = False
    degraded_reason: str = ""
    fallback_sources: List[str] = field(default_factory=list)
    confidence_score: float = 1.0  # 1.0 = live, 0.7 = fallback
```

### UI Signalétique

Quand le mode dégradé est actif, un bandeau s'affiche :

```
┌─────────────────────────────────────────────────────┐
│ Mode dégradé                      Confiance: 70%  │
│ Raison : API peers indisponible pour AAPL          │
│ Sources : Damodaran 2024 - Technology sector       │
└─────────────────────────────────────────────────────┘
```

---

## Données Récupérées

### Financières (Yahoo Finance)
- États financiers publiés (Income, Balance, Cash Flow)
- Prix de marché (temps réel si disponible)
- Métriques de valorisation (P/E, EV/EBITDA)
- Beta et volatilité

### Macro (Yahoo Macro Provider)
- Taux sans risque (obligations 10 ans par pays)
- Primes de risque marché
- Taux d'inflation

### Référence (ref_data/)
- Matrice pays (Rf, MRP, taux d'imposition)
- Multiples sectoriels moyens (Damodaran)

---

## Gestion des Erreurs

### Timeout

```python
def safe_api_call(func, label, max_retries=2, timeout_seconds=10):
    """Appel API sécurisé avec timeout et retries."""
```

### Validation des Données

```python
def _validate_multiples(self, multiples: MultiplesData) -> bool:
    """Détecte les données aberrantes."""
    if multiples.median_pe < 1.0 or multiples.median_pe > 500.0:
        return False
    return True
```

---

## Limites Connues

| Limite | Impact | Mitigation |
|--------|--------|------------|
| Données publiques uniquement | Qualité variable | Fallback sectoriel |
| Délais de mise à jour | Données pas temps réel | Cache 1h |
| Couverture géographique | Moins de données hors US | Matrice pays |
| Rate limiting Yahoo | Blocages possibles | Retries + timeout |

Ces limites sont intégrées dans le calcul du Confidence Score.

---

## Intégration avec l'Audit

Le mode dégradé impacte le Confidence Score :

```python
# Dans AuditEngine
if provider.is_degraded_mode():
    score_penalty = (1.0 - provider.status.confidence_score) * 10
    final_score -= score_penalty
```

---

## Logging

Format QuantLogger (ST-4.2) :

```
[PROVIDER][WARNING] Ticker: AAPL | DegradedMode: ACTIVE | 
  Reason: API timeout | Source: Damodaran 2024 | Confidence: 70%
```
