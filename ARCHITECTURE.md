# Architecture d'Intrinsic Value Pricer

## Vue d'Ensemble

Intrinsic Value Pricer suit une architecture modulaire en couches, séparant clairement la logique métier de l'interface utilisateur et de l'infrastructure.

## Flux de Données

```
Utilisateur → Interface → Registre → Stratégie → Pipeline → Résultat
     ↓         ↓         ↓         ↓         ↓         ↓
  Paramètres   UI     Injection   Calcul   Exécution  Audit
```

### 1. Interface Utilisateur (app/)
- **Responsabilité** : Capture des paramètres utilisateur et présentation des résultats
- **Technologies** : Streamlit, composants UI spécialisés
- **Principe** : Interface réactive sans logique métier

### 2. Registre Centralisé (src/valuation/registry.py)
- **Rôle** : Point unique d'injection des dépendances
- **Fonction** : Routage des stratégies et auditeurs par mode de valorisation
- **Avantages** : Configuration centralisée, testabilité, extensibilité

### 3. Stratégies de Valorisation (src/valuation/strategies/)
- **Responsabilité** : Orchestration des calculs selon la méthode choisie
- **Pattern** : Strategy Pattern avec classe abstraite `ValuationStrategy`
- **Chaque stratégie** :
  - Sélectionne les données appropriées
  - Configure le pipeline de calcul
  - Génère l'audit report
  - Valide le contrat de sortie

### 4. Pipeline de Calcul (src/valuation/pipelines.py)
- **Rôle** : Séquence standardisée des opérations de valorisation
- **Étapes** :
  1. Calcul du taux d'actualisation (WACC/Ke)
  2. Projection des flux selon le projecteur choisi
  3. Calcul de la valeur terminale
  4. Actualisation des flux (VAN)
  5. Pont actionnarial (equity bridge)
  6. Ajustement de dilution SBC

### 5. Moteurs de Calcul (src/computation/)
- **Responsabilité** : Fonctions mathématiques pures
- **Modules** :
  - `financial_math.py` : Formules financières atomiques
  - `growth.py` : Projecteurs de flux avec stratégies de croissance
  - `statistics.py` : Générateurs de tirages Monte Carlo

## Architecture en Couches

```
┌─────────────────────────────────────┐
│         Interface Utilisateur       │  app/
│         (Streamlit Components)      │
├─────────────────────────────────────┤
│         Logique Métier Pure         │  src/
│         (Pydantic, Pure Functions)  │
├─────────────────────────────────────┤
│         Infrastructure              │  infra/
│         (Data Providers, Audit)     │
└─────────────────────────────────────┘
```

### Principes d'Étanchéité

- **src/** n'importe jamais `app/` ou `streamlit`
- **infra/** peut importer `src/` mais pas `app/`
- **app/** importe `src/` et `infra/` pour l'injection de dépendances

## Registre Centralisé

Le registre (`src/valuation/registry.py`) constitue le point d'entrée unique pour :

- **Découverte automatique** des stratégies disponibles
- **Injection des dépendances** (auditeurs, UI renderers)
- **Configuration centralisée** des mappings stratégie → composants

### Avantages

- **Maintenance** : Un seul endroit pour enregistrer une nouvelle stratégie
- **Testabilité** : Injection de mocks simplifiée
- **Extensibilité** : Ajout de nouvelles méthodes sans modifier le code existant

## Gestion des Données

### Fournisseurs de Données (infra/data_providers/)
- **YahooProvider** : Interface principale avec données temps réel
- **Fallback** : Multiples sectoriels en cas de panne
- **Normalisation** : Validation et standardisation des données brutes

### Modèles de Données (src/models/)
- **Pydantic Models** : Validation automatique et sérialisation
- **Contrats** : Interfaces strictes entre composants
- **Glass Box** : Traçabilité complète des calculs

## Système d'Audit

### Audit Engine (infra/auditing/audit_engine.py)
- **Évaluation systématique** de la qualité des valorisations
- **Piliers d'audit** : Données, Hypothèses, Modèle, Méthode
- **Rapports structurés** : Score pondéré avec diagnostics détaillés

### Diagnostic Registry (src/diagnostics.py)
- **Messages pédagogiques** : Erreurs traduites en conseils métier
- **Contextes financiers** : Explication des risques économiques
- **Internationalisation** : Support multilingue via i18n

## Gestion des Configurations

### Constantes Centralisées (src/config/constants.py)
- **Source unique de vérité** pour seuils et paramètres
- **Validation automatique** de cohérence
- **Documentation intégrée** des hypothèses économiques

### Internationalisation (src/i18n/)
- **Messages centralisés** par domaine fonctionnel
- **Support multilingue** extensible
- **Séparation UI/Backend** : Textes d'interface vs messages système

## Tests et Validation

### Tests Contractuels (tests/contracts/)
- **Validation des interfaces** entre composants
- **Tests d'étanchéité** : Vérification des dépendances interdites
- **Contrats de sortie** : Validation systématique des résultats

### Tests d'Intégration (tests/integration/)
- **Flux complets** : Interface → Calcul → Résultat
- **Scénarios réels** : Tests avec données Yahoo Finance
- **Performance** : Validation des temps de réponse

Cette architecture assure la maintenabilité, la testabilité et l'extensibilité du système tout en garantissant la séparation des préoccupations et la transparence des calculs financiers.