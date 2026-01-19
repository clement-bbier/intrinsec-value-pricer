"""
core/diagnostics.py
Système de types pour le diagnostic et la gestion d'erreurs structurée.
Audit-Grade : Ajout du registre normatif des événements financiers.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, List
# DT-001/002: Import depuis core.i18n
from src.i18n import DiagnosticTexts

class SeverityLevel(Enum):
    """Niveau de gravité du diagnostic."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class DiagnosticDomain(Enum):
    """Domaine d'origine du problème."""
    DATA = "DATA"
    MODEL = "MODEL"
    PROVIDER = "PROVIDER"
    USER_INPUT = "USER_INPUT"
    SYSTEM = "SYSTEM"

@dataclass(frozen=True)
class DiagnosticEvent:
    """
    Représente un événement de diagnostic unique.
    """
    code: str
    severity: SeverityLevel
    domain: DiagnosticDomain
    message: str
    technical_detail: Optional[str] = None
    remediation_hint: Optional[str] = None

    @property
    def is_blocking(self) -> bool:
        """Retourne Vrai si ce diagnostic empêche le calcul de continuer."""
        return self.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "domain": self.domain.value,
            "message": self.message,
            "is_blocking": self.is_blocking
        }

# ==============================================================================
# REGISTRE NORMATIF DES ÉVÉNEMENTS
# ==============================================================================

class DiagnosticRegistry:
    """
    Catalogue centralisé des événements utilisant DiagnosticTexts.
    """

    @staticmethod
    def model_g_divergence(g: float, wacc: float) -> DiagnosticEvent:
        """Erreur de convergence Gordon Shapiro."""
        return DiagnosticEvent(
            code="MODEL_G_DIVERGENCE",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.MODEL,
            message=DiagnosticTexts.MODEL_G_DIV_MSG.format(g=g, wacc=wacc),
            remediation_hint=DiagnosticTexts.MODEL_G_DIV_HINT
        )

    @staticmethod
    def model_mc_instability(valid_ratio: float, threshold: float) -> DiagnosticEvent:
        """Instabilité statistique lors des simulations Monte Carlo."""
        return DiagnosticEvent(
            code="MODEL_MC_INSTABILITY",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.MODEL,
            message=DiagnosticTexts.MODEL_MC_INST_MSG.format(valid_ratio=valid_ratio, threshold=threshold),
            remediation_hint=DiagnosticTexts.MODEL_MC_INST_HINT
        )

    @staticmethod
    def data_missing_core_metric(metric_name: str) -> DiagnosticEvent:
        """Donnée critique manquante empêchant la valorisation."""
        return DiagnosticEvent(
            code="DATA_MISSING_CORE_METRIC",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.DATA,
            message=DiagnosticTexts.DATA_MISSING_CORE_MSG.format(metric_name=metric_name),
            remediation_hint=DiagnosticTexts.DATA_MISSING_CORE_HINT
        )

    @staticmethod
    def risk_excessive_growth(g: float) -> DiagnosticEvent:
        """Alerte sur une hypothèse de croissance irréaliste."""
        return DiagnosticEvent(
            code="RISK_EXCESSIVE_GROWTH",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.USER_INPUT,
            message=DiagnosticTexts.RISK_EXCESSIVE_GROWTH_MSG.format(g=g),
            remediation_hint=DiagnosticTexts.RISK_EXCESSIVE_GROWTH_HINT
        )

    @staticmethod
    def data_negative_beta(beta: float) -> DiagnosticEvent:
        """Détection d'un Beta inhabituel."""
        return DiagnosticEvent(
            code="DATA_NEGATIVE_BETA",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.DATA,
            message=DiagnosticTexts.DATA_NEGATIVE_BETA_MSG.format(beta=beta),
            remediation_hint=DiagnosticTexts.DATA_NEGATIVE_BETA_HINT
        )

    @staticmethod
    def fcfe_negative_flow(val: float) -> DiagnosticEvent:
        """Erreur : Le flux FCFE calculé est négatif."""
        return DiagnosticEvent(
            code="FCFE_NEGATIVE_FLOW",
            severity=SeverityLevel.CRITICAL,  # Bloquant
            domain=DiagnosticDomain.MODEL,
            message=DiagnosticTexts.FCFE_NEGATIVE_MSG.format(val=val),
            remediation_hint=DiagnosticTexts.FCFE_NEGATIVE_HINT
        )

    @staticmethod
    def ddm_payout_excessive(payout: float) -> DiagnosticEvent:
        """Avertissement : Le Payout Ratio dépasse les bénéfices."""
        return DiagnosticEvent(
            code="DDM_PAYOUT_EXCESSIVE",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.MODEL,
            message=DiagnosticTexts.DDM_PAYOUT_MSG.format(payout=payout),
            remediation_hint=DiagnosticTexts.DDM_PAYOUT_HINT
        )

    @staticmethod
    def model_sgr_divergence(g: float, sgr: float) -> DiagnosticEvent:
        """Avertissement : Croissance > Sustainable Growth Rate."""
        return DiagnosticEvent(
            code="MODEL_SGR_DIVERGENCE",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.MODEL,
            message=DiagnosticTexts.MODEL_SGR_DIV_MSG.format(g=g, sgr=sgr),
            remediation_hint=DiagnosticTexts.MODEL_SGR_DIV_HINT
        )
