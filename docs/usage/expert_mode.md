# Mode EXPERT — Contrôle Total

**Version** : 2.0 — Janvier 2026  
**Sprint** : 3 (UX Pitchbook)

Le **mode EXPERT** permet à l'utilisateur
de fournir explicitement ses propres hypothèses
via 7 terminaux spécialisés.

---

## Philosophie

- Flexibilité maximale
- Responsabilité utilisateur explicite
- Contrôle direct des paramètres clés
- Workflow séquencé "Logical Path" (ST-3.1)

Le système vérifie la cohérence,
mais n'impose pas d'hypothèses normatives.

---

## Terminaux Disponibles

### Hiérarchie Analytique

Les modèles sont ordonnés par niveau de complexité :

| Tier | Terminal | Fichier |
|------|----------|---------|
| **DEFENSIVE** | Graham Value | `graham_value_terminal.py` |
| **RELATIVE** | RIM Banks | `rim_bank_terminal.py` |
| **RELATIVE** | DDM | `ddm_terminal.py` |
| **FUNDAMENTAL** | FCFF Standard | `fcff_standard_terminal.py` |
| **FUNDAMENTAL** | FCFF Normalized | `fcff_normalized_terminal.py` |
| **FUNDAMENTAL** | FCFF Growth | `fcff_growth_terminal.py` |
| **FUNDAMENTAL** | FCFE | `fcfe_terminal.py` |

---

## Workflow "Logical Path"

Chaque terminal suit un séquençage strict :

```
┌─────────────────────────────────────┐
│ SECTION 1 : HEADER                  │
│ Logo, titre, description méthode    │
├─────────────────────────────────────┤
│ SECTION 2 : OPÉRATIONNEL            │
│ CA, Marges, BFR, Flux de base       │
├─────────────────────────────────────┤
│ SECTION 3 : RISQUE & CAPITAL        │
│ Rf, Beta, MRP, Kd, WACC             │
├─────────────────────────────────────┤
│ SECTION 4 : VALEUR TERMINALE        │
│ Gordon Growth ou Exit Multiple      │
├─────────────────────────────────────┤
│ SECTION 5 : EQUITY BRIDGE           │
│ Dette, Cash, Minoritaires, Actions  │
├─────────────────────────────────────┤
│ SECTION 6 : EXTENSIONS              │
│ Monte Carlo, Scénarios, Peers       │
├─────────────────────────────────────┤
│ SECTION 7 : SUBMIT                  │
│ Bouton de lancement                 │
└─────────────────────────────────────┘
```

---

## Paramètres Configurables

### Coût du Capital

| Paramètre | Description | Plage typique |
|-----------|-------------|---------------|
| Rf | Taux sans risque | 2-5% |
| Beta | Sensibilité au marché | 0.5-2.0 |
| MRP | Prime de risque marché | 4-7% |
| Kd | Coût de la dette | 3-8% |
| Tax | Taux d'imposition | 15-35% |

### Croissance

| Paramètre | Description | Plage typique |
|-----------|-------------|---------------|
| g | Croissance des flux | 2-10% |
| gn | Croissance perpétuelle | 1-3% |
| Années | Horizon de projection | 5-10 |

### Valeur Terminale

| Méthode | Description |
|---------|-------------|
| **Gordon Growth** | TV = FCF × (1+g) / (WACC - g) |
| **Exit Multiple** | TV = EBITDA × Multiple |

### Equity Bridge

| Paramètre | Description |
|-----------|-------------|
| Dette totale | Dette financière brute |
| Trésorerie | Cash et équivalents |
| Minoritaires | Intérêts minoritaires |
| Provisions retraite | Engagements non provisionnés |
| Actions | Nombre dilué |

---

## Extensions Optionnelles

### Monte Carlo

Simulation stochastique des hypothèses :

| Paramètre | Description |
|-----------|-------------|
| Activé | Oui/Non |
| Simulations | 1000-10000 |
| Vol. flux | Volatilité du flux de base |
| Vol. Beta | Volatilité du Beta |
| Vol. g | Volatilité de la croissance |

### Scénarios

Analyse Bull/Base/Bear :

| Scénario | Probabilité | Croissance | Marge |
|----------|-------------|------------|-------|
| Bull | 25% | +2% | +5pp |
| Base | 50% | 0% | 0pp |
| Bear | 25% | -2% | -5pp |

### Peers Manuels

Liste de comparables pour triangulation :
```
AAPL, MSFT, GOOG, META
```

---

## Widgets Partagés (ST-3.4)

### Equity Bridge Unifié

Tous les terminaux utilisent le même widget :

```python
from app.ui.expert.terminals.shared_widgets import render_equity_bridge_inputs

def render_equity_bridge(self) -> None:
    render_equity_bridge_inputs(
        debt=self.financials.total_debt,
        cash=self.financials.cash,
        shares=self.financials.shares_outstanding,
        ...
    )
```

---

## Performance (ST-3.2)

### Fragments Streamlit

Les graphiques sont isolés avec `@st.fragment` :
- Pas de rechargement complet de l'UI
- Mise à jour ciblée des composants
- Navigation fluide entre onglets

---

## Responsabilité Utilisateur

**Attention** :
- Toute hypothèse irréaliste impacte directement le résultat
- L'audit reste actif et pénalisant si nécessaire
- Les diagnostics expliquent les risques (ST-4.2)

**Recommandations** :
- Vérifier les hypothèses avec les données du marché
- Comparer avec les guidances du management
- Consulter les consensus analystes
- Utiliser les scénarios pour tester la sensibilité

---

## Recommandé Pour

- Analystes expérimentés
- Cas spécifiques (restructurations, M&A)
- Scénarios avancés
- Valorisations approfondies
