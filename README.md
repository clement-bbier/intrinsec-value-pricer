# 📘 Intrinsic Value Pricer
**Glass-Box Valuation Engine — DCF Simple, DCF Fondamental & Monte Carlo**

> Éducation • Analyse financière • Modélisation avancée • Transparence totale

---

## 🎯 Objectif du projet

**Intrinsic Value Pricer** est une application open-source de valorisation d’entreprises cotées, conçue pour être :

- **Rigoureuse** sur le plan financier,
- **Transparente** sur le plan méthodologique ("Glass Box"),
- **Pédagogique** dans son exposition,
- **Auditable** dans ses résultats.

Le projet vise à **expliquer comment une valeur intrinsèque est construite**, et non à fournir un chiffre opaque ou une promesse de surperformance.

> ⚠️ **Disclaimer**
> Ce projet est strictement **éducatif et analytique**.
> Il ne constitue **en aucun cas** une recommandation d’investissement.

---

## 🧠 Qu’est-ce que la valeur intrinsèque ?

La valeur intrinsèque représente une **estimation économique** de ce que vaut une entreprise indépendamment de son prix de marché, à partir :

- de sa capacité à générer des flux de trésorerie,
- de ses fondamentaux financiers,
- de son coût du capital (WACC),
- de ses hypothèses de croissance et de risque.

Elle se distingue de :
- le **prix de marché** (offre, demande, psychologie),
- la **valeur comptable** (historique, non économique),
- les **valorisations spéculatives** (narratifs, momentum).

> Il n’existe **pas une valeur intrinsèque unique**.
> Chaque modèle repose sur un **jeu d’hypothèses explicites**.

---

## 🧩 Méthodes de valorisation implémentées

Chaque méthode est indépendante, documentée, testée et auditée.

📚 Documentation détaillée : `docs/methodology/`

### 1️⃣ DCF Simple — FCFF Direct (Two-Stage)
* **Cible :** Entreprises stables et matures.
* **Approche :** Projection directe des Free Cash Flows sans reconstruction détaillée du bilan.
* **Processus :**
    1. FCFF de base (TTM ou lissé).
    2. Projection à croissance simple (Stage 1).
    3. WACC via CAPM.
    4. Valeur terminale à croissance perpétuelle (Stage 2).
    5. Actualisation → EV → Equity → Valeur par action.

📄 Voir : `docs/methodology/dcf_standard.md`

### 2️⃣ DCF Fondamental — FCFF Reconstruit
* **Cible :** Niveau equity research / M&A.
* **Approche :** Modélisation complète des flux économiques depuis l'EBIT.
* **Construction du FCFF :**
    * EBIT → NOPAT
    * \+ D&A
    * − ΔBFR
    * − Capex
    * = FCFF normatif lissé
* **Hypothèses explicites :** Bêta (levier/délevé), ERP, coût de la dette net d'impôt, structure cible.

📄 Voir : `docs/methodology/dcf_fundamental.md`

### 3️⃣ DCF Monte Carlo — Distribution probabiliste
* **Cible :** Environnements incertains et analyse de risque.
* **Approche :** Simulation stochastique sur les inputs clés (pas sur le modèle).
* **Simulation :**
    * Volatilité du FCF.
    * Distribution de la croissance et du WACC.
* **Sorties :** Distribution complète des valeurs, quantiles (P10/P50/P90), bornes de confiance.

📄 Voir : `docs/methodology/monte_carlo.md`

### 4️⃣ Méthodes complémentaires
* **Graham (1974 révisé) :** Approche historique et conservatrice.
* **Residual Income Model (RIM) :** Spécifique pour banques et financières.

📄 Voir : `docs/methodology/graham_value.md` | `docs/methodology/rim_banks.md`

---

## ⚙️ Modes d’utilisation

📘 Documentation utilisateur : `docs/usage/`

### 🔁 Mode Automatique (AUTO)
L’utilisateur fournit : un **Ticker**, une **Méthode**, un **Horizon**.

Le moteur :
1. Récupère les données publiques (Yahoo Finance + Macro).
2. Dérive automatiquement les hypothèses (Proxies documentés).
3. Calcule la valorisation et applique les tests d’intégrité.
4. Génère un audit de confiance et explique le résultat.

### 🧪 Mode Expert / Manuel (MANUAL)
Destiné aux analystes et à la formation financière.
L’utilisateur saisit **directement toutes les hypothèses** et visualise les **formules exactes utilisées** via des toggles intelligents (ex: *Dette Nette* vs *Dette Brute*).

---

## 🧮 Audit & Score de Confiance

