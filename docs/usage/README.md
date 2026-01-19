# Guide Utilisateur

**Version** : 2.0 — Janvier 2026

Ce dossier explique **comment utiliser correctement**
le moteur de valorisation et **comment interpréter les résultats**.

Il s'adresse à :
- utilisateurs non-développeurs,
- analystes financiers,
- étudiants / profils pédagogiques.

---

## Philosophie d'Utilisation

L'outil fournit :
- une **valeur intrinsèque estimée**,
- une **mesure d'incertitude** (Monte Carlo),
- un **niveau de confiance** (Audit Score),
- un **Pitchbook PDF exportable** (ST-5.2).

**L'outil ne fournit jamais** :
- une prédiction de prix,
- une recommandation d'investissement,
- une garantie de performance.

---

## Modes d'Analyse

### Mode AUTO

| Caractéristique | Description |
|-----------------|-------------|
| **Cible** | Utilisateurs débutants |
| **Hypothèses** | Normatives (système) |
| **Contrôle** | Minimal |
| **Risque** | Faible (garde-fous) |

**Idéal pour** : Screening, apprentissage, comparaisons rapides.

→ Détails : `auto_mode.md`

### Mode EXPERT

| Caractéristique | Description |
|-----------------|-------------|
| **Cible** | Analystes expérimentés |
| **Hypothèses** | Manuelles (utilisateur) |
| **Contrôle** | Total (7 terminaux) |
| **Risque** | Élevé (responsabilité utilisateur) |

**Idéal pour** : Valorisations approfondies, scénarios personnalisés.

→ Détails : `expert_mode.md`

---

## Workflow Standard

```
1. Sélection du ticker (ex: AAPL, MC.PA)
       ↓
2. Choix du mode (AUTO / EXPERT)
       ↓
3. Configuration (si EXPERT)
   - Modèle de valorisation
   - Paramètres de risque
   - Valeur terminale
   - Monte Carlo (optionnel)
       ↓
4. Lancer l'analyse
       ↓
5. Consultation des résultats
   - Synthèse exécutive
   - Preuve de calcul
   - Rapport d'audit
   - Triangulation sectorielle
       ↓
6. Export Pitchbook PDF (optionnel)
```

---

## Onglets de Résultats

| Onglet | Contenu |
|--------|---------|
| **Synthèse Exécutive** | IV, prix, upside, recommandation |
| **Hypothèses** | Paramètres utilisés |
| **Preuve de Calcul** | Étapes Glass Box avec formules |
| **Rapport d'Audit** | Score et alertes |
| **Multiples** | Triangulation sectorielle |
| **Scénarios** | Bull/Base/Bear (si activé) |
| **Monte Carlo** | Distribution (si activé) |
| **Backtest** | Validation historique (si activé) |

---

## Fonctionnalités Clés

### Glass Box V2

Chaque calcul est transparent :
- Formule théorique LaTeX
- Substitution numérique réelle
- Source de chaque variable
- Badge de confiance (Vert/Orange/Rouge)

### Mode Dégradé (ST-4.1)

Si Yahoo Finance échoue :
- Fallback automatique sur données sectorielles
- Bandeau d'avertissement affiché
- Score de confiance réduit

### Pitchbook PDF (ST-5.2)

Export professionnel de 3 pages :
1. Résumé exécutif
2. Preuves de calcul
3. Analyse de risque

---

## Contenu du Dossier

| Fichier | Description |
|---------|-------------|
| `auto_mode.md` | Mode guidé, hypothèses normatives |
| `expert_mode.md` | Mode avancé, 7 terminaux |
| `interpreting_results.md` | Lecture des résultats |

---

## Principe Clé

La qualité d'une valorisation dépend :
- des **hypothèses** retenues,
- de la **méthode** choisie,
- de la **cohérence économique**.

L'utilisateur reste **responsable de l'interprétation finale**.

---

## Prochaine Lecture

- Nouveau ? → `auto_mode.md`
- Expérimenté ? → `expert_mode.md`
- Résultats en main ? → `interpreting_results.md`
