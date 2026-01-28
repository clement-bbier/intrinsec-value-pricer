"""
src/valuation/strategies/abstract.py

ABSTRACT VALUATION STRATEGY BASE
================================
Role: Foundation for all valuation methodologies.
Pattern: Strategy Pattern (Gang of Four).
Invariants: Mandatory Glass Box traceability and output contract validation.

Standard: SOLID / Institutional Grade.
Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

from src.exceptions import CalculationError
from src.models.valuation import ValuationResult
from src.models.glass_box import CalculationStep, TraceHypothesis
from src.models.company import CompanyFinancials
from src.models.dcf_parameters import DCFParameters

# Centralized i18n Mapping
from src.i18n import CalculationErrors

if TYPE_CHECKING:
    from infra.auditing.audit_engine import AuditEngine, AuditorFactory

logger = logging.getLogger(__name__)


class ValuationStrategy(ABC):
    """
    Base class for all financial valuation strategies.

    Manages the lifecycle of a valuation run, including the capture of
    intermediate calculation steps and the final audit trigger.
    """

    def __init__(self, glass_box_enabled: bool = True):
        """
        Initializes the strategy with telemetry configuration.

        Parameters
        ----------
        glass_box_enabled : bool, default=True
            If True, intermediate calculation steps are recorded for the Audit Report.
        """
        self.glass_box_enabled = glass_box_enabled
        self.calculation_trace: List[CalculationStep] = []

    @abstractmethod
    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
        """
        Primary entry point for the valuation methodology.

        Concrete implementations must execute their specific logic (e.g., RIM, DCF)
        and return a validated result object.
        """
        pass

    def add_step(
            self,
            step_key: str,
            result: float,
            numerical_substitution: str,
            label: str = "",
            theoretical_formula: str = "",
            interpretation: str = "",
            source: str = "",
            hypotheses: Optional[List[TraceHypothesis]] = None
    ) -> None:
        """
        Records a calculation step in the Glass Box trace for auditability.

        Parameters
        ----------
        step_key : str
            Unique identifier for the step (linking to the Glass Box registry).
        result : float
            The raw numeric output of the calculation.
        numerical_substitution : str
            Details of the calculation with real values (e.g., "100 * 1.05").
        label : str, optional
            Display name. Defaults to `step_key` if empty.
        theoretical_formula : str, optional
            LaTeX expression of the financial formula.
        interpretation : str, optional
            Pedagogical note explaining the logic.
        source : str, optional
            Origin of the data (e.g., "Yahoo Finance", "Analyst Override").
        hypotheses : List[TraceHypothesis], optional
            Critical assumptions associated with this specific step.
        """
        if not self.glass_box_enabled:
            return

        step = CalculationStep(
            step_id=len(self.calculation_trace) + 1,
            step_key=step_key,
            label=label or step_key,
            theoretical_formula=theoretical_formula,
            hypotheses=hypotheses or [],
            numerical_substitution=numerical_substitution,
            result=result,
            interpretation=interpretation,
            source=source
        )

        self.calculation_trace.append(step)

    @staticmethod
    def generate_audit_report(result: ValuationResult) -> None:
        """
        Triggers the institutional audit report generation.

        Identifies the appropriate auditor based on the valuation mode and
        delegates the reliability scoring to the AuditEngine.
        """
        # Local imports to prevent circular dependencies during initialization
        from infra.auditing.audit_engine import AuditEngine, AuditorFactory
        from src.models.valuation import (
            ValuationRequest, DCFValuationResult, RIMValuationResult,
            GrahamValuationResult, MultiplesValuationResult
        )
        from src.models.enums import ValuationMode, InputSource

        if result.request is None:
            # Dynamic mode determination for fallback requests
            if isinstance(result, DCFValuationResult):
                mode = ValuationMode.FCFF_STANDARD
            elif isinstance(result, RIMValuationResult):
                mode = ValuationMode.RIM
            elif isinstance(result, GrahamValuationResult):
                mode = ValuationMode.GRAHAM
            else:
                mode = ValuationMode.FCFF_STANDARD

            result.request = ValuationRequest(
                ticker=result.financials.ticker,
                projection_years=result.params.growth.projection_years,
                mode=mode,
                input_source=InputSource.AUTO,
                options={}
            )

        # Specialized auditor selection
        if isinstance(result, MultiplesValuationResult):
            from infra.auditing.auditors import MultiplesAuditor
            auditor = MultiplesAuditor()
        else:
            auditor = AuditorFactory.get_auditor(result.request.mode)

        result.audit_report = AuditEngine.compute_audit(result, auditor)

    def verify_output_contract(self, result: ValuationResult) -> None:
        """
        Validates that the result object adheres to model invariants (SOLID).

        Raises
        ------
        CalculationError
            If the output contract is invalid or missing required components.
        """
        contract = result.build_output_contract()
        if not contract.is_valid():
            raise CalculationError(
                CalculationErrors.CONTRACT_VIOLATION.format(cls=self.__class__.__name__)
            )

    def _merge_traces(self, result: ValuationResult) -> None:
        """
        Merges the strategy-specific trace with the pipeline trace.

        Ensures that setup steps (e.g., FCF selection) appear at the beginning
        of the mathematical proof.
        """
        result.calculation_trace = self.calculation_trace + result.calculation_trace