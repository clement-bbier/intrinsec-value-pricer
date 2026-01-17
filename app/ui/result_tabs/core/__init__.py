"""
app/ui/result_tabs/core/
Onglets toujours visibles dans les résultats.

- inputs_summary.py      : Récapitulatif des hypothèses
- calculation_proof.py   : Preuve de calcul (Glass Box)
- audit_report.py        : Score de fiabilité
"""

from app.ui.result_tabs.core.inputs_summary import InputsSummaryTab
from app.ui.result_tabs.core.calculation_proof import CalculationProofTab
from app.ui.result_tabs.core.audit_report import AuditReportTab

__all__ = [
    "InputsSummaryTab",
    "CalculationProofTab",
    "AuditReportTab",
]
