"""
core/diagnostics.py
Système de types pour le diagnostic et la gestion d'erreurs structurée.
Audit-Grade : Ajout du registre normatif des événements financiers.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, List

class SeverityLevel(Enum):
    """Niveau de gravité du diagnostic."""
    INFO = "INFO"           # Information contextuelle
    WARNING = "WARNING"     # Attention requise, mais calcul possible
    ERROR = "ERROR"         # Erreur sérieuse, une partie du calcul a échoué
    CRITICAL = "CRITICAL"   # Bloquant, impossible de continuer

class DiagnosticDomain(Enum):
    """Domaine d'origine du problème."""
    DATA = "DATA"           # Problème de données (Yahoo, API, Trous)
    MODEL = "MODEL"         # Problème mathématique ou logique financière
    PROVIDER = "PROVIDER"   # Problème d'infrastructure (Connexion, Timeout)
    USER_INPUT = "USER_INPUT" # Erreur de saisie utilisateur
    SYSTEM = "SYSTEM"       # Erreur interne du code

@dataclass(frozen=True)
class DiagnosticEvent:
    """
    Représente un événement de diagnostic unique.
    C'est l'atome de base de notre système de gestion d'erreurs.
    """
    code: str                       # Code unique (ex: 'DATA_MISSING_FCF')
    severity: SeverityLevel         # Niveau de gravité
    domain: DiagnosticDomain        # Domaine
    message: str                    # Message lisible pour l'humain
    technical_detail: Optional[str] = None # Détail pour le dev
    remediation_hint: Optional[str] = None # Conseil pour l'utilisateur

    @property
    def is_blocking(self) -> bool:
        """Retourne Vrai si ce diagnostic empêche le calcul de continuer."""
        return self.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]

    def to_dict(self) -> dict:
        """Sérialisation pour logs ou API."""
        return {
            "code": self.code,
            "severity": self.severity.value,
            "domain": self.domain.value,
            "message": self.message,
            "is_blocking": self.is_blocking
        }

# ==============================================================================
# REGISTRE NORMATIF DES ÉVÉNEMENTS (NOUVEAU - AUDIT-GRADE)
# ==============================================================================

class DiagnosticRegistry:
    """
    Catalogue centralisé des événements de diagnostic.
    Permet de garantir l'uniformité des messages entre le moteur et l'UI.
    """

    @staticmethod
    def MODEL_G_DIVERGENCE(g: float, wacc: float) -> DiagnosticEvent:
        """Détecté lorsque la croissance perpétuelle invalide le modèle de Gordon."""
        return DiagnosticEvent(
            code="MODEL_G_DIVERGENCE",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.MODEL,
            message=f"Divergence mathématique : g ({g:.2%}) >= WACC ({wacc:.2%}).",
            remediation_hint="Réduisez le taux de croissance perpétuelle ou revoyez le WACC."
        )

    @staticmethod
    def DATA_MISSING_CORE_METRIC(metric_name: str) -> DiagnosticEvent:
        """Donnée critique manquante empêchant la valorisation."""
        return DiagnosticEvent(
            code="DATA_MISSING_CORE_METRIC",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.DATA,
            message=f"Métrique critique manquante : {metric_name}.",
            remediation_hint="Utilisez le mode 'Expert' pour saisir manuellement cette donnée."
        )

    @staticmethod
    def RISK_EXCESSIVE_GROWTH(g: float) -> DiagnosticEvent:
        """Alerte sur une hypothèse de croissance irréaliste sur le long terme."""
        return DiagnosticEvent(
            code="RISK_EXCESSIVE_GROWTH",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.USER_INPUT,
            message=f"Croissance projetée agressive ({g:.2%}).",
            remediation_hint="Vérifiez si ce taux est soutenable face à la moyenne du secteur."
        )

    @staticmethod
    def DATA_NEGATIVE_BETA(beta: float) -> DiagnosticEvent:
        """Détection d'un Beta inhabituel."""
        return DiagnosticEvent(
            code="DATA_NEGATIVE_BETA",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.DATA,
            message=f"Beta atypique détecté ({beta:.2f}).",
            remediation_hint="Un Beta négatif est rare ; vérifiez la source ou saisissez un Beta sectoriel."
        )