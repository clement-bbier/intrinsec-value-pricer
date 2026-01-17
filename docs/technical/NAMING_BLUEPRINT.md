# NAMING_BLUEPRINT.md — Plan de Nommage Standardise

## Vue d'Ensemble

Ce document etablit la correspondance entre l'ancien monde (legacy) et le nouveau monde (refactorise), facilitant la migration progressive et assurant la coherence semantique.

---

## 1. Mapping Fichiers : Ancien → Nouveau

| Ancien Fichier | Nouveau Fichier | Responsabilite |
|----------------|-----------------|---------------|
| `app/main.py` | `app/main.py` | Point d'entree principal (migration progressive) |
| `app/workflow.py` | `app/workflow.py` | Orchestrateur logique (enrichi) |
| `app/ui_components/ui_inputs_expert.py` | `app/ui/expert_terminals/` | Terminaux experts (7 classes) |
| `app/ui_components/ui_kpis.py` | `app/ui/result_tabs/` | Onglets de resultats (8 onglets) |
| `core/models.py` | `core/models/` | 7 fichiers specialises |
| `core/texts.py` | `core/i18n/fr/` | Internationalisation structuree |

---

## 2. Mapping Classes : Ancien → Nouveau

### 2.1 Terminaux Experts

| Ancienne Fonction | Nouvelle Classe | Pattern |
|------------------|-----------------|---------|
| `render_standard_fcff_inputs()` | `FCFFStandardTerminal` | Template Method |
| `render_fundamental_fcff_inputs()` | `FCFFNormalizedTerminal` | Template Method |
| `render_growth_fcff_inputs()` | `FCFFGrowthTerminal` | Template Method |
| `render_fcfe_inputs()` | `FCFETerminal` | Template Method |
| `render_ddm_inputs()` | `DDMTerminal` | Template Method |
| `render_rim_inputs()` | `RIMBankTerminal` | Template Method |
| `render_graham_inputs()` | `GrahamValueTerminal` | Template Method |

### 2.2 Onglets de Resultats

| Ancienne Fonction | Nouvelle Classe | Pattern |
|------------------|-----------------|---------|
| `render_executive_summary()` | `InputsSummaryTab` | Template Method |
| `display_valuation_details()` | `CalculationProofTab` | Template Method |
| `display_audit_report()` | `AuditReportTab` | Template Method |
| N/A | `PeerMultiplesTab` | Template Method |
| N/A | `SOTPBreakdownTab` | Template Method |
| N/A | `ScenarioAnalysisTab` | Template Method |
| N/A | `HistoricalBacktestTab` | Template Method |
| N/A | `MonteCarloDistributionTab` | Template Method |

### 2.3 Modeles de Donnees

| Ancienne Classe | Nouvelles Classes | Pattern |
|----------------|-------------------|---------|
| `ValuationRequest` | `ValuationRequest` (enrichi) | Data Class |
| `ValuationResult` | `ValuationResult` (enrichi) | Data Class |
| `DCFParameters` | `DCFParameters` (enrichi) | Data Class |
| `ScenarioParameters` | `ScenarioParameters` | Data Class |
| `AuditReport` | `AuditReport` | Data Class |

---

## 3. Mapping Fonctions : Ancien → Nouveau

### 3.1 Fonctions de Calcul

| Ancienne Fonction | Nouvelle Fonction | Module |
|------------------|-------------------|---------|
| `safe_factory_params()` | `build_dcf_parameters()` | `shared_widgets.py` |
| `calculate_wacc()` | `calculate_wacc()` | `financial_math.py` |
| `calculate_cost_of_equity_capm()` | `calculate_cost_of_equity_capm()` | `financial_math.py` |

### 3.2 Fonctions UI

| Ancienne Fonction | Nouvelle Fonction | Module |
|------------------|-------------------|---------|
| `render_expert_form()` | `render()` | `expert_terminal.py` |
| `display_kpis()` | `render()` | `result_tab.py` |

---

## 4. Mapping Constantes : Ancien → Nouveau

### 4.1 Constantes Systeme

