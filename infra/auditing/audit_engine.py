from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np
from core.models import CompanyFinancials, DCFParameters, ValuationMode, InputSource


@dataclass
class AuditReport:
    global_score: float
    rating: str
    breakdown: Dict[str, float]
    ui_details: List[Dict]
    terminal_logs: List[str]
    data_quality_score: float
    stability_metric: float
    block_monte_carlo: bool = False
    block_history: bool = False
    critical_warning: bool = False
    audit_mode_description: str = ""


class AuditEngine:
    """
    Moteur d'audit V6 (Contextual & Sanity Check).
    """

    @staticmethod
    def compute_audit(
            financials: CompanyFinancials,
            params: DCFParameters,
            simulation_results: Optional[List[float]] = None,
            hist_coverage: Optional[float] = None,
            mode: ValuationMode = ValuationMode.SIMPLE_FCFF,
            tv_ev_ratio: Optional[float] = None,
            input_source: InputSource = InputSource.AUTO
    ) -> AuditReport:

        is_manual = (input_source == InputSource.MANUAL)

        # --- 1. CALCUL DES SCORES (PILOTÉ PAR LA SOURCE) ---

        if is_manual:
            data_penalty = 0.0
            data_items = []
            assump_penalty = 0.0
            assump_items = [{"penalty": 0, "reason": "✅ Inputs validés par l'expert.", "severity": "low"}]
        else:
            data_penalty, data_items = AuditEngine._check_data_quality(financials)
            assump_penalty, assump_items = AuditEngine._check_assumptions_specificity(financials, params)

        data_score = max(0.0, 100.0 + data_penalty)
        assump_score = max(0.0, 100.0 + assump_penalty)

        # Stabilité (CRITIQUE dans tous les modes)
        stab_penalty, stab_items, stability_metric = AuditEngine._check_stability_and_coherence(
            simulation_results, params, financials, tv_ev_ratio
        )
        stability_score = max(0.0, 100.0 + stab_penalty)

        # Adéquation Méthode
        mode_penalty, mode_items = AuditEngine._check_mode_fit(financials, mode, stability_metric, hist_coverage)
        mode_score = max(0.0, 100.0 + mode_penalty)

        # --- 2. PONDÉRATION ADAPTATIVE ---

        context_msg = ""

        if is_manual:
            W_DATA, W_ASSUMP, W_STABILITY, W_MODE = 0.0, 0.0, 0.80, 0.20
            raw_score = (stability_score * W_STABILITY) + (mode_score * W_MODE)
            context_msg = "Contrôle technique de cohérence (Mode Expert)."

        elif mode == ValuationMode.MONTE_CARLO:
            W_DATA, W_ASSUMP, W_STABILITY, W_MODE = 0.25, 0.35, 0.30, 0.10
            raw_score = (data_score * W_DATA) + (assump_score * W_ASSUMP) + (stability_score * W_STABILITY) + (
                        mode_score * W_MODE)
            context_msg = "Audit de Qualité des Données & Robustesse (Mode Auto)."

        else:
            W_DATA, W_ASSUMP, W_STABILITY, W_MODE = 0.35, 0.35, 0.15, 0.15
            raw_score = (data_score * W_DATA) + (assump_score * W_ASSUMP) + (stability_score * W_STABILITY) + (
                        mode_score * W_MODE)
            context_msg = "Audit Standard (Qualité Données de Marché)."

        # --- 3. GUILLOTINE ---
        if stability_score < 50:
            raw_score = min(raw_score, stability_score)

        final_score = max(0.0, min(100.0, raw_score))

        # --- 4. FORMATTAGE FINAL ---

        for d in data_items: d['ui_category'] = 'Qualité Données'
        for d in assump_items: d['ui_category'] = 'Spécificité'
        for d in stab_items: d['ui_category'] = 'Stabilité'
        for d in mode_items: d['ui_category'] = 'Adéquation Méthode'

        all_details = data_items + assump_items + stab_items + mode_items
        severity_map = {"high": 0, "medium": 1, "low": 2}
        all_details.sort(key=lambda x: severity_map.get(x.get("severity", "low"), 3))

        block_mc = (data_score < 45) or (stability_metric < 30)
        block_hist = (data_score < 40) or (hist_coverage is not None and hist_coverage < 0.60)

        return AuditReport(
            global_score=final_score,
            rating=AuditEngine._get_rating(final_score),
            breakdown={
                "Données": data_score,
                "Spécificité": assump_score,
                "Stabilité": stability_score,
                "Méthode": mode_score
            },
            ui_details=all_details,
            terminal_logs=AuditEngine._generate_logs(all_details),
            data_quality_score=data_score,
            stability_metric=stability_metric,
            block_monte_carlo=block_mc,
            block_history=block_hist,
            critical_warning=(final_score < 50),
            audit_mode_description=context_msg
        )

    # -------------------------------------------------------------------------
    # VÉRIFICATEURS DÉTAILLÉS (LOGIQUE COMPLÈTE)
    # -------------------------------------------------------------------------

    @staticmethod
    def _check_data_quality(f: CompanyFinancials) -> Tuple[float, List[Dict]]:
        penalty = 0.0
        items = []

        if f.source_fcf == "none": return -100.0, [
            {"penalty": -100, "reason": "FATAL : Aucun Cash Flow disponible", "severity": "high"}]

        if f.source_fcf == "simple":
            penalty -= 40
            items.append({"penalty": -40, "reason": "Flux basés sur 1 seul bilan annuel", "severity": "high"})
        elif f.source_fcf == "weighted":
            penalty -= 10
            items.append({"penalty": -10, "reason": "Flux lissés", "severity": "low"})

        if f.total_debt == 0 and f.interest_expense > 0:
            penalty -= 20
            items.append({"penalty": -20, "reason": "Incohérence Bilan : Intérêts payés sans dette faciale",
                          "severity": "medium"})

        return penalty, items

    @staticmethod
    def _check_assumptions_specificity(f: CompanyFinancials, p: DCFParameters) -> Tuple[float, List[Dict]]:
        penalty = 0.0
        items = []

        if f.source_growth == "macro":
            penalty -= 40
            items.append(
                {"penalty": -40, "reason": "CRITIQUE : Croissance générique (PIB) utilisée.", "severity": "high"})
        elif f.source_growth == "cagr":
            penalty -= 20
            items.append({"penalty": -20, "reason": "Croissance rétroviseur (CAGR)", "severity": "medium"})

        if f.source_debt == "sector":
            penalty -= 25
            items.append({"penalty": -25, "reason": "CRITIQUE : Coût de la dette sectoriel (Non spécifique)",
                          "severity": "high"})

        if f.beta == 1.0 and f.sector != "Unknown":
            penalty -= 10
            items.append(
                {"penalty": -10, "reason": "Beta neutre (1.0) suspect. Manque de spécificité.", "severity": "low"})

        return penalty, items

    @staticmethod
    def _check_stability_and_coherence(
            sim_results: Optional[List[float]],
            p: DCFParameters,
            f: CompanyFinancials,
            tv_ev_ratio: Optional[float]
    ) -> Tuple[float, List[Dict], float]:
        penalty = 0.0
        items = []
        metric = 100.0

        if tv_ev_ratio is not None and tv_ev_ratio > 0.0:
            if tv_ev_ratio > 0.85:
                penalty -= 40
                items.append({
                    "penalty": -40, "reason": "VULNÉRABILITÉ : Valeur Terminale > 85% de l'EV.", "severity": "high"
                })
            elif tv_ev_ratio > 0.70:
                penalty -= 15
                items.append({
                    "penalty": -15, "reason": "Forte dépendance à la Valeur Terminale (>70% EV).", "severity": "medium"
                })

        ke_approx = p.risk_free_rate + f.beta * p.market_risk_premium
        if ke_approx < p.perpetual_growth_rate + 0.01:
            penalty -= 30
            items.append({"penalty": -30, "reason": "Danger Mathématique : WACC proche de g (Explosion de la TV)",
                          "severity": "high"})

        if sim_results:
            values = np.array(sim_results)
            mean = np.mean(values)
            if mean > 0:
                cv = np.std(values) / mean
                if cv > 0.40: penalty -= 50; metric = 10.0; items.append(
                    {"penalty": -50, "reason": "Instabilité Monte Carlo Extrême (CV > 40%)", "severity": "high"})

        return penalty, items, metric

    @staticmethod
    def _check_mode_fit(f: CompanyFinancials, mode: ValuationMode, stability_metric: float,
                        hist_cov: Optional[float]) -> Tuple[float, List[Dict]]:
        penalty = 0.0
        items = []

        if f.fcf_last and f.fcf_fundamental_smoothed:
            deviation = abs(f.fcf_last - f.fcf_fundamental_smoothed) / abs(
                f.fcf_fundamental_smoothed) if f.fcf_fundamental_smoothed != 0 else 0
            if deviation > 0.30 and mode == ValuationMode.SIMPLE_FCFF:
                penalty -= 30
                items.append(
                    {"penalty": -30, "reason": "DANGER : Année en cours anormale. Méthode Simple déconseillée.",
                     "severity": "high"})

        if mode == ValuationMode.SIMPLE_FCFF and f.beta > 1.3:
            penalty -= 20
            items.append({"penalty": -20, "reason": "Méthode Simple trop rigide pour profil High Beta (>1.3)",
                          "severity": "medium"})

        elif mode == ValuationMode.MONTE_CARLO and (f.source_growth == "macro" or f.source_debt == "sector"):
            penalty -= 40
            items.append(
                {"penalty": -40, "reason": "Simulation inutile : Inputs génériques (GIGO)", "severity": "high"})

        return penalty, items

    @staticmethod
    def _get_rating(score: float) -> str:
        if score >= 95: return "EXCELLENT (A+)"
        if score >= 85: return "TRÈS SOLIDE (A)"
        if score >= 75: return "FIABLE (B)"
        if score >= 60: return "MODÉRÉ (C)"
        if score >= 45: return "SPÉCULATIF (D)"
        return "DANGEREUX (F)"

    @staticmethod
    def _generate_logs(details: List[Dict]) -> List[str]:
        logs = []
        for d in details:
            logs.append(f"[{d['penalty']} pts] {d['reason']}")
        return logs