"""
core/models/
Modeles de donnees pour le moteur de valorisation.

Structure :
- enums.py          : Enumerations (ValuationMode, InputSource, etc.)
- glass_box.py      : Tracabilite (CalculationStep, AuditStep)
- company.py        : Donnees entreprise (CompanyFinancials)
- parameters.py     : Parametres DCF (DCFParameters et segments), Scenarios et SOTP (ScenarioVariant, BusinessUnit)
- audit.py          : Audit (AuditReport, AuditPillarScore)
- valuation.py : Requetes/Resultats (ValuationRequest, ValuationResult)

Tous les modeles sont re-exportes ici pour la compatibilite.
"""

# Enumerations et Alias Financiers
from .enums import (
    # Enumerations
    ValuationMode,
    InputSource,
    TerminalValueMethod,
    AuditSeverity,
    SOTPMethod,
    AuditPillar,
    # Type Aliases (ST-1.2 Type-Safe)
    Rate,
    Currency,
    Percentage,
    Multiple,
    ShareCount,
    Years,
    Ratio,
)

# Glass Box (ST-2.1 Enhanced)
from .glass_box import (
    VariableSource,
    VariableInfo,
    TraceHypothesis,
    CalculationStep,
    AuditStep,
)

# Donnees Entreprise
from .company import (
    CompanyFinancials,
)

# Parametres DCF
from .parameters import (
    CoreRateParameters,
    GrowthParameters,
    MonteCarloParameters,
    Parameters,
    ScenarioVariant,
    ScenarioResult,
    ScenarioSynthesis,
    ScenarioParameters,
    BusinessUnit,
    SOTPParameters
)

# Audit
from .audit import (
    AuditPillarScore,
    AuditScoreBreakdown,
    AuditLog,
    AuditReport,
    ValuationOutputContract,
)

# Requetes et Resultats
from .valuation import (
    ValuationRequest,
    ValuationResult,
    DCFValuationResult,
    RIMValuationResult,
    GrahamValuationResult,
    EquityDCFValuationResult,
    PeerMetric,
    MultiplesData,
    MultiplesValuationResult,
    HistoricalPoint,
    BacktestResult,
)

__all__ = [
    # Enums
    "ValuationMode",
    "InputSource",
    "TerminalValueMethod",
    "AuditSeverity",
    "SOTPMethod",
    "AuditPillar",
    # Type Aliases (ST-1.2 Type-Safe)
    "Rate",
    "Currency",
    "Percentage",
    "Multiple",
    "ShareCount",
    "Years",
    "Ratio",
    # Glass Box (ST-2.1 Enhanced)
    "VariableSource",
    "VariableInfo",
    "TraceHypothesis",
    "CalculationStep",
    "AuditStep",
    # Scenarios
    "ScenarioVariant",
    "ScenarioResult",
    "ScenarioSynthesis",
    "ScenarioParameters",
    "BusinessUnit",
    "SOTPParameters",
    # Company
    "CompanyFinancials",
    # DCF Inputs
    "CoreRateParameters",
    "GrowthParameters",
    "MonteCarloParameters",
    "Parameters",
    # Audit
    "AuditPillarScore",
    "AuditScoreBreakdown",
    "AuditLog",
    "AuditReport",
    "ValuationOutputContract",
    # Results
    "ValuationRequest",
    "ValuationResult",
    "DCFValuationResult",
    "RIMValuationResult",
    "GrahamValuationResult",
    "EquityDCFValuationResult",
    "PeerMetric",
    "MultiplesData",
    "MultiplesValuationResult",
    "HistoricalPoint",
    "BacktestResult",
]
