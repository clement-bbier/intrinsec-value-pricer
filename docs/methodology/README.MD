# Méthodologies de Valorisation

**Version** : 2.0 — Janvier 2026

Ce dossier regroupe la **documentation méthodologique financière**
du projet *Intrinsic Value Pricer*.

Il constitue la référence pédagogique pour comprendre :
- les **méthodes de valorisation** implémentées,
- leurs **hypothèses économiques**,
- leurs **formules financières**,
- leurs **limites d'usage**.

Cette documentation est conçue pour être :
- exploitable par un **analyste junior** (apprentissage),
- auditable par un **analyste senior** (revue modèle),
- strictement alignée avec le **code source**.

---

## Philosophie Générale

Le moteur de valorisation repose sur trois principes non négociables :

### 1. Glass Box V2

Chaque méthode expose explicitement :
- ses hypothèses,
- ses formules (LaTeX),
- chaque étape de calcul,
- chaque résultat intermédiaire,
- **la source de chaque variable** (ST-3.3).

### 2. Déterminisme des Modèles

Les méthodes de valorisation sont **strictement déterministes**.
Toute incertitude est traitée via des **extensions séparées** (Monte Carlo).

### 3. Traçabilité Complète

Toute information affichée dans l'interface :
- provient du moteur,
- est traçable jusqu'au code,
- affiche un **badge de confiance** (Certifié/Estimé/Manuel).

---

## Comment Lire une Méthode de Valorisation

Chaque méthode documentée dans ce dossier suit **la même structure**.

### 1. Objectif de la Méthode
- Quel problème économique la méthode cherche à résoudre
- Pour quel type d'entreprise elle est adaptée

### 2. Principe Économique
- Logique financière sous-jacente
- Hypothèses structurantes

### 3. Formules Financières
- Écriture mathématique canonique (LaTeX)
- Correspondance exacte avec le code

### 4. Étapes de Calcul (Glass Box)

Chaque étape correspond directement à une
`CalculationStep` générée par le moteur :

- sélection des données de base,
- calcul des taux (WACC, Ke),
- projections,
- valeur terminale,
- passage à la valeur par action.

**Ces étapes sont visibles intégralement dans l'interface utilisateur.**

### 5. Implémentation Technique

Chaque page indique explicitement :
- le fichier Python concerné,
- la classe de stratégie utilisée.

### 6. Limites et Cas d'Usage
- Quand la méthode est pertinente
- Quand elle ne doit pas être utilisée
- Principales sources d'erreur d'interprétation

---

## Lien entre Documentation, Code et Interface

| Élément | Localisation | Rôle |
|---------|--------------|------|
| Stratégies | `src/valuation/strategies/*.py` | Implémentation du calcul |
| Formules | `CalculationStep.theoretical_formula` | LaTeX dans l'UI |
| Variables | `CalculationStep.variables_map` | Traçabilité des sources |
| Interface | `app/ui/results/` | Restitution interactive |

**Il n'existe aucune méthode documentée qui ne soit implémentée dans le code.**
**Il n'existe aucune logique implémentée qui ne soit documentée.**

---

## Méthodes Disponibles

### Méthodes DCF (Discounted Cash Flow)

| Méthode | Fichier | Cible |
|---------|---------|-------|
| **DCF Standard — FCFF Two-Stage** | `dcf_standard.py` | Entreprises matures |
| **DCF Fondamental — FCFF Normalisé** | `dcf_fundamental.py` | Cycliques / industrielles |
| **DCF Croissance — Revenue-Driven** | `dcf_growth.py` | Tech / forte croissance |
| **FCFE — Flux vers Actionnaires** | `dcf_equity.py` | Sociétés endettées stables |
| **DDM — Dividend Discount** | `dcf_dividend.py` | Dividendes réguliers |

### Méthodes Non DCF

| Méthode | Fichier | Cible |
|---------|---------|-------|
| **Graham Intrinsic Value (1974)** | `graham_value.py` | Screening rapide |
| **Residual Income Model (RIM)** | `rim_banks.py` | Banques / assurances |
| **Multiples Sectoriels** | `multiples.py` | Triangulation relative |

### Extensions (Incertitude)

| Extension | Fichier | Rôle |
|-----------|---------|------|
| **Monte Carlo** | `monte_carlo.py` | Quantification de l'incertitude |

---

## Hiérarchie Analytique (ST-3.1)

Les méthodes sont ordonnées par niveau de complexité :

```
┌─────────────────────────────────────────────────┐
│ TIER 1 : DEFENSIVE                              │
│ Graham Value — Approche heuristique             │
├─────────────────────────────────────────────────┤
│ TIER 2 : RELATIVE                               │
│ RIM, DDM, Multiples — Valorisation comparative  │
├─────────────────────────────────────────────────┤
│ TIER 3 : FUNDAMENTAL                            │
│ DCF variants — Valorisation fondamentale        │
└─────────────────────────────────────────────────┘
```

---

## Point Clé sur l'Incertitude

L'analyse Monte Carlo :
- **n'est pas** une méthode de valorisation,
- **ne modifie jamais** la logique des modèles,
- **quantifie uniquement l'incertitude** autour des hypothèses.

Les valeurs centrales restent issues des **modèles déterministes**.

---

## Audit et Gouvernance

Toutes les méthodes sont compatibles avec :
- l'**Audit Engine** (score de confiance),
- le **diagnostic pédagogique** (ST-4.2),
- les exigences de **Model Validation**.

La documentation méthodologique doit toujours être lue conjointement
avec la section **Rapport d'Audit** de l'interface.

---

## Règles de Maintenance

- Toute nouvelle méthode implique :
  - une nouvelle stratégie dans `src/valuation/strategies/`,
  - une page dédiée dans ce dossier,
  - une entrée dans le Registry.

- Toute modification de formule implique :
  - mise à jour du code,
  - mise à jour de la documentation,
  - cohérence vérifiable via la trace Glass Box.

---

## Prochaine Lecture Recommandée

1. Commencer par la méthode correspondant au profil de l'entreprise analysée
2. Puis consulter la page dédiée à Monte Carlo pour l'incertitude
3. Enfin, lire `docs/technical/audit_engine.md` pour le scoring
