""" A SUPPRIMER
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
from typing import Dict, List, Optional, TYPE_CHECKING

from src.exceptions import CalculationError
from src.models.valuation import ValuationResult
from src.models.glass_box import CalculationStep, TraceHypothesis, VariableInfo, VariableSource
from src.models.company import Company
from src.models.parameters import Parameters

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

    Attributes
    ----------
    glass_box_enabled : bool
        Flag controlling whether calculation steps are recorded for audit.
    calculation_trace : List[CalculationStep]
        Sequential registry of all mathematical steps performed.
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
    def execute(
        self,
        financials: Company,
        params: Parameters
    ) -> ValuationResult:
        """
        Primary entry point for the valuation methodology.

        Concrete implementations must execute their specific logic (e.g., RIM, DCF)
        and return a validated result object.

        Parameters
        ----------
        financials : Company
            Target company financial data.
        params : Parameters
            Calculation hypotheses and configuration.

        Returns
        -------
        ValuationResult
            The completed valuation output with audit trace.
        """
        pass

    def add_step(
        self,
        step_key: str,
        result: float,
        actual_calculation: str = "",
        label: str = "",
        theoretical_formula: str = "",
        interpretation: str = "",
        source: str = "",
        hypotheses: Optional[List[TraceHypothesis]] = None,
        variables_map: Optional[Dict[str, VariableInfo]] = None
    ) -> None:
        """
        Records a calculation step in the Glass Box trace for auditability.

        This method captures the full mathematical context of each computation,
        including variable provenance for transparency reporting.

        Parameters
        ----------
        step_key : str
            Unique identifier for the step (linking to the Glass Box registry).
        result : float
            The raw numeric output of the calculation.
        actual_calculation : str
            The executed calculation string with substituted values.
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
        variables_map : Dict[str, VariableInfo], optional
            Mapping of mathematical symbols to their metadata and provenance.
            Enables the UI to display source indicators (Yahoo/Manual/Default).


        Notes
        -----
        The `variables_map` parameter is essential for Glass Box transparency.
        Each variable should include:
        - symbol: LaTeX notation (e.g., r"R_f", r"\\beta")
        - value: The numeric value used
        - source: VariableSource enum indicating provenance
        - is_overridden: True if user manually changed the automated value
        - original_value: The provider value before override (if applicable)
        """
        if not self.glass_box_enabled:
            return

        step = CalculationStep(
            step_id=len(self.calculation_trace) + 1,
            step_key=step_key,
            label=label or step_key,
            theoretical_formula=theoretical_formula,
            actual_calculation=actual_calculation,
            variables_map=variables_map or {},
            hypotheses=hypotheses or [],
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

        Parameters
        ----------
        result : ValuationResult
            The valuation output to be audited.

        Notes
        -----
        This method handles fallback mode determination when the request
        object is missing, ensuring audit coverage for all execution paths.
        """
        # Local imports to prevent circular dependencies during initialization
        from infra.auditing.audit_engine import AuditEngine, AuditorFactory
        from src.models.valuation import (
            ValuationRequest, DCFValuationResult, RIMValuationResult,
            GrahamValuationResult, MultiplesValuationResult
        )
        from src.models.enums import ValuationMethodology, ParametersSource

        if result.request is None:
            # Dynamic mode determination for fallback requests
            if isinstance(result, DCFValuationResult):
                mode = ValuationMethodology.FCFF_STANDARD
            elif isinstance(result, RIMValuationResult):
                mode = ValuationMethodology.RIM
            elif isinstance(result, GrahamValuationResult):
                mode = ValuationMethodology.GRAHAM
            else:
                mode = ValuationMethodology.FCFF_STANDARD

            result.request = ValuationRequest(
                ticker=result.financials.ticker,
                projection_years=result.params.growth.projection_years,
                mode=mode,
                input_source=ParametersSource.AUTO,
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

        Parameters
        ----------
        result : ValuationResult
            The valuation output to validate.

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
        of the mathematical proof, maintaining logical calculation flow.

        Parameters
        ----------
        result : ValuationResult
            The valuation output whose trace will be enriched.
        """
        result.calculation_trace = self.calculation_trace + result.calculation_trace

    @staticmethod
    def _build_variable_info(
            symbol: str,
            value: float,
            manual_value: Optional[float],
            provider_value: Optional[float],
            description: str = "",
            default_source: VariableSource = VariableSource.YAHOO_FINANCE,
            format_as_pct: bool = False,
            decimals: int = 2
    ) -> VariableInfo:
        """
        Constructs a VariableInfo object with automatic provenance detection.

        This helper determines the source of a variable based on whether
        a manual override was provided, simplifying Glass Box population.

        Parameters
        ----------
        symbol : str
            Mathematical symbol (e.g., "WACC", "g", "Rf").
        value : float
            The actual value used in the calculation.
        manual_value : Optional[float]
            The value provided by the user (None if not overridden).
        provider_value : Optional[float]
            The value from the data provider (e.g., Yahoo Finance).
        description : str, optional
            Pedagogical description of the variable.
        default_source : VariableSource, optional
            Source to use if no manual override is present (default is YAHOO_FINANCE).
        format_as_pct : bool, optional
            If True, formats the value as a percentage (default is False).
        decimals : int, optional
            Number of decimal places for formatting (default is 2).

        Returns
        -------
        VariableInfo
            Complete variable metadata for Glass Box traceability.
        """
        is_overridden = manual_value is not None

        if is_overridden:
            source = VariableSource.MANUAL_OVERRIDE
            original = provider_value
        elif provider_value is not None:
            source = default_source
            original = None
        else:
            source = VariableSource.DEFAULT
            original = None

        from src.utilities.formatting import format_smart_number
        formatted = f"{value:.{decimals}%}" if format_as_pct else format_smart_number(value)

        return VariableInfo(
            symbol=symbol,
            value=value,
            formatted_value=formatted,
            source=source,
            description=description,
            is_overridden=is_overridden,
            original_value=original
        )