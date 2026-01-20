# Intrinsic Value Pricer

Application de valorisation d'entreprises cotées avec transparence totale des calculs.

---

## Présentation

**Intrinsic Value Pricer** est une application open-source conçue pour l'analyse financière institutionnelle. Elle offre une valorisation rigoureuse des entreprises cotées en rendant explicite chaque étape de calcul, chaque hypothèse et chaque source de données.

Le projet privilégie la pédagogie sur l'automatisation : il explique comment une valeur intrinsèque est construite plutôt que de fournir un résultat opaque.

> **Avertissement**  
> Cette application est strictement éducative et analytique.  
> Elle ne constitue en aucun cas un conseil d'investissement.

---

## Fonctionnalités

### Méthodes de Valorisation
- **Discounted Cash Flow (DCF)** : 5 variantes (FCFF Standard, Growth, Fundamental, FCFE, DDM)
- **Residual Income Model (RIM)** : Valorisation par revenus résiduels
- **Benjamin Graham Formula** : Screening rapide
- **Multiples de marché** : Valorisation relative sectorielle
- **Simulations Monte Carlo** : Analyse probabiliste des risques

### Transparence et Auditabilité
- **Glass Box** : Traçabilité complète de chaque variable et calcul
- **Rapports d'audit** : Évaluation systématique de la qualité des données et hypothèses
- **Export PDF professionnel** : Documentation complète des valorisations
- **Internationalisation** : Support multilingue (Français, Anglais à venir)

### Robustesse
- **Mode dégradé** : Fallback automatique sur données sectorielles
- **Validation des données** : Détection automatique des anomalies
- **Backtesting historique** : Validation des modèles sur périodes passées

---

## Architecture

```
intrinsec-value-pricer/
├── src/                       # Logique métier pure
│   ├── models/                # Modèles de données Pydantic
│   ├── valuation/             # Moteur et stratégies de valorisation
│   ├── computation/           # Fonctions mathématiques
│   ├── config/                # Constantes centralisées
│   ├── i18n/                  # Internationalisation
│   ├── diagnostics.py         # Système de diagnostics
│   └── quant_logger.py        # Logging institutionnel
│
├── app/                       # Interface utilisateur Streamlit
│   ├── ui/                    # Composants d'interface
│   └── adapters/              # Couche d'adaptation
│
├── infra/                     # Infrastructure
│   ├── data_providers/        # Fournisseurs de données
│   ├── auditing/              # Moteur d'audit
│   └── ref_data/              # Données de référence
│
├── docs/                      # Documentation
├── tests/                     # Tests unitaires et d'intégration
└── config/                    # Configuration
```

### Principes Architecturaux

- **Séparation des préoccupations** : Logique métier indépendante de l'interface
- **Injection de dépendances** : Registre centralisé pour la configuration
- **Tests contractuels** : Validation systématique des interfaces

---

## Méthodes de Valorisation

### Approches DCF (Flux Actualisés)
- **FCFF Standard** : Valorisation d'entreprises matures avec flux stables
- **FCFF Fundamental** : Normalisation des flux cycliques
- **FCFF Growth** : Convergence de marges pour entreprises en croissance
- **FCFE** : Valorisation directe des fonds propres
- **DDM** : Modèle de dividende actualisé

### Autres Approches
- **RIM** : Modèle du revenu résiduel (banques et assurances)
- **Graham** : Formule de Benjamin Graham pour screening
- **Multiples** : Valorisation relative par comparables sectoriels

### Analyse de Risque
- **Monte Carlo** : Simulation probabiliste des valorisations
- **Scénarios** : Analyse de sensibilité déterministe
- **Backtesting** : Validation historique des modèles

Documentation complète : `docs/methodology/`

---

## Modes d'Utilisation

### Mode Automatique
Acquisition automatique des données via Yahoo Finance avec hypothèses normatives du système. Garde-fous économiques intégrés et mode dégradé en cas de panne API.

**Public cible** : Apprentissage, screening rapide, utilisateurs débutants.

### Mode Expert
Contrôle total des paramètres via terminaux spécialisés. Workflow séquencé permettant la configuration précise de chaque hypothèse de valorisation.

**Public cible** : Analystes professionnels, valorisations approfondies, recherche institutionnelle.

Documentation utilisateur : `docs/usage/`

---

## Installation et Utilisation

### Prérequis
- Python 3.10 ou supérieur
- pip

### Installation
```bash
pip install -r requirements.txt
```

### Lancement
```bash
streamlit run app/main.py
```

### Tests
```bash
# Tests contractuels
pytest tests/contracts/ -v

# Suite complète
pytest tests/ -v
```


---

## Système d'Audit

Chaque valorisation fait l'objet d'un audit systématique évaluant :

- **Qualité des données** : Disponibilité et cohérence des métriques financières
- **Robustesse des hypothèses** : Plausibilité économique des paramètres utilisés
- **Cohérence méthodologique** : Adéquation du modèle choisi
- **Risques de valorisation** : Sensibilité aux variations de paramètres

Le rapport d'audit fournit un score de confiance pondéré selon ces critères.

---

## Documentation

- `docs/methodology/` : Théorie financière et formules mathématiques
- `docs/technical/` : Architecture et principes de conception
- `docs/usage/` : Guides utilisateur détaillés
- `docs/references/` : Sources académiques et bibliographiques

## Licence et Usage

Ce projet est fourni à des fins éducatives, analytiques et de recherche. Il ne constitue en aucun cas un conseil financier, une incitation à investir, ou une recommandation d'achat ou de vente de titres financiers.

La valeur intrinsèque est un outil d'analyse permettant d'évaluer la décote ou la prime d'un titre par rapport à ses fondamentaux économiques. Elle ne constitue pas une prédiction de cours ni une garantie de performance.