Chaque valorisation génère un **AuditReport**, structuré autour de 4 piliers d'incertitude :

1. **Data Confidence** (Qualité de la donnée source).
2. **Assumption Risk** (Sensibilité des hypothèses choisies).
3. **Model Risk** (Adéquation du modèle mathématique).
4. **Method Fit** (Pertinence de la méthode pour ce secteur).

> Le score **n’est pas un signal d’investissement**.
> Il mesure uniquement la **robustesse économique et logique du modèle**.

---

## 🔒 Gouvernance & Intégrité Financière

Le moteur applique des **invariants économiques non négociables**. Si un invariant est violé, le calcul est rejeté ou flaggé.

* `WACC >= Taux sans risque`
* `Croissance terminale <= Croissance économique`
* `Valeur terminale >= 0` (sauf exception justifiée)
* `Résultats finis` (pas de NaN, pas d’infini)

📄 Voir : `docs/technical/governance.md`

---

## 🧱 Architecture Technique

```text
intrinsic-value-pricer/
├── app/                  # UI Streamlit & Orchestration
│   ├── main.py
│   └── components/       # Widgets (Inputs, Charts, Audit)
├── core/                 # Cœur mathématique & Modèles
│   ├── valuation/        # Moteurs (DCF, Graham, RIM)
│   ├── computation/      # Formules financières pures
│   └── audit/            # Moteur d'audit et de scoring
├── infra/                # Data Providers & Macro
├── docs/                 # Documentation (Methodology, Usage, Tech)
├── tests/                # Tests unitaires & Invariants financiers
├── config/               # Settings.yaml
└── requirements.txt
```
---

## 📊 Restitution & Visualisations

Selon la méthode et le mode sélectionnés, l’application restitue de manière explicite :

- la **valeur intrinsèque par action**,
- la **valeur d’entreprise (EV)** et le **bridge vers l’Equity Value**,
- le **WACC détaillé** (rE, rD, pondérations, fiscalité),
- les **projections de flux de trésorerie**,
- le **poids de la valeur terminale** dans la valorisation totale,
- la **distribution Monte Carlo** des valeurs intrinsèques (le cas échéant),
- les **quantiles clés** (P10 / P50 / P90),
- l’**historique de valeur intrinsèque** comparé au prix de marché,
- une **explication pas-à-pas du calcul** (formules, hypothèses, substitutions numériques).

L’objectif est de permettre à l’utilisateur de **comprendre précisément d’où vient chaque chiffre**.

---

## 🚀 Installation & Lancement

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Lancement de l’application

```bash
streamlit run app/main.py
```

### Configuration

Les paramètres globaux du moteur (hypothèses par défaut, options automatiques,
comportements de sécurité) sont centralisés dans le fichier suivant :

```text
config/settings.yaml
```

Ce fichier permet notamment de :
- définir les hypothèses macro-financières par défaut,
- encadrer les comportements automatiques du moteur,
- appliquer les règles de gouvernance et de sécurité,
- garantir la reproductibilité des calculs.

---

## 🧭 Roadmap maîtrisée

Les évolutions envisagées respectent strictement la philosophie du projet :
**rigueur financière, transparence méthodologique, pédagogie et gouvernance stricte**.

### Extensions cohérentes et réalistes

- scénarios multi-hypothèses (Bull / Base / Bear),
- multiples de valorisation pédagogiques (EV/EBITDA, EV/EBIT, P/E),
- export de rapports (PDF / PowerPoint),
- mode batch léger (analyse simultanée de quelques tickers),
- API locale pour usage Python / Jupyter,
- portage éventuel vers Dash ou un frontend web dédié.

### Éléments volontairement exclus

- modèles LBO complexes,
- trading, market timing ou signaux d’achat / vente,
- promesses de surperformance,
- API publique ouverte,
- données institutionnelles payantes.

Ces exclusions sont **assumées** afin de préserver la clarté pédagogique,
la gouvernance du moteur et l’honnêteté intellectuelle du projet.

---

## 🧠 Philosophie du projet

> **Le moteur ne décide jamais.**  
> Il rend explicites les hypothèses,  
> calcule leurs conséquences économiques,  
> et laisse le jugement final à l’humain.

La valeur intrinsèque est un **outil d’analyse**,
pas une vérité absolue ni une prédiction de marché.

---

## ⚠️ Disclaimer final

Ce projet est fourni **à des fins éducatives, analytiques et de recherche**.  
Il ne constitue **en aucun cas** un conseil financier,
une incitation à investir,
ou une recommandation d’achat ou de vente de titres financiers.
