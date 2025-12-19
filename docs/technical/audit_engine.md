# Audit Engine & Confidence Score

Ce document décrit le rôle du **moteur d’audit**
chargé d’évaluer la robustesse d’une valorisation.

L’audit ne modifie jamais la valeur intrinsèque calculée.
Il fournit une **mesure de confiance** associée au résultat.

---

## 🎯 Objectif de l’audit

- détecter les incohérences économiques,
- mesurer l’incertitude structurelle,
- qualifier la fiabilité du résultat.

👉 L’audit est une **méthode d’évaluation**, pas un jugement d’investissement.

---

## 📌 Implémentation

- **Module** : `infra/auditing/`
- **Fichier principal** : `audit_engine.py`
- **Auditeurs spécialisés** : `auditors.py`

Chaque auditeur :
- évalue un pilier de risque,
- produit un score partiel,
- remonte des diagnostics explicites.

---

## 🧱 Piliers évalués

- Qualité des données
- Risque lié aux hypothèses
- Risque de modèle
- Adéquation méthode / entreprise

Les scores sont agrégés
selon une pondération dépendant du mode AUTO / EXPERT.

---

## ⚠️ Invariants

- l’audit est post-calcul,
- aucune hypothèse n’est modifiée,
- tout signal est traçable et explicite.
