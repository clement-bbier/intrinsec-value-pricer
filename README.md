# Intrinsic Value Pricer

**Glass-Box Valuation Engine — Production-Ready**

**Version** : 3.0 — Janvier 2026  
**Architecture** : V2.0  
**Sprints** : 1-5 Complétés

> Éducation • Analyse financière • Modélisation avancée • Transparence totale

---

## Objectif du Projet

**Intrinsic Value Pricer** est une application open-source de valorisation d'entreprises cotées, conçue pour être :

- **Rigoureuse** sur le plan financier,
- **Transparente** sur le plan méthodologique ("Glass Box V2"),
- **Pédagogique** dans son exposition (diagnostics ST-4.2),
- **Auditable** dans ses résultats (Pitchbook PDF ST-5.2),
- **Résiliente** face aux pannes (Mode Dégradé ST-4.1).

Le projet vise à **expliquer comment une valeur intrinsèque est construite**, et non à fournir un chiffre opaque ou une promesse de surperformance.

> **Disclaimer**  
> Ce projet est strictement **éducatif et analytique**.  
> Il ne constitue **en aucun cas** une recommandation d'investissement.

---

## Fonctionnalités Clés

| Fonctionnalité | Description |
|----------------|-------------|
| **9 Méthodes de Valorisation** | DCF, RIM, Graham, Multiples, DDM |
| **Glass Box V2** | Traçabilité complète avec source de chaque variable |
| **Monte Carlo** | Distribution probabiliste de la valeur |
| **Scénarios Bull/Base/Bear** | Analyse de sensibilité |
| **Backtest Historique** | Validation sur 3 années passées |
| **Mode Dégradé** | Fallback automatique (ST-4.1) |
| **Diagnostic Pédagogique** | Erreurs traduites en conseils (ST-4.2) |
| **Pitchbook PDF** | Export professionnel 3 pages (ST-5.2) |
| **Internationalisation** | Classes Python centralisées (FR) |

---

## Architecture

```
intrinsec-value-pricer/
├── src/                       # Logique métier pure (Zéro Streamlit)
│   ├── domain/models/         # 9 modèles Pydantic
│   ├── valuation/             # Moteur + 9 stratégies
│   ├── computation/           # Fonctions mathématiques
│   ├── config/                # Constantes centralisées
│   ├── i18n/                  # Classes i18n centralisées (FR)
│   ├── reporting/             # Pitchbook PDF (FPDF2)
│   ├── diagnostics.py         # DiagnosticEvent + FinancialContext
│   └── quant_logger.py        # Logging institutionnel
│
├── app/                       # Couche présentation (Streamlit)
│   ├── ui/expert/terminals/   # 7 terminaux + Factory
│   ├── ui/results/            # Orchestrator + Onglets
│   └── adapters/              # Injection de dépendances
│
├── infra/                     # Infrastructure
│   ├── data_providers/        # Yahoo Finance + Fallback
│   ├── auditing/              # AuditEngine + Backtester
│   └── ref_data/              # Multiples sectoriels
│
├── config/                    # Configuration YAML
├── docs/                      # Documentation complète
└── tests/                     # 51+ tests de contrats
```

### Étanchéité Architecturale

- `src/` n'importe **jamais** de `app/` ni de `streamlit`
- `infra/` peut importer de `src/` mais pas de `app/`
- Validation : `pytest tests/contracts/ -v`

---

## Méthodes de Valorisation

### DCF (Discounted Cash Flow)

| Méthode | Cible | Fichier |
|---------|-------|---------|
| **FCFF Standard** | Entreprises matures | `dcf_standard.py` |
| **FCFF Normalisé** | Cycliques / industrielles | `dcf_fundamental.py` |
| **FCFF Growth** | Tech / forte croissance | `dcf_growth.py` |
| **FCFE** | Sociétés endettées stables | `dcf_equity.py` |
| **DDM** | Dividendes réguliers | `dcf_dividend.py` |

### Autres Méthodes

| Méthode | Cible | Fichier |
|---------|-------|---------|
| **Graham 1974** | Screening rapide | `graham_value.py` |
| **RIM Banks** | Banques / assurances | `rim_banks.py` |
| **Multiples** | Triangulation relative | `multiples.py` |

