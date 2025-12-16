import logging
import numpy as np
from typing import Optional, Union, List

from core.models import (
    ValuationResult,
    ValuationMode,
    AuditReport,
    AuditLog,
    CompanyFinancials,
    DCFParameters,
    InputSource
)
# On importe les auditeurs spécialisés définis précédemment
from infra.auditing.auditors import (
    IValuationAuditor,
    StandardDCFAuditor,
    BankAuditor,
    GrahamAuditor
)

logger = logging.getLogger(__name__)


class AuditEngine:
    """
    Moteur d'Audit Central (Factory Pattern).
    Responsabilité : Router la demande vers le bon auditeur spécialisé.
    Gère la compatibilité pour l'audit préliminaire (Données) et final (Résultats).
    """

    @staticmethod
    def compute_audit(
            arg1: Union[ValuationResult, CompanyFinancials],
            arg2: Optional[DCFParameters] = None,
            **kwargs
    ) -> AuditReport:
        """
        Point d'entrée unique et intelligent.

        Signature 1 (Audit Final) : compute_audit(result: ValuationResult)
        Signature 2 (Audit Data)  : compute_audit(financials: CompanyFinancials, params: DCFParameters)
        """
        try:
            # --- CAS 1 : AUDIT SUR RÉSULTAT (FINAL) ---
            if isinstance(arg1, ValuationResult):
                result = arg1
                auditor = AuditEngine._get_auditor_for_mode(result.request.mode if result.request else None)

                # Exécution Audit Métier
                report = auditor.audit(result)

                # Enrichissement Monte Carlo (si présent)
                if result.simulation_results:
                    AuditEngine._enrich_with_monte_carlo_audit(result.simulation_results, report)

                return report

            # --- CAS 2 : AUDIT SUR INPUTS (PRÉLIMINAIRE / COMPATIBILITÉ PROVIDER) ---
            elif isinstance(arg1, CompanyFinancials) and isinstance(arg2, DCFParameters):
                financials, params = arg1, arg2
                # On crée un faux résultat temporaire pour utiliser la logique de l'auditeur
                # Cela évite de dupliquer la logique de validation des données dans auditors.py
                from core.models import DCFValuationResult, ValuationRequest

                # Dummy Request
                req = ValuationRequest(
                    ticker=financials.ticker,
                    mode=ValuationMode.SIMPLE_FCFF,  # Mode par défaut pour check data
                    projection_years=params.projection_years,
                    input_source=InputSource.AUTO
                )

                # Dummy Result (Vide, juste pour passer les financials à l'auditeur)
                dummy_result = DCFValuationResult(
                    request=req,
                    financials=financials,
                    params=params,
                    intrinsic_value_per_share=0.0,
                    market_price=financials.current_price,
                    wacc=0.0, cost_of_equity=0.0, cost_of_debt_after_tax=0.0,
                    projected_fcfs=[], discount_factors=[], sum_discounted_fcf=0.0,
                    terminal_value=0.0, discounted_terminal_value=0.0,
                    enterprise_value=0.0, equity_value=0.0
                )

                # On utilise l'auditeur standard juste pour checker la qualité des données (_check_data_quality)
                auditor = StandardDCFAuditor()
                report = auditor.audit(dummy_result)

                # On marque que c'est un audit partiel
                report.audit_mode = "DataQualityCheck"
                return report

            else:
                raise ValueError("Arguments invalides pour compute_audit")

        except Exception as e:
            logger.error(f"Audit failed: {e}", exc_info=True)
            return AuditEngine._get_fallback_report(str(e))

    @staticmethod
    def _get_auditor_for_mode(mode: Optional[ValuationMode]) -> IValuationAuditor:
        """Factory : Instancie le bon auditeur."""
        if mode == ValuationMode.DDM_BANKS:
            return BankAuditor()
        elif mode == ValuationMode.GRAHAM_VALUE:
            return GrahamAuditor()
        else:
            # Par défaut (Simple, Fundamental, Growth, Monte Carlo) -> Standard
            return StandardDCFAuditor()

    @staticmethod
    def _enrich_with_monte_carlo_audit(sims: List[float], report: AuditReport) -> None:
        """Analyse la stabilité statistique."""
        if not sims: return

        values = np.array(sims)
        mean_val = np.mean(values)

        if mean_val > 0:
            std_dev = np.std(values)
            cv = std_dev / mean_val  # Coefficient de Variation

            if cv > 0.50:
                report.logs.append(AuditLog(
                    "Monte Carlo", "HIGH",
                    f"Instabilité extrême (CV={cv:.2f}). Résultat peu fiable.", -30
                ))
                report.global_score -= 30
            elif cv > 0.30:
                report.logs.append(AuditLog(
                    "Monte Carlo", "WARN",
                    f"Forte dispersion (CV={cv:.2f}). Fourchette large.", -10
                ))
                report.global_score -= 10
            else:
                report.logs.append(AuditLog(
                    "Monte Carlo", "INFO",
                    f"Convergence robuste (CV={cv:.2f}).", 0
                ))

        report.global_score = max(0.0, report.global_score)

    @staticmethod
    def _get_fallback_report(error_msg: str) -> AuditReport:
        return AuditReport(
            global_score=0.0,
            rating="Error",
            audit_mode="SystemFailure",
            logs=[AuditLog("System", "CRITICAL", f"Audit crash: {error_msg}", -100)],
            breakdown={}
        )