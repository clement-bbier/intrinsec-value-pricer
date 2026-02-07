"""
src/core/diagnostics.py

DIAGNOSTIC TYPE SYSTEM AND STRUCTURED ERROR MANAGEMENT
======================================================
Role: Defines diagnostic events with pedagogical financial context.
Facilitates analyst understanding of model risks and technical failures.

Architecture: Type-Safe Registry Pattern.
Style: Numpy docstrings.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Dict

# You will need to ensure src.i18n is updated to English or keys are used correctly
# For this file, I am focusing on the structure and English context.


class SeverityLevel(Enum):
    """Classification of diagnostic impact on the valuation lifecycle."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DiagnosticDomain(Enum):
    """Categorization of the problem origin for audit routing."""
    CONFIG = "CONFIG"
    ENGINE = "ENGINE"
    DATA = "DATA"
    MODEL = "MODEL"
    PROVIDER = "PROVIDER"
    USER_INPUT = "USER_INPUT"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class FinancialContext:
    """
    Pedagogical financial context explaining parameter risk.

    Attributes
    ----------
    parameter_name : str
        The name of the financial parameter (e.g., "Market Beta").
    current_value : float
        The calculated or input value being diagnosed.
    typical_range : tuple[float, float]
        The normative bounds for this parameter (min, max).
    statistical_risk : str
        Explanation of why the current value is statistically or economically risky.
    recommendation : str
        Guidance for the analyst to remediate the risk.
    """
    parameter_name: str
    current_value: float
    typical_range: tuple[float, float]
    statistical_risk: str
    recommendation: str

    def to_human_readable(self) -> str:
        """
        Converts the context into a human-readable paragraph.

        Returns
        -------
        str
            The formatted pedagogical explanation.
        """
        range_str = f"{self.typical_range[0]:.2f} - {self.typical_range[1]:.2f}"
        return (
            f"The parameter '{self.parameter_name}' ({self.current_value:.2f}) "
            f"is outside the typical range ({range_str}). "
            f"{self.statistical_risk}. "
            f"Recommendation: {self.recommendation}."
        )


