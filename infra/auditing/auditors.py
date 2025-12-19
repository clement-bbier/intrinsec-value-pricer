import logging
from abc import ABC, abstractmethod
from typing import List

from core.models import (
    ValuationResult,
    DCFValuationResult,
    DDMValuationResult,
    GrahamValuationResult,
    AuditReport,
    AuditLog,
    InputSource
)

logger = logging.getLogger(__name__)


# ==============================================================================
# AUDIT ENGINE — CHAPITRE 5 (AUTO / EXPERT)
#
# Règles :
# - Le moteur d’audit est unique
# - Aucune règle métier ne dépend du mode
# - Seule la pondération de l’audit "Data Quality" change
# - Les aberrations sont TOUJOURS bloquantes
# ==============================================================================


class IValuationAuditor(ABC):
    """
    Template Method Pattern.
    L’audit est toujours exécuté intégralement.
    Seule la pondération dépend de la responsabilité utilisateur.
    """

    def audit(self, result: ValuationResult) -> AuditReport:
        logs: List[AuditLog] = []
        score = 100.0

        # ------------------------------------------------------------------
        # 1. DATA QUALITY AUDIT (pondération variable)
        # ------------------------------------------------------------------
        penalty_data, logs_data = self._check_data_quality(result)
        score += penalty_data
        logs.extend(logs_data)

        # ------------------------------------------------------------------
        # 2. LOGIQUE FINANCIÈRE (STRICTE, TOUJOURS)
        # ------------------------------------------------------------------
        penalty_logic, logs_logic = self._check_specific_logic(result)
        score += penalty_logic
        logs.extend(logs_logic)

        # ------------------------------------------------------------------
        # 3. FINALISATION
        # ------------------------------------------------------------------
        final_score = max(0.0, min(100.0, score))
        rating = self._compute_rating(final_score)

        return AuditReport(
            global_score=final_score,
            rating=rating,
            audit_mode=self.__class__.__name__,
            logs=logs,
            breakdown={
                "Data Quality": max(0.0, 100.0 + penalty_data),
                "Logic & Financial Consistency": max(0.0, 100.0 + penalty_logic)
            },
            critical_warning=any(l.severity == "CRITICAL" for l in logs)
        )

    # ----------------------------------------------------------------------
    # DATA QUALITY — RESPONSABILITÉ UTILISATEUR
    # ----------------------------------------------------------------------
    def _check_data_quality(self, result: ValuationResult) -> tuple[float, List[AuditLog]]:
        logs: List[AuditLog] = []
        penalty = 0.0
        f = result.financials

        is_expert = (
            result.request is not None
            and result.request.input_source == InputSource.MANUAL
        )

        if is_expert:
            logs.append(
                AuditLog(
                    category="Data",
                    severity="INFO",
                    message=(
                        "Mode EXPERT : qualité des données affichée à titre informatif. "
                        "La responsabilité incombe à l’utilisateur."
                    ),
                    penalty=0
                )
            )

        # --- Règles communes (toujours évaluées) ---
        if f.total_debt == 0 and f.interest_expense > 0:
            logs.append(
                AuditLog(
                    "Data", "WARN",
                    "Dette nulle mais charges d'intérêts présentes.",
                    -5
                )
            )
            if not is_expert:
                penalty -= 5

        if f.beta < 0.4 or f.beta > 3.0:
            logs.append(
                AuditLog(
                    "Data", "WARN",
                    f"Beta atypique ({f.beta:.2f}). Vérifier la cohérence sectorielle.",
                    -5
                )
            )
            if not is_expert:
                penalty -= 5

        if f.source_growth == "macro":
            logs.append(
                AuditLog(
                    "Data", "WARN",
                    "Croissance issue de proxy macro-économique (faible précision).",
                    -10
                )
            )
            if not is_expert:
                penalty -= 10

        return penalty, logs

    # ----------------------------------------------------------------------
    # LOGIQUE MÉTIER — STRICTE
    # ----------------------------------------------------------------------
    @abstractmethod
    def _check_specific_logic(
        self,
        result: ValuationResult
    ) -> tuple[float, List[AuditLog]]:
        pass

    # ----------------------------------------------------------------------
    # RATING
    # ----------------------------------------------------------------------
    def _compute_rating(self, score: float) -> str:
        if score >= 90:
            return "AAA (High Confidence)"
        if score >= 75:
            return "AA (Good)"
        if score >= 60:
            return "BBB (Investable)"
        if score >= 40:
            return "BB (Speculative)"
        return "C (Invalid / High Risk)"