| Ancienne Constante | Nouvelle Constante | Module |
|-------------------|---------------------|---------|
| `_DEFAULT_TICKER` | `CommonTexts.DEFAULT_TICKER` | `i18n/fr/ui/common.py` |
| `_DEFAULT_PROJECTION_YEARS` | `SystemDefaults.DEFAULT_PROJECTION_YEARS` | `core/config/constants.py` |
| `_MIN_PROJECTION_YEARS` | `SystemDefaults.MIN_PROJECTION_YEARS` | `core/config/constants.py` |
| `_MAX_PROJECTION_YEARS` | `SystemDefaults.MAX_PROJECTION_YEARS` | `core/config/constants.py` |
| `_MIN_MC_SIMULATIONS` | `MonteCarloDefaults.MIN_SIMULATIONS` | `core/config/constants.py` |
| `_MAX_MC_SIMULATIONS` | `MonteCarloDefaults.MAX_SIMULATIONS` | `core/config/constants.py` |
| `_DEFAULT_MC_SIMULATIONS` | `MonteCarloDefaults.DEFAULT_SIMULATIONS` | `core/config/constants.py` |

### 4.2 Seuils d'Audit

| Ancienne Constante | Nouvelle Constante | Module |
|-------------------|---------------------|---------|
| `PENALTY_CRITICAL` | `AuditPenalties.CRITICAL` | `core/config/constants.py` |
| `PENALTY_HIGH` | `AuditPenalties.HIGH` | `core/config/constants.py` |
| `PENALTY_MEDIUM` | `AuditPenalties.MEDIUM` | `core/config/constants.py` |
| `PENALTY_LOW` | `AuditPenalties.LOW` | `core/config/constants.py` |
| `PENALTY_INFO` | `AuditPenalties.INFO` | `core/config/constants.py` |

---

## 5. Mapping Textes : Ancien → Nouveau

### 5.1 Textes UI

| Ancien Texte | Nouvelle Constante | Module |
|--------------|---------------------|---------|
| `"Lancer la valorisation"` | `ExpertTerminalTexts.BTN_CALCULATE` | `i18n/fr/ui/expert.py` |
| `"Horizon de projection"` | `ExpertTerminalTexts.INP_PROJ_YEARS` | `i18n/fr/ui/expert.py` |
| `"Taux sans risque"` | `ExpertTerminalTexts.INP_RF` | `i18n/fr/ui/expert.py` |
| `"Croissance moyenne"` | `ExpertTerminalTexts.INP_GROWTH_G` | `i18n/fr/ui/expert.py` |

### 5.2 Messages d'Erreur

| Ancien Message | Nouvelle Constante | Module |
|----------------|---------------------|---------|
| `"Erreur de calcul"` | `ErrorTexts.CALCULATION_ERROR` | `i18n/fr/backend/errors.py` |
| `"Donnees indisponibles"` | `ErrorTexts.DATA_UNAVAILABLE` | `i18n/fr/backend/errors.py` |

---

## 6. Conventions de Migration

### 6.1 Principes Generaux

1. **Pas de Breaking Changes** : L'API publique reste stable
2. **Migration Progressive** : Nouveau systeme ajoute en parallele
3. **Fallback Automatique** : Retour a l'ancien systeme en cas d'erreur
4. **Logging Complet** : Trace des migrations reussies/echouees

### 6.2 Strategie de Migration

```python
# Pattern de migration adopte
def migrate_to_new_system():
    try:
        # Essai du nouveau systeme
        new_result = use_new_system()
        logger.info("[Migration] Nouveau systeme reussi")
        return new_result
    except Exception as e:
        # Fallback vers l'ancien
        logger.warning(f"[Migration] Fallback vers ancien: {str(e)}")
        old_result = use_old_system()
        return old_result
```

### 6.3 Validation Post-Migration

Apres chaque migration, verifier :
- Tests passent (119/119)
- Imports fonctionnels
- UI s'affiche correctement
- Resultats identiques

---

## 7. Etat de la Migration (Sprint 1)

### 7.1 Termine

- [x] Terminaux experts (7/7 classes)
- [x] Onglets de resultats (8/8 onglets)
- [x] Modeles de donnees (7/7 fichiers)
- [x] Constantes centralisees
- [x] Textes i18n structures
- [x] Workflow migre (avec fallback)
- [x] CONTRIBUTING.md cree
- [x] Logs standardises
- [x] Tests passent (119/119)

### 7.2 En Cours

- [ ] Suppression fichiers legacy (Sprint 1.4)
- [ ] Docstrings Google Style systematique (Sprint 2)
- [ ] Type hints 100% (Sprint 2)

### 7.3 A Venir

- [ ] Glass Box 2.0 (Sprint 3)
- [ ] i18n YAML (Sprint 4)
- [ ] UX ameliorations (Sprint 5)
- [ ] PDF export (Sprint 6)

---

*Ce document evolue avec la migration. Derniere mise a jour : 2026-01-17*