# Interpréter les résultats de valorisation

Ce document explique comment lire et interpréter correctement
les résultats produits par le moteur de valorisation.

---

## 🧮 Valeur intrinsèque

La valeur intrinsèque par action représente :
- une estimation économique,
- conditionnelle aux hypothèses retenues,
- issue d’un modèle déterministe.

👉 Ce n’est **pas** une prévision de prix à court terme.

---

## 📈 Upside / Downside

L’upside (ou downside) mesure l’écart relatif
entre la valeur intrinsèque et le prix de marché actuel.

\[
Upside = \frac{Valeur\ intrinsèque - Prix\ marché}{Prix\ marché}
\]

👉 Un upside positif n’implique pas une opportunité d’investissement automatique.

---

## 📊 Résultats Monte Carlo

Lorsque l’extension Monte Carlo est activée, l’utilisateur voit :

- une distribution de valeurs,
- des quantiles (P10, P50, P90),
- une mesure de dispersion.

### Lecture correcte
- **P50** : estimation centrale
- **P10 / P90** : scénarios défavorables / favorables
- forte dispersion = incertitude élevée

---

## 🛡️ Confidence Score

Le Confidence Score synthétise :
- la qualité des données,
- la robustesse des hypothèses,
- la stabilité des résultats.

👉 Un score élevé signifie :
- cohérence globale,
- faible sensibilité extrême.

👉 Un score faible indique :
- incertitude structurelle,
- hypothèses fragiles ou données limitées.

---

## ⚠️ Erreurs d’interprétation fréquentes

- confondre valeur intrinsèque et objectif de prix,
- ignorer les hypothèses sous-jacentes,
- comparer deux valeurs issues de méthodes différentes sans précaution,
- sur-interpréter des quantiles extrêmes.

---

## 🎯 Bonne pratique

Toujours interpréter les résultats conjointement avec :
- la méthode utilisée,
- les hypothèses clés,
- l’audit et le Confidence Score.
