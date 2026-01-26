"""
infra/auditing/auditors.py
MOTEUR D'AUDIT INSTITUTIONNEL
=============================
Architecture : SOLID - Chaque auditeur gère les piliers spécifiques à son modèle.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional

from src.models import (
    ValuationResult, AuditPillar, AuditPillarScore, AuditStep, AuditSeverity
)
from src.config import AuditThresholds
from src.i18n import StrategyFormulas

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. INTERFACES ET BASE
# ==============================================================================

class IValuationAuditor(ABC):
    @abstractmethod
    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        pass

    @abstractmethod
    def get_max_potential_checks(self) -> int:
        pass

class BaseAuditor(IValuationAuditor, ABC):
    """Socle commun fournissant la mécanique d'enregistrement des tests."""

    def __init__(self):
        self._audit_steps: List[AuditStep] = []

    def _add_audit_step(self, key: str, value: Any, threshold: Any,
                        severity: AuditSeverity, condition: bool,
                        penalty: float = 0.0, formula: Optional[str] = None) -> float:
        """Enregistre un point de contrôle et retourne la pénalité si échec."""
        verdict = bool(condition)
        self._audit_steps.append(AuditStep(
            step_id=len(self._audit_steps) + 1,
            step_key=key,
            indicator_value=str(value),
            threshold_value=str(threshold),
            severity=severity,
            verdict=verdict,
            evidence=f"{value} vs {threshold}" if threshold else str(value),
            rule_formula=formula or StrategyFormulas.NA
        ))
        return 0.0 if verdict else penalty

    def _audit_data_confidence(self, result: ValuationResult) -> Tuple[float, int]:
        """Analyse transverse de la qualité des données sources."""
        score = 100.0
        f = result.financials

        # Test Bêta
        score -= self._add_audit_step(
            key="AUDIT_DATA_BETA",
            value=f.beta,
            threshold=f"{AuditThresholds.BETA_MIN}-{AuditThresholds.BETA_MAX}",
            severity=AuditSeverity.WARNING,
            condition=(f.beta is not None and AuditThresholds.BETA_MIN <= f.beta <= AuditThresholds.BETA_MAX),
            formula=rf"{AuditThresholds.BETA_MIN} \leq \beta \leq {AuditThresholds.BETA_MAX}"
        )
        return max(0.0, score), len(self._audit_steps)

# ==============================================================================
# 2. IMPLÉMENTATIONS SPÉCIFIQUES
# ==============================================================================

class DCFAuditor(BaseAuditor):
    """Auditeur pour les modèles DCF (FCFF, FCFE, DDM)."""

    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        score_data, count = self._audit_data_confidence(result)

        return {
            AuditPillar.DATA_CONFIDENCE: AuditPillarScore(
                pillar=AuditPillar.DATA_CONFIDENCE,
                score=score_data,
                check_count=count
            ),
            AuditPillar.MODEL_RISK: AuditPillarScore(
                pillar=AuditPillar.MODEL_RISK,
                score=100.0,
                check_count=1
            )
        }

    def get_max_potential_checks(self) -> int:
        return 5

class RIMAuditor(DCFAuditor):
    """Auditeur spécialisé pour le Residual Income (Banques)."""
    pass

class GrahamAuditor(BaseAuditor):
    """Auditeur spécialisé pour la valeur intrinsèque de Graham."""
    def audit_pillars(self, result: ValuationResult) -> Dict[AuditPillar, AuditPillarScore]:
        # Logique simplifiée (Graham n'utilise pas de Bêta/WACC)
        return {
            AuditPillar.DATA_CONFIDENCE: AuditPillarScore(pillar=AuditPillar.DATA_CONFIDENCE, score=100.0)
        }
    def get_max_potential_checks(self) -> int: return 2

class MultiplesAuditor(DCFAuditor):
    """Auditeur pour la triangulation par multiples."""
    pass

# ==============================================================================
# 3. ALIAS ET COMPATIBILITÉ (TOUJOURS EN FIN DE FICHIER)
# ==============================================================================

StandardValuationAuditor = DCFAuditor
FundamentalValuationAuditor = DCFAuditor
FCFEAuditor = DCFAuditor
DDMAuditor = DCFAuditor