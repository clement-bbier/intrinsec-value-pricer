"""
Énumérations et alias de types du domaine de valorisation.

Ce module définit les types énumérés et alias utilisés dans
le domaine de la valorisation financière, assurant la
consistance des valeurs acceptées.
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
    """Modes de valorisation disponibles.

    Énumération des différentes méthodes de valorisation
    implémentées dans le système.
    """

    # Approche Entité (Firm Value)
    FCFF_STANDARD = "DCF - Free Cash Flow to Firm"
    FCFF_NORMALIZED = "DCF - Normalized Free Cash Flow"
    FCFF_GROWTH = "DCF - Revenue-Driven Growth"

    # Approche Actionnaire (Equity Value)
    FCFE = "DCF - Free Cash Flow to Equity"
    DDM = "Dividend Discount Model"

    # Autres Modèles
    RIM = "Residual Income Model"
    GRAHAM = "Graham Intrinsic Value"

    @property
    def supports_monte_carlo(self) -> bool:
        """Indique si le mode supporte les simulations Monte Carlo.

        Returns
        -------
        bool
            True si les simulations Monte Carlo sont disponibles.
        """
        return self != ValuationMode.GRAHAM

    @property
    def is_direct_equity(self) -> bool:
        """Détermine si le modèle calcule directement la valeur actionnariale.

        Returns
        -------
        bool
            True si le modèle produit directement la valeur par action.
        """
        return self in [
            ValuationMode.FCFE,
            ValuationMode.DDM,
            ValuationMode.RIM,
            ValuationMode.GRAHAM
        ]


class InputSource(str, Enum):
    """Source des paramètres d'entrée.

    Définit l'origine des paramètres utilisés dans
    le calcul de valorisation.
    """

    AUTO = "AUTO"
    MANUAL = "MANUAL"
    SYSTEM = "SYSTEM"


class TerminalValueMethod(str, Enum):
    """Méthode de calcul de la valeur terminale.

    Approches disponibles pour estimer la valeur
    résiduelle au-delà de la période de projection.
    """

    GORDON_GROWTH = "GORDON_GROWTH"
    EXIT_MULTIPLE = "EXIT_MULTIPLE"


class AuditSeverity(str, Enum):
    """Niveau de sévérité des alertes d'audit.

    Classification des problèmes détectés pendant
    l'audit des valorisations.
    """

    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class SOTPMethod(str, Enum):
    """Méthodes de valorisation par segment (SOTP).

    Approches disponibles pour valoriser chaque
    segment d'activité dans l'analyse SOTP.
    """

    DCF = "DCF"
    MULTIPLES = "MULTIPLES"
    ASSET_VALUE = "ASSET_VALUE"


class AuditPillar(str, Enum):
    """Piliers d'évaluation de l'audit.

    Dimensions fondamentales évaluées lors de
    l'audit d'une valorisation.
    """

    DATA_CONFIDENCE = "Data Confidence"
    ASSUMPTION_RISK = "Assumption Risk"
    MODEL_RISK = "Model Risk"
    METHOD_FIT = "Method Fit"
