# DCF Croissance — Revenue-Driven FCFF

## 1. Objectif de la méthode

La méthode **DCF Croissance (Revenue-Driven)** vise à valoriser des entreprises
en **forte croissance**, pour lesquelles :

- le Free Cash Flow actuel est faible, nul ou négatif,
- la dynamique économique est d’abord portée par le chiffre d’affaires,
- les marges sont appelées à converger progressivement vers un niveau soutenable.

Elle est particulièrement adaptée aux :

- entreprises technologiques,
- sociétés en phase de scale-up,
- modèles SaaS, plateformes, biotechs (hors banques).

---

## 2. Pourquoi un DCF spécifique à la croissance ?

Dans un DCF classique :
- le FCFF est le point de départ.

Dans un DCF croissance :
- le **chiffre d’affaires** est la variable structurante,
- les marges, le Capex et le BFR sont **endogènes** à la croissance.

👉 Cette méthode vise à **reconstruire un FCFF futur crédible**, et non
à extrapoler un flux actuel non représentatif.

---

## 3. Principe économique

La logique repose sur trois piliers :

1. **Croissance du chiffre d’affaires**  
   Forte au départ, puis décroissante.

2. **Convergence des marges**  
   Marges faibles ou négatives au début, convergeant vers un niveau cible.

3. **Transition vers un régime mature**  
   À l’horizon terminal, l’entreprise se comporte comme une entreprise mature.

---

## 4. Formulation générale

### 4.1 Projection du chiffre d’affaires

\[
Revenue_t = Revenue_{t-1} \times (1 + g_t)
\]

avec \( g_t \) décroissant dans le temps.

---

### 4.2 Construction du FCFF

\[
FCFF_t =
Revenue_t \times Margin_t
- Capex_t
- \Delta BFR_t
\]

où :

- \( Margin_t \) : marge opérationnelle à l’année \( t \)
- \( Capex_t \) : investissements nécessaires à la croissance
- \( \Delta BFR_t \) : besoin en fonds de roulement lié à l’expansion

---

## 5. Étapes de calcul — Glass Box

Chaque étape est explicitement tracée dans le moteur.

---

### Étape 1 — Projection du chiffre d’affaires

- Hypothèses de croissance explicites
- Possibilité de trajectoire décroissante
- Ancrage sur des comparables sectoriels

📌 **Code**  
`core/valuation/strategies/dcf_growth.py`

---

### Étape 2 — Modélisation des marges

- Marges initiales observées ou estimées
- Convergence progressive vers une marge cible
- La vitesse de convergence est un paramètre clé

📌 **Risque majeur**  
Surestimer la marge cible conduit à une survalorisation significative.

---

### Étape 3 — Capex et BFR

- Capex proportionnel à la croissance
- BFR indexé sur le chiffre d’affaires
- Stabilisation progressive en régime mature

---

### Étape 4 — Calcul du FCFF annuel

Le FCFF est reconstruit année par année à partir des composantes précédentes.

👉 Les premières années peuvent produire des FCFF négatifs, ce qui est normal.

---

### Étape 5 — Actualisation et valeur terminale

- Les flux sont actualisés au WACC
- La valeur terminale repose sur un régime **mature** :

\[
TV = \frac{FCFF_n \times (1 + g)}{WACC - g}
\]

📌 **Transition clé**  
Les hypothèses terminales doivent être cohérentes
avec une entreprise arrivée à maturité.

---

## 6. Implémentation technique

- **Stratégie** : `DCFGrowthStrategy`
- **Fichier** : `core/valuation/strategies/dcf_growth.py`
- **Mode** : déterministe
- **Compatible Monte Carlo** : oui (extension)

---

## 7. Sorties produites

- Trajectoire de chiffre d’affaires
- Marges projetées
- FCFF reconstruits
- Valeur d’entreprise
- Valeur intrinsèque par action
- Trace Glass Box complète

---

## 8. Limites et risques

### Limites
- Forte dépendance aux hypothèses de croissance
- Sensibilité extrême à la marge terminale
- Incertitude élevée sur le long terme

### Erreurs fréquentes
- Maintenir une croissance trop élevée trop longtemps
- Négliger la convergence des marges
- Utiliser un WACC trop faible pour une entreprise risquée

---

## 9. Quand utiliser cette méthode

✔️ Entreprise en forte croissance  
✔️ Modèle économique scalable  
✔️ FCFF actuel non représentatif  

❌ Entreprise mature  
❌ Banque / assurance  
❌ Absence totale de visibilité économique  

---

📎 **Méthode suivante recommandée**  
➡️ `Residual Income Model (RIM) — Banques`
