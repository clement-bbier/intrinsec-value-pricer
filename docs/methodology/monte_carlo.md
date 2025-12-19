# Extension Monte Carlo — Analyse d’incertitude

## 1. Statut normatif

L’analyse **Monte Carlo** n’est **PAS** une méthode de valorisation.

👉 Elle constitue une **extension probabiliste** appliquée
**exclusivement aux hypothèses d’entrée** des modèles déterministes
(DCF, RIM, etc.).

Les modèles de valorisation restent :
- déterministes,
- inchangés,
- exécutés intégralement à chaque simulation.

---

## 2. Objectif de l’extension Monte Carlo

L’objectif de Monte Carlo est de :

- **quantifier l’incertitude** autour d’une valeur intrinsèque,
- produire une **distribution de valeurs possibles**,
- mesurer la **sensibilité du résultat** aux hypothèses clés.

👉 Monte Carlo **ne cherche jamais à prédire un prix futur**.

---

## 3. Principe fondamental

Le principe est strictement le suivant :

1. On définit des **distributions probabilistes** sur certaines hypothèses.
2. Chaque tirage génère un **jeu d’inputs distinct**.
3. Le modèle déterministe est **ré-exécuté intégralement**.
4. La valeur intrinsèque résultante est stockée.
5. Le processus est répété \( N \) fois.

\[
Simulation_i = Modèle_{déterministe}(Inputs_i)
\]

---

## 4. Variables stochastiques autorisées

Seules les **hypothèses exogènes** peuvent être rendues stochastiques.

### Variables typiques
- taux de croissance,
- beta,
- composantes du WACC,
- marges (selon méthode),
- multiples (le cas échéant).

### Variables interdites
- données comptables historiques,
- logique de calcul,
- formules financières,
- structure du modèle.

👉 **Aucune simulation ne modifie la logique du modèle.**

---

## 5. Distributions utilisées

Les distributions sont paramétrées par l’utilisateur ou par défaut :

- loi normale (cas standard),
- bornes économiques explicites,
- corrélations possibles entre variables.

📌 **Exemple**
- croissance et beta peuvent être corrélés négativement,
- afin de refléter une relation risque ↔ rendement.

📌 **Code**
- Génération statistique : `core/computation/statistics.py`
- Orchestration : `core/valuation/strategies/monte_carlo.py`

---

## 6. Étapes de calcul — Glass Box

Chaque simulation suit **exactement** les mêmes étapes :

1. Tirage des hypothèses
2. Construction du jeu d’inputs
3. Exécution du modèle déterministe
4. Calcul de la valeur intrinsèque
5. Stockage du résultat

👉 **La traçabilité est totale** :  
le modèle exécuté est le même que sans Monte Carlo.

---

## 7. Sorties produites

L’analyse Monte Carlo génère :

- une **distribution de valeurs intrinsèques**,
- des **quantiles** (P10, P50, P90),
- des **statistiques de dispersion** (variance, écart-type),
- une visualisation graphique dans l’interface.

📌 **Lecture correcte**
- P50 ≈ estimation centrale
- P10 / P90 ≈ bornes de scénarios défavorables / favorables

---

## 8. Lien avec le Confidence Score

Monte Carlo alimente indirectement le **Confidence Score** :

- forte dispersion → incertitude élevée,
- sensibilité extrême → pénalisation du score,
- stabilité du résultat → score renforcé.

👉 Monte Carlo **ne modifie jamais la valeur centrale**,
mais influence l’évaluation de la **robustesse**.

---

## 9. Limites et mauvaises interprétations

### Limites
- dépendance forte au choix des distributions,
- résultats sensibles aux bornes imposées,
- illusion de précision si mal paramétré.

### Erreurs fréquentes
- interpréter la distribution comme une prévision de prix,
- oublier que le modèle sous-jacent reste hypothétique,
- sur-interpréter des quantiles extrêmes.

---

## 10. Quand utiliser Monte Carlo

✔️ Hypothèses incertaines  
✔️ Décision nécessitant une mesure de risque  
✔️ Analyse comparative de robustesse  

❌ Données extrêmement spéculatives  
❌ Absence totale de modèle économique  
❌ Usage prédictif court terme  

---

## 11. Implémentation technique

- **Stratégie** : `MonteCarloStrategy`
- **Fichier** : `core/valuation/strategies/monte_carlo.py`
- **Couche statistique** : `core/computation/statistics.py`
- **Mode** : extension probabiliste

---

📎 **Lecture complémentaire recommandée**
- Audit & Confidence Score
- Limites des méthodes de valorisation
