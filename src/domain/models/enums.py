"""
src/domain/models/enums.py

Énumérations et alias de types du domaine de valorisation.

Version : V2.0 — ST-1.2 Type-Safe Resolution
Pattern : Value Objects + Type Aliases
Style : Numpy Style docstrings

RISQUES FINANCIERS:
- Les enums définissent les modes de valorisation disponibles
- Une erreur de mapping peut conduire à utiliser le mauvais modèle

DEPENDANCES CRITIQUES:
- Aucune dépendance externe (module autonome)
"""

from __future__ import annotations

from enum import Enum
from typing import TypeAlias


# ==============================================================================
# 1. ALIAS FINANCIERS (TYPE-SAFE)
# ==============================================================================
# Ces alias améliorent la lisibilité et permettent une validation future
# sans impact sur les performances runtime.

Rate: TypeAlias = float
"""Taux financier (WACC, croissance, actualisation). Exemple: 0.08 pour 8%."""

Currency: TypeAlias = float
"""Montant monétaire en devise de base. Exemple: 1_500_000.00 pour 1.5M."""

Percentage: TypeAlias = float
"""Pourcentage normalisé entre 0.0 et 1.0. Exemple: 0.15 pour 15%."""

Multiple: TypeAlias = float
"""Multiple de valorisation (P/E, EV/EBITDA). Exemple: 15.5 pour un P/E de 15.5x."""

ShareCount: TypeAlias = int
"""Nombre d'actions en circulation. Exemple: 1_000_000_000."""

Years: TypeAlias = int
"""Durée en années. Exemple: 5 pour une projection sur 5 ans."""

Ratio: TypeAlias = float
"""Ratio financier générique. Exemple: 0.35 pour un ratio dette/equity de 35%."""


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
