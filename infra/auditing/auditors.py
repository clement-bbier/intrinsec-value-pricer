import logging
from abc import ABC, abstractmethod
from typing import List, Optional

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


class IValuationAuditor(ABC):
    """
    Interface de base pour les auditeurs de valorisation.
    Implémente le Template Method Pattern : validation commune + validation spécifique.
    """

    def audit(self, result: ValuationResult) -> AuditReport:
        """Point d'entrée principal de l'audit."""
        logs: List[AuditLog] = []
        score = 100.0

        # 1. Audit Qualité des Données (Commun)
        penalty_data, logs_data = self._check_data_quality(result)
        score += penalty_data
        logs.extend(logs_data)

        # 2. Audit Spécifique à la Stratégie (Abstrait)
        penalty_algo, logs_algo = self._check_specific_logic(result)
        score += penalty_algo
        logs.extend(logs_algo)

        # 3. Calcul Final
        final_score = max(0.0, min(100.0, score))
        rating = self._compute_rating(final_score)

        return AuditReport(
            global_score=final_score,
            rating=rating,
            audit_mode=self.__class__.__name__,
            logs=logs,
            breakdown={
                "Data Quality": max(0.0, 100.0 + penalty_data),
                "Algorithm & Assumptions": max(0.0, 100.0 + penalty_algo)
            },
            critical_warning=any(l.severity == "CRITICAL" for l in logs)
        )

    @abstractmethod
    def _check_specific_logic(self, result: ValuationResult) -> tuple[float, List[AuditLog]]:
        """Logique de validation spécifique à implémenter par les sous-classes."""
        pass

    def _check_data_quality(self, result: ValuationResult) -> tuple[float, List[AuditLog]]:
        """Vérifie la cohérence des données financières en entrée."""
        logs = []
        penalty = 0.0
        f = result.financials

        # Si mode manuel, on est plus tolérant sur la source, mais on vérifie les valeurs
        if result.request and result.request.input_source == InputSource.MANUAL:
            logs.append(AuditLog("Data", "INFO", "Source Manuelle : Validation expert présumée.", 0))
            return 0.0, logs

        # Vérifications standards
        if f.total_debt == 0 and f.interest_expense > 0:
            logs.append(AuditLog("Data", "WARN", "Dette nulle mais charges d'intérêts présentes.", -5))
            penalty -= 5

        if f.beta < 0.4 or f.beta > 3.0:
            logs.append(AuditLog("Data", "WARN", f"Beta atypique ({f.beta:.2f}). Vérifier secteur.", -5))
            penalty -= 5

        if f.source_growth == "macro":
            logs.append(AuditLog("Data", "WARN", "Croissance basée sur macro-économie (faible précision).", -10))
            penalty -= 10

        return penalty, logs

    def _compute_rating(self, score: float) -> str:
        if score >= 90: return "AAA (High Confidence)"
        if score >= 75: return "AA (Good)"
        if score >= 60: return "BBB (Investable)"
        if score >= 40: return "BB (Speculative)"
        return "C (Junk / Errors)"


# ==============================================================================
# 1. AUDITEUR STANDARD (DCF Classique & Growth)
# ==============================================================================