### Extensions

| Extension | Rôle | Fichier |
|-----------|------|---------|
| **Monte Carlo** | Quantification de l'incertitude | `monte_carlo.py` |

Documentation détaillée : `docs/methodology/`

---

## Modes d'Utilisation

### Mode AUTO

- Hypothèses normatives (système)
- Données automatiques (Yahoo Finance)
- Garde-fous économiques stricts
- Mode dégradé automatique si panne API

**Idéal pour** : Débutants, screening, apprentissage

### Mode EXPERT

- 7 terminaux spécialisés
- Contrôle total des hypothèses
- Workflow séquencé "Logical Path"
- Responsabilité utilisateur

**Idéal pour** : Analystes, valorisations approfondies

Documentation : `docs/usage/`

---

## Installation & Lancement

### Prérequis

- Python 3.10+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Lancement

```bash
streamlit run app/main.py
```

### Tests

```bash
# Tests de contrats (51+)
pytest tests/contracts/ -v

# Tous les tests
pytest tests/ -v
```

---

## Nouvelles Fonctionnalités (Sprints 4-5)

### Mode Dégradé (ST-4.1)

Si Yahoo Finance échoue :
- Fallback automatique sur multiples sectoriels (Damodaran)
- Bandeau d'avertissement affiché
- Score de confiance réduit (70%)

### Diagnostic Pédagogique (ST-4.2)

Les erreurs techniques sont traduites en conseils métier :

```
❌ Avant : "Math Error: Division by zero"

✅ Après : "La croissance perpétuelle (5.00%) dépasse le WACC (4.50%).
           Le modèle de Gordon ne peut pas converger.
           Recommandation : Réduire g en dessous de 3%."
```

### QuantLogger (ST-4.2)

Format de log institutionnel :

```
[VALUATION][SUCCESS] Ticker: AAPL | Model: FCFF_STANDARD | IV: 185.20 | AuditScore: 88.5%
```

### Pitchbook PDF (ST-5.2)

Export professionnel de 3 pages :
1. Résumé exécutif (IV, prix, upside, audit)
2. Preuves de calcul (formules, paramètres)
3. Analyse de risque (Monte Carlo, scénarios)

---

## Audit & Confidence Score

Chaque valorisation génère un **AuditReport** structuré :

| Pilier | Description |
|--------|-------------|
| **Profitabilité** | ROE, marges |
| **Solvabilité** | ICR, D/E |
| **Valorisation** | g < WACC, Beta |
| **Marché** | Données disponibles |

### Grades

| Score | Grade | Signification |
|-------|-------|---------------|
| 90-100 | A | Excellent |
| 80-89 | B | Bon |
| 70-79 | C | Acceptable |
| 60-69 | D | Risqué |
| 0-59 | F | Critique |

---

## Documentation

| Section | Contenu |
|---------|---------|
| `docs/methodology/` | Théorie financière, formules |
| `docs/technical/` | Architecture, patterns |
| `docs/usage/` | Guide utilisateur |
| `docs/references/` | Sources externes |

---

## Philosophie du Projet

> **Le moteur ne décide jamais.**  
> Il rend explicites les hypothèses,  
> calcule leurs conséquences économiques,  
> et laisse le jugement final à l'humain.

La valeur intrinsèque est un **outil d'analyse**,
pas une vérité absolue ni une prédiction de marché.

---

## Roadmap

### Complétés

- [x] Sprint 1 : Souveraineté Technique
- [x] Sprint 2 : Glass Box V2
- [x] Sprint 3 : UX Pitchbook
- [x] Sprint 4 : Résilience & Intelligence
- [x] Sprint 5 : Internationalisation & PDF
- [x] Sprint 6 : Zero Debt & Hardening

### Futurs

- [ ] Sprint 7 : Multi-Langue (EN)
- [ ] Sprint 8 : Analytics & Monitoring

---

## Disclaimer Final

Ce projet est fourni **à des fins éducatives, analytiques et de recherche**.  
Il ne constitue **en aucun cas** un conseil financier,
une incitation à investir,
ou une recommandation d'achat ou de vente de titres financiers.
