"""
core/models/
Modeles de donnees pour le moteur de valorisation.

Structure :
- enums.py          : Enumerations (ValuationMode, InputSource, etc.)
- glass_box.py      : Tracabilite (CalculationStep, AuditStep)
- scenarios.py      : Scenarios et SOTP (ScenarioVariant, BusinessUnit)
- company.py        : Donnees entreprise (CompanyFinancials)
- dcf_inputs.py     : Parametres DCF (DCFParameters et segments)
- audit.py          : Audit (AuditReport, AuditPillarScore)
- request_response.py : Requetes/Resultats (ValuationRequest, ValuationResult)

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

# Scenarios et SOTP
from .scenarios import (
    ScenarioVariant,
    ScenarioResult,
    ScenarioSynthesis,
    ScenarioParameters,
    BusinessUnit,
    SOTPParameters,
)

# Donnees Entreprise
from .company import (
    CompanyFinancials,
)

# Parametres DCF
from .dcf_inputs import (
    CoreRateParameters,
    GrowthParameters,
    MonteCarloConfig,
    DCFParameters,
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
from .request_response import (
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
    "MonteCarloConfig",
    "DCFParameters",
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
