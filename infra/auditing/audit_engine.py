"""
infra/auditing/audit_engine.py

Audit Engine — Chapitre 6
Audit comme méthode normalisée et auditable.

Responsabilités :
- Router vers l’auditeur métier
- Agréger les piliers d’incertitude
- Appliquer les pondérations (mode × modèle)
- Produire un AuditReport entièrement explicable
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, List

# --- STREAMLIT OPTIMIZATION (Optionnel) ---
# Décommenter la ligne suivante pour activer le cache d'audit
# import streamlit as st

from core.models import (
    ValuationResult,
    ValuationMode,
    AuditReport,
    AuditLog,
    AuditPillar,
    AuditPillarScore,
    AuditScoreBreakdown,
    InputSource
)

from infra.auditing.auditors import IValuationAuditor, StandardValuationAuditor

logger = logging.getLogger(__name__)


# ==============================================================================
# PONDÉRATIONS NORMATIVES — MODE × MÉTHODE
# ==============================================================================

# Invariants par MODE
MODE_WEIGHTS = {
    InputSource.AUTO: {
        AuditPillar.DATA_CONFIDENCE: 0.30,
        AuditPillar.ASSUMPTION_RISK: 0.30,
        AuditPillar.MODEL_RISK: 0.25,
        AuditPillar.METHOD_FIT: 0.15,
    },
    InputSource.MANUAL: {  # EXPERT
        AuditPillar.DATA_CONFIDENCE: 0.10,  # Faible impact (l'expert sait)
        AuditPillar.ASSUMPTION_RISK: 0.50,  # Fort impact (responsabilité utilisateur)
        AuditPillar.MODEL_RISK: 0.20,
        AuditPillar.METHOD_FIT: 0.20,
    }
}


class AuditEngine:
    """
    Moteur d'Audit (Static Service).
    Orchestre la vérification de conformité et le scoring.
    """

    # Pour activer le cache, décommenter : @st.cache_data(ttl=3600)
    @staticmethod
    def compute_audit(
        result: ValuationResult,
        auditor: Optional[IValuationAuditor] = None
    ) -> AuditReport:
        """
        Point d'entrée unique de l'audit.

        Args:
            result: Le résultat de valorisation à auditer.
            auditor: (Optionnel) L'implémentation de l'auditeur.
                     Si None, utilise StandardValuationAuditor par défaut.
        """
        try:
            # --------------------------------------------------------
            # 0. INJECTION DE DÉPENDANCE (FIX CRITIQUE)
            # --------------------------------------------------------
            # Si main.py n'envoie pas d'auditeur, on prend celui par défaut.
            if auditor is None:
                auditor = StandardValuationAuditor()

            # --------------------------------------------------------
            # 1. ANALYSE PAR PILIER (Délégation)
            # --------------------------------------------------------
            # L'auditeur spécialisé scanne les piliers un par un
            raw_pillars = auditor.audit_pillars(result)

            # --------------------------------------------------------
            # 2. APPLICATION DES PONDÉRATIONS (Business Logic)
            # --------------------------------------------------------
            # Sélection du profil de pondération selon la source (AUTO/MANUAL)
            source_mode = result.request.input_source if result.request else InputSource.AUTO
            weights_profile = MODE_WEIGHTS.get(source_mode, MODE_WEIGHTS[InputSource.AUTO])

            weighted_pillars: Dict[AuditPillar, AuditPillarScore] = {}
            total_score = 0.0

            for pillar, raw_score_obj in raw_pillars.items():
                weight = weights_profile.get(pillar, 0.0)

                # Calcul de la contribution pondérée
                contribution = raw_score_obj.score * weight

                # Mise à jour de l'objet Score
                weighted_pillars[pillar] = AuditPillarScore(
                    pillar=pillar,
                    score=raw_score_obj.score,
                    weight=weight,
                    contribution=contribution,
                    diagnostics=raw_score_obj.diagnostics
                )

                total_score += contribution

            # --------------------------------------------------------
            # 3. SÉCURITÉ DE CALCUL (BLOCAGE DES FONCTIONS INSTABLES)
            # --------------------------------------------------------
            # On extrait les scores spécifiques pour la gestion des risques
            model_risk_score = weighted_pillars.get(AuditPillar.MODEL_RISK).score if AuditPillar.MODEL_RISK in weighted_pillars else 100.0
            data_conf_score = weighted_pillars.get(AuditPillar.DATA_CONFIDENCE).score if AuditPillar.DATA_CONFIDENCE in weighted_pillars else 100.0

            # --- LOGIQUE DE SÉCURITÉ ---
            # Si le modèle diverge (g >= WACC), l'auditeur met le MODEL_RISK à 0.
            # On bloque alors les simulations de Monte Carlo qui seraient fausses.
            block_mc = model_risk_score <= 0.0
            block_hist = data_conf_score < 40.0

            # --------------------------------------------------------
            # 4. CONSTRUCTION DU RAPPORT FINAL
            # --------------------------------------------------------
            rating = AuditEngine._compute_rating(total_score)

            # Agrégation des logs pour affichage linéaire
            all_logs = AuditEngine._collect_logs(weighted_pillars)

            # Contrat de sortie : Rapport immuable
            report = AuditReport(
                global_score=total_score,
                rating=rating,
                audit_mode=source_mode.value,
                logs=all_logs,
                breakdown={p.value: ps.score for p, ps in weighted_pillars.items()},
                pillar_breakdown=AuditScoreBreakdown(
                    pillars=weighted_pillars,
                    aggregation_formula="Sum(Score * Weight)",
                    total_score=total_score
                ),
                block_monte_carlo=block_mc,
                block_history=block_hist,
                critical_warning=any(l.severity == "CRITICAL" for l in all_logs)
            )

            logger.info(
                f"[Audit] Completed | Score={total_score:.1f}/100 | Rating={rating}"
            )
            return report

        except Exception as e:
            logger.error(f"[Audit] Critical Failure: {e}", exc_info=True)
            return AuditEngine._fallback_report(str(e))

    # ------------------------------------------------------------------
    # HELPERS INTERNES
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_rating(score: float) -> str:
        """Échelle de notation standardisée."""
        if score >= 90:
            return "AAA (High Confidence)"
        if score >= 75:
            return "AA (Good)"
        if score >= 60:
            return "BBB (Moderate)"
        if score >= 40:
            return "BB (Speculative)"
        return "C (Low Confidence)"

    @staticmethod
    def _collect_logs(
        pillars: Dict[AuditPillar, AuditPillarScore]
    ) -> List[AuditLog]:
        """Aplatit la structure hiérarchique pour l'affichage des logs."""
        logs: List[AuditLog] = []
        for ps in pillars.values():
            for msg in ps.diagnostics:
                # On détermine la sévérité implicite selon le message
                severity = "CRITICAL" if "CRITICAL" in msg.upper() else "INFO"
                if "WARN" in msg.upper():
                    severity = "WARNING"

                logs.append(
                    AuditLog(
                        category=ps.pillar.value,
                        severity=severity,
                        message=msg,
                        penalty=0 # La pénalité est déjà dans le score
                    )
                )
        return logs

    @staticmethod
    def _fallback_report(error: str) -> AuditReport:
        """Circuit Breaker en cas de panne de l'auditeur."""
        return AuditReport(
            global_score=0.0,
            rating="Error",
            audit_mode="SystemFailure",
            logs=[
                AuditLog(
                    category="System",
                    severity="CRITICAL",
                    message=f"Audit failure: {error}",
                    penalty=-100
                )
            ],
            breakdown={},
            pillar_breakdown=None,
            critical_warning=True,
            block_monte_carlo=True,
            block_history=True
        )