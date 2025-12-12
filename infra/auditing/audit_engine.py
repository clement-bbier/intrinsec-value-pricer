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
    Moteur d'audit V6.
    Vérifie la cohérence des données et des hypothèses (Sanity Check).
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

        is_manual = (input_source == InputSource.MANUAL)

        # 1. QUALITÉ DONNÉES & SPÉCIFICITÉ
        if is_manual:
            data_penalty = 0.0
            data_items = []
            assump_penalty = 0.0
            assump_items = [{"penalty": 0, "reason": "Inputs validés par l'expert.", "severity": "low"}]
        else:
            data_penalty, data_items = AuditEngine._check_data_quality(financials)
            assump_penalty, assump_items = AuditEngine._check_assumptions_specificity(financials, params)

        data_score = max(0.0, 100.0 + data_penalty)
        assump_score = max(0.0, 100.0 + assump_penalty)

        # 2. STABILITÉ (Critique)
        stab_penalty, stab_items, stability_metric = AuditEngine._check_stability_and_coherence(
            simulation_results, params, financials, tv_ev_ratio
        )
        stability_score = max(0.0, 100.0 + stab_penalty)

        # 3. ADÉQUATION MÉTHODE
        mode_penalty, mode_items = AuditEngine._check_mode_fit(financials, mode)
        mode_score = max(0.0, 100.0 + mode_penalty)

        # 4. SCORING FINAL
        if is_manual:
            # En manuel, la stabilité prime
            raw_score = (stability_score * 0.8) + (mode_score * 0.2)
            context_msg = "Contrôle Cohérence (Mode Expert)"
        elif mode == ValuationMode.MONTE_CARLO:
            # En Monte Carlo, la qualité des données est cruciale
            raw_score = (data_score * 0.25) + (assump_score * 0.35) + (stability_score * 0.30) + (mode_score * 0.10)
            context_msg = "Audit Robustesse (Mode Auto)"
        else:
            raw_score = (data_score * 0.35) + (assump_score * 0.35) + (stability_score * 0.15) + (mode_score * 0.15)
            context_msg = "Audit Standard"

        # Guillotine de sécurité
        if stability_score < 50:
            raw_score = min(raw_score, stability_score)

        final_score = max(0.0, min(100.0, raw_score))

        # 5. FORMATAGE UI
        for d in data_items: d['ui_category'] = 'Qualité Données'
        for d in assump_items: d['ui_category'] = 'Spécificité'
        for d in stab_items: d['ui_category'] = 'Stabilité'
        for d in mode_items: d['ui_category'] = 'Adéquation Méthode'

        all_details = data_items + assump_items + stab_items + mode_items

        # Flags de blocage
        block_mc = (data_score < 45) or (stability_metric < 30)
        block_hist = (data_score < 40)

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

    # --- CHECKERS INTERNES ---

    @staticmethod
    def _check_data_quality(f: CompanyFinancials) -> Tuple[float, List[Dict]]:
        penalty = 0.0
        items = []
        if f.source_fcf == "none":
            return -100.0, [{"penalty": -100, "reason": "FATAL: Aucun flux disponible", "severity": "high"}]
        if f.source_fcf == "simple":
            penalty -= 40
            items.append({"penalty": -40, "reason": "Flux basés sur 1 an seulement", "severity": "high"})
        return penalty, items

    @staticmethod
    def _check_assumptions_specificity(f: CompanyFinancials, p: DCFParameters) -> Tuple[float, List[Dict]]:
        penalty = 0.0
        items = []
        if f.source_growth == "macro":
            penalty -= 40
            items.append({"penalty": -40, "reason": "Croissance générique (PIB)", "severity": "high"})
        if f.source_debt == "sector":
            penalty -= 25
            items.append({"penalty": -25, "reason": "Coût dette sectoriel", "severity": "high"})
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

        # WACC vs g
        ke_approx = p.risk_free_rate + f.beta * p.market_risk_premium
        if ke_approx < p.perpetual_growth_rate + 0.005:
            penalty -= 50
            items.append(
                {"penalty": -50, "reason": "CRITIQUE: WACC proche de g (Explosion Mathématique)", "severity": "high"})

        # TV Weight
        if tv_ev_ratio and tv_ev_ratio > 0.85:
            penalty -= 30
            items.append({"penalty": -30, "reason": "Dépendance Valeur Terminale > 85%", "severity": "medium"})

        return penalty, items, metric

    @staticmethod
    def _check_mode_fit(f: CompanyFinancials, mode: ValuationMode) -> Tuple[float, List[Dict]]:
        penalty = 0.0
        items = []
        if mode == ValuationMode.SIMPLE_FCFF and f.beta > 1.5:
            penalty -= 20
            items.append({"penalty": -20, "reason": "Méthode Simple trop rigide pour High Beta", "severity": "medium"})
        return penalty, items

    @staticmethod
    def _get_rating(score: float) -> str:
        if score >= 90: return "EXCELLENT"
        if score >= 75: return "SOLIDE"
        if score >= 50: return "MITIGÉ"
        return "RISQUÉ"

    @staticmethod
    def _generate_logs(details: List[Dict]) -> List[str]:
        return [f"[{d['penalty']}] {d['reason']}" for d in details]