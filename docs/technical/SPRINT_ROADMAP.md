# SPRINT ROADMAP — Intrinsic Value Pricer

**Version** : 3.0  
**Date** : Janvier 2026  
**Statut** : Sprints 1-5 COMPLÉTÉS

---

## État Actuel de l'Architecture

### Structure Validée (Post-Sprint 5)

```
intrinsec-value-pricer/
├── src/                           # Logique métier pure
│   ├── domain/models/             # 9 fichiers Pydantic
│   │   ├── enums.py
│   │   ├── glass_box.py           # VariableInfo + CalculationStep
│   │   ├── scenarios.py
│   │   ├── company.py
│   │   ├── dcf_inputs.py
│   │   ├── audit.py
│   │   ├── request_response.py
│   │   └── pitchbook.py           # ST-5.2 NEW
│   ├── i18n/                      # Internationalisation
│   │   ├── __init__.py
│   │   ├── text_registry.py       # ST-5.1 NEW
│   │   └── fr/                    # Classes Python (legacy)
│   ├── config/                    # Constantes centralisées
│   ├── interfaces/                # Abstractions UI
│   ├── computation/               # Fonctions mathématiques
│   ├── valuation/                 # Moteur + 9 Stratégies
│   ├── reporting/                 # ST-5.2 NEW
│   │   └── pdf_generator.py       # Pitchbook FPDF2
│   ├── diagnostics.py             # ST-4.2 Enhanced
│   └── quant_logger.py            # ST-4.2 NEW
│
├── app/                           # Couche présentation
│   ├── ui/
│   │   ├── base/                  # Classes abstraites
│   │   ├── expert/terminals/      # 7 terminaux + factory
│   │   ├── results/               # Orchestrator + onglets
│   │   └── components/            # Charts (@st.fragment)
│   └── adapters/                  # Streamlit adapters
│
├── infra/                         # Infrastructure
│   ├── auditing/
│   ├── data_providers/            # ST-4.1 Mode Dégradé
│   ├── ref_data/
│   │   └── sector_fallback.py     # ST-4.1 Enhanced
│   └── macro/
│
├── locales/                       # ST-5.1 NEW
│   └── fr.yaml                    # Textes français YAML
│
├── config/
│   └── sector_multiples.yaml      # ST-4.1 Enhanced
│
└── tests/                         # 51+ tests
    ├── unit/
    ├── contracts/
    ├── integration/
    └── e2e/
```

---

## Historique des Sprints

### Sprint 1 : Souveraineté Technique & Hygiène ✅

**Objectif** : Éradiquer les reliquats, gouvernance Type-Safe

| Tâche | Description | Statut |
|-------|-------------|--------|
| ST 1.1 | CONTRIBUTING.md avec étanchéité src/ | ✅ |
| ST 1.2 | Typage strict, alias financiers | ✅ |
| ST 1.3 | Invariants mathématiques (Golden Dataset) | ✅ |

**Livrables** :
- `mypy --strict src/` = 0 erreur
- Zéro import streamlit dans `src/`

---

### Sprint 2 : Rigueur Financière & Glass Box V2 ✅

**Objectif** : Chaque calcul = preuve auditable

| Tâche | Description | Statut |
|-------|-------------|--------|
| ST 2.1 | CalculationStep enrichi (actual_calculation, variables_map) | ✅ |
| ST 2.2 | Formules LaTeX par stratégie | ✅ |
| ST 2.3 | Migration constantes hardcodées → config/ | ✅ |

**Livrables** :
- `VariableInfo` avec source et is_override
- Formules dans tous les CalculationStep
- `src/config/constants.py` centralisé

---

### Sprint 3 : UX Pitchbook & Performance ✅

**Objectif** : Outil fluide selon standards McKinsey/Damodaran

| Tâche | Description | Statut |
|-------|-------------|--------|
| ST 3.1 | Séquençage "Logical Path" dans factory.py | ✅ |
| ST 3.2 | @st.fragment pour charts (anti-flicker) | ✅ |
| ST 3.3 | Badges de confiance dans step_renderer.py | ✅ |
| ST 3.4 | render_equity_bridge_inputs() partagé | ✅ |

**Livrables** :
- `AnalyticalTier` : DEFENSIVE → RELATIVE → FUNDAMENTAL
- 5 fonctions chart avec @st.fragment
- Badges vert/orange/rouge sur chaque étape
- Cache Monte Carlo dans orchestrator.py

---

### Sprint 4 : Résilience & Intelligence ✅

**Objectif** : Outil indestructible face aux pannes API

| Tâche | Description | Statut |
|-------|-------------|--------|
| ST 4.1 | Fallback sectoriel + Mode Dégradé | ✅ |
| ST 4.2 | Diagnostic pédagogique (FinancialContext) | ✅ |
| ST 4.2 | QuantLogger institutionnel | ✅ |

**Livrables** :
- `SectorFallbackResult` avec confidence_score
- `DataProviderStatus` dans yahoo_provider.py
- `render_degraded_mode_banner()` dans ui_kpis.py
- `FinancialContext` dans DiagnosticEvent
- `src/quant_logger.py` complet

---

### Sprint 5 : Internationalisation & Rendu Premium ✅

**Objectif** : Pitchbook PDF professionnel

| Tâche | Description | Statut |
|-------|-------------|--------|
| ST 5.1 | locales/fr.yaml + TextRegistry | ✅ |
| ST 5.2 | PitchbookData DTO + FPDF2 Generator | ✅ |

**Livrables** :
- `locales/fr.yaml` avec 200+ clés
- `src/i18n/text_registry.py` avec placeholders
- `src/domain/models/pitchbook.py` (DTO)
- `src/reporting/pdf_generator.py` (3 pages)

---

## Sprints Futurs (Backlog)

### Sprint 6 : Tests E2E Complets

| Tâche | Description | Priorité |
|-------|-------------|----------|
| ST 6.1 | Tests Playwright/Selenium sur l'UI | MOYENNE |
| ST 6.2 | Golden Dataset étendu (50 tickers) | MOYENNE |
| ST 6.3 | Benchmarks de performance | BASSE |

### Sprint 7 : Multi-Langue

| Tâche | Description | Priorité |
|-------|-------------|----------|
| ST 7.1 | locales/en.yaml complet | MOYENNE |
| ST 7.2 | Sélecteur de langue dans sidebar | MOYENNE |
| ST 7.3 | Documentation traduite | BASSE |

### Sprint 8 : Analytics & Monitoring

| Tâche | Description | Priorité |
|-------|-------------|----------|
| ST 8.1 | Dashboard de logs QuantLogger | BASSE |
| ST 8.2 | Métriques d'usage anonymisées | BASSE |
| ST 8.3 | Alertes sur dégradations | BASSE |

---

## Métriques de Qualité

| Métrique | Avant Sprints | Après Sprint 5 |
|----------|---------------|----------------|
| Tests | 8 | 51+ |
| Imports app/ dans src/ | 16 | 0 |
| Constantes hardcodées | ~15 | 0 |
| Docstrings | ~40% | ~85% |
| Type Hints | ~50% | ~95% |
| Fichiers avec @st.fragment | 0 | 6 |
| Couverture i18n YAML | 0% | 100% (FR) |

---

## Critères de Qualité "Zéro Dette"

- [x] `mypy --strict src/` = 0 erreur
- [x] Aucun import streamlit dans `src/`
- [x] 51+ tests de contrats passent
- [x] Glass Box V2 opérationnel
- [x] Mode Dégradé fonctionnel
- [x] PDF exportable < 5 secondes
- [x] TextRegistry charge fr.yaml
