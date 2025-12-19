# Documentation — Intrinsic Value Pricer

Cette documentation constitue la **référence financière, technique et utilisateur**
du projet *Intrinsic Value Pricer*.

Elle est conçue pour permettre :
- la **compréhension** des méthodes de valorisation,
- la **vérification** des calculs et hypothèses,
- l’**apprentissage** des logiques financières sous-jacentes.

La documentation est strictement alignée avec :
- le moteur de calcul,
- l’interface utilisateur,
- les principes de transparence Glass Box.

---

## 🧭 Comment naviguer dans la documentation

La documentation est organisée en couches distinctes :

### 📘 Méthodologie (`docs/methodology/`)
- Théorie financière
- Méthodes de valorisation
- Formules et limites
- 1 méthode = 1 page

### 🛠️ Technique (`docs/technical/`)
- Architecture du moteur
- Responsabilités des modules
- Invariants techniques

### 👤 Usage (`docs/usage/`)
- Modes AUTO / EXPERT
- Interprétation des résultats
- Bonnes pratiques utilisateur

### 📚 Références (`docs/references/`)
- Sources externes
- Données de marché
- Hypothèses macro-financières

---

## ⚠️ Principe clé

Aucune information présente dans cette documentation
n’est indépendante du code source.

👉 Toute méthode documentée est implémentée.  
👉 Toute logique implémentée est documentée.

---

📎 **Point d’entrée recommandé**
- Nouvel utilisateur : `usage/README.md`
- Analyste financier : `methodology/README.md`
- Développeur / reviewer : `technical/README.md`
