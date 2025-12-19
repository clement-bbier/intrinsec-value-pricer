# DCF Fondamental — FCFF Normalisé

## 1. Objectif de la méthode

La méthode **DCF Fondamental (FCFF Normalisé)** vise à estimer la valeur
intrinsèque d’une entreprise à partir d’un **flux de trésorerie économique
représentatif d’un cycle moyen**, et non d’une photographie conjoncturelle.

Elle est particulièrement adaptée aux :

- entreprises **cycliques**,
- sociétés industrielles,
- groupes ayant connu des **événements exceptionnels récents**,
- contextes où le dernier FCF observé n’est pas représentatif.

---

## 2. Différence clé avec le DCF Standard

| DCF Standard | DCF Fondamental |
|------------|----------------|
| FCFF observé | FCFF reconstruit |
| Photographie | Vision économique normalisée |
| Peu de retraitements | Retraitements explicites |
| Simplicité | Robustesse économique |

👉 Le DCF Fondamental privilégie la **qualité économique du flux**
à la simplicité du calcul.

---

## 3. Principe économique

Le flux de trésorerie utilisé n’est **pas directement observé**,
mais **reconstruit analytiquement** à partir du compte de résultat
et du bilan.

L’objectif est d’obtenir un **FCFF normatif**, reflétant la capacité
structurelle de l’entreprise à générer de la trésorerie.

---

## 4. Reconstruction du FCFF normatif

### 4.1 Formule générale

\[
FCFF = EBIT \times (1 - t)
+ Dotations\ aux\ amortissements
- Capex_{normatif}
- \Delta BFR_{normatif}
\]

où :

- \( EBIT \) : résultat opérationnel retraité
- \( t \) : taux d’imposition normatif
- \( Capex_{normatif} \) : investissement de maintien
- \( \Delta BFR_{normatif} \) : variation de besoin en fonds de roulement normalisée

---

### 4.2 Étape 1 — Normalisation de l’EBIT

- Retraitement des éléments non récurrents
- Neutralisation des effets exceptionnels
- Lissage éventuel sur plusieurs exercices

📌 **Jugement clé**  
Cette étape repose sur une **analyse qualitative** des comptes.

📌 **Code**  
`core/valuation/strategies/dcf_fundamental.py`

---

### 4.3 Étape 2 — Capex normatif

- Distinction entre :
  - Capex de maintien
  - Capex de croissance
- Seul le **Capex de maintien** est retenu dans le FCFF normatif

📌 **Principe**  
L’entreprise doit maintenir son outil productif avant de croître.

---

### 4.4 Étape 3 — BFR normatif

- Neutralisation des variations exceptionnelles
- Hypothèse de stabilité du BFR à long terme
- Possibilité d’indexation sur le chiffre d’affaires

---

## 5. Projection des flux

Une fois le FCFF normatif déterminé :

- il est projeté sur un horizon explicite,
- selon un taux de croissance cohérent avec le potentiel économique réel.

\[
FCFF_t = FCFF_{normatif} \times (1 + g)^t
\]

👉 La croissance est **structurelle**, pas conjoncturelle.

---

## 6. Actualisation et valeur terminale

Les flux sont actualisés au **WACC**, comme dans un DCF standard.

La valeur terminale repose sur une hypothèse de régime permanent :

\[
TV = \frac{FCFF_n \times (1 + g)}{WACC - g}
\]

📌 **Invariant critique**
- \( WACC > g \)

---

## 7. Étapes de calcul — Glass Box

Chaque composante fait l’objet d’une `CalculationStep` dédiée :

1. EBIT retraité
2. Calcul du FCFF normatif
3. Projection des flux
4. Calcul du WACC
5. Valeur terminale
6. Actualisation
7. Passage à la valeur par action

👉 **Toutes ces étapes sont visibles dans l’interface utilisateur.**

---

## 8. Implémentation technique

- **Stratégie** : `DCFFundamentalStrategy`
- **Fichier** : `core/valuation/strategies/dcf_fundamental.py`
- **Mode** : déterministe
- **Compatible Monte Carlo** : oui (extension)

---

## 9. Sorties produites

- FCFF normatif explicite
- Valeur d’entreprise
- Valeur des fonds propres
- Valeur intrinsèque par action
- Trace Glass Box complète
- Compatible Audit & Confidence Score

---

## 10. Limites et risques

### Limites
- Forte dépendance au jugement analytique
- Sensibilité aux hypothèses de normalisation
- Plus complexe à expliquer à un public non financier

### Risques d’erreur
- Sur-normalisation excessive
- Hypothèses trop optimistes
- Confusion entre Capex de croissance et de maintien

---

## 11. Quand utiliser cette méthode

✔️ Entreprise cyclique  
✔️ Résultats perturbés récemment  
✔️ Analyse fondamentale approfondie  

❌ Start-up sans historique  
❌ Entreprise financière (banques)  
❌ Cas où le FCFF observé est déjà représentatif  

---

📎 **Méthode suivante recommandée**  
➡️ `DCF Croissance — Revenue-Driven`
