# 📘 Intrinsic Value Pricer  
**Application professionnelle de valorisation d’entreprise (DCF simple, DCF fondamental, Monte Carlo).**  
**Éducation • Analyse financière • Modélisation avancée • Transparence totale**

---

# 🎯 Objectifs du Projet

Cette application propose une plateforme **rigoureuse, transparente et pédagogique** pour estimer la **valeur intrinsèque** d'une entreprise cotée.

Elle permet de :

- comparer plusieurs **méthodes de valorisation** (DCF simple, DCF fondamental, DCF Monte Carlo),  
- comprendre **comment les hypothèses influencent le résultat**,  
- analyser la **robustesse** d’une valorisation via un audit,  
- explorer les paramètres manuellement dans un environnement **expert**,  
- fournir des explications claires, étape par étape.

> **⚠️ Disclaimer :**  
> Ce projet est à vocation **éducative et analytique**.  
> Ce n’est PAS une recommandation d’investissement.

---

# 🧠 1. Qu’est-ce que la valeur intrinsèque ?

La valeur intrinsèque représente ce que vaut économiquement une entreprise **indépendamment du marché**, basée sur :

- sa capacité réelle à générer du cash,
- ses fondamentaux financiers,
- son coût du capital (WACC),
- son profil de croissance.

Elle est différente de :

- **Prix de marché** : déterminé par la psychologie et la liquidité,  
- **Valeur comptable** : historique, pas économique,  
- **Prix spéculatif** : dépend des narratifs et du momentum.

> **Il n'existe pas une seule vraie valeur intrinsèque.**  
> Chaque modèle est un jeu d’hypothèses.

---

# 🧩 2. Méthodes de valorisation disponibles

L'application implémente trois moteurs indépendants, chacun avec sa logique, ses paramètres, ses validations et son interface dédiée.

---

## **Méthode 1 – DCF Simple (FCFF direct)**

✔ Adaptée aux entreprises stables  
✔ Très pédagogique  
✔ Hypothèses limitées

Processus :

1. Calcul d’un **FCFF de base** (FCF TTM ou lissé)  
2. Projection avec une croissance simple  
3. WACC via CAPM  
4. Valeur terminale (croissance perpétuelle)  
5. Actualisation → Valeur d’entreprise → Valeur Equity → Valeur par action

Utilisation typique : entreprises matures et prévisibles.

---

## **Méthode 2 – DCF Fondamental (FCFF reconstruit)**

✔ Niveau “professionnel” (M&A, equity research)  
✔ Modèle complet des flux économiques  

Construction du FCFF :

- EBIT → NOPAT  
- + Dépréciation  
- – Variation du BFR  
- – Capex  
- = FCFF normatif lissé (moyenne pondérée 3–5 ans)

Hypothèses :

- Beta (levier ou délevé)  
- Taux sans risque  
- Prime de risque marché / pays  
- Coût de la dette après impôts  
- Structure du capital cible  
- Croissance long terme cohérente macro/secteur  

L’interface affiche clairement la formule utilisée et la valeur injectée dans chaque équation.

---

## **Méthode 3 – DCF Monte Carlo (distribution probabiliste de VI)**

✔ Pour environnements incertains  
✔ Analyse probabiliste  
✔ Intervalle de valeurs intrinsèques

Simulation :

- volatilité du FCF,  
- distribution des taux de croissance,  
- distribution du WACC,  
- incertitude multipériode.

Sorties :

- Distribution complète des valeurs  
- P10 / P50 / P90  
- Histogrammes + densité  
- Intervalle de confiance  

---

# ⚙️ 3. Mode Automatique

L’utilisateur fournit :

- ticker  
- méthode  
- horizon de projection  

L’application :

- récupère automatiquement les données nécessaires (Yahoo Finance + macro),  
- dérive toutes les hypothèses financières,  
- calcule la valeur intrinsèque,  
- affiche les tableaux spécifiques à la méthode,  
- génère un audit qualitatif,  
- explique toutes les étapes du calcul.

Chaque méthode possède :

- ses propres hypothèses,  
- ses propres formules,  
- ses propres graphiques,  
- son propre audit.

---

# 🧪 4. Mode Manuel / Expert

Mode conçu pour :

✔ investisseurs avancés  
✔ analystes  
✔ formation au DCF

