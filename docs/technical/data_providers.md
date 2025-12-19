# Data Providers & Sources de données

Ce document décrit la couche de récupération
et de préparation des données financières et macroéconomiques.

---

## 🎯 Rôle des data providers

Les providers sont responsables de :
- l’accès aux données externes,
- la normalisation des formats,
- la gestion des données manquantes.

Ils ne contiennent **aucune logique de valorisation**.

---

## 📌 Implémentation

- **Données financières** :
  - `infra/data_providers/yahoo_provider.py`
- **Données macro** :
  - `infra/macro/yahoo_macro_provider.py`

---

## 🔍 Données récupérées

- états financiers publiés,
- prix de marché,
- taux sans risque,
- primes de risque,
- données macro de référence.

---

## ⚠️ Limites connues

- dépendance à des sources publiques,
- qualité variable selon les entreprises,
- délais de mise à jour possibles.

Ces limites sont intégrées
dans le calcul du Confidence Score.
