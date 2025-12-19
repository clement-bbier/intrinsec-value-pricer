# Documentation technique

Ce dossier décrit l’**architecture interne** du moteur de valorisation.

Il s’adresse principalement à :
- développeurs,
- maintainers,
- reviewers techniques,
- profils quant / risk / model validation.

---

## 🧱 Architecture globale

Le moteur est structuré en couches :

1. **Stratégies de valorisation**
   - Implémentation des méthodes financières
   - Déterministes par construction

2. **Couche de calcul**
   - Fonctions mathématiques
   - Statistiques et transformations

3. **Orchestration**
   - Sélection dynamique des stratégies
   - Pipeline transactionnel

4. **Audit & gouvernance**
   - Vérification des invariants
   - Confidence Score

---

## 📂 Contenu du dossier

- `valuation_engines.md`  
  → orchestration des stratégies de valorisation

- `audit_engine.md`  
  → logique d’audit et score de confiance

- `data_providers.md`  
  → récupération et préparation des données

---

## ⚠️ Règles techniques

- aucune stratégie ne contient de logique UI
- aucune méthode ne mélange calcul et audit
- les modèles sont déterministes par défaut
- toute incertitude passe par des extensions dédiées

---

📌 **Note**
Cette documentation technique ne remplace pas la lecture du code,
mais fournit une vue d’ensemble des responsabilités et invariants.
