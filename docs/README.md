# Documentation — Intrinsic Value Pricer

**Version** : 3.0 — Janvier 2026  
**Architecture** : V2.0 Production-Ready  
**Sprints** : 1-5 Complétés

Cette documentation constitue la **référence financière, technique et utilisateur**
du projet *Intrinsic Value Pricer*.

Elle est conçue pour permettre :
- la **compréhension** des méthodes de valorisation,
- la **vérification** des calculs et hypothèses,
- l'**apprentissage** des logiques financières sous-jacentes,
- la **génération** de Pitchbooks PDF professionnels.

La documentation est strictement alignée avec :
- le moteur de calcul (`src/valuation/`),
- l'interface utilisateur (`app/ui/`),
- les principes de transparence **Glass Box V2**,
- le système de **diagnostic pédagogique** (ST-4.2).

---

## Architecture du Projet

```
intrinsec-value-pricer/
├── src/                       # Logique métier pure (Zéro Streamlit)
│   ├── domain/models/         # Modèles Pydantic (9 fichiers)
│   ├── valuation/             # Moteur + 9 Stratégies
│   ├── computation/           # Fonctions mathématiques
│   ├── config/                # Constantes centralisées
│   ├── i18n/                  # TextRegistry + Classes FR
│   ├── reporting/             # Génération PDF Pitchbook
│   ├── diagnostics.py         # DiagnosticEvent + FinancialContext
│   └── quant_logger.py        # Logging institutionnel
│
├── app/                       # Couche présentation (Streamlit)
│   ├── ui/base/               # ExpertTerminal (Template Method)
│   ├── ui/expert/terminals/   # 7 terminaux + Factory
│   ├── ui/results/            # Orchestrator + Onglets
│   └── adapters/              # Injection de dépendances
│
├── infra/                     # Infrastructure externe
│   ├── data_providers/        # Yahoo Finance + Fallback ST-4.1
│   ├── auditing/              # AuditEngine + Backtester
│   └── ref_data/              # Multiples sectoriels
│
├── locales/                   # Fichiers i18n YAML (ST-5.1)
├── config/                    # Configuration YAML
└── tests/                     # 51+ Tests de contrats
```

---

## Comment naviguer dans la documentation

La documentation est organisée en couches distinctes :

### Méthodologie (`docs/methodology/`)
- Théorie financière (DCF, RIM, Graham)
- 7 méthodes de valorisation documentées
- Formules LaTeX et limites d'usage
- Extension Monte Carlo

### Technique (`docs/technical/`)
- Architecture en couches étanches
- Design Patterns (Factory, Template, Mediator)
- Glass Box V2 avec traçabilité des sources
- Mode Dégradé et résilience (ST-4.1)

### Usage (`docs/usage/`)
- Mode AUTO (hypothèses normatives)
- Mode EXPERT (contrôle total, 7 terminaux)
- Interprétation des résultats et Pitchbook PDF

### Références (`docs/references/`)
- Yahoo Finance (données et limites)
- Damodaran (multiples sectoriels)
- Hypothèses macro-financières

---

## Fonctionnalités Clés (Post-Sprint 5)

| Fonctionnalité | Description |
|----------------|-------------|
| **Glass Box V2** | Traçabilité complète avec `VariableInfo` et badge de confiance |
| **Mode Dégradé** | Fallback automatique sur multiples sectoriels (ST-4.1) |
| **Diagnostic Pédagogique** | Erreurs traduites en conseils métier (ST-4.2) |
| **QuantLogger** | Logging institutionnel structuré |
| **TextRegistry YAML** | Internationalisation via fichiers YAML (ST-5.1) |
| **Pitchbook PDF** | Export professionnel 3 pages (ST-5.2) |

---

## Principes Clés

1. **Étanchéité Architecturale**  
   `src/` ne dépend jamais de `app/` ni de Streamlit.

2. **Typage Strict**  
   `from __future__ import annotations` dans tous les fichiers.

3. **Glass Box**  
   Toute valeur affichée est traçable jusqu'à sa source.

4. **Résilience**  
   Aucune panne API ne bloque la valorisation (fallback sectoriel).

---

## Points d'entrée recommandés

| Profil | Document |
|--------|----------|
| Nouvel utilisateur | `usage/README.md` |
| Analyste financier | `methodology/README.md` |
| Développeur | `technical/README.md` |
| Contributeur | `../CONTRIBUTING.md` |
