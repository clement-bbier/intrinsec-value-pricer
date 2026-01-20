# GOVERNANCE & ANTI-DÉRIVE

## Intrinsic Value Pricer — Technical Governance Charter

**Statut** : Normatif — Document de référence  
**Version** : 2.0 — Janvier 2026  
**Portée** : Ensemble du projet (code, documentation, usage)

---

## 1. Objectif du Document

Ce document définit les **règles de gouvernance techniques et méthodologiques non négociables**
du projet *Intrinsic Value Pricer*.

Il a pour objectifs :

- empêcher toute dérive fonctionnelle ou méthodologique
- verrouiller les règles d'extension du moteur
- garantir la traçabilité, l'auditabilité et la reproductibilité
- assurer l'alignement avec les standards institutionnels  
  *(CFA Institute, Damodaran, Model Risk Management)*

Ce document prévaut sur toute interprétation implicite du code ou de la documentation.

---

## 2. Principes Immuables

Les principes suivants sont **absolus** et **non négociables** :

| Principe | Description |
|----------|-------------|
| **Une méthode = une source** | Chaque méthode dans `src/valuation/strategies/` |
| **Une feature = une version** | Changelog explicite |
| **Un calcul = une trace** | Glass Box V2 obligatoire |
| **Un score = une formule** | Audit transparent |
| **Aucune logique implicite** | Tout est documenté |
| **Responsabilité claire** | AUTO vs EXPERT |

Toute violation invalide la conformité du projet.

---

## 3. Étanchéité Architecturale

### Règle d'Or

```
src/  ──────────> Zéro dépendance vers app/ ou streamlit
infra/ ─────────> Peut importer src/, jamais app/
app/  ──────────> Importe src/ et infra/
```

### Validation

```bash
# Test automatisé
pytest tests/contracts/test_architecture_contracts.py -v

# Vérification manuelle
grep -r "import streamlit" src/
# Doit retourner 0 résultat
```

---

## 4. Moteur de Valorisation

Le moteur de valorisation est :

- **Déterministe** par construction
- **Centralisé** via `run_valuation()`
- **Typé** strictement (Pydantic)

**Point d'entrée unique** :

```python
from src.valuation.engines import run_valuation

result = run_valuation(request, financials, params)
```

L'instanciation directe d'une stratégie hors moteur est **formellement interdite**.

---

## 5. Référentiel Officiel des Méthodes

Les méthodes autorisées sont exclusivement celles :

| Critère | Localisation |
|---------|--------------|
| Déclarées | `ValuationMode` enum |
| Implémentées | `src/valuation/strategies/` |
| Enregistrées | `src/valuation/registry.py` |
| Documentées | `docs/methodology/` |

Toute méthode non listée est **inexistante par définition**.

---

## 6. Glass Box V2 — Traçabilité Obligatoire

Toute méthode de valorisation **doit** produire :

| Élément | Obligatoire |
|---------|-------------|
| `CalculationStep[]` | Oui |
| `theoretical_formula` (LaTeX) | Oui |
| `actual_calculation` | Oui (ST-2.1) |
| `variables_map` | Oui (ST-2.1) |
| `VariableInfo.source` | Oui (ST-3.3) |

**Aucun calcul implicite n'est autorisé.**  
**Une valeur sans trace est considérée comme invalide.**

---

## 7. Monte Carlo — Statut Normatif

Monte Carlo est une **extension probabiliste**, et **non une méthode de valorisation**.

Règles non négociables :

| Règle | Description |
|-------|-------------|
| Scope | Paramètres d'entrée uniquement |
| Logique | Reste déterministe |
| Pivot | P50 sans stochasticité |
| Autonomie | Jamais de valeur IV autonome |

Toute utilisation contraire constitue une dérive méthodologique.

---

## 8. Audit & Confidence Score

L'audit est une **méthode normalisée** au même titre que la valorisation.

| Règle | Description |
|-------|-------------|
| Formule explicite | Visible dans le code |
| Pondérations visibles | `AuditWeights` |
| Piliers indépendants | 4 piliers |
| Pénalités traçables | Chaque -X points justifié |

Le moteur d'audit est **unique et centralisé** (`infra/auditing/`).

---

## 9. Mode Dégradé (ST-4.1)

En cas de panne API, le système **doit** :