class StandardDCFAuditor(IValuationAuditor):
    """
    Auditeur pour les méthodes DCF basées sur l'Enterprise Value (Simple, Fundamental, Growth).
    Focus : WACC, Cohérence Croissance, Poids Terminal Value.
    """

    def _check_specific_logic(self, result: ValuationResult) -> tuple[float, List[AuditLog]]:
        if not isinstance(result, DCFValuationResult):
            return 0.0, [AuditLog("System", "CRITICAL", "Type de résultat incompatible avec StandardDCFAuditor", -100)]

        logs = []
        penalty = 0.0
        p = result.params

        # A. Règle d'Or : WACC vs Croissance Perpétuelle
        spread = result.wacc - p.perpetual_growth_rate
        if spread <= 0:
            logs.append(AuditLog("Logic", "CRITICAL",
                                 f"WACC ({result.wacc:.2%}) <= g ({p.perpetual_growth_rate:.2%}). Modèle invalide.",
                                 -100))
            penalty -= 100
        elif spread < 0.015:
            logs.append(
                AuditLog("Logic", "HIGH", f"Spread WACC-g très faible ({spread:.2%}). Sensibilité extrême.", -20))
            penalty -= 20

        # B. Poids de la Valeur Terminale (TV)
        if result.enterprise_value > 0:
            tv_weight = result.discounted_terminal_value / result.enterprise_value
            if tv_weight > 0.85:
                logs.append(AuditLog("Structure", "HIGH", f"Dépendance critique à la TV ({tv_weight:.1%}).", -15))
                penalty -= 15
            elif tv_weight > 0.70:
                logs.append(
                    AuditLog("Structure", "MEDIUM", f"Poids TV élevé ({tv_weight:.1%}). Standard pour Growth.", -5))
                penalty -= 5

        # C. Cohérence WACC
        if result.wacc < 0.05:
            logs.append(
                AuditLog("Risk", "WARN", f"WACC anormalement bas ({result.wacc:.2%}). Sous-évaluation du risque ?",
                         -10))
            penalty -= 10
        elif result.wacc > 0.15:
            logs.append(AuditLog("Risk", "INFO", f"WACC élevé ({result.wacc:.2%}). Prudence intégrée.", 0))

        return penalty, logs


# ==============================================================================
# 2. AUDITEUR BANCAIRE (DDM)
# ==============================================================================

class BankAuditor(IValuationAuditor):
    """
    Auditeur spécifique pour les banques (DDM).
    Ignore le WACC et l'EBITDA. Focus sur le Ke et les Dividendes.
    """

    def _check_specific_logic(self, result: ValuationResult) -> tuple[float, List[AuditLog]]:
        if not isinstance(result, DDMValuationResult):
            return 0.0, [AuditLog("System", "CRITICAL", "Incompatible BankAuditor", -100)]

        logs = []
        penalty = 0.0
        p = result.params
        f = result.financials

        # A. Validation du Ke (Cost of Equity) uniquement
        # Les banques ont souvent des Betas faibles ou volatils
        if result.cost_of_equity < 0.04:
            logs.append(AuditLog("Risk", "HIGH", f"Coût Equity trop bas ({result.cost_of_equity:.2%}).", -20))
            penalty -= 20

        # B. Politique de Dividende
        if f.last_dividend <= 0:
            logs.append(AuditLog("Data", "CRITICAL", "Banque sans dividende. Modèle DDM inapplicable.", -100))
            penalty -= 100

        # C. Spread Ke vs Growth
        spread = result.cost_of_equity - p.perpetual_growth_rate
        if spread <= 0.01:
            logs.append(AuditLog("Logic", "HIGH", "Spread Ke-g trop faible pour une banque mature.", -25))
            penalty -= 25

        return penalty, logs


# ==============================================================================
# 3. AUDITEUR GRAHAM (Value)
# ==============================================================================

class GrahamAuditor(IValuationAuditor):
    """
    Auditeur pour la formule de Graham.
    Vérifie la positivité des métriques comptables.
    """

    def _check_specific_logic(self, result: ValuationResult) -> tuple[float, List[AuditLog]]:
        if not isinstance(result, GrahamValuationResult):
            return 0.0, [AuditLog("System", "CRITICAL", "Incompatible GrahamAuditor", -100)]

        logs = []
        penalty = 0.0

        # A. Qualité des Actifs
        if result.book_value_used <= 0:
            logs.append(
                AuditLog("Data", "CRITICAL", "Capitaux Propres (Book Value) négatifs. Graham impossible.", -100))
            penalty -= 100

        # B. Rentabilité
        if result.eps_used <= 0:
            logs.append(AuditLog("Data", "CRITICAL", "EPS négatif. Entreprise non rentable.", -100))
            penalty -= 100

        # C. Cohérence Prix
        if result.intrinsic_value_per_share > 0:
            implied_pe = result.intrinsic_value_per_share / result.eps_used
            if implied_pe > 50:
                logs.append(
                    AuditLog("Logic", "WARN", f"Résultat Graham implique un P/E > 50 ({implied_pe:.1f}). Douteux.",
                             -10))
                penalty -= 10

        return penalty, logs