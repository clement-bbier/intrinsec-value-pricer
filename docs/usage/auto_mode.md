# Mode AUTO — Hypothèses Normatives

**Version** : 2.0 — Janvier 2026

Le **mode AUTO** est conçu pour fournir
une valorisation cohérente avec un minimum d'intervention utilisateur.

---

## Philosophie

- Hypothèses standardisées basées sur les données de marché
- Proxies de marché validés (Yahoo Finance, Damodaran)
- Garde-fous économiques stricts
- Mode dégradé automatique en cas de panne API (ST-4.1)

**La responsabilité principale est portée par le système.**

---

## Fonctionnement

### Acquisition des Données

```
1. Ticker entré par l'utilisateur
       ↓
2. Récupération Yahoo Finance
   - États financiers (TTM)
   - Prix de marché
   - Beta historique
   - Données de comparables
       ↓
3. Récupération Macro
   - Taux sans risque (pays)
   - Prime de risque marché
       ↓
4. En cas d'échec → Mode Dégradé
   - Fallback sur multiples sectoriels
   - Bandeau d'avertissement affiché
```

### Calcul des Paramètres

| Paramètre | Source | Méthode |
|-----------|--------|---------|
| Rf | Obligations 10 ans | Yahoo Macro Provider |
| Beta | Historique 2 ans | Yahoo Finance |
| MRP | Matrice pays | Damodaran |
| Kd | Spread synthétique | ICR + Rf |
| g | CAGR FCF historique | 3-5 ans |
| gn | Inflation pays | Matrice pays |

### Contrôles Automatiques

| Contrôle | Action |
|----------|--------|
| g > WACC | Erreur bloquante |
| Beta < 0 | Avertissement |
| Beta > 3 | Avertissement |
| Payout > 100% | Avertissement |
| FCF négatif | Erreur (FCFE) |

---

## Avantages

| Avantage | Description |
|----------|-------------|
| **Simplicité** | Un seul clic pour lancer l'analyse |
| **Cohérence** | Hypothèses standardisées |
| **Rapidité** | Résultat en < 30 secondes |
| **Apprentissage** | Idéal pour découvrir les méthodes |
| **Résilience** | Fallback automatique (ST-4.1) |

---

## Limites

| Limite | Impact |
|--------|--------|
| Moins de flexibilité | Pas de personnalisation |
| Hypothèses conservatrices | Sous-estimation possible |
| Dépendance données | Qualité variable selon ticker |
| Pas de scénarios | Pas d'analyse Bull/Bear |

---

## Options Disponibles

Même en mode AUTO, quelques options sont configurables :

| Option | Description | Défaut |
|--------|-------------|--------|
| Monte Carlo | Activer les simulations | Non |
| Nb simulations | Si MC activé | 5000 |
| Backtest | Validation historique | Non |

---

## Mode Dégradé (ST-4.1)

Si Yahoo Finance échoue ou renvoie des données aberrantes :

1. **Détection automatique**
   - Timeout API (> 10 secondes)
   - Données invalides (P/E > 500, etc.)

2. **Basculement**
   - Utilisation des multiples sectoriels moyens
   - Source : Damodaran 2024

3. **Signalétique**
   - Bandeau orange affiché
   - Score de confiance réduit (70%)
   - Source clairement indiquée

---

## Recommandé Pour

| Profil | Cas d'usage |
|--------|-------------|
| **Débutants** | Premiers pas en valorisation |
| **Screening** | Analyse rapide de nombreux titres |
| **Comparaisons** | Benchmark entre entreprises |
| **Apprentissage** | Comprendre les méthodes DCF |

---

## Prochaines Étapes

Après une analyse en mode AUTO :

1. **Consulter le rapport d'audit**
   - Vérifier le score et les alertes
   - Comprendre les risques identifiés

2. **Examiner les hypothèses**
   - Valider la cohérence économique
   - Comparer avec vos attentes

3. **Basculer en EXPERT si nécessaire**
   - Pour affiner les hypothèses
   - Pour tester des scénarios

4. **Exporter le Pitchbook PDF**
   - Rapport professionnel de 3 pages
   - Prêt pour la présentation