@dataclass(frozen=True)
class DiagnosticEvent:
    """
    Encapsulates a unique diagnostic event with full institutional lineage.

    Attributes
    ----------
    code : str
        Unique alphanumeric event code (e.g., "MODEL_G_DIVERGENCE").
    severity : SeverityLevel
        Visual and logical severity of the event.
    domain : DiagnosticDomain
        The architecture layer where the event occurred.
    message : str
        The primary analyst-facing message.
    technical_detail : str | None
        Raw error string or stack trace for development/debugging.
    remediation_hint : str | None
        Actionable advice to solve the issue.
    financial_context : FinancialContext | None
        Extended financial rationale for institutional auditing.
    """
    code: str
    severity: SeverityLevel
    domain: DiagnosticDomain
    message: str
    technical_detail: Optional[str] = None
    remediation_hint: Optional[str] = None
    financial_context: Optional[FinancialContext] = None

    @property
    def is_blocking(self) -> bool:
        """Determines if this event prevents the valuation from completing."""
        return self.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the event for transmission.

        Returns
        -------
        Dict[str, Any]
            JSON-serializable representation of the event.
        """
        result: Dict[str, Any] = {
            "code": self.code,
            "severity": self.severity.value,
            "domain": self.domain.value,
            "message": self.message,
            "is_blocking": self.is_blocking
        }

        if self.financial_context:
            result["financial_context"] = {
                "parameter": self.financial_context.parameter_name,
                "value": self.financial_context.current_value,
                "typical_range": list(self.financial_context.typical_range),
                "risk": self.financial_context.statistical_risk,
                "recommendation": self.financial_context.recommendation
            }

        return result


class DiagnosticRegistry:
    """
    Centralized catalog of standardized diagnostic events.
    Maps technical mathematical errors into institutional insights.
    """

    @staticmethod
    def model_g_divergence(g: float, wacc: float) -> DiagnosticEvent:
        """Gordon Shapiro convergence error (g >= WACC)."""
        return DiagnosticEvent(
            code="MODEL_G_DIVERGENCE",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.MODEL,
            message=f"Perpetual growth rate ({g:.2%}) exceeds or equals WACC ({wacc:.2%}).",
            remediation_hint="Reduce 'g' below 3% or use the Exit Multiple method.",
            financial_context=FinancialContext(
                parameter_name="Perpetual Growth Rate (g)",
                current_value=g,
                typical_range=(0.01, 0.03),
                statistical_risk=(
                    f"The Gordon model requires g < WACC. With g={g:.2%} and WACC={wacc:.2%}, "
                    "the formula TV = FCF/(WACC-g) produces a negative or infinite value"
                ),
                recommendation="Adjust 'g' to be at least 100bps lower than WACC."
            )
        )

    @staticmethod
    def model_mc_instability(valid_ratio: float, threshold: float) -> DiagnosticEvent:
        """Statistical instability during Monte Carlo draws."""
        return DiagnosticEvent(
            code="MODEL_MC_INSTABILITY",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.MODEL,
            message=f"Monte Carlo convergence failed. Valid Ratio: {valid_ratio:.0%} (Threshold: {threshold:.0%}).",
            remediation_hint="Reduce input volatilities or widen parameter bounds.",
            financial_context=FinancialContext(
                parameter_name="Valid Simulation Ratio",
                current_value=valid_ratio,
                typical_range=(0.90, 1.00),
                statistical_risk=(
                    f"Only {valid_ratio:.0%} of simulations converged. "
                    "Results are not statistically significant."
                ),
                recommendation="Check for aggressive growth assumptions interacting with high WACC volatility."
            )
        )

    @staticmethod
    def risk_excessive_growth(g: float) -> DiagnosticEvent:
        """Alert for unrealistic high-growth phase assumptions."""
        return DiagnosticEvent(
            code="RISK_EXCESSIVE_GROWTH",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.USER_INPUT,
            message=f"Explicit growth rate {g:.1%} appears excessively high.",
            remediation_hint="Verify against management guidance and consensus.",
            financial_context=FinancialContext(
                parameter_name="Flow Growth Rate",
                current_value=g,
                typical_range=(0.02, 0.08),
                statistical_risk=(
                    f"A growth rate of {g:.1%} is rarely sustainable long-term. "
                    "Only hyper-growth tech companies sustain >10% over 5 years."
                ),
                recommendation="Consider smoothing the growth ramp-down."
            )
        )

    @staticmethod
    def fcfe_negative_flow(val: float) -> DiagnosticEvent:
        """FCFE model error: cash burn detected."""
        return DiagnosticEvent(
            code="FCFE_NEGATIVE_FLOW",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.MODEL,
            message=f"Negative Free Cash Flow to Equity detected ({val:,.0f}).",
            remediation_hint="Switch to FCFF model or extend projection horizon.",
            financial_context=FinancialContext(
                parameter_name="Free Cash Flow to Equity",
                current_value=val,
                typical_range=(0.0, float('inf')),
                statistical_risk=(
                    f"Negative FCFE ({val:,.0f}) implies structural shareholder cash burn."
                ),
                recommendation="Use FCFF (Enterprise Value) for loss-making entities."
            )
        )

    @staticmethod
    def risk_missing_sbc_dilution(sector: str, rate: float) -> DiagnosticEvent:
        """Generates a warning when Stock-Based Compensation dilution is ignored."""
        return DiagnosticEvent(
            code="RISK_MISSING_SBC_DILUTION",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.MODEL,
            message=f"SBC Dilution ignored for sector: {sector}.",
            remediation_hint="Enable SBC Dilution adjustment in parameters.",
            financial_context=FinancialContext(
                parameter_name=f"Dilution Rate ({sector})",
                current_value=rate,
                typical_range=(0.01, 0.05),
                statistical_risk="Ignoring SBC in Tech/Growth leads to intrinsic value overestimation.",
                recommendation="Apply a dilution rate of 2-3% for this sector."
            )
        )