# 🔒 GOVERNANCE & ANTI-DÉRIVE  
## Intrinsic Value Pricer — Technical Governance Charter

**Statut** : Normatif — Document de référence  
**Version** : 1.0  
**Portée** : Ensemble du projet (code, documentation, usage)  

---

## 1. Objectif du document

Ce document définit les **règles de gouvernance techniques et méthodologiques non négociables**
du projet *Intrinsic Value Pricer*.

Il a pour objectifs :

- empêcher toute dérive fonctionnelle ou méthodologique
- verrouiller les règles d’extension du moteur
- garantir la traçabilité, l’auditabilité et la reproductibilité
- assurer l’alignement avec les standards institutionnels  
  *(CFA Institute, Damodaran, Model Risk Management)*

Ce document prévaut sur toute interprétation implicite du code ou de la documentation.

---

## 2. Principes immuables

Les principes suivants sont **absolus** et **non négociables** :

- **Une méthode = une source**
- **Une feature = une version**
- **Un calcul = une trace**
- **Un score = une formule**
- **Aucune logique implicite**
- **Aucune responsabilité ambiguë (AUTO vs EXPERT)**

Toute violation invalide la conformité du projet.

---

## 3. Périmètre normatif du moteur

### 3.1 Moteur de valorisation

Le moteur de valorisation est :

- déterministe par construction
- piloté exclusivement via le point d’entrée central
- strictement typé par des contrats explicites

📌 Toute exécution de méthode de valorisation **doit** passer par le moteur central
(`run_valuation` / registre officiel).

L’instanciation directe d’une stratégie hors moteur est **formellement interdite**.

---

## 4. Référentiel officiel des méthodes

Les méthodes de valorisation autorisées sont exclusivement celles :

- déclarées dans le référentiel `ValuationMode`
- implémentées dans `core/valuation/strategies/`
- documentées dans `core/methodology/texts.py`
- décrites dans `docs/methodology/`

Toute méthode non listée est **inexistante par définition**.

---

## 5. Glass Box — Traçabilité obligatoire

Toute méthode de valorisation doit produire :

- une trace complète, séquentielle et lisible
- une décomposition étape par étape
- des hypothèses explicites et sourcées
- une substitution numérique visible
- une interprétation économique

📌 **Aucun calcul implicite n’est autorisé.**  
📌 Une valeur sans trace est considérée comme invalide.

---

## 6. Monte Carlo — Statut normatif

Monte Carlo est une **extension probabiliste**, et **non une méthode de valorisation**.

Règles non négociables :

- Monte Carlo agit exclusivement sur les **paramètres d’entrée**
- la logique financière reste strictement déterministe
- chaque simulation est une exécution complète du modèle déterministe
- le scénario pivot (P50) est **sans stochasticité**
- Monte Carlo ne produit **jamais** une valeur intrinsèque autonome

Toute utilisation contraire constitue une dérive méthodologique.

---

## 7. Audit & Confidence Score

L’audit est une **méthode normalisée à part entière**, au même titre que la valorisation.

Règles :

- le score est une **formule explicite**
- les pondérations sont visibles
- les piliers sont indépendants
- aucune agrégation implicite n’est autorisée
- toute pénalité est traçable

Le moteur d’audit est unique et centralisé.

---

## 8. Responsabilité utilisateur — AUTO vs EXPERT

### Mode AUTO

- hypothèses normatives
- proxies autorisés
- audit pénalisant et conservateur
- responsabilité portée par le système

### Mode EXPERT

- hypothèses fournies par l’utilisateur
- données présumées exactes
- audit logique et financier strict
- responsabilité transférée à l’utilisateur

Aucune ambiguïté entre les deux modes n’est tolérée.

---

## 9. Providers de données — Contrat strict

Toute source de données **doit** implémenter strictement l’interface `DataProvider`.

Règles :

- aucune logique financière dans les providers
- aucune calibration implicite
- aucune hypothèse métier
- uniquement extraction, normalisation et contrôle de cohérence

Tout provider hors contrat est interdit.

---

## 10. Interface utilisateur (UI)

L’UI est un **canal de restitution uniquement**.

Interdictions formelles :

- calcul financier
- règle économique
- décision méthodologique
- modification implicite des hypothèses

Toute logique métier dans l’UI est une violation de la gouvernance.

---

## 11. Documentation & source de vérité

La source de vérité **canonique** des méthodes est :

- `core/methodology/texts.py`

Les documents Markdown :

- sont explicatifs
- non contractuels
- ne peuvent introduire aucune méthode ou règle nouvelle

Toute divergence est considérée comme une erreur documentaire.

---

## 12. Archives & documents historiques

Le dossier `_archive/` contient :

- des documents historiques
- des réflexions passées
- des pistes abandonnées

Ces documents sont **non normatifs**, **non contractuels** et **non applicables**.

Ils ne doivent en aucun cas être utilisés comme référence.

---

## 13. Règles d’extension du projet

Toute extension du projet implique :

- une nouvelle version explicite
- une documentation associée
- un audit de cohérence
- une validation des invariants

Les ajout
