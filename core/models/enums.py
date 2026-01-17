"""
core/models/enums.py
Enumerations du domaine de valorisation.
"""

from enum import Enum


class ValuationMode(str, Enum):
    """Modes de valorisation disponibles."""
    
    # Approche Entite (Firm Value)
    FCFF_TWO_STAGE = "FCFF Two-Stage (Damodaran)"
    FCFF_NORMALIZED = "FCFF Normalized (Cyclical / Industrial)"
    FCFF_REVENUE_DRIVEN = "FCFF Revenue-Driven (High Growth / Tech)"

    # Approche Actionnaire (Equity Value)
    FCFE_TWO_STAGE = "FCFE Two-Stage (Direct Equity)"
    DDM_GORDON_GROWTH = "Dividend Discount Model (Gordon / DDM)"

    # Autres Modeles
    RESIDUAL_INCOME_MODEL = "Residual Income Model (Penman)"
    GRAHAM_1974_REVISED = "Graham Intrinsic Value (1974 Revised)"

    @property
    def supports_monte_carlo(self) -> bool:
        """Indique si le mode supporte les simulations Monte Carlo."""
        return self != ValuationMode.GRAHAM_1974_REVISED

    @property
    def is_direct_equity(self) -> bool:
        """Determine si le modele calcule directement la valeur actionnariale."""
        return self in [
            ValuationMode.FCFE_TWO_STAGE,
            ValuationMode.DDM_GORDON_GROWTH,
            ValuationMode.RESIDUAL_INCOME_MODEL,
            ValuationMode.GRAHAM_1974_REVISED
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