# ==============================================================================
# STANDARD DCF AUDITOR
# ==============================================================================

class StandardDCFAuditor(IValuationAuditor):

    def _check_specific_logic(self, result: ValuationResult):
        if not isinstance(result, DCFValuationResult):
            return 0.0, [
                AuditLog(
                    "System", "CRITICAL",
                    "Type de résultat incompatible avec StandardDCFAuditor.",
                    -100
                )
            ]

        logs: List[AuditLog] = []
        penalty = 0.0
        p = result.params

        spread = result.wacc - p.perpetual_growth_rate

        if spread <= 0:
            logs.append(
                AuditLog(
                    "Logic", "CRITICAL",
                    f"WACC ({result.wacc:.2%}) ≤ g ({p.perpetual_growth_rate:.2%}). Modèle invalide.",
                    -100
                )
            )
            penalty -= 100

        elif spread < 0.015:
            logs.append(
                AuditLog(
                    "Logic", "HIGH",
                    f"Spread WACC − g très faible ({spread:.2%}). Sensibilité extrême.",
                    -20
                )
            )
            penalty -= 20

        if result.enterprise_value > 0:
            tv_weight = result.discounted_terminal_value / result.enterprise_value
            if tv_weight > 0.85:
                logs.append(
                    AuditLog(
                        "Structure", "HIGH",
                        f"Dépendance excessive à la valeur terminale ({tv_weight:.1%}).",
                        -15
                    )
                )
                penalty -= 15

        return penalty, logs


# ==============================================================================
# BANK / DDM AUDITOR
# ==============================================================================

class BankAuditor(IValuationAuditor):

    def _check_specific_logic(self, result: ValuationResult):
        if not isinstance(result, DDMValuationResult):
            return 0.0, [
                AuditLog(
                    "System", "CRITICAL",
                    "Type de résultat incompatible avec BankAuditor.",
                    -100
                )
            ]

        logs: List[AuditLog] = []
        penalty = 0.0
        p = result.params
        f = result.financials

        if result.cost_of_equity < 0.04:
            logs.append(
                AuditLog(
                    "Risk", "HIGH",
                    f"Coût des fonds propres trop faible ({result.cost_of_equity:.2%}).",
                    -20
                )
            )
            penalty -= 20

        if f.last_dividend <= 0:
            logs.append(
                AuditLog(
                    "Data", "CRITICAL",
                    "Banque sans dividende : modèle DDM invalide.",
                    -100
                )
            )
            penalty -= 100

        spread = result.cost_of_equity - p.perpetual_growth_rate
        if spread <= 0.01:
            logs.append(
                AuditLog(
                    "Logic", "HIGH",
                    "Spread Ke − g trop faible pour une banque mature.",
                    -25
                )
            )
            penalty -= 25

        return penalty, logs


# ==============================================================================
# GRAHAM AUDITOR
# ==============================================================================

class GrahamAuditor(IValuationAuditor):

    def _check_specific_logic(self, result: ValuationResult):
        if not isinstance(result, GrahamValuationResult):
            return 0.0, [
                AuditLog(
                    "System", "CRITICAL",
                    "Type de résultat incompatible avec GrahamAuditor.",
                    -100
                )
            ]

        logs: List[AuditLog] = []
        penalty = 0.0

        if result.eps_used <= 0:
            logs.append(
                AuditLog(
                    "Data", "CRITICAL",
                    "EPS négatif : entreprise non rentable.",
                    -100
                )
            )
            penalty -= 100

        implied_pe = (
            result.intrinsic_value_per_share / result.eps_used
            if result.eps_used > 0 else 0
        )

        if implied_pe > 50:
            logs.append(
                AuditLog(
                    "Logic", "WARN",
                    f"Résultat Graham implique un P/E > 50 ({implied_pe:.1f}).",
                    -10
                )
            )
            penalty -= 10

        return penalty, logs
