# DCF Standard — FCFF Two-Stage

## 1. Objectif de la méthode

La méthode **DCF Standard (FCFF Two-Stage)** vise à estimer la valeur
intrinsèque d’une entreprise en actualisant les flux de trésorerie
économiques futurs disponibles pour l’ensemble des apporteurs de capitaux
(actionnaires et créanciers).

Elle est particulièrement adaptée aux :

- entreprises **matures**,
- modèles économiques **prévisibles**,
- sociétés à **croissance modérée et stable**.

---

## 2. Principe économique

La valeur de l’entreprise correspond à la somme :

1. des **Free Cash Flows to the Firm (FCFF)** projetés sur une période explicite,
2. de la **valeur terminale**, représentant l’ensemble des flux au-delà
   de l’horizon de projection.

Ces flux sont actualisés à un taux reflétant le **coût moyen pondéré du capital (WACC)**.

---

## 3. Formulation mathématique

### 3.1 Valeur d’entreprise (Enterprise Value)

\[
EV = \sum_{t=1}^{n} \frac{FCFF_t}{(1 + WACC)^t}
+ \frac{FCFF_n \times (1 + g)}{(WACC - g)} \times \frac{1}{(1 + WACC)^n}
\]

où :

- \( FCFF_t \) : Free Cash Flow to the Firm à l’année \( t \)
- \( WACC \) : coût moyen pondéré du capital
- \( g \) : taux de croissance de long terme
- \( n \) : horizon explicite de projection

---

### 3.2 Passage à la valeur des fonds propres

\[
Equity\ Value = EV - Dette\ Nette
\]

\[
Valeur\ par\ action = \frac{Equity\ Value}{Nombre\ d’actions}
\]

---

## 4. Étapes de calcul — Glass Box

Chaque étape décrite ci-dessous correspond **exactement** à une
`CalculationStep` visible dans l’interface utilisateur.

---

### Étape 1 — Sélection du FCFF de base

- Le dernier FCFF disponible est utilisé comme point de départ.
- Il peut être :
  - TTM,
  - lissé,
  - ou retraité automatiquement selon la qualité des données.

📌 **Code**  
`core/valuation/strategies/dcf_standard.py`

---

### Étape 2 — Calcul du WACC

Le WACC reflète le rendement exigé par l’ensemble des financeurs.

\[
WACC = w_e \times K_e + w_d \times K_d (1 - t)
\]

avec :

- \( K_e = R_f + \beta \times MRP \) (CAPM)
- \( K_d \) : coût de la dette
- \( t \) : taux d’imposition
- \( w_e, w_d \) : pondérations cibles

📌 **Code**
- Calcul CAPM : `core/computation/financial_math.py`
- Vérification visible dans l’UI (onglet Méthodologie)

---

### Étape 3 — Projection des flux explicites

Les FCFF sont projetés sur \( n \) années selon un taux de croissance constant \( g \).

\[
FCFF_t = FCFF_0 \times (1 + g)^t
\]

📌 **Code**  
`dcf_standard.py` — projection déterministe

---

### Étape 4 — Calcul de la valeur terminale

La valeur terminale est calculée à l’aide de la formule de Gordon-Shapiro.

\[
TV = \frac{FCFF_n \times (1 + g)}{WACC - g}
\]

📌 **Invariant critique**
- \( WACC > g \) (condition bloquante dans le moteur)

---

### Étape 5 — Actualisation

Chaque flux (y compris la valeur terminale) est actualisé au WACC :

\[
PV_t = \frac{Flux_t}{(1 + WACC)^t}
\]

La somme des valeurs actualisées constitue la **valeur d’entreprise**.

---

### Étape 6 — Passage à la valeur par action

- Déduction de la dette nette
- Division par le nombre d’actions en circulation

📌 **Résultat final affiché**
- valeur intrinsèque par action
- écart avec le prix de marché
- upside / downside

---

## 5. Implémentation technique

- **Stratégie** : `DCFStandardStrategy`
- **Fichier** : `core/valuation/strategies/dcf_standard.py`
- **Mode** : déterministe
- **Compatible Monte Carlo** : oui (extension)

---

## 6. Sorties produites

- Valeur d’entreprise (EV)
- Valeur des fonds propres
- Valeur intrinsèque par action
- Trace complète du calcul (Glass Box)
- Compatible avec :
  - Audit Engine
  - Confidence Score
  - Analyse Monte Carlo

---

## 7. Limites et erreurs fréquentes

### Limites
- Forte sensibilité au WACC et à \( g \)
- Peu adapté aux entreprises cycliques
- Hypothèse de croissance constante parfois irréaliste

### Erreurs fréquentes
- Choisir un \( g \) supérieur au WACC
- Utiliser le DCF standard pour des sociétés en hypercroissance
- Interpréter la valeur comme une prédiction de prix

---

## 8. Quand utiliser cette méthode

✔️ Entreprise mature  
✔️ Cash-flows stables  
✔️ Visibilité raisonnable à moyen terme  

❌ Start-up  
❌ Société très cyclique  
❌ Modèle économique instable  

---

## 9. Références académiques

Cette méthode s'appuie sur les travaux suivants :

1. **Damodaran, A. (2012).** *Investment Valuation*, Chapter 12-15 : DCF Valuation.
   - Méthodologie complète du DCF et calcul du WACC
   
2. **McKinsey & Company (2020).** *Valuation*, Chapter 6-7 : Forecasting Performance and Estimating Continuing Value.
   - Approche two-stage et valeur terminale
   
3. **Modigliani, F., & Miller, M. (1958).** *The Cost of Capital, Corporation Finance and the Theory of Investment*.
   - Fondements théoriques du WACC

---

📎 **Méthode suivante recommandée**  
➡️ `DCF Fondamental — FCFF Normalisé`
