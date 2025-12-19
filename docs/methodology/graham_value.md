# Graham Intrinsic Value — Formule révisée (1974)

## 1. Statut de la méthode

La **méthode de Graham** est une **heuristique historique** proposée par
Benjamin Graham pour estimer une valeur intrinsèque à partir du bénéfice
et de la croissance attendue.

⚠️ **Ce n’est pas un modèle financier complet**  
⚠️ **Ce n’est pas un DCF**  
⚠️ **Elle ne remplace jamais une analyse fondamentale approfondie**

Dans ce projet, elle est utilisée **exclusivement comme outil comparatif
et pédagogique**.

---

## 2. Objectif de la méthode

La formule de Graham vise à :

- fournir un **ordre de grandeur** de valorisation,
- comparer rapidement des entreprises entre elles,
- illustrer l’impact du bénéfice et de la croissance sur la valeur.

Elle est adaptée à :
- une analyse préliminaire,
- une comparaison relative,
- un usage éducatif.

---

## 3. Principe économique

La logique sous-jacente est la suivante :

- la valeur d’une entreprise dépend de son **bénéfice par action (EPS)**,
- la croissance future justifie une **prime de valorisation**,
- le niveau des taux d’intérêt influence les multiples acceptables.

👉 La formule intègre implicitement une logique de **multiple ajusté du bénéfice**.

---

## 4. Formulation mathématique

### 4.1 Formule révisée (1974)

\[
IV = EPS \times (8.5 + 2g) \times \frac{4.4}{Y_{AAA}}
\]

où :

- \( EPS \) : bénéfice par action
- \( g \) : taux de croissance attendu du bénéfice
- \( Y_{AAA} \) : rendement des obligations AAA
- 8.5 : multiple de base pour une entreprise sans croissance
- 4.4 : rendement obligataire de référence à l’époque de Graham

---

## 5. Étapes de calcul — Glass Box

Dans le moteur, la méthode est décomposée explicitement :

---

### Étape 1 — Sélection de l’EPS

- EPS courant ou normalisé
- Données issues des états financiers publiés
- Aucun retraitement complexe

📌 **Code**  
`core/valuation/strategies/graham_value.py`

---

### Étape 2 — Hypothèse de croissance

- Croissance fournie par l’utilisateur ou estimée automatiquement
- Hypothèse **fortement structurante**
- Aucune modélisation multi-phases

---

### Étape 3 — Ajustement par les taux

- Utilisation d’un rendement obligataire AAA courant
- Mise à l’échelle de la valorisation selon le niveau des taux

---

### Étape 4 — Calcul de la valeur intrinsèque

La valeur intrinsèque est obtenue **directement par application de la formule**,
sans actualisation explicite des flux.

👉 Chaque étape est affichée dans le Glass Box.

---

## 6. Implémentation technique

- **Stratégie** : `GrahamValueStrategy`
- **Fichier** : `core/valuation/strategies/graham_value.py`
- **Mode** : heuristique déterministe
- **Compatible Monte Carlo** : non (hors périmètre)

---

## 7. Sorties produites

- Valeur intrinsèque par action (heuristique)
- Comparaison avec le prix de marché
- Trace Glass Box du calcul
- Compatible Audit & Confidence Score (pondération prudente)

---

## 8. Limites et risques majeurs

### Limites structurelles
- Hypothèse de croissance simpliste
- Aucune prise en compte explicite du risque
- Sensibilité élevée aux taux obligataires

### Risques d’interprétation
- Confondre heuristique et modèle fondamental
- Utiliser la valeur comme cible de prix
- Comparer directement avec un DCF sans précaution

---

## 9. Quand utiliser cette méthode

✔️ Analyse comparative rapide  
✔️ Outil pédagogique  
✔️ Screening initial  

❌ Décision d’investissement isolée  
❌ Entreprise complexe ou cyclique  
❌ Valorisation institutionnelle  

---

📎 **Méthode suivante recommandée**  
➡️ `Extension Monte Carlo — Analyse d’incertitude`
