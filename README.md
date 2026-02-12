# Intrinsic Value Pricer

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-750%20passing-brightgreen)
![Type Safety](https://img.shields.io/badge/mypy-passing-brightgreen)
![Linting](https://img.shields.io/badge/ruff-passing-brightgreen)
![License](https://img.shields.io/badge/license-Educational-orange)

Application de valorisation d'entreprises cotées avec transparence totale des calculs.

---

## Présentation

**Intrinsic Value Pricer** est une application open-source conçue pour l'analyse financière institutionnelle. Elle offre une valorisation rigoureuse des entreprises cotées en rendant explicite chaque étape de calcul, chaque hypothèse et chaque source de données.

Le projet privilégie la pédagogie sur l'automatisation : il explique comment une valeur intrinsèque est construite plutôt que de fournir un résultat opaque.

> **Avertissement**  
> Cette application est strictement éducative et analytique.  
> Elle ne constitue en aucun cas un conseil d'investissement.

---

## 🚀 Quick Start

### Installation

```bash
# Cloner le repository
git clone https://github.com/clement-bbier/intrinsec-value-pricer.git
cd intrinsec-value-pricer

# Installer les dépendances
pip install -e .

# Lancer l'application
streamlit run app/main.py
```

### Développement

```bash
# Installer avec les dépendances de développement
pip install -e ".[dev]"

# Lancer les tests
pytest tests/

# Vérifier le code
ruff check src/ app/ infra/
mypy src/
```

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

## Qualité et Standards

### Tests et Couverture

- **750 tests** : Suite de tests complète (unit, integration, contracts, e2e)
- **96% de couverture** : Sur les modules core (src/, infra/)
- **Tests propriétés** : Validation avec Hypothesis
- **Tests contractuels** : Garantie de stabilité des interfaces

```bash
# Lancer tous les tests
pytest tests/

# Avec couverture
pytest tests/ --cov=src --cov=infra --cov-report=html
```

### Qualité du Code

- **Ruff** : Linting automatique (0 erreurs)
- **Mypy** : Type safety avec configuration pragmatique (0 erreurs)
- **Pydantic** : Validation automatique des modèles de données
- **Documentation** : Docstrings style Numpy pour toutes les fonctions publiques

```bash
# Vérifier le linting
ruff check src/ app/ infra/

# Vérifier les types
mypy src/

# Auto-fix les problèmes simples
ruff check src/ app/ infra/ --fix
```

Voir `docs/MYPY_CONFIG.md` pour la philosophie de configuration type safety.

### CI/CD Pipeline

Pipeline GitHub Actions automatisé :
1. ✅ **Ruff** : Code linting
2. ✅ **Mypy** : Type checking
3. ✅ **Pytest** : 750 tests avec coverage ≥95%
4. ✅ **pip-audit** : Scan de sécurité

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

---

## Références Académiques

Les méthodologies de valorisation implémentées dans cette application s'appuient sur des travaux académiques et professionnels reconnus :

### Ouvrages de Référence

1. **Damodaran, A. (2012).** *Investment Valuation: Tools and Techniques for Determining the Value of Any Asset*. 3rd Edition. Wiley Finance.
   - Référence principale pour les méthodologies DCF et l'estimation du coût du capital

2. **McKinsey & Company, Koller, T., Goedhart, M., & Wessels, D. (2020).** *Valuation: Measuring and Managing the Value of Companies*. 7th Edition. Wiley.
   - Standard de l'industrie pour la valorisation d'entreprise et les flux de trésorerie

3. **Graham, B., & Dodd, D. (1974).** *Security Analysis: Principles and Technique*. 4th Edition. McGraw-Hill.
   - Fondation de l'analyse fondamentale et de la formule de Benjamin Graham

### Publications Académiques

4. **Ohlson, J. A. (1995).** *Earnings, Book Values, and Dividends in Equity Valuation*. Contemporary Accounting Research, 11(2), 661-687.
   - Modèle du revenu résiduel (RIM) pour la valorisation bancaire

5. **Hamada, R. S. (1972).** *The Effect of the Firm's Capital Structure on the Systematic Risk of Common Stocks*. The Journal of Finance, 27(2), 435-452.
   - Formule de Hamada pour l'ajustement du bêta en fonction du levier financier

### Standards Professionnels

- **CFA Institute (2015).** *Equity Asset Valuation*. 3rd Edition.
- **IASB.** International Financial Reporting Standards (IFRS)
- **AMF (Autorité des Marchés Financiers).** Bonnes pratiques de l'analyse financière

### Ressources en Ligne

- **Damodaran Online:** http://pages.stern.nyu.edu/~adamodar/
  - Données de marché, primes de risque par pays, multiples sectoriels

---

## Licence et Usage

Ce projet est fourni à des fins éducatives, analytiques et de recherche. Il ne constitue en aucun cas un conseil financier, une incitation à investir, ou une recommandation d'achat ou de vente de titres financiers.

La valeur intrinsèque est un outil d'analyse permettant d'évaluer la décote ou la prime d'un titre par rapport à ses fondamentaux économiques. Elle ne constitue pas une prédiction de cours ni une garantie de performance.

---

## Contributeurs

- **@clement-bbier**: Mainteneur du projet et développeur principal

Pour contribuer au projet, consultez `CONTRIBUTING.md`.
