"""
infra/auditing/auditors.py
AUDITEUR INSTITUTIONNEL — VERSION V8. 1 (SOLID & CLEAN CODE)
Rôle : Analyse multidimensionnelle de la fiabilité des valorisations.
Architecture : Interface Segregation + Liskov Substitution.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from core.models import (
    ValuationResult, DCFValuationResult, RIMValuationResult, GrahamValuationResult,
    AuditLog, AuditPillar, AuditPillarScore, InputSource
)

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. INTERFACE & BASE ABSTRAITE (SOLID :  Interface Segregation)
# ==============================================================================

class IValuationAuditor(ABC):
    """Interface imposant la structure de scoring et de couverture."""

    @abstractmethod
    def audit_pillars(self, result:  ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        """Exécute l'audit complet par pilier."""
        pass

    @abstractmethod
    def get_max_potential_checks(self) -> int:
        """Retourne le nombre total de tests programmés pour ce modèle."""
        pass


class BaseAuditor(IValuationAuditor):
    """Socle commun de tests transverses (Données et Macro)."""

    # =========================================================================
    # CONSTANTES DE PÉNALITÉ (Barème Institutionnel)
    # =========================================================================
    PENALTY_CRITICAL = 100.0
    PENALTY_HIGH = 35.0
    PENALTY_MEDIUM = 15.0
    PENALTY_LOW = 5.0

    # =========================================================================
    # MÉTHODES UTILITAIRES
    # =========================================================================

    def _create_log(self, category: str, severity: str, message: str, penalty: float = 0.0) -> AuditLog:
        """Factory method pour créer un AuditLog de manière homogène."""
        return AuditLog(category=category, severity=severity, message=message, penalty=penalty)

    # =========================================================================
    # AUDIT TRANSVERSE : DATA CONFIDENCE (Tests 1-4)
    # =========================================================================

    def _audit_data_confidence(self, result: ValuationResult) -> Tuple[float, List[AuditLog], int]:
        """
        Audit du socle de données.
        Retourne :  (score, logs, nombre_de_checks)
        """
        logs:  List[AuditLog] = []
        score = 100.0
        f = result.financials
        is_expert = result.request.input_source == InputSource.MANUAL if result.request else False
        checks = 0

        # --- Test 1 : Beta (Cohérence) ---
        checks += 1
        if f.beta is None:
            logs.append(self._create_log("Data", "WARNING", "Beta manquant.", -self.PENALTY_MEDIUM))
            if not is_expert:
                score -= self.PENALTY_MEDIUM
        elif not (0.4 <= f.beta <= 3.0):
            logs.append(self._create_log("Data", "WARNING", f"Beta atypique ({f.beta:.2f})", -self.PENALTY_LOW))
            score -= self. PENALTY_LOW

        # --- Test 2 : Solvabilité (ICR) ---
        checks += 1
        ebit = f.ebit_ttm or 0.0
        if ebit > 0 and f.interest_expense > 0:
            icr = ebit / f.interest_expense
            if icr < 1.5:
                logs.append(self._create_log("Data", "WARNING", f"Solvabilité fragile (ICR:  {icr:.2f} < 1.5)", -self.PENALTY_MEDIUM))
                score -= self. PENALTY_MEDIUM

        # --- Test 3 : Cash vs MCap (Net-Net) ---
        checks += 1
        if f.market_cap > 0 and f. cash_and_equivalents > f.market_cap:
            logs.append(self._create_log("Data", "CRITICAL", "Anomalie : Trésorerie > Capitalisation (Situation Net-Net)", -self.PENALTY_CRITICAL))
            score -= self.PENALTY_CRITICAL

        # --- Test 4 : Liquidité (Small-Cap) ---
        checks += 1
        if f.market_cap < 250_000_000:
            logs.append(self._create_log("Data", "WARNING", "Segment Small-Cap :  Risque de liquidité et volatilité.", -self.PENALTY_LOW))
            score -= self. PENALTY_LOW

        return max(0.0, score), logs, checks

    # =========================================================================
    # AUDIT TRANSVERSE : MACRO INVARIANTS (Tests 5-6)
    # =========================================================================

    def _audit_macro_invariants(self, params) -> Tuple[float, List[str], int]:
        """
        Audit des hypothèses macroéconomiques.
        Retourne : (ajustement_score, messages, nombre_de_checks)
        """
        score_adj = 0.0
        logs: List[str] = []
        checks = 0

        # --- Test 5 : Convergence Perpétuelle ---
        checks += 1
        g_perp = params.perpetual_growth_rate or 0.0
        rf = params.risk_free_rate or 0.0
        if g_perp > rf:
            logs.append(f"Divergence macro :  g perpétuel ({g_perp:. 1%}) > Taux sans risque ({rf:.1%}).")
            score_adj -= self.PENALTY_MEDIUM

        # --- Test 6 : Plancher du Taux Sans Risque ---
        checks += 1
        if rf < 0.01:
            logs.append("Paramétrage Rf < 1% : Risque de survalorisation mécanique.")
            score_adj -= self.PENALTY_LOW

        return score_adj, logs, checks


