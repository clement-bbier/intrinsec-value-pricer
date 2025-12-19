# Orchestration des moteurs de valorisation

Ce document décrit le rôle du module d’orchestration
chargé d’exécuter les stratégies de valorisation.

---

## 📌 Rôle du moteur

Le moteur de valorisation :
- sélectionne la stratégie appropriée,
- injecte les données et paramètres,
- exécute le calcul déterministe,
- collecte la trace Glass Box.

📌 **Fichier clé**
- `core/valuation/engines.py`

---

## 🧠 Sélection des stratégies

Les stratégies sont :
- implémentées dans `core/valuation/strategies/`,
- sélectionnées dynamiquement selon le mode et la méthode.

Chaque stratégie :
- hérite d’un contrat commun (`abstract.py`),
- expose une méthode d’exécution standardisée.

---

## 🔄 Pipeline d’exécution

1. Validation des entrées
2. Construction du contexte de calcul
3. Exécution de la stratégie
4. Collecte des étapes (`CalculationStep`)
5. Construction du résultat final

---

## ⚠️ Invariants

- une stratégie = une méthode financière
- aucune stratégie ne dépend de l’UI
- aucune logique probabiliste dans le moteur déterministe
