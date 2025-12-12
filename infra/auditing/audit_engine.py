from typing import List, Dict, Optional, Tuple
import numpy as np

from core.models import (
    CompanyFinancials,
    DCFParameters,
    ValuationMode,
    InputSource,
    AuditReport,
    AuditLog
)


class AuditEngine:
    """
    Moteur d'audit institutionnel.
    Génère désormais des logs positifs (preuves de fiabilité) et négatifs (risques).
    """

    @staticmethod
    def compute_audit(
            financials: CompanyFinancials,
            params: DCFParameters,
            simulation_results: Optional[List[float]] = None,
            tv_ev_ratio: Optional[float] = None,
            mode: ValuationMode = ValuationMode.SIMPLE_FCFF,
            input_source: InputSource = InputSource.AUTO
    ) -> AuditReport:

        logs: List[AuditLog] = []
        is_manual = (input_source == InputSource.MANUAL)

        # --- 1. AUDIT DES DONNÉES ---
        score_data = 100.0
        if not is_manual:
            penalty, data_logs = AuditEngine._check_data_quality(financials)
            score_data = max(0.0, 100.0 + penalty)
            logs.extend(data_logs)
        else:
            # En manuel, on valide explicitement
            score_data = 100.0
            logs.append(AuditLog("Données", "success", "Inputs validés manuellement par l'expert.", 0.0))

        # --- 2. AUDIT DE COHÉRENCE MATHÉMATIQUE ---
        penalty_math, math_logs = AuditEngine._check_math_coherence(params, financials, tv_ev_ratio)
        score_math = max(0.0, 100.0 + penalty_math)
        logs.extend(math_logs)

        # --- 3. AUDIT SPÉCIFIQUE MÉTHODE ---
        penalty_mode, mode_logs, stability_metric = AuditEngine._check_method_fit(
            mode, financials, params, simulation_results
        )
        score_mode = max(0.0, 100.0 + penalty_mode)
        logs.extend(mode_logs)

        # --- 4. CALCUL DU SCORE GLOBAL (Indicatif backend, moins visible UI) ---
        if is_manual:
            global_score = (score_math * 0.70) + (score_mode * 0.30)
            audit_desc = "Cohérence Expert"
        elif mode == ValuationMode.MONTE_CARLO:
            global_score = (score_data * 0.30) + (score_math * 0.30) + (score_mode * 0.40)
            audit_desc = "Robustesse Simulation"
        else:
            global_score = (score_data * 0.50) + (score_math * 0.30) + (score_mode * 0.20)
            audit_desc = "Qualité Standard"

        if score_math < 50:
            global_score = min(global_score, score_math)

        # --- 5. FORMATAGE ---
        # On ne trie plus par sévérité brute, mais on garde l'ordre logique des catégories dans l'UI

        block_mc = (score_data < 50 and not is_manual) or (stability_metric < 40)

        return AuditReport(
            global_score=round(global_score, 1),
            rating=AuditEngine._get_rating(global_score),
            audit_mode=audit_desc,
            logs=logs,
            breakdown={
                "Données": round(score_data, 1),
                "Cohérence": round(score_math, 1),
                "Méthode": round(score_mode, 1)
            },
            block_monte_carlo=block_mc,
            block_history=(score_data < 40),
            critical_warning=(global_score < 50)
        )

    # -------------------------------------------------------------------------
    # RÈGLES DÉTAILLÉES (AVEC BRANCHES POSITIVES)
    # -------------------------------------------------------------------------

    @staticmethod
    def _check_data_quality(f: CompanyFinancials) -> Tuple[float, List[AuditLog]]:
        penalty = 0.0
        logs = []

        # 1. Source FCF
        if f.source_fcf == "none":
            penalty -= 100
            logs.append(AuditLog("Données", "critical", "FATAL : Aucun Cash Flow disponible.", -100))
        elif f.source_fcf == "simple":
            penalty -= 30
            logs.append(AuditLog("Données", "medium", "Source : FCF Annuel Unique (Risque Cyclicité).", -30))
        elif f.source_fcf == "weighted":
            logs.append(AuditLog("Données", "success", "Source : FCF Lissé sur 5 ans (Robuste).", 0))
        elif f.source_fcf == "ttm":
            logs.append(AuditLog("Données", "success", "Source : FCF TTM (À jour).", 0))

        # 2. Croissance
        if f.source_growth == "macro":
            penalty -= 40
            logs.append(AuditLog("Données", "high", "Croissance : Générique (PIB) - Manque de spécificité.", -40))
        elif f.source_growth == "analysts":
            logs.append(AuditLog("Données", "success", "Croissance : Consensus Analystes.", 0))
        elif f.source_growth == "cagr":
            logs.append(AuditLog("Données", "success", "Croissance : Historique (CAGR).", 0))

        # 3. Dette
        if f.source_debt == "sector":
            penalty -= 20
            logs.append(AuditLog("Données", "medium", "Coût Dette : Sectoriel (Générique).", -20))
        elif f.source_debt == "synthetic":
            logs.append(AuditLog("Données", "success", "Coût Dette : Synthétique (Basé sur ICR réel).", 0))

        # 4. Intégrité Bilan
        if f.total_debt == 0 and f.interest_expense > 0:
            penalty -= 15
            logs.append(AuditLog("Données", "low", "Bilan : Intérêts payés sans dette faciale.", -15))
        else:
            logs.append(AuditLog("Données", "success", "Bilan : Cohérence Dette/Intérêts.", 0))

        return penalty, logs

    @staticmethod
    def _check_math_coherence(p: DCFParameters, f: CompanyFinancials, tv_ev_ratio: Optional[float]) -> Tuple[
        float, List[AuditLog]]:
        penalty = 0.0
        logs = []

        # WACC vs g
        ke_approx = p.risk_free_rate + f.beta * p.market_risk_premium
        if ke_approx <= p.perpetual_growth_rate:
            penalty -= 100
            logs.append(AuditLog("Cohérence", "critical", "Mathématique : WACC <= g (Convergence Impossible).", -100))
        elif ke_approx < p.perpetual_growth_rate + 0.01:
            penalty -= 50
            logs.append(AuditLog("Cohérence", "high", "Mathématique : Spread WACC-g trop faible (<1%).", -50))
        else:
            spread = ke_approx - p.perpetual_growth_rate
            logs.append(AuditLog("Cohérence", "success", f"Mathématique : Spread WACC-g sain ({spread:.1%}).", 0))

        # Poids Terminal
        if tv_ev_ratio is not None:
            if tv_ev_ratio > 0.85:
                penalty -= 30
                logs.append(
                    AuditLog("Cohérence", "high", f"Structure Valeur : Dépendance TV critique ({tv_ev_ratio:.0%}).",
                             -30))
            elif tv_ev_ratio > 0.75:
                penalty -= 10
                logs.append(
                    AuditLog("Cohérence", "medium", f"Structure Valeur : Dépendance TV élevée ({tv_ev_ratio:.0%}).",
                             -10))
            else:
                logs.append(
                    AuditLog("Cohérence", "success", f"Structure Valeur : Équilibrée (TV={tv_ev_ratio:.0%}).", 0))

        return penalty, logs

    @staticmethod
    def _check_method_fit(
            mode: ValuationMode,
            f: CompanyFinancials,
            p: DCFParameters,
            sim_results: Optional[List[float]]
    ) -> Tuple[float, List[AuditLog], float]:

        penalty = 0.0
        logs = []
        stability = 100.0

        if mode == ValuationMode.SIMPLE_FCFF:
            if f.beta > 1.4:
                penalty -= 20
                logs.append(
                    AuditLog("Méthode", "medium", "Profil : Beta élevé (>1.4). Méthode Simple trop rigide.", -20))
            else:
                logs.append(AuditLog("Méthode", "success", "Profil : Compatible Méthode Simple.", 0))

        elif mode == ValuationMode.MONTE_CARLO:
            if sim_results:
                values = np.array(sim_results)
                mean = np.mean(values)
                if mean > 0:
                    cv = np.std(values) / mean
                    if cv > 0.50:
                        penalty -= 50
                        stability = 20.0
                        logs.append(
                            AuditLog("Méthode", "high", f"Stabilité : Convergence critique (CV={cv:.2f}).", -50))
                    elif cv > 0.30:
                        penalty -= 20
                        stability = 60.0
                        logs.append(AuditLog("Méthode", "medium", f"Stabilité : Dispersion forte (CV={cv:.2f}).", -20))
                    else:
                        logs.append(
                            AuditLog("Méthode", "success", f"Stabilité : Convergence robuste (CV={cv:.2f}).", 0))

        return penalty, logs, stability

    @staticmethod
    def _get_rating(score: float) -> str:
        if score >= 90: return "A"
        if score >= 75: return "B"
        if score >= 50: return "C"
        if score >= 30: return "D"
        return "F"