"""
app/ui/result_tabs/core/
Onglets toujours visibles dans les résultats.

- inputs_summary.py      : Récapitulatif des hypothèses
- calculation_proof.py   : Preuve de calcul (Glass Box)
- audit_report.py        : Score de fiabilité
"""

from .inputs_summary import InputsSummaryTab
from .calculation_proof import CalculationProofTab
from .audit_report import AuditReportTab
from .risk_engineering import RiskEngineeringTab
from .market_analysis import MarketAnalysisTab

__all__ = [
    "InputsSummaryTab",
    "CalculationProofTab",
    "AuditReportTab",
    "RiskEngineeringTab",
    "MarketAnalysisTab"
]
