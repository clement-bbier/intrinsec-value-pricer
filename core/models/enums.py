"""
core/models/enums.py
Enumerations du domaine de valorisation.
"""

from enum import Enum


class ValuationMode(str, Enum):
    """Modes de valorisation disponibles."""
    
    # Approche Entite (Firm Value)
    FCFF_STANDARD = "DCF - Free Cash Flow to Firm"
    FCFF_NORMALIZED = "DCF - Normalized Free Cash Flow"
    FCFF_GROWTH = "DCF - Revenue-Driven Growth"

    # Approche Actionnaire (Equity Value)
    FCFE = "DCF - Free Cash Flow to Equity"
    DDM = "Dividend Discount Model"

    # Autres Modeles
    RIM = "Residual Income Model"
    GRAHAM = "Graham Intrinsic Value"

    @property
    def supports_monte_carlo(self) -> bool:
        """Indique si le mode supporte les simulations Monte Carlo."""
        return self != ValuationMode.GRAHAM

    @property
    def is_direct_equity(self) -> bool:
        """Determine si le modele calcule directement la valeur actionnariale."""
        return self in [
            ValuationMode.FCFE,
            ValuationMode.DDM,
            ValuationMode.RIM,
            ValuationMode.GRAHAM
        ]


class InputSource(str, Enum):
    """Source des parametres d'entree."""
    AUTO = "AUTO"
    MANUAL = "MANUAL"
    SYSTEM = "SYSTEM"


class TerminalValueMethod(str, Enum):
    """Methode de calcul de la valeur terminale."""
    GORDON_GROWTH = "GORDON_GROWTH"
    EXIT_MULTIPLE = "EXIT_MULTIPLE"


class AuditSeverity(str, Enum):
    """Niveau de severite des alertes d'audit."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class SOTPMethod(str, Enum):
    """Methodes de valorisation par segment (SOTP)."""
    DCF = "DCF"
    MULTIPLES = "MULTIPLES"
    ASSET_VALUE = "ASSET_VALUE"


class AuditPillar(str, Enum):
    """Piliers d'evaluation de l'audit."""
    DATA_CONFIDENCE = "Data Confidence"
    ASSUMPTION_RISK = "Assumption Risk"
    MODEL_RISK = "Model Risk"
    METHOD_FIT = "Method Fit"