L’utilisateur choisit :

- la méthode (Simple, Fondamental, Monte Carlo),  
- **tous les paramètres manuellement**, avec visibilité claire des formules utilisées.

---

## 🔀 Toggles X ↔ Y : flexibilité totale et formules explicites

Le mode Expert offre des **toggles intelligents** permettant d’entrer un paramètre sous plusieurs formes équivalentes :

| Toggle | Utilité |
|--------|---------|
| Dette ↔ Dette nette | Le moteur reconstruit la variable nécessaire au WACC |
| Beta levier ↔ Beta délevé | Application automatique des formules de levier/delevier |
| CAPM ↔ Coût des fonds propres direct | Le moteur utilise CAPM ou rE selon choix |
| Croissance simple ↔ Croissance paramétrée | Génération automatique du vecteur g(t) |

Chaque toggle :

- **adapte la formule utilisée**,  
- **met à jour les champs visibles**,  
- **met en évidence la formule dans “Comprendre le calcul”**,  
- assure une totale transparence : l’utilisateur voit *quelle valeur alimente quelle formule*.

---

# 🧮 5. Audit & Score de Confiance

L’audit évalue 4 dimensions :

1. Cohérence des hypothèses  
2. Qualité des données (AUTO uniquement)  
3. Robustesse du modèle (TV/EV, stabilité)  
4. Spécificité sectorielle / pays

### Mode AUTO
- Analyse la fiabilité des données Yahoo et des heuristiques.

### Mode MANUEL
- Analyse exclusivement la **cohérence logique des paramètres saisis**.

Chaque méthode possède un audit adapté à sa structure.

---

# 🧱 6. Architecture du projet

Architecture modulaire, inspirée des standards professionnels (DDD / clean architecture).

```text
intrinsic-value-pricer/
├── app/ # UI Streamlit
│ ├── ui_components/                # Inputs, toggles, KPIs, charts
│ ├── main.py # Point d’entrée
│ └── workflow.py # Orchestration
│
├── core/
│ ├── models.py                     # DCFParameters, MethodConfig, Financials…
│ ├── computation/                  # Discounting, growth, stats
│ ├── valuation/                    # Moteurs DCF & reverse DCF
│ └── exceptions.py
│
├── infra/
│ ├── data_providers/               # Yahoo, base provider
│ ├── macro/                        # Taux sans risque, primes pays
│ └── auditing/
│ └── audit_engine.py
│
├── config/                         # Paramètres par défaut
├── tests/                          # Tests unitaires et intégration
└── requirements.txt
```

Cette architecture permet une **extensibilité naturelle** (nouvelles méthodes, nouveaux providers).

---

# 📊 7. Visualisations & Explications

L'application fournit automatiquement :

- Valeur intrinsèque  
- Valeur d’entreprise (EV)  
- WACC détaillé  
- Poids de la valeur terminale  
- Projections de FCF  
- Distribution Monte Carlo  
- Historique de valeur intrinsèque  
- Explication complète du calcul (méthode par méthode)

---

# 🚀 8. Installation & Lancement

Installation :

```bash
pip install -r requirements.txt
```

Lancement :

```bash
streamlit run app/main.py
```

Configuration :
```arduino
config/settings.yaml
```

---

## 🧭 9. Roadmap (Extensions Faisables Pour Tous)

Ces extensions sont réalistes, utilisables par un particulier, et cohérentes avec l’architecture :

- **Multiples avancés** (EV/EBITDA, EV/EBIT, P/E forward)  
- **DDM / Résidual Income** (versions pédagogiques)  
- **Modèle H simplifié** (croissance dégressive accessible)  
- **UI mobile avancée**  
- **Export PDF / PowerPoint**  
- **Mode batch léger** (5–20 tickers)  
- **Mini-API local** (Jupyter / Python)  
- **Option : portage Dash / React** (si besoin futur)

---

### ❌ Éléments volontairement exclus (non pertinents pour particuliers)

- LBO  
- Batch massif (100+ tickers)  
- API publique  
- Modélisations de risque avancées  

---

## ⚠️ Disclaimer

Cette application est fournie **pour la formation, la recherche et l’analyse**.  
Elle ne constitue **en aucun cas** un conseil en investissement.
