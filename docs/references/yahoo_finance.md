# Référence Yahoo Finance

**Version** : 2.0 — Janvier 2026

Ce document décrit l'utilisation de Yahoo Finance
comme source de données principale du projet.

---

## Vue d'Ensemble

Yahoo Finance est la source publique principale pour :
- les données financières (états financiers, ratios)
- les prix de marché (temps réel si disponible)
- les données de comparables (peers)
- les données macro (obligations, indices)

---

## Implémentation

### Fichiers

| Fichier | Rôle |
|---------|------|
| `infra/data_providers/yahoo_provider.py` | Provider principal |
| `infra/data_providers/yahoo_raw_fetcher.py` | Fetcher brut |
| `infra/data_providers/financial_normalizer.py` | Normalisation TTM |
| `infra/macro/yahoo_macro_provider.py` | Données macro |

### Bibliothèque

Le projet utilise la bibliothèque `yfinance` :

```python
import yfinance as yf
ticker = yf.Ticker("AAPL")
info = ticker.info
```

---

## Données Récupérées

### Financières

| Donnée | Source | Utilisation |
|--------|--------|-------------|
| Revenue TTM | `income_stmt` | Croissance, DCF Growth |
| EBIT TTM | `income_stmt` | NOPAT, DCF |
| Net Income TTM | `income_stmt` | EPS, ROE |
| Free Cash Flow | `cash_flow` | DCF |
| Total Debt | `balance_sheet` | Equity Bridge |
| Cash | `balance_sheet` | Equity Bridge |
| Shares Outstanding | `info` | Valeur par action |
| Beta | `info` | CAPM |
| Sector | `info` | Fallback sectoriel |

### Prix

| Donnée | Source | Utilisation |
|--------|--------|-------------|
| Prix actuel | `info["currentPrice"]` | Upside |
| Historique | `history()` | Backtest |

### Comparables

| Donnée | Source | Utilisation |
|--------|--------|-------------|
| P/E peers | `info` des peers | Triangulation |
| EV/EBITDA peers | `info` des peers | Triangulation |
| EV/Revenue peers | `info` des peers | Triangulation |

---

## Normalisation

### TTM (Trailing Twelve Months)

Les données financières sont normalisées sur 12 mois glissants :

```python
# Dans financial_normalizer.py
revenue_ttm = sum(quarterly_revenues[-4:])
```

### Gestion des Manquants

| Stratégie | Description |
|-----------|-------------|
| Fallback sur annuel | Si trimestriel manquant |
| Interpolation | Pour certaines métriques |
| Secteur moyen | Si donnée critique manquante (ST-4.1) |

---

## Mode Dégradé (ST-4.1)

Si Yahoo Finance échoue ou renvoie des données aberrantes :

### Détection

```python
# Timeout
if response_time > 10 seconds:
    activate_degraded_mode()

# Données aberrantes
if pe_ratio > 500 or pe_ratio < 1:
    activate_degraded_mode()
```

### Fallback

Les données de secours proviennent de :
- `config/sector_multiples.yaml` (Damodaran 2024)
- `infra/ref_data/country_matrix.py` (données pays)

### Traçabilité

```python
@dataclass
class DataProviderStatus:
    is_degraded_mode: bool
    degraded_reason: str
    fallback_sources: List[str]
    confidence_score: float  # 1.0 = live, 0.7 = fallback
```

---

## Limites Connues

| Limite | Impact | Mitigation |
|--------|--------|------------|
| Données publiques | Qualité variable | Fallback sectoriel |
| Rate limiting | Blocages possibles | Retries + timeout |
| Délais de mise à jour | Pas temps réel | Cache 1h |
| Couverture | Moins de données hors US | Matrice pays |
| Données aberrantes | P/E > 500, etc. | Validation + fallback |

---

## Gestion des Erreurs

### Types d'Erreurs

| Erreur | Cause | Action |
|--------|-------|--------|
| `TickerNotFoundError` | Ticker invalide | Message utilisateur |
| `ExternalServiceError` | API down | Mode dégradé |
| `ValidationError` | Données invalides | Mode dégradé |

### Retries

```python
def safe_api_call(func, label, max_retries=2, timeout_seconds=10):
    """Appel API sécurisé avec retries et timeout."""
```

---

## Caching

Le provider utilise le cache Streamlit :

```python
@st.cache_data(ttl=3600, show_spinner=False)
def get_company_financials(ticker: str) -> CompanyFinancials:
    ...
```

| TTL | Donnée |
|-----|--------|
| 1h | Financières |
| 4h | Historique prix |
| 1h | Peers |

---

## Logging

Format QuantLogger (ST-4.2) :

```
[DATA][INFO] Ticker: AAPL | Source: Yahoo Finance | Status: OK
[PROVIDER][WARNING] Ticker: MSFT | DegradedMode: ACTIVE | Reason: Timeout
```

---

## Références

- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [Yahoo Finance API](https://finance.yahoo.com/)
- [Damodaran Data](http://pages.stern.nyu.edu/~adamodar/)
