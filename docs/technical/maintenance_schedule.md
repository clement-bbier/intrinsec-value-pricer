# Maintenance Schedule

**Version** : 2.0 — Janvier 2026

Ce document définit le calendrier de maintenance
du projet *Intrinsic Value Pricer*.

---

## Maintenance Continue

### Tests Automatisés

| Fréquence | Action | Outil |
|-----------|--------|-------|
| À chaque commit | Tests de contrats | `pytest tests/contracts/` |
| À chaque PR | Tous les tests | `pytest tests/` |
| Hebdomadaire | Couverture complète | `pytest --cov` |

### Vérifications d'Architecture

| Fréquence | Action | Validation |
|-----------|--------|------------|
| À chaque commit | Imports src/ | `test_architecture_contracts.py` |
| À chaque commit | Type hints | `mypy --strict src/` |
| Mensuelle | Revue de code | Manuelle |

---

## Maintenance des Données

### Multiples Sectoriels

| Fréquence | Action | Source |
|-----------|--------|--------|
| Annuelle | Mise à jour | Damodaran NYU Stern |
| Fichier | `config/sector_multiples.yaml` | |

### Matrice Pays

| Fréquence | Action | Source |
|-----------|--------|--------|
| Semestrielle | Mise à jour Rf | Banques centrales |
| Fichier | `infra/ref_data/country_matrix.py` | |

---

## Maintenance de la Documentation

### Documentation Technique

| Fréquence | Action |
|-----------|--------|
| À chaque feature | Mise à jour `docs/technical/` |
| À chaque sprint | Mise à jour `SPRINT_ROADMAP.md` |
| À chaque correction | Mise à jour `TECHNICAL_DEBT.md` |

### Documentation Méthodologique

| Fréquence | Action |
|-----------|--------|
| À chaque nouvelle méthode | Nouvelle page dans `docs/methodology/` |
| À chaque modification formule | Mise à jour de la page concernée |

---

## Maintenance des Dépendances

### Bibliothèques Python

| Fréquence | Action | Fichier |
|-----------|--------|---------|
| Trimestrielle | Mise à jour mineures | `requirements.txt` |
| Annuelle | Mise à jour majeures | `requirements.txt` |

### Bibliothèques Critiques

| Bibliothèque | Version | Surveillance |
|--------------|---------|--------------|
| `yfinance` | Latest | API changes |
| `streamlit` | >= 1.28 | Breaking changes |
| `pydantic` | >= 2.0 | Migration V2 faite |
| `fpdf2` | >= 2.7 | PDF generation |

---

## Maintenance des Sprints

### État Actuel

| Sprint | Statut | Date |
|--------|--------|------|
| Sprint 1 | ✅ Complété | Janvier 2026 |
| Sprint 2 | ✅ Complété | Janvier 2026 |
| Sprint 3 | ✅ Complété | Janvier 2026 |
| Sprint 4 | ✅ Complété | Janvier 2026 |
| Sprint 5 | ✅ Complété | Janvier 2026 |
| Sprint 6 | Planifié | Q1 2026 |
| Sprint 7 | Planifié | Q2 2026 |

### Prochaine Revue

| Date | Action |
|------|--------|
| Février 2026 | Revue trimestrielle |
| Avril 2026 | Sprint 6 planning |

---

## Métriques de Santé

### Indicateurs Clés

| Métrique | Cible | Actuel |
|----------|-------|--------|
| Tests de contrats | 100% passent | ✅ 51/51 |
| Imports app/ dans src/ | 0 | ✅ 0 |
| Constantes hardcodées | 0 | ✅ 0 |
| Docstrings | > 80% | ✅ ~85% |

### Alertes

| Condition | Action |
|-----------|--------|
| Test échoue | Bloquer le merge |
| Import interdit | Bloquer le merge |
| Dette technique | Documenter dans `TECHNICAL_DEBT.md` |

---

## Contacts

| Rôle | Responsabilité |
|------|----------------|
| Maintainer | Revues de code, releases |
| Contributeur | PRs, documentation |

---

## Historique des Maintenances

| Date | Action | Statut |
|------|--------|--------|
| Janvier 2026 | Sprints 1-5 | ✅ Complété |
| Janvier 2026 | Documentation V2 | ✅ Complété |
| Janvier 2026 | Multiples 2024 | ✅ Complété |