| Étape | Action |
|-------|--------|
| 1 | Détecter l'échec (timeout, données aberrantes) |
| 2 | Basculer sur fallback sectoriel |
| 3 | Afficher bandeau d'avertissement |
| 4 | Réduire le score de confiance |
| 5 | Logger l'événement (QuantLogger) |

Le fallback sectoriel est défini dans `config/sector_multiples.yaml`.

---

## 10. Diagnostic Pédagogique (ST-4.2)

Toute erreur technique **doit** être traduite en conseil métier.

| Composant | Rôle |
|-----------|------|
| `DiagnosticEvent` | Événement structuré |
| `FinancialContext` | Explication du risque |
| `get_pedagogical_message()` | Message complet |

---

## 11. Responsabilité Utilisateur

### Mode AUTO

| Aspect | Description |
|--------|-------------|
| Hypothèses | Normatives (système) |
| Proxies | Autorisés |
| Audit | Conservateur |
| Responsabilité | Système |

### Mode EXPERT

| Aspect | Description |
|--------|-------------|
| Hypothèses | Utilisateur |
| Données | Présumées exactes |
| Audit | Strict |
| Responsabilité | Utilisateur |

**Aucune ambiguïté entre les deux modes n'est tolérée.**

---

## 12. Providers de Données

Toute source de données **doit** implémenter l'interface `DataProvider`.

Interdictions :

| Interdit | Raison |
|----------|--------|
| Logique financière | Réservée à `src/` |
| Calibration implicite | Doit être explicite |
| Hypothèse métier | Réservée aux stratégies |

Tout provider hors contrat est interdit.

---

## 13. Interface Utilisateur (UI)

L'UI est un **canal de restitution uniquement**.

Interdictions formelles :

| Interdit | Alternative |
|----------|-------------|
| Calcul financier | `src/computation/` |
| Règle économique | `src/valuation/strategies/` |
| Décision méthodologique | `src/valuation/registry.py` |
| Modification implicite | Mode EXPERT explicite |

Toute logique métier dans l'UI est une violation de la gouvernance.

---

## 14. Documentation & Source de Vérité

| Type | Localisation | Statut |
|------|--------------|--------|
| Code | `src/valuation/strategies/` | Canonique |
| Registry | `src/valuation/registry.py` | Canonique |
| Textes | `locales/*.yaml` | Canonique (ST-5.1) |
| Docs MD | `docs/` | Explicatif, non contractuel |

Toute divergence est considérée comme une erreur documentaire.

---

## 15. Règles d'Extension

Toute extension du projet implique :

| Étape | Obligatoire |
|-------|-------------|
| Version explicite | Oui |
| Documentation associée | Oui |
| Tests de contrats | Oui |
| Validation des invariants | Oui |

---

## 16. Logging Institutionnel (ST-4.2)

Format obligatoire via `QuantLogger` :

```
[DOMAIN][LEVEL] Ticker: XXX | Key1: Val1 | Key2: Val2
```

Exemple :

```
[VALUATION][SUCCESS] Ticker: AAPL | Model: FCFF_STANDARD | IV: 185.20 | AuditScore: 88.5%
```

---

## 17. Internationalisation (ST-5.1)

| Règle | Description |
|-------|-------------|
| Source | `locales/*.yaml` |
| Accès | `TextRegistry.get()` ou `t()` |
| Placeholders | Format `{variable}` |
| Fallback | FR si clé manquante |

---

## 18. Export PDF (ST-5.2)

Le Pitchbook PDF **doit** contenir :

| Page | Contenu |
|------|---------|
| 1 | Résumé exécutif (IV, prix, upside, audit) |
| 2 | Preuves de calcul (formules, paramètres) |
| 3 | Analyse de risque (MC, scénarios) |

Performance cible : < 5 secondes.

---

## 19. Métriques de Conformité

| Métrique | Cible | Validation |
|----------|-------|------------|
| Imports app/ dans src/ | 0 | `test_architecture_contracts.py` |
| Tests de contrats | 51+ passent | `pytest tests/contracts/` |
| Constantes hardcodées | 0 | `src/config/constants.py` |
| Fichiers avec docstrings | 85%+ | Revue manuelle |

---

## 20. Violations et Sanctions

Toute violation de cette charte :

1. Invalide la conformité de la version
2. Doit être corrigée avant merge
3. Est documentée dans les issues GitHub

La gouvernance est appliquée via les tests de contrats automatisés.
