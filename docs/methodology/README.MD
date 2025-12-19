# Méthodologies de valorisation

Ce dossier regroupe la **documentation méthodologique financière**
du projet *Intrinsic Value Pricer*.

Il constitue la référence pédagogique pour comprendre :
- les **méthodes de valorisation** implémentées,
- leurs **hypothèses économiques**,
- leurs **formules financières**,
- leurs **limites d’usage**.

Cette documentation est conçue pour être :
- exploitable par un **analyste junior** (apprentissage),
- auditable par un **analyste senior** (revue modèle),
- strictement alignée avec le **code source**.

---

## 🎯 Philosophie générale

Le moteur de valorisation repose sur trois principes non négociables :

1. **Glass Box**  
   Chaque méthode expose explicitement :
   - ses hypothèses,
   - ses formules,
   - chaque étape de calcul,
   - chaque résultat intermédiaire.

2. **Déterminisme des modèles**  
   Les méthodes de valorisation sont **strictement déterministes**.  
   Toute incertitude est traitée via des **extensions séparées** (Monte Carlo).

3. **Traçabilité complète**  
   Toute information affichée dans l’interface :
   - provient du moteur,
   - est traçable jusqu’au code,
   - est vérifiable ligne par ligne.

---

## 🧠 Comment lire une méthode de valorisation

Chaque méthode documentée dans ce dossier suit **la même structure**.

### 1️⃣ Objectif de la méthode
- Quel problème économique la méthode cherche à résoudre
- Pour quel type d’entreprise elle est adaptée

### 2️⃣ Principe économique
- Logique financière sous-jacente
- Hypothèses structurantes

### 3️⃣ Formules financières
- Écriture mathématique canonique
- Correspondance exacte avec le code

### 4️⃣ Étapes de calcul (Glass Box)
Chaque étape correspond directement à une
`CalculationStep` générée par le moteur :

- sélection des données de base,
- calcul des taux (WACC, Ke),
- projections,
- valeur terminale,
- passage à la valeur par action.

👉 **Ces étapes sont visibles intégralement dans l’interface utilisateur.**

### 5️⃣ Implémentation technique
Chaque page indique explicitement :
- le fichier Python concerné,
- la classe de stratégie utilisée.

### 6️⃣ Limites et cas d’usage
- Quand la méthode est pertinente
- Quand elle ne doit pas être utilisée
- Principales sources d’erreur d’interprétation

---

## 🧮 Lien entre documentation, code et interface

La documentation méthodologique est **directement reliée au code** :

| Élément | Rôle |
|------|------|
| `core/valuation/strategies/*.py` | Implémentation du calcul |
| `core/methodology/texts.py` | Texte canonique court (UI) |
| `CalculationStep` | Trace détaillée du calcul |
| Interface Streamlit | Restitution interactive |

👉 **Il n’existe aucune méthode documentée qui ne soit implémentée dans le code.**  
👉 **Il n’existe aucune logique implémentée qui ne soit documentée.**

---

## 📚 Méthodes disponibles

Les méthodes actuellement implémentées et documentées sont :

### Méthodes DCF (Discounted Cash Flow)

- **DCF Standard — FCFF Two-Stage**  
  Entreprises matures à flux stables  
  → `dcf_standard.py`

- **DCF Fondamental — FCFF Normalisé**  
  Entreprises cycliques / industrielles  
  → `dcf_fundamental.py`

- **DCF Croissance — Revenue-Driven**  
  Entreprises en forte croissance / tech  
  → `dcf_growth.py`

### Méthodes non DCF

- **Residual Income Model (RIM)**  
  Banques, assurances, institutions financières  
  → `rim_banks.py`

- **Graham Intrinsic Value (1974)**  
  Méthode heuristique comparative  
  → `graham_value.py`

### Extensions (incertitude)

- **Monte Carlo**  
  Extension probabiliste appliquée aux hypothèses  
  → `monte_carlo.py`

---

## ⚠️ Point clé sur l’incertitude

L’analyse Monte Carlo :
- **n’est pas** une méthode de valorisation,
- **ne modifie jamais** la logique des modèles,
- **quantifie uniquement l’incertitude** autour des hypothèses.

Les valeurs centrales restent issues
des **modèles déterministes**.

---

## 🛡️ Audit et gouvernance

Toutes les méthodes sont compatibles avec :
- l’**Audit Engine**,
- le **Confidence Score**,
- les exigences de **Model Validation**.

La documentation méthodologique doit toujours être lue conjointement
avec la section **Audit & Confiance** de l’interface.

---

## 📌 Règles de maintenance

- Toute nouvelle méthode implique :
  - une nouvelle stratégie dans `core/valuation/strategies/`,
  - une page dédiée dans ce dossier,
  - une entrée correspondante dans `texts.py`.

- Toute modification de formule implique :
  - mise à jour du code,
  - mise à jour de la documentation,
  - cohérence vérifiable via la trace Glass Box.

---

📎 **Prochaine lecture recommandée**  
➡️ Commencer par la méthode correspondant au profil de l’entreprise analysée  
➡️ Puis consulter la page dédiée à l’audit et à l’incertitude
