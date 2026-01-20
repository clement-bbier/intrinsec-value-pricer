# Interpréter les Résultats de Valorisation

**Version** : 2.0 — Janvier 2026

Ce document explique comment lire et interpréter correctement
les résultats produits par le moteur de valorisation.

---

## Valeur Intrinsèque

La valeur intrinsèque par action représente :
- une **estimation économique**,
- **conditionnelle** aux hypothèses retenues,
- issue d'un **modèle déterministe**.

**Ce n'est PAS** :
- une prévision de prix à court terme,
- une garantie de performance,
- une recommandation d'investissement.

---

## Upside / Downside

L'upside (ou downside) mesure l'écart relatif
entre la valeur intrinsèque et le prix de marché actuel.

$$
\text{Upside} = \frac{\text{Valeur intrinsèque} - \text{Prix marché}}{\text{Prix marché}}
$$

### Interprétation

| Upside | Signification | Recommandation |
|--------|---------------|----------------|
| > +30% | Fort potentiel | ACHAT FORT |
| +10% à +30% | Potentiel modéré | ACHAT |
| -10% à +10% | Valeur proche du prix | CONSERVER |
| -30% à -10% | Surévaluation modérée | VENTE |
| < -30% | Forte surévaluation | VENTE FORTE |

**Attention** : Un upside positif n'implique pas une opportunité automatique.
Toujours considérer :
- Le score d'audit
- La qualité des données
- Les risques identifiés

---

## Résultats Monte Carlo

Lorsque l'extension Monte Carlo est activée, l'utilisateur voit :
- une **distribution de valeurs**,
- des **quantiles** (P10, P50, P90),
- une mesure de **dispersion**.

### Lecture Correcte

| Quantile | Signification |
|----------|---------------|
| **P10** | Scénario défavorable (10% des cas) |
| **P50** | Estimation centrale (médiane) |
| **P90** | Scénario favorable (10% des cas) |
| **Std** | Écart-type (dispersion) |

### Signaux d'Alerte

| Signal | Interprétation |
|--------|----------------|
| P10/P90 très écartés | Forte incertitude |
| P50 ≠ valeur déterministe | Asymétrie dans les hypothèses |
| < 80% simulations valides | Instabilité du modèle |

---

## Confidence Score

Le Confidence Score synthétise :
- la **qualité des données**,
- la **robustesse des hypothèses**,
- la **stabilité des résultats**.

### Grades

| Score | Grade | Signification |
|-------|-------|---------------|
| 90-100 | A | Excellent, haute confiance |
| 80-89 | B | Bon, confiance modérée |
| 70-79 | C | Acceptable, vigilance requise |
| 60-69 | D | Risqué, hypothèses fragiles |
| 0-59 | F | Critique, résultat peu fiable |

### Score élevé signifie

- Cohérence globale des hypothèses
- Faible sensibilité aux paramètres extrêmes
- Données de qualité

### Score faible indique

- Incertitude structurelle
- Hypothèses fragiles
- Données limitées ou aberrantes

---

## Glass Box V2 (Preuve de Calcul)

Chaque étape de calcul est transparente :

### Badges de Confiance

| Badge | Couleur | Signification |
|-------|---------|---------------|
| Certifié | Vert | Données Yahoo Finance |
| Estimé | Orange | Données calculées |
| Manuel | Bleu | Surcharge expert |
| Fallback | Rouge | Données de secours |

### Expander "Détails"

Cliquez sur chaque étape pour voir :
- Les variables utilisées
- Leur source
- La formule appliquée

---

## Mode Dégradé

Si un bandeau orange s'affiche :

```
┌─────────────────────────────────────────────────────┐
│ Mode dégradé                      Confiance: 70%  │
│ Raison : API peers indisponible                    │
│ Sources : Damodaran 2024 - Sector average          │
└─────────────────────────────────────────────────────┘
```

**Signification** :
- Les données de marché sont indisponibles
- Des moyennes sectorielles sont utilisées
- Le score de confiance est réduit
- Le résultat reste indicatif

---

## Triangulation Sectorielle

L'onglet "Multiples" montre le **Football Field** :

| Méthode | Description |
|---------|-------------|
| DCF | Valeur intrinsèque calculée |
| P/E | Prix × P/E sectoriel médian |
| EV/EBITDA | (EV/EBITDA × EBITDA - Dette + Cash) / Actions |
| EV/Revenue | Idem avec Revenue |
| Prix actuel | Ligne de référence |

### Interprétation

- Toutes les méthodes convergent → Haute confiance
- Divergence importante → Investiguer les raisons
- DCF isolé → Vérifier les hypothèses de croissance

---

## Erreurs Fréquentes

| Erreur | Impact | Comment éviter |
|--------|--------|----------------|
| Confondre IV et objectif de prix | Déception si le prix ne bouge pas | L'IV est structurelle, pas prédictive |
| Ignorer les hypothèses | Résultat hors contexte | Toujours consulter l'onglet Hypothèses |
| Comparer méthodes différentes | Pommes et oranges | Utiliser la même méthode pour comparer |
| Sur-interpréter les quantiles | Faux sentiment de précision | Les bornes sont indicatives |
| Ignorer le score d'audit | Fausse confiance | Un score < 70 = vigilance requise |

---

## Bonne Pratique

Toujours interpréter les résultats conjointement avec :

1. **La méthode utilisée**
   - Est-elle adaptée au profil de l'entreprise ?

2. **Les hypothèses clés**
   - Sont-elles réalistes ?

3. **L'audit et le Confidence Score**
   - Quels risques sont identifiés ?

4. **La triangulation**
   - Les méthodes convergent-elles ?

5. **Le contexte marché**
   - Y a-t-il des facteurs externes ?

---

## Exporter le Pitchbook

Pour partager l'analyse, exportez le Pitchbook PDF :

1. Cliquez sur "Exporter PDF"
2. Le rapport de 3 pages inclut :
   - Résumé exécutif
   - Preuves de calcul
   - Analyse de risque
3. Format professionnel institutionnel
