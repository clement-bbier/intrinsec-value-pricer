# Residual Income Model (RIM) — Banques & Institutions financières

## 1. Objectif de la méthode

Le **Residual Income Model (RIM)** vise à estimer la valeur intrinsèque
des **institutions financières** (banques, assurances),
pour lesquelles les méthodes DCF classiques sont inadaptées.

Il est particulièrement adapté lorsque :
- le Free Cash Flow n’est pas significatif,
- le bilan est au cœur du modèle économique,
- la création de valeur se mesure via la **rentabilité des fonds propres**.

---

## 2. Pourquoi le DCF est inadapté aux banques

Dans une banque :

- la dette est une **matière première**, pas un financement externe,
- le Capex et le BFR n’ont pas le même sens que dans l’industrie,
- le FCFF est difficilement interprétable.

👉 Le RIM contourne ces limites en valorisant :
**la capacité à générer un rendement supérieur au coût des fonds propres**.

---

## 3. Principe économique

La valeur intrinsèque est égale à :

1. la **valeur comptable actuelle des fonds propres**,  
2. plus la somme actualisée des **résultats résiduels futurs**.

Un résultat résiduel correspond à la création (ou destruction) de valeur
au-delà du rendement exigé par les actionnaires.

---

## 4. Formulation mathématique

### 4.1 Valeur intrinsèque

\[
IV = BV_0 + \sum_{t=1}^{n} \frac{RI_t}{(1 + K_e)^t}
\]

où :

- \( BV_0 \) : valeur comptable initiale des fonds propres
- \( RI_t \) : résultat résiduel à l’année \( t \)
- \( K_e \) : coût des fonds propres

---

### 4.2 Résultat résiduel

\[
RI_t = Net\ Income_t - (K_e \times BV_{t-1})
\]

👉 Une banque crée de la valeur si :
\[
ROE > K_e
\]

---

## 5. Étapes de calcul — Glass Box

Chaque étape est tracée explicitement dans le moteur.

---

### Étape 1 — Valeur comptable initiale

- Fonds propres publiés
- Ajustements éventuels (éléments non récurrents)

📌 **Code**  
`core/valuation/strategies/rim_banks.py`

---

### Étape 2 — Projection du résultat net

- Hypothèses de croissance du résultat
- Cohérence avec le modèle économique et la régulation
- Possibilité de trajectoire conservatrice

---

### Étape 3 — Calcul du coût des fonds propres (Ke)

\[
K_e = R_f + \beta \times MRP
\]

- Beta spécifique au secteur bancaire
- Prime de risque ajustée au contexte macro-financier

📌 **Invariant**
- \( K_e > 0 \)

---

### Étape 4 — Calcul des résultats résiduels

Pour chaque période :

- calcul du rendement exigé sur les fonds propres,
- calcul de l’excédent (ou déficit) de résultat.

👉 Chaque \( RI_t \) peut être positif ou négatif.

---

### Étape 5 — Actualisation

Les résultats résiduels sont actualisés au coût des fonds propres \( K_e \).

---

### Étape 6 — Valeur terminale (si applicable)

Lorsque le modèle inclut une valeur terminale :

\[
TV = \frac{RI_n}{K_e - g}
\]

📌 **Invariant critique**
- \( K_e > g \)

---

## 6. Implémentation technique

- **Stratégie** : `RIMBanksStrategy`
- **Fichier** : `core/valuation/strategies/rim_banks.py`
- **Mode** : déterministe
- **Compatible Monte Carlo** : oui (extension sur hypothèses)

---

## 7. Sorties produites

- Valeur comptable initiale
- Résultats résiduels projetés
- Valeur intrinsèque des fonds propres
- Valeur intrinsèque par action
- Trace Glass Box complète
- Compatible Audit & Confidence Score

---

## 8. Limites et risques

### Limites
- Dépend fortement de la qualité des fonds propres comptables
- Sensible aux hypothèses de ROE long terme
- Fortement dépendant du cadre réglementaire

### Erreurs fréquentes
- Utiliser un ROE irréaliste
- Négliger l’impact de la régulation prudentielle
- Confondre croissance comptable et création de valeur

---

## 9. Quand utiliser cette méthode

✔️ Banque universelle  
✔️ Assurance  
✔️ Institution financière régulée  

❌ Entreprise industrielle  
❌ Société technologique  
❌ Start-up non rentable  

---

📎 **Méthode suivante recommandée**  
➡️ `Graham Intrinsic Value — Méthode heuristique`