# ==============================================================================
# 2. AUDITEURS SPÉCIALISÉS (SOLID :  Liskov Substitution)
# ==============================================================================

class DCFAuditor(BaseAuditor):
    """Auditeur spécialisé pour les modèles de flux de trésorerie (12 tests)."""

    def get_max_potential_checks(self) -> int:
        return 12

    def audit_pillars(self, result: DCFValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        p, f = result.params, result.financials
        pillars:  Dict[AuditPillar, AuditPillarScore] = {}

        # =====================================================================
        # PILIER 1 : DATA CONFIDENCE (Tests 1-4 + Test 7)
        # =====================================================================
        data_score, data_logs, d_checks = self._audit_data_confidence(result)

        # Test 7 : Levier financier
        d_checks += 1
        ebit = f.ebit_ttm or 0.0
        if ebit > 0 and (f.total_debt / ebit) > 4.0:
            data_logs.append(self._create_log("Data", "WARNING", "Levier financier excessif (> 4x EBIT).", -self.PENALTY_MEDIUM))
            data_score -= self.PENALTY_MEDIUM

        pillars[AuditPillar.DATA_CONFIDENCE] = AuditPillarScore(
            pillar=AuditPillar.DATA_CONFIDENCE,
            score=max(0.0, data_score),
            diagnostics=[log.message for log in data_logs],
            check_count=d_checks
        )

        # =====================================================================
        # PILIER 2 : ASSUMPTION RISK (Tests 5-6 + Tests 8-9)
        # =====================================================================
        m_adj, m_logs, m_checks = self._audit_macro_invariants(p)
        a_score = 100.0 + m_adj
        a_checks = m_checks

        # Test 8 :  Taux d'investissement
        a_checks += 1
        if f.capex and f.depreciation_and_amortization:
            if abs(f.capex) < f.depreciation_and_amortization * 0.8:
                m_logs.append("Déficit de réinvestissement : Capex < 80% des dotations aux amortissements.")
                a_score -= self.PENALTY_MEDIUM

        # Test 9 : Croissance agressive
        a_checks += 1
        if (p.fcf_growth_rate or 0.0) > 0.20:
            m_logs.append(f"Taux de croissance g ({p.fcf_growth_rate:.1%}) hors normes normatives.")
            a_score -= self.PENALTY_HIGH

        pillars[AuditPillar.ASSUMPTION_RISK] = AuditPillarScore(
            pillar=AuditPillar.ASSUMPTION_RISK,
            score=max(0.0, a_score),
            diagnostics=m_logs,
            check_count=a_checks
        )

        # =====================================================================
        # PILIER 3 : MODEL RISK (Tests 10-12)
        # =====================================================================
        model_logs:  List[str] = []
        model_score = 100.0
        model_checks = 0

        # Test 10 :  WACC minimum
        model_checks += 1
        if result.wacc < 0.06:
            model_logs.append(f"Taux d'actualisation WACC ({result.wacc:. 1%}) excessivement bas.")
            model_score -= self.PENALTY_MEDIUM

        # Test 11 : Concentration TV
        model_checks += 1
        if result.enterprise_value > 0 and result.discounted_terminal_value:
            tv_weight = result.discounted_terminal_value / result. enterprise_value
            if tv_weight > 0.90:
                model_logs.append(f"Concentration de valeur critique :  {tv_weight:.1%} repose sur la TV.")
                model_score -= self.PENALTY_HIGH

        # Test 12 :  Gordon Convergence
        model_checks += 1
        if (p.perpetual_growth_rate or 0.0) >= result.wacc:
            model_score = 0.0
            model_logs. append("Instabilité mathématique : Taux g >= WACC.")

        pillars[AuditPillar.MODEL_RISK] = AuditPillarScore(
            pillar=AuditPillar.MODEL_RISK,
            score=max(0.0, model_score),
            diagnostics=model_logs,
            check_count=model_checks
        )

        # =====================================================================
        # PILIER 4 : METHOD FIT (Neutre pour DCF)
        # =====================================================================
        pillars[AuditPillar.METHOD_FIT] = AuditPillarScore(
            pillar=AuditPillar.METHOD_FIT,
            score=100.0,
            check_count=1
        )

        return pillars


class RIMAuditor(BaseAuditor):
    """Auditeur spécialisé pour le Residual Income Model (8 tests)."""

    def get_max_potential_checks(self) -> int:
        return 8

    def audit_pillars(self, result: RIMValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        f, p = result.financials, result.params
        pillars: Dict[AuditPillar, AuditPillarScore] = {}

        # =====================================================================
        # PILIER 1 : DATA CONFIDENCE (Tests 1-4 avec neutralisation sectorielle)
        # =====================================================================
        data_score, raw_logs, d_checks = self._audit_data_confidence(result)
        refined_logs:  List[AuditLog] = []

        for log in raw_logs:
            if "Trésorerie > Capitalisation" in log.message:
                # Neutralisation sectorielle pour les banques
                data_score += self. PENALTY_CRITICAL
                refined_logs.append(self._create_log("Data", "INFO", "Note sectorielle : Trésorerie élevée (Standard Bancaire).", 0))
            else:
                refined_logs.append(log)

        pillars[AuditPillar.DATA_CONFIDENCE] = AuditPillarScore(
            pillar=AuditPillar.DATA_CONFIDENCE,
            score=min(100.0, data_score),
            diagnostics=[log.message for log in refined_logs],
            check_count=d_checks
        )

        # =====================================================================
        # PILIER 2 : ASSUMPTION RISK (Tests 5-6)
        # =====================================================================
        a_logs:  List[str] = []
        a_score = 100.0
        a_checks = 0

        # Test 5 : Persistance (Omega)
        a_checks += 1
        omega = p.exit_multiple_value or 0.60
        if omega > 0.95:
            a_logs.append("Hypothèse de persistance des surprofits (ω) statistiquement extrême.")
            a_score -= self.PENALTY_HIGH

        # Test 6 : Soutenabilité Payout
        a_checks += 1
        payout = f.dividends_total_calculated / (f.net_income_ttm or 1.0)
        if payout > 1.0:
            a_logs.append(f"Payout Ratio ({payout:.1%}) > 100% : risque d'érosion des fonds propres.")
            a_score -= self.PENALTY_MEDIUM

        pillars[AuditPillar.ASSUMPTION_RISK] = AuditPillarScore(
            pillar=AuditPillar. ASSUMPTION_RISK,
            score=max(0.0, a_score),
            diagnostics=a_logs,
            check_count=a_checks
        )

        # =====================================================================
        # PILIER 3 : METHOD FIT (Tests 7-8)
        # =====================================================================
        fit_logs: List[str] = []
        fit_score = 100.0
        fit_checks = 0

        # Test 7 : Spread ROE-Ke
        fit_checks += 1
        if f.eps_ttm and f.book_value_per_share and f.book_value_per_share > 0:
            roe = f.eps_ttm / f.book_value_per_share
            if abs(roe - result.cost_of_equity) < 0.01:
                fit_logs.append("Spread ROE-Ke quasi nul :  absence de création de richesse additionnelle.")
                fit_score -= self.PENALTY_LOW

        # Test 8 :  Ratio P/B
        fit_checks += 1
        if f.market_cap and f.book_value:
            pb_ratio = f.market_cap / f.book_value
            if pb_ratio > 8.0:
                fit_logs.append(f"Ratio P/B élevé ({pb_ratio:.1f}x) : le modèle RIM perd en pertinence.")
                fit_score -= self.PENALTY_MEDIUM

        pillars[AuditPillar.METHOD_FIT] = AuditPillarScore(
            pillar=AuditPillar.METHOD_FIT,
            score=max(0.0, fit_score),
            diagnostics=fit_logs,
            check_count=fit_checks
        )

        # =====================================================================
        # PILIER 4 : MODEL RISK (Neutre pour RIM)
        # =====================================================================
        pillars[AuditPillar. MODEL_RISK] = AuditPillarScore(
            pillar=AuditPillar.MODEL_RISK,
            score=100.0,
            check_count=1
        )

        return pillars


class GrahamAuditor(BaseAuditor):
    """Auditeur spécialisé pour la valeur intrinsèque Graham (4 tests)."""

    def get_max_potential_checks(self) -> int:
        return 4

    def audit_pillars(self, result: GrahamValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        f, p = result.financials, result.params
        pillars: Dict[AuditPillar, AuditPillarScore] = {}

        # =====================================================================
        # PILIER 1 : DATA CONFIDENCE (Tests 1-4)
        # =====================================================================
        data_score, data_logs, d_checks = self._audit_data_confidence(result)

        pillars[AuditPillar.DATA_CONFIDENCE] = AuditPillarScore(
            pillar=AuditPillar.DATA_CONFIDENCE,
            score=data_score,
            diagnostics=[log.message for log in data_logs],
            check_count=d_checks
        )

        # =====================================================================
        # PILIER 2 : ASSUMPTION RISK (Test de croissance)
        # =====================================================================
        a_logs: List[str] = []
        a_score = 100.0

        g = p.fcf_growth_rate or 0.0
        if g > 0.15:
            a_logs.append(f"Taux de croissance g Graham ({g:.1%}) hors périmètre de prudence.")
            a_score -= self.PENALTY_HIGH

        pillars[AuditPillar.ASSUMPTION_RISK] = AuditPillarScore(
            pillar=AuditPillar.ASSUMPTION_RISK,
            score=max(0.0, a_score),
            diagnostics=a_logs,
            check_count=1
        )

        # =====================================================================
        # PILIER 3 : METHOD FIT (Validité EPS)
        # =====================================================================
        eps_valid = (f.eps_ttm or 0) > 0

        pillars[AuditPillar.METHOD_FIT] = AuditPillarScore(
            pillar=AuditPillar.METHOD_FIT,
            score=100.0 if eps_valid else 0.0,
            check_count=1
        )

        # =====================================================================
        # PILIER 4 : MODEL RISK (Neutre pour Graham)
        # =====================================================================
        pillars[AuditPillar.MODEL_RISK] = AuditPillarScore(
            pillar=AuditPillar.MODEL_RISK,
            score=100.0,
            check_count=1
        )

        return pillars


# ==============================================================================
# 3. ALIAS DE COMPATIBILITÉ
# ==============================================================================

class StandardValuationAuditor(DCFAuditor):
    """Alias pour compatibilité système."""
    pass