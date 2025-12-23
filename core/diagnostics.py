"""
core/diagnostics.py
Système de types pour le diagnostic et la gestion d'erreurs structurée.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any

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