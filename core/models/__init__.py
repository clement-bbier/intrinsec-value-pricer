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

# Enumerations
from core.models.enums import (
    ValuationMode,
    InputSource,
    TerminalValueMethod,
    AuditSeverity,
    SOTPMethod,
    AuditPillar,
)

# Glass Box
from core.models.glass_box import (
    TraceHypothesis,
    CalculationStep,
    AuditStep,
)

# Scenarios et SOTP
from core.models.scenarios import (
    ScenarioVariant,
    ScenarioResult,
    ScenarioSynthesis,
    ScenarioParameters,
    BusinessUnit,
    SOTPParameters,
)

# Donnees Entreprise
from core.models.company import (
    CompanyFinancials,
    HistoricalPoint,
    BacktestResult,
)

# Parametres DCF
from core.models.dcf_inputs import (
    CoreRateParameters,
    GrowthParameters,
    MonteCarloConfig,
    DCFParameters,
)

# Audit
from core.models.audit import (
    AuditPillarScore,
    AuditScoreBreakdown,
    AuditLog,
    AuditReport,
    ValuationOutputContract,
)

# Requetes et Resultats
from core.models.request_response import (
    ValuationRequest,
    ValuationResult,
    DCFValuationResult,
    RIMValuationResult,
    GrahamValuationResult,
    EquityDCFValuationResult,
    PeerMetric,
    MultiplesData,
    MultiplesValuationResult,
)


__all__ = [
    # Enums
    "ValuationMode",
    "InputSource",
    "TerminalValueMethod",
    "AuditSeverity",
    "SOTPMethod",
    "AuditPillar",
    # Glass Box
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
    "HistoricalPoint",
    "BacktestResult",
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
]
